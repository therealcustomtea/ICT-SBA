from __future__ import annotations

import base64
import json
import ssl
import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from mastermind_api.auth import JWT_CLOCK_SKEW_SECONDS, SupabaseJWTVerifier
from mastermind_api.config import Settings
from mastermind_api.crypto import SecretCipher
from mastermind_api.database import prepare_asyncpg_connection
from mastermind_api.errors import APIError
from mastermind_api.logging import redact_sensitive
from mastermind_core import DomainError


def production_settings(**overrides: object) -> Settings:
    common: dict[str, object] = {
        "environment": "production",
        "allowed_origins": ("https://play.cipherboard.internal",),
        "supabase_url": "https://abcdefghijklmnop.supabase.co",
        "supabase_service_role_key": f"sb_secret_{'a' * 40}",
        "secret_encryption_keys": json.dumps({"v1": base64.b64encode(b"e" * 32).decode()}),
        "daily_hmac_keys": json.dumps({"v1": "d" * 32}),
        "public_identifier_hmac_key": "i" * 32,
        "database_url": (
            "postgresql+asyncpg://user:pass@database.cipherboard.internal/game"
            "?ssl=verify-full&sslrootcert=system"
        ),
        "redis_url": "rediss://cache.cipherboard.internal/0",
        "release": "sha-0123456789abcdef",
    }
    return Settings.model_validate(common | overrides)


def test_aes_gcm_round_trip_tamper_and_key_version() -> None:
    key = base64.b64encode(b"k" * 32).decode()
    cipher = SecretCipher.from_settings(
        Settings(
            environment="test",
            secret_encryption_keys=json.dumps({"v3": key}),
            secret_active_key_version="v3",
        )
    )
    encrypted = cipher.encrypt(("R", "B", "G", "Y"), context="game:one:rules_v1")
    assert cipher.decrypt(
        encrypted.ciphertext,
        encrypted.nonce,
        encrypted.key_version,
        context="game:one:rules_v1",
    ) == ("R", "B", "G", "Y")
    with pytest.raises(DomainError, match="cannot be recovered"):
        cipher.decrypt(
            encrypted.ciphertext[:-1] + bytes([encrypted.ciphertext[-1] ^ 1]),
            encrypted.nonce,
            encrypted.key_version,
            context="game:one:rules_v1",
        )
    with pytest.raises(DomainError, match="cannot be recovered"):
        cipher.decrypt(
            encrypted.ciphertext,
            encrypted.nonce,
            "missing",
            context="game:one:rules_v1",
        )


def test_daily_hmac_keyring_requires_and_selects_versioned_keys() -> None:
    settings = Settings(
        environment="test",
        daily_hmac_keys=json.dumps({"2026-q2": "a" * 32, "2026-q3": "b" * 32}),
        daily_hmac_active_key_version="2026-q3",
    )
    assert settings.daily_hmac_key_for_version("2026-q2") == b"a" * 32
    assert settings.daily_hmac_key_for_version("2026-q3") == b"b" * 32
    with pytest.raises(ValueError, match="unavailable"):
        settings.daily_hmac_key_for_version("retired")
    with pytest.raises(ValueError, match="absent"):
        Settings(
            environment="production",
            allowed_origins=("https://play.example.com",),
            supabase_url="https://project.supabase.co",
            supabase_service_role_key="server-only",
            secret_encryption_keys=json.dumps({"v1": base64.b64encode(b"e" * 32).decode()}),
            daily_hmac_keys=json.dumps({"old": "o" * 32}),
            daily_hmac_active_key_version="current",
            public_identifier_hmac_key="i" * 32,
            redis_url="rediss://cache.example.com/0",
        )


def test_secret_encryption_keyring_validates_every_version_at_startup() -> None:
    encoded_keys = {
        "v1": base64.b64encode(b"a" * 16).decode(),
        "v2": base64.b64encode(b"b" * 24).decode(),
        "v3": base64.b64encode(b"c" * 32).decode(),
    }
    settings = Settings(
        environment="test",
        secret_encryption_keys=json.dumps(encoded_keys),
        secret_active_key_version="v3",
    )
    assert settings.secret_encryption_keyring() == {
        "v1": b"a" * 16,
        "v2": b"b" * 24,
        "v3": b"c" * 32,
    }

    with pytest.raises(ValueError, match="keyring is malformed"):
        Settings(
            environment="test",
            secret_encryption_keys=json.dumps(encoded_keys | {"retired": "not-base64"}),
            secret_active_key_version="v3",
        )
    with pytest.raises(ValueError, match="16, 24, or 32 bytes"):
        Settings(
            environment="test",
            secret_encryption_keys=json.dumps(
                encoded_keys | {"retired": base64.b64encode(b"x" * 15).decode()}
            ),
            secret_active_key_version="v3",
        )
    with pytest.raises(ValueError, match="exactly 32 bytes"):
        production_settings(secret_encryption_keys=json.dumps(encoded_keys))


def test_production_configuration_rejects_local_services_and_mutable_release() -> None:
    with pytest.raises(ValueError, match="exact HTTPS origins"):
        production_settings(allowed_origins=("ftp://play.cipherboard.internal",))
    with pytest.raises(ValueError, match="Supabase URL must be an exact HTTPS origin"):
        production_settings(supabase_url="https://abcdefghijklmnop.supabase.co/auth/v1")
    with pytest.raises(ValueError, match="local development host"):
        production_settings(
            database_url=(
                "postgresql+asyncpg://user:pass@localhost/game?ssl=verify-full&sslrootcert=system"
            )
        )
    with pytest.raises(ValueError, match="ssl=verify-full"):
        production_settings(
            database_url="postgresql+asyncpg://user:pass@database.cipherboard.internal/game"
        )
    with pytest.raises(ValueError, match="ssl=verify-full"):
        production_settings(
            database_url=(
                "postgresql+asyncpg://user:pass@database.cipherboard.internal/game?ssl=require"
            )
        )
    with pytest.raises(ValueError, match="sslrootcert CA source"):
        production_settings(
            database_url=(
                "postgresql+asyncpg://user:pass@database.cipherboard.internal/game?ssl=verify-full"
            )
        )
    with pytest.raises(ValueError, match="absolute CA path"):
        production_settings(
            database_url=(
                "postgresql+asyncpg://user:pass@database.cipherboard.internal/game"
                "?ssl=verify-full&sslrootcert=provider-ca.pem"
            )
        )
    secure_database_url = (
        "postgresql+asyncpg://user:pass@database.cipherboard.internal/game"
        "?ssl=verify-full&sslrootcert=system"
    )
    assert production_settings(database_url=secure_database_url).database_url == secure_database_url
    with pytest.raises(ValueError, match="TLS rediss"):
        production_settings(
            database_url=secure_database_url,
            redis_url="redis://cache.example.com/0",
        )
    with pytest.raises(ValueError, match="immutable release"):
        production_settings(
            database_url=secure_database_url,
            release="latest",
        )


@pytest.mark.parametrize(
    "overrides",
    [
        {
            "database_url": (
                "postgresql+asyncpg://user:pass@database.example.invalid/game"
                "?ssl=verify-full&sslrootcert=system"
            )
        },
        {"redis_url": "rediss://cache.example.invalid/0"},
        {"supabase_url": "https://project.supabase.co"},
        {"allowed_origins": ("https://play.example.invalid",)},
        {"supabase_service_role_key": "ci-only-service-role-material-32-bytes"},
    ],
)
def test_production_configuration_rejects_known_placeholders(
    overrides: dict[str, object],
) -> None:
    with pytest.raises(ValueError, match="placeholder endpoint"):
        production_settings(**overrides)


def test_ci_placeholder_scope_is_explicit_and_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    placeholder_configuration: dict[str, object] = {
        "config_scope": "ci_validation",
        "database_url": (
            "postgresql+asyncpg://user:pass@database.example.invalid/game"
            "?ssl=verify-full&sslrootcert=system"
        ),
        "redis_url": "rediss://cache.example.invalid/0",
        "supabase_url": "https://auth.example.invalid",
        "supabase_service_role_key": "ci-only-service-role-material-32-bytes",
        "allowed_origins": ("https://play.example.invalid",),
        "release": f"ci-{'0' * 40}",
    }
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    with pytest.raises(ValueError, match="CI-only configuration validation"):
        production_settings(**placeholder_configuration)

    monkeypatch.setenv("CI", "true")
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    settings = production_settings(**placeholder_configuration)
    assert settings.config_scope == "ci_validation"
    with pytest.raises(ValueError, match="CI-only configuration validation"):
        production_settings(**(placeholder_configuration | {"release": "sha-production"}))


def test_verify_full_connection_builds_hostname_checking_ssl_context() -> None:
    database_url = (
        "postgresql+asyncpg://user:pass@database.cipherboard.internal/game"
        "?application_name=cipherboard&ssl=verify-full&sslrootcert=system"
    )
    connection_url, connect_args = prepare_asyncpg_connection(database_url)
    assert connection_url == (
        "postgresql+asyncpg://user:pass@database.cipherboard.internal/game"
        "?application_name=cipherboard"
    )
    context = connect_args["ssl"]
    assert isinstance(context, ssl.SSLContext)
    assert context.check_hostname is True
    assert context.verify_mode == ssl.CERT_REQUIRED


def test_verify_full_connection_loads_the_configured_provider_ca(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    loaded_ca_files: list[str | None] = []

    def create_context(*, cafile: str | None = None) -> ssl.SSLContext:
        loaded_ca_files.append(cafile)
        return ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)

    monkeypatch.setattr("mastermind_api.database.ssl.create_default_context", create_context)
    connection_url, connect_args = prepare_asyncpg_connection(
        "postgresql+asyncpg://user:pass@database.cipherboard.internal/game"
        "?ssl=verify-full&sslrootcert=%2Frun%2Fsecrets%2Fcipherboard%2Fpostgres-ca.pem"
    )
    assert loaded_ca_files == ["/run/secrets/cipherboard/postgres-ca.pem"]
    assert connection_url == ("postgresql+asyncpg://user:pass@database.cipherboard.internal/game")
    assert isinstance(connect_args["ssl"], ssl.SSLContext)


def test_jwt_verifies_signature_issuer_audience_expiry_and_subject() -> None:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    settings = Settings(environment="test", supabase_url="https://project.supabase.co")
    verifier = SupabaseJWTVerifier(settings)
    verifier.jwks.get_signing_key_from_jwt = lambda _token: SimpleNamespace(key=public_key)  # type: ignore[assignment,return-value]
    now = datetime.now(UTC)
    claims = {
        "iss": "https://project.supabase.co/auth/v1",
        "aud": "authenticated",
        "sub": str(uuid.uuid4()),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=5)).timestamp()),
        "is_anonymous": True,
        "app_metadata": {"role": "admin"},
    }
    token = jwt.encode(claims, private_key, algorithm="RS256", headers={"kid": "test"})
    authenticated = verifier.verify(token)
    assert authenticated.is_anonymous is True
    assert authenticated.user_id == uuid.UUID(str(claims["sub"]))
    assert not hasattr(authenticated, "app_role")
    within_clock_skew = jwt.encode(
        claims
        | {
            "iat": int((now + timedelta(seconds=2)).timestamp()),
            "exp": int((now + timedelta(minutes=5)).timestamp()),
        },
        private_key,
        algorithm="RS256",
        headers={"kid": "test"},
    )
    assert verifier.verify(within_clock_skew).is_anonymous is True

    beyond_clock_skew = jwt.encode(
        claims
        | {
            "iat": int((now + timedelta(seconds=JWT_CLOCK_SKEW_SECONDS + 5)).timestamp()),
            "exp": int((now + timedelta(minutes=5)).timestamp()),
        },
        private_key,
        algorithm="RS256",
        headers={"kid": "test"},
    )
    with pytest.raises(APIError) as immature_error:
        verifier.verify(beyond_clock_skew)
    assert immature_error.value.code == "INVALID_ACCESS_TOKEN"

    expired = jwt.encode(
        claims | {"exp": int((now - timedelta(seconds=JWT_CLOCK_SKEW_SECONDS + 5)).timestamp())},
        private_key,
        algorithm="RS256",
        headers={"kid": "test"},
    )
    with pytest.raises(APIError) as error:
        verifier.verify(expired)
    assert error.value.code == "INVALID_ACCESS_TOKEN"


def test_structured_log_redaction_is_recursive_and_catches_formatted_exceptions() -> None:
    redacted = redact_sensitive(
        None,
        "error",
        {
            "authorization": "Bearer sensitive",
            "nested": {"guess": ["R", "B"], "ciphertext": "bytes"},
            "exception": "SQL parameters included a private guess",
            "safe": "kept",
        },
    )
    assert redacted == {
        "authorization": "[REDACTED]",
        "nested": {"guess": "[REDACTED]", "ciphertext": "[REDACTED]"},
        "exception": "[REDACTED]",
        "safe": "kept",
    }
