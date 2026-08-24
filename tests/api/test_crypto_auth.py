# Defers type-annotation evaluation to support modern hints safely.
from __future__ import annotations

# Imports `base64` so the module can use that dependency.
import base64

# Imports `json` so the module can use that dependency.
import json

# Imports `ssl` so the module can use that dependency.
import ssl

# Imports `uuid` so the module can use that dependency.
import uuid

# Imports selected names from `datetime` for use in this module.
from datetime import UTC, datetime, timedelta

# Imports selected names from `types` for use in this module.
from types import SimpleNamespace

# Imports `jwt` so the module can use that dependency.
import jwt

# Imports `pytest` so the module can use that dependency.
import pytest

# Imports selected names from `cryptography.hazmat.primitives.asymmetric` for use in this module.
from cryptography.hazmat.primitives.asymmetric import rsa

# Imports selected names from `mastermind_api.auth` for use in this module.
from mastermind_api.auth import JWT_CLOCK_SKEW_SECONDS, SupabaseJWTVerifier

# Imports selected names from `mastermind_api.config` for use in this module.
from mastermind_api.config import Settings

# Imports selected names from `mastermind_api.crypto` for use in this module.
from mastermind_api.crypto import SecretCipher

# Imports selected names from `mastermind_api.database` for use in this module.
from mastermind_api.database import prepare_asyncpg_connection

# Imports selected names from `mastermind_api.errors` for use in this module.
from mastermind_api.errors import APIError

# Imports selected names from `mastermind_api.logging` for use in this module.
from mastermind_api.logging import redact_sensitive

# Imports selected names from `mastermind_core` for use in this module.
from mastermind_core import DomainError


# Defines the `production_settings` callable and its typed interface.
def production_settings(**overrides: object) -> Settings:
    # Computes and stores `common` for subsequent operations.
    common: dict[str, object] = {
        # Associates the `environment` key with its value.
        "environment": "production",
        # Associates the `allowed_origins` key with its value.
        "allowed_origins": ("https://play.cipherboard.internal",),
        # Associates the `supabase_url` key with its value.
        "supabase_url": "https://abcdefghijklmnop.supabase.co",
        # Associates the `supabase_service_role_key` key with its value.
        "supabase_service_role_key": f"sb_secret_{'a' * 40}",
        # Associates the `secret_encryption_keys` key with its value.
        "secret_encryption_keys": json.dumps({"v1": base64.b64encode(b"e" * 32).decode()}),
        # Associates the `daily_hmac_keys` key with its value.
        "daily_hmac_keys": json.dumps({"v1": "d" * 32}),
        # Associates the `public_identifier_hmac_key` key with its value.
        "public_identifier_hmac_key": "i" * 32,
        # Associates the `database_url` key with its value.
        "database_url": (
            # Executes this statement as the next step in the surrounding logic.
            "postgresql+asyncpg://user:pass@database.cipherboard.internal/game"
            # Executes this statement as the next step in the surrounding logic.
            "?ssl=verify-full&sslrootcert=system"
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Associates the `redis_url` key with its value.
        "redis_url": "rediss://cache.cipherboard.internal/0",
        # Associates the `release` key with its value.
        "release": "sha-0123456789abcdef",
        # Closes the multiline call, declaration, or collection started above.
    }
    # Returns this result to the caller and ends the current function.
    return Settings.model_validate(common | overrides)


# Defines the `test_aes_gcm_round_trip_tamper_and_key_version` callable and its typed interface.
def test_aes_gcm_round_trip_tamper_and_key_version() -> None:
    # Computes and stores `key` for subsequent operations.
    key = base64.b64encode(b"k" * 32).decode()
    # Computes and stores `cipher` for subsequent operations.
    cipher = SecretCipher.from_settings(
        # Calls `Settings` with the supplied values.
        Settings(
            # Provides the `environment` parameter or keyword argument.
            environment="test",
            # Provides the `secret_encryption_keys` parameter or keyword argument.
            secret_encryption_keys=json.dumps({"v3": key}),
            # Provides the `secret_active_key_version` parameter or keyword argument.
            secret_active_key_version="v3",
            # Closes the multiline call, declaration, or collection started above.
        )
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `encrypted` for subsequent operations.
    encrypted = cipher.encrypt(("R", "B", "G", "Y"), context="game:one:rules_v1")
    # Asserts this invariant so an unexpected test state fails immediately.
    assert cipher.decrypt(
        # Supplies this item to the surrounding call or collection.
        encrypted.ciphertext,
        # Supplies this item to the surrounding call or collection.
        encrypted.nonce,
        # Supplies this item to the surrounding call or collection.
        encrypted.key_version,
        # Provides the `context` parameter or keyword argument.
        context="game:one:rules_v1",
        # Executes this statement as the next step in the surrounding logic.
    ) == ("R", "B", "G", "Y")
    # Acquires this managed resource and guarantees cleanup afterward.
    with pytest.raises(DomainError, match="cannot be recovered"):
        # Calls `cipher.decrypt` with the supplied values.
        cipher.decrypt(
            # Supplies this item to the surrounding call or collection.
            encrypted.ciphertext[:-1] + bytes([encrypted.ciphertext[-1] ^ 1]),
            # Supplies this item to the surrounding call or collection.
            encrypted.nonce,
            # Supplies this item to the surrounding call or collection.
            encrypted.key_version,
            # Provides the `context` parameter or keyword argument.
            context="game:one:rules_v1",
            # Closes the multiline call, declaration, or collection started above.
        )
    # Acquires this managed resource and guarantees cleanup afterward.
    with pytest.raises(DomainError, match="cannot be recovered"):
        # Calls `cipher.decrypt` with the supplied values.
        cipher.decrypt(
            # Supplies this item to the surrounding call or collection.
            encrypted.ciphertext,
            # Supplies this item to the surrounding call or collection.
            encrypted.nonce,
            # Supplies this item to the surrounding call or collection.
            "missing",
            # Provides the `context` parameter or keyword argument.
            context="game:one:rules_v1",
            # Closes the multiline call, declaration, or collection started above.
        )


# Defines the `test_daily_hmac_keyring_requires_and_selects_versioned_keys` callable and its typed
# interface.
def test_daily_hmac_keyring_requires_and_selects_versioned_keys() -> None:
    # Computes and stores `settings` for subsequent operations.
    settings = Settings(
        # Provides the `environment` parameter or keyword argument.
        environment="test",
        # Provides the `daily_hmac_keys` parameter or keyword argument.
        daily_hmac_keys=json.dumps({"2026-q2": "a" * 32, "2026-q3": "b" * 32}),
        # Provides the `daily_hmac_active_key_version` parameter or keyword argument.
        daily_hmac_active_key_version="2026-q3",
        # Closes the multiline call, declaration, or collection started above.
    )
    # Asserts this invariant so an unexpected test state fails immediately.
    assert settings.daily_hmac_key_for_version("2026-q2") == b"a" * 32
    # Asserts this invariant so an unexpected test state fails immediately.
    assert settings.daily_hmac_key_for_version("2026-q3") == b"b" * 32
    # Acquires this managed resource and guarantees cleanup afterward.
    with pytest.raises(ValueError, match="unavailable"):
        # Calls `settings.daily_hmac_key_for_version` with the supplied values.
        settings.daily_hmac_key_for_version("retired")
    # Acquires this managed resource and guarantees cleanup afterward.
    with pytest.raises(ValueError, match="absent"):
        # Calls `Settings` with the supplied values.
        Settings(
            # Provides the `environment` parameter or keyword argument.
            environment="production",
            # Provides the `allowed_origins` parameter or keyword argument.
            allowed_origins=("https://play.example.com",),
            # Provides the `supabase_url` parameter or keyword argument.
            supabase_url="https://project.supabase.co",
            # Provides the `supabase_service_role_key` parameter or keyword argument.
            supabase_service_role_key="server-only",
            # Provides the `secret_encryption_keys` parameter or keyword argument.
            secret_encryption_keys=json.dumps({"v1": base64.b64encode(b"e" * 32).decode()}),
            # Provides the `daily_hmac_keys` parameter or keyword argument.
            daily_hmac_keys=json.dumps({"old": "o" * 32}),
            # Provides the `daily_hmac_active_key_version` parameter or keyword argument.
            daily_hmac_active_key_version="current",
            # Provides the `public_identifier_hmac_key` parameter or keyword argument.
            public_identifier_hmac_key="i" * 32,
            # Provides the `redis_url` parameter or keyword argument.
            redis_url="rediss://cache.example.com/0",
            # Closes the multiline call, declaration, or collection started above.
        )


# Defines the `test_secret_encryption_keyring_validates_every_version_at_startup` callable and its
# typed interface.
def test_secret_encryption_keyring_validates_every_version_at_startup() -> None:
    # Computes and stores `encoded_keys` for subsequent operations.
    encoded_keys = {
        # Associates the `v1` key with its value.
        "v1": base64.b64encode(b"a" * 16).decode(),
        # Associates the `v2` key with its value.
        "v2": base64.b64encode(b"b" * 24).decode(),
        # Associates the `v3` key with its value.
        "v3": base64.b64encode(b"c" * 32).decode(),
        # Closes the multiline call, declaration, or collection started above.
    }
    # Computes and stores `settings` for subsequent operations.
    settings = Settings(
        # Provides the `environment` parameter or keyword argument.
        environment="test",
        # Provides the `secret_encryption_keys` parameter or keyword argument.
        secret_encryption_keys=json.dumps(encoded_keys),
        # Provides the `secret_active_key_version` parameter or keyword argument.
        secret_active_key_version="v3",
        # Closes the multiline call, declaration, or collection started above.
    )
    # Asserts this invariant so an unexpected test state fails immediately.
    assert settings.secret_encryption_keyring() == {
        # Associates the `v1` key with its value.
        "v1": b"a" * 16,
        # Associates the `v2` key with its value.
        "v2": b"b" * 24,
        # Associates the `v3` key with its value.
        "v3": b"c" * 32,
        # Closes the multiline call, declaration, or collection started above.
    }

    # Acquires this managed resource and guarantees cleanup afterward.
    with pytest.raises(ValueError, match="keyring is malformed"):
        # Calls `Settings` with the supplied values.
        Settings(
            # Provides the `environment` parameter or keyword argument.
            environment="test",
            # Provides the `secret_encryption_keys` parameter or keyword argument.
            secret_encryption_keys=json.dumps(encoded_keys | {"retired": "not-base64"}),
            # Provides the `secret_active_key_version` parameter or keyword argument.
            secret_active_key_version="v3",
            # Closes the multiline call, declaration, or collection started above.
        )
    # Acquires this managed resource and guarantees cleanup afterward.
    with pytest.raises(ValueError, match="16, 24, or 32 bytes"):
        # Calls `Settings` with the supplied values.
        Settings(
            # Provides the `environment` parameter or keyword argument.
            environment="test",
            # Computes and stores `secret_encryption_keys` for subsequent operations.
            secret_encryption_keys=json.dumps(
                # Executes this statement as the next step in the surrounding logic.
                encoded_keys | {"retired": base64.b64encode(b"x" * 15).decode()}
                # Closes the multiline call, declaration, or collection started above.
            ),
            # Provides the `secret_active_key_version` parameter or keyword argument.
            secret_active_key_version="v3",
            # Closes the multiline call, declaration, or collection started above.
        )
    # Acquires this managed resource and guarantees cleanup afterward.
    with pytest.raises(ValueError, match="exactly 32 bytes"):
        # Calls `production_settings` with the supplied values.
        production_settings(secret_encryption_keys=json.dumps(encoded_keys))


# Defines the `test_production_configuration_rejects_local_services_and_mutable_release` callable
# and its typed interface.
def test_production_configuration_rejects_local_services_and_mutable_release() -> None:
    # Acquires this managed resource and guarantees cleanup afterward.
    with pytest.raises(ValueError, match="exact HTTPS origins"):
        # Calls `production_settings` with the supplied values.
        production_settings(allowed_origins=("ftp://play.cipherboard.internal",))
    # Acquires this managed resource and guarantees cleanup afterward.
    with pytest.raises(ValueError, match="Supabase URL must be an exact HTTPS origin"):
        # Calls `production_settings` with the supplied values.
        production_settings(supabase_url="https://abcdefghijklmnop.supabase.co/auth/v1")
    # Acquires this managed resource and guarantees cleanup afterward.
    with pytest.raises(ValueError, match="local development host"):
        # Calls `production_settings` with the supplied values.
        production_settings(
            # Computes and stores `database_url` for subsequent operations.
            database_url=(
                # Executes this statement as the next step in the surrounding logic.
                "postgresql+asyncpg://user:pass@localhost/game?ssl=verify-full&sslrootcert=system"
                # Closes the multiline call, declaration, or collection started above.
            )
            # Closes the multiline call, declaration, or collection started above.
        )
    # Acquires this managed resource and guarantees cleanup afterward.
    with pytest.raises(ValueError, match="ssl=verify-full"):
        # Calls `production_settings` with the supplied values.
        production_settings(
            # Computes and stores `database_url` for subsequent operations.
            database_url="postgresql+asyncpg://user:pass@database.cipherboard.internal/game"
            # Closes the multiline call, declaration, or collection started above.
        )
    # Acquires this managed resource and guarantees cleanup afterward.
    with pytest.raises(ValueError, match="ssl=verify-full"):
        # Calls `production_settings` with the supplied values.
        production_settings(
            # Computes and stores `database_url` for subsequent operations.
            database_url=(
                # Executes this statement as the next step in the surrounding logic.
                "postgresql+asyncpg://user:pass@database.cipherboard.internal/game?ssl=require"
                # Closes the multiline call, declaration, or collection started above.
            )
            # Closes the multiline call, declaration, or collection started above.
        )
    # Acquires this managed resource and guarantees cleanup afterward.
    with pytest.raises(ValueError, match="sslrootcert CA source"):
        # Calls `production_settings` with the supplied values.
        production_settings(
            # Computes and stores `database_url` for subsequent operations.
            database_url=(
                # Executes this statement as the next step in the surrounding logic.
                "postgresql+asyncpg://user:pass@database.cipherboard.internal/game?ssl=verify-full"
                # Closes the multiline call, declaration, or collection started above.
            )
            # Closes the multiline call, declaration, or collection started above.
        )
    # Acquires this managed resource and guarantees cleanup afterward.
    with pytest.raises(ValueError, match="absolute CA path"):
        # Calls `production_settings` with the supplied values.
        production_settings(
            # Computes and stores `database_url` for subsequent operations.
            database_url=(
                # Executes this statement as the next step in the surrounding logic.
                "postgresql+asyncpg://user:pass@database.cipherboard.internal/game"
                # Executes this statement as the next step in the surrounding logic.
                "?ssl=verify-full&sslrootcert=provider-ca.pem"
                # Closes the multiline call, declaration, or collection started above.
            )
            # Closes the multiline call, declaration, or collection started above.
        )
    # Computes and stores `secure_database_url` for subsequent operations.
    secure_database_url = (
        # Executes this statement as the next step in the surrounding logic.
        "postgresql+asyncpg://user:pass@database.cipherboard.internal/game"
        # Executes this statement as the next step in the surrounding logic.
        "?ssl=verify-full&sslrootcert=system"
        # Closes the multiline call, declaration, or collection started above.
    )
    # Asserts this invariant so an unexpected test state fails immediately.
    assert production_settings(database_url=secure_database_url).database_url == secure_database_url
    # Acquires this managed resource and guarantees cleanup afterward.
    with pytest.raises(ValueError, match="TLS rediss"):
        # Calls `production_settings` with the supplied values.
        production_settings(
            # Provides the `database_url` parameter or keyword argument.
            database_url=secure_database_url,
            # Provides the `redis_url` parameter or keyword argument.
            redis_url="redis://cache.example.com/0",
            # Closes the multiline call, declaration, or collection started above.
        )
    # Acquires this managed resource and guarantees cleanup afterward.
    with pytest.raises(ValueError, match="immutable release"):
        # Calls `production_settings` with the supplied values.
        production_settings(
            # Provides the `database_url` parameter or keyword argument.
            database_url=secure_database_url,
            # Provides the `release` parameter or keyword argument.
            release="latest",
            # Closes the multiline call, declaration, or collection started above.
        )


# Applies `@pytest.mark.parametrize(` to configure the declaration immediately below.
@pytest.mark.parametrize(
    # Supplies this item to the surrounding call or collection.
    "overrides",
    # Begins the nested block or multiline expression completed below.
    [
        # Begins the nested block or multiline expression completed below.
        {
            # Associates the `database_url` key with its value.
            "database_url": (
                # Executes this statement as the next step in the surrounding logic.
                "postgresql+asyncpg://user:pass@database.example.invalid/game"
                # Executes this statement as the next step in the surrounding logic.
                "?ssl=verify-full&sslrootcert=system"
                # Closes the multiline call, declaration, or collection started above.
            )
            # Closes the multiline call, declaration, or collection started above.
        },
        # Supplies this item to the surrounding call or collection.
        {"redis_url": "rediss://cache.example.invalid/0"},
        # Supplies this item to the surrounding call or collection.
        {"supabase_url": "https://project.supabase.co"},
        # Supplies this item to the surrounding call or collection.
        {"allowed_origins": ("https://play.example.invalid",)},
        # Supplies this item to the surrounding call or collection.
        {"supabase_service_role_key": "ci-only-service-role-material-32-bytes"},
        # Closes the multiline call, declaration, or collection started above.
    ],
    # Closes the multiline call, declaration, or collection started above.
)
# Defines the `test_production_configuration_rejects_known_placeholders` callable and its typed
# interface.
def test_production_configuration_rejects_known_placeholders(
    # Declares the typed `overrides` data field.
    overrides: dict[str, object],
    # Completes the signature and declares the callable return type.
) -> None:
    # Acquires this managed resource and guarantees cleanup afterward.
    with pytest.raises(ValueError, match="placeholder endpoint"):
        # Calls `production_settings` with the supplied values.
        production_settings(**overrides)


# Defines the `test_ci_placeholder_scope_is_explicit_and_fail_closed` callable and its typed
# interface.
def test_ci_placeholder_scope_is_explicit_and_fail_closed(
    # Declares the typed `monkeypatch` data field.
    monkeypatch: pytest.MonkeyPatch,
    # Completes the signature and declares the callable return type.
) -> None:
    # Computes and stores `placeholder_configuration` for subsequent operations.
    placeholder_configuration: dict[str, object] = {
        # Associates the `config_scope` key with its value.
        "config_scope": "ci_validation",
        # Associates the `database_url` key with its value.
        "database_url": (
            # Executes this statement as the next step in the surrounding logic.
            "postgresql+asyncpg://user:pass@database.example.invalid/game"
            # Executes this statement as the next step in the surrounding logic.
            "?ssl=verify-full&sslrootcert=system"
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Associates the `redis_url` key with its value.
        "redis_url": "rediss://cache.example.invalid/0",
        # Associates the `supabase_url` key with its value.
        "supabase_url": "https://auth.example.invalid",
        # Associates the `supabase_service_role_key` key with its value.
        "supabase_service_role_key": "ci-only-service-role-material-32-bytes",
        # Associates the `allowed_origins` key with its value.
        "allowed_origins": ("https://play.example.invalid",),
        # Associates the `release` key with its value.
        "release": f"ci-{'0' * 40}",
        # Closes the multiline call, declaration, or collection started above.
    }
    # Configures this test double for the scenario being verified.
    monkeypatch.delenv("CI", raising=False)
    # Configures this test double for the scenario being verified.
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    # Acquires this managed resource and guarantees cleanup afterward.
    with pytest.raises(ValueError, match="CI-only configuration validation"):
        # Calls `production_settings` with the supplied values.
        production_settings(**placeholder_configuration)

    # Configures this test double for the scenario being verified.
    monkeypatch.setenv("CI", "true")
    # Configures this test double for the scenario being verified.
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    # Computes and stores `settings` for subsequent operations.
    settings = production_settings(**placeholder_configuration)
    # Asserts this invariant so an unexpected test state fails immediately.
    assert settings.config_scope == "ci_validation"
    # Acquires this managed resource and guarantees cleanup afterward.
    with pytest.raises(ValueError, match="CI-only configuration validation"):
        # Calls `production_settings` with the supplied values.
        production_settings(**(placeholder_configuration | {"release": "sha-production"}))


# Defines the `test_verify_full_connection_builds_hostname_checking_ssl_context` callable and its
# typed interface.
def test_verify_full_connection_builds_hostname_checking_ssl_context() -> None:
    # Computes and stores `database_url` for subsequent operations.
    database_url = (
        # Executes this statement as the next step in the surrounding logic.
        "postgresql+asyncpg://user:pass@database.cipherboard.internal/game"
        # Executes this statement as the next step in the surrounding logic.
        "?application_name=cipherboard&ssl=verify-full&sslrootcert=system"
        # Closes the multiline call, declaration, or collection started above.
    )
    # Executes this statement as the next step in the surrounding logic.
    connection_url, connect_args = prepare_asyncpg_connection(database_url)
    # Asserts this invariant so an unexpected test state fails immediately.
    assert connection_url == (
        # Executes this statement as the next step in the surrounding logic.
        "postgresql+asyncpg://user:pass@database.cipherboard.internal/game"
        # Executes this statement as the next step in the surrounding logic.
        "?application_name=cipherboard"
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `context` for subsequent operations.
    context = connect_args["ssl"]
    # Asserts this invariant so an unexpected test state fails immediately.
    assert isinstance(context, ssl.SSLContext)
    # Asserts this invariant so an unexpected test state fails immediately.
    assert context.check_hostname is True
    # Asserts this invariant so an unexpected test state fails immediately.
    assert context.verify_mode == ssl.CERT_REQUIRED


# Defines the `test_verify_full_connection_loads_the_configured_provider_ca` callable and its typed
# interface.
def test_verify_full_connection_loads_the_configured_provider_ca(
    # Declares the typed `monkeypatch` data field.
    monkeypatch: pytest.MonkeyPatch,
    # Completes the signature and declares the callable return type.
) -> None:
    # Computes and stores `loaded_ca_files` for subsequent operations.
    loaded_ca_files: list[str | None] = []

    # Defines the `create_context` callable and its typed interface.
    def create_context(*, cafile: str | None = None) -> ssl.SSLContext:
        # Calls `loaded_ca_files.append` with the supplied values.
        loaded_ca_files.append(cafile)
        # Returns this result to the caller and ends the current function.
        return ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)

    # Configures this test double for the scenario being verified.
    monkeypatch.setattr("mastermind_api.database.ssl.create_default_context", create_context)
    # Begins the nested block or multiline expression completed below.
    connection_url, connect_args = prepare_asyncpg_connection(
        # Executes this statement as the next step in the surrounding logic.
        "postgresql+asyncpg://user:pass@database.cipherboard.internal/game"
        # Executes this statement as the next step in the surrounding logic.
        "?ssl=verify-full&sslrootcert=%2Frun%2Fsecrets%2Fcipherboard%2Fpostgres-ca.pem"
        # Closes the multiline call, declaration, or collection started above.
    )
    # Asserts this invariant so an unexpected test state fails immediately.
    assert loaded_ca_files == ["/run/secrets/cipherboard/postgres-ca.pem"]
    # Asserts this invariant so an unexpected test state fails immediately.
    assert connection_url == ("postgresql+asyncpg://user:pass@database.cipherboard.internal/game")
    # Asserts this invariant so an unexpected test state fails immediately.
    assert isinstance(connect_args["ssl"], ssl.SSLContext)


# Defines the `test_jwt_verifies_signature_issuer_audience_expiry_and_subject` callable and its
# typed interface.
def test_jwt_verifies_signature_issuer_audience_expiry_and_subject() -> None:
    # Computes and stores `private_key` for subsequent operations.
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    # Computes and stores `public_key` for subsequent operations.
    public_key = private_key.public_key()
    # Computes and stores `settings` for subsequent operations.
    settings = Settings(environment="test", supabase_url="https://project.supabase.co")
    # Computes and stores `verifier` for subsequent operations.
    verifier = SupabaseJWTVerifier(settings)
    # Computes and stores `verifier.jwks.get_signing_key_from_jwt` for subsequent operations.
    verifier.jwks.get_signing_key_from_jwt = lambda _token: SimpleNamespace(key=public_key)  # type: ignore[assignment,return-value]
    # Computes and stores `now` for subsequent operations.
    now = datetime.now(UTC)
    # Computes and stores `claims` for subsequent operations.
    claims = {
        # Associates the `iss` key with its value.
        "iss": "https://project.supabase.co/auth/v1",
        # Associates the `aud` key with its value.
        "aud": "authenticated",
        # Associates the `sub` key with its value.
        "sub": str(uuid.uuid4()),
        # Associates the `iat` key with its value.
        "iat": int(now.timestamp()),
        # Associates the `exp` key with its value.
        "exp": int((now + timedelta(minutes=5)).timestamp()),
        # Associates the `is_anonymous` key with its value.
        "is_anonymous": True,
        # Associates the `app_metadata` key with its value.
        "app_metadata": {"role": "admin"},
        # Closes the multiline call, declaration, or collection started above.
    }
    # Computes and stores `token` for subsequent operations.
    token = jwt.encode(claims, private_key, algorithm="RS256", headers={"kid": "test"})
    # Computes and stores `authenticated` for subsequent operations.
    authenticated = verifier.verify(token)
    # Asserts this invariant so an unexpected test state fails immediately.
    assert authenticated.is_anonymous is True
    # Asserts this invariant so an unexpected test state fails immediately.
    assert authenticated.user_id == uuid.UUID(str(claims["sub"]))
    # Asserts this invariant so an unexpected test state fails immediately.
    assert not hasattr(authenticated, "app_role")
    # Computes and stores `within_clock_skew` for subsequent operations.
    within_clock_skew = jwt.encode(
        # Executes this statement as the next step in the surrounding logic.
        claims
        # Begins the nested block or multiline expression completed below.
        | {
            # Associates the `iat` key with its value.
            "iat": int((now + timedelta(seconds=2)).timestamp()),
            # Associates the `exp` key with its value.
            "exp": int((now + timedelta(minutes=5)).timestamp()),
            # Closes the multiline call, declaration, or collection started above.
        },
        # Supplies this item to the surrounding call or collection.
        private_key,
        # Provides the `algorithm` parameter or keyword argument.
        algorithm="RS256",
        # Provides the `headers` parameter or keyword argument.
        headers={"kid": "test"},
        # Closes the multiline call, declaration, or collection started above.
    )
    # Asserts this invariant so an unexpected test state fails immediately.
    assert verifier.verify(within_clock_skew).is_anonymous is True

    # Computes and stores `beyond_clock_skew` for subsequent operations.
    beyond_clock_skew = jwt.encode(
        # Executes this statement as the next step in the surrounding logic.
        claims
        # Begins the nested block or multiline expression completed below.
        | {
            # Associates the `iat` key with its value.
            "iat": int((now + timedelta(seconds=JWT_CLOCK_SKEW_SECONDS + 5)).timestamp()),
            # Associates the `exp` key with its value.
            "exp": int((now + timedelta(minutes=5)).timestamp()),
            # Closes the multiline call, declaration, or collection started above.
        },
        # Supplies this item to the surrounding call or collection.
        private_key,
        # Provides the `algorithm` parameter or keyword argument.
        algorithm="RS256",
        # Provides the `headers` parameter or keyword argument.
        headers={"kid": "test"},
        # Closes the multiline call, declaration, or collection started above.
    )
    # Acquires this managed resource and guarantees cleanup afterward.
    with pytest.raises(APIError) as immature_error:
        # Calls `verifier.verify` with the supplied values.
        verifier.verify(beyond_clock_skew)
    # Asserts this invariant so an unexpected test state fails immediately.
    assert immature_error.value.code == "INVALID_ACCESS_TOKEN"

    # Computes and stores `expired` for subsequent operations.
    expired = jwt.encode(
        # Supplies this item to the surrounding call or collection.
        claims | {"exp": int((now - timedelta(seconds=JWT_CLOCK_SKEW_SECONDS + 5)).timestamp())},
        # Supplies this item to the surrounding call or collection.
        private_key,
        # Provides the `algorithm` parameter or keyword argument.
        algorithm="RS256",
        # Provides the `headers` parameter or keyword argument.
        headers={"kid": "test"},
        # Closes the multiline call, declaration, or collection started above.
    )
    # Acquires this managed resource and guarantees cleanup afterward.
    with pytest.raises(APIError) as error:
        # Calls `verifier.verify` with the supplied values.
        verifier.verify(expired)
    # Asserts this invariant so an unexpected test state fails immediately.
    assert error.value.code == "INVALID_ACCESS_TOKEN"


# Defines the `test_structured_log_redaction_is_recursive_and_catches_formatted_exceptions` callable
# and its typed interface.
def test_structured_log_redaction_is_recursive_and_catches_formatted_exceptions() -> None:
    # Computes and stores `redacted` for subsequent operations.
    redacted = redact_sensitive(
        # Supplies this item to the surrounding call or collection.
        None,
        # Supplies this item to the surrounding call or collection.
        "error",
        # Begins the nested block or multiline expression completed below.
        {
            # Associates the `authorization` key with its value.
            "authorization": "Bearer sensitive",
            # Associates the `nested` key with its value.
            "nested": {"guess": ["R", "B"], "ciphertext": "bytes"},
            # Associates the `exception` key with its value.
            "exception": "SQL parameters included a private guess",
            # Associates the `safe` key with its value.
            "safe": "kept",
            # Closes the multiline call, declaration, or collection started above.
        },
        # Closes the multiline call, declaration, or collection started above.
    )
    # Asserts this invariant so an unexpected test state fails immediately.
    assert redacted == {
        # Associates the `authorization` key with its value.
        "authorization": "[REDACTED]",
        # Associates the `nested` key with its value.
        "nested": {"guess": "[REDACTED]", "ciphertext": "[REDACTED]"},
        # Associates the `exception` key with its value.
        "exception": "[REDACTED]",
        # Associates the `safe` key with its value.
        "safe": "kept",
        # Closes the multiline call, declaration, or collection started above.
    }
