from __future__ import annotations

import base64
import ipaddress
import json
import os
import re
from functools import lru_cache
from pathlib import PurePosixPath
from typing import Literal
from urllib.parse import parse_qs, urlparse

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def postgres_verify_full_root_certificate(value: str) -> str:
    """Return the explicit CA source for a verify-full asyncpg URL."""

    parsed = urlparse(value)
    query = parse_qs(parsed.query, keep_blank_values=True)
    if query.get("ssl") != ["verify-full"]:
        raise ValueError(
            "Production PostgreSQL must verify TLS with the URL option ssl=verify-full."
        )
    root_certificates = query.get("sslrootcert")
    if root_certificates is None or len(root_certificates) != 1:
        raise ValueError("Production PostgreSQL must configure exactly one sslrootcert CA source.")
    root_certificate = root_certificates[0]
    if root_certificate != "system" and not PurePosixPath(root_certificate).is_absolute():
        raise ValueError(
            "Production PostgreSQL sslrootcert must be 'system' or an absolute CA path."
        )
    return root_certificate


def validate_deployed_postgres_url(value: str, *, allow_placeholder: bool = False) -> None:
    """Require a remote asyncpg endpoint with an explicit verified CA source."""

    parsed = urlparse(value)
    if parsed.scheme != "postgresql+asyncpg":
        raise ValueError("Production requires PostgreSQL through the asyncpg driver.")
    if parsed.hostname in {None, "localhost", "127.0.0.1", "::1"}:
        raise ValueError("Production PostgreSQL cannot use a local development host.")
    postgres_verify_full_root_certificate(value)
    if not allow_placeholder and _uses_placeholder_endpoint(value):
        raise ValueError("Production PostgreSQL cannot use a placeholder endpoint.")


_PLACEHOLDER_HOSTS = {
    "example.com",
    "example.net",
    "example.org",
    "localhost",
    "project.supabase.co",
    "test.supabase.co",
}
_PLACEHOLDER_HOST_SUFFIXES = (
    ".example",
    ".example.com",
    ".example.net",
    ".example.org",
    ".invalid",
    ".localhost",
    ".test",
)
_PLACEHOLDER_SECRET_MARKERS = (
    "change-me",
    "changeme",
    "ci-only",
    "dummy",
    "example",
    "placeholder",
    "replace-me",
    "server-only",
    "service-role-material",
)


def _uses_placeholder_endpoint(value: str) -> bool:
    hostname = (urlparse(value).hostname or "").lower().rstrip(".")
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        address = None
    return bool(
        (address and (address.is_loopback or address.is_unspecified))
        or hostname in _PLACEHOLDER_HOSTS
        or hostname.endswith(_PLACEHOLDER_HOST_SUFFIXES)
    )


def _is_exact_https_origin(value: str) -> bool:
    parsed = urlparse(value)
    return bool(
        parsed.scheme == "https"
        and parsed.hostname
        and parsed.username is None
        and parsed.password is None
        and parsed.path in {"", "/"}
        and not parsed.params
        and not parsed.query
        and not parsed.fragment
    )


def _uses_placeholder_service_key(value: str) -> bool:
    normalized = value.strip().lower()
    return any(marker in normalized for marker in _PLACEHOLDER_SECRET_MARKERS) or (
        bool(normalized) and len(set(normalized)) == 1
    )


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="MASTERMIND_",
        case_sensitive=False,
        extra="ignore",
    )

    environment: Literal["development", "test", "staging", "production"] = "development"
    product_name: str = Field(default="Cipherboard", min_length=1, max_length=64)
    database_url: str = "postgresql+asyncpg://mastermind:mastermind@localhost:5432/mastermind"
    redis_url: str | None = "redis://localhost:6379/0"
    allowed_origins: tuple[str, ...] = ("http://localhost:3000",)
    supabase_url: str = ""
    supabase_internal_url: str = ""
    supabase_service_role_key: str = ""
    supabase_jwt_audience: str = "authenticated"
    secret_encryption_keys: str = ""
    secret_active_key_version: str = "v1"
    daily_hmac_key: str = ""
    daily_hmac_keys: str = ""
    daily_hmac_active_key_version: str = "v1"
    public_identifier_hmac_key: str = ""
    trusted_proxy_ips: tuple[str, ...] = ()
    admin_recent_auth_seconds: int = Field(default=900, ge=60, le=3600)
    request_body_limit_bytes: int = Field(default=65_536, ge=1024, le=1_048_576)
    request_timeout_seconds: int = Field(default=15, ge=1, le=120)
    rate_limit_per_minute: int = Field(default=120, ge=10, le=10_000)
    room_tie_window_ms: int = Field(default=250, ge=50, le=2000)
    websocket_frame_limit_bytes: int = Field(default=4096, ge=1024, le=4096)
    websocket_user_connection_limit: int = Field(default=3, ge=1, le=20)
    websocket_ip_connection_limit: int = Field(default=20, ge=1, le=200)
    websocket_connection_ttl_seconds: int = Field(default=90, ge=60, le=300)
    config_scope: Literal["application", "migration", "ci_validation"] = "application"
    release: str = "development"
    log_level: str = "INFO"
    metrics_enabled: bool = True
    error_reporting_url: str = ""
    error_reporting_token: str = ""
    feature_daily: bool = True
    feature_leaderboards: bool = True
    feature_friend_challenges: bool = True
    feature_multiplayer: bool = True
    feature_achievements: bool = True
    feature_account_registration: bool = True
    feature_analytics: bool = False

    @field_validator("database_url")
    @classmethod
    def normalize_database_scheme(cls, value: str) -> str:
        if value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql+asyncpg://", 1)
        if value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+asyncpg://", 1)
        return value

    @model_validator(mode="after")
    def validate_production(self) -> Settings:
        if bool(self.error_reporting_url) != bool(self.error_reporting_token):
            raise ValueError(
                "MASTERMIND_ERROR_REPORTING_URL and MASTERMIND_ERROR_REPORTING_TOKEN "
                "must be configured together."
            )
        if self.error_reporting_url and not self.error_reporting_url.startswith("https://"):
            raise ValueError("The error-reporting endpoint must use HTTPS.")
        if self.secret_encryption_keys:
            encryption_keys = self.secret_encryption_keyring()
            if self.environment in {"staging", "production"} and any(
                len(key) != 32 for key in encryption_keys.values()
            ):
                raise ValueError("Every deployed AES-GCM key must decode to exactly 32 bytes.")
        if self.config_scope == "migration":
            if self.environment not in {"staging", "production"}:
                raise ValueError(
                    "Migration-only configuration is restricted to deployed environments."
                )
            return self
        ci_validation = self.config_scope == "ci_validation"
        if ci_validation and (
            self.environment != "production"
            or os.getenv("CI", "").lower() != "true"
            or os.getenv("GITHUB_ACTIONS", "").lower() != "true"
            or re.fullmatch(r"ci-[0-9a-f]{40}", self.release) is None
        ):
            raise ValueError(
                "CI-only configuration validation requires GitHub Actions production validation "
                "and a full ci-* commit release."
            )
        if self.environment in {"staging", "production"}:
            missing = [
                name
                for name, value in (
                    ("MASTERMIND_SUPABASE_URL", self.supabase_url),
                    ("MASTERMIND_SUPABASE_SERVICE_ROLE_KEY", self.supabase_service_role_key),
                    ("MASTERMIND_SECRET_ENCRYPTION_KEYS", self.secret_encryption_keys),
                    (
                        "MASTERMIND_DAILY_HMAC_KEYS or MASTERMIND_DAILY_HMAC_KEY",
                        self.daily_hmac_keys or self.daily_hmac_key,
                    ),
                    ("MASTERMIND_PUBLIC_IDENTIFIER_HMAC_KEY", self.public_identifier_hmac_key),
                    ("MASTERMIND_REDIS_URL", self.redis_url),
                )
                if not value
            ]
            if missing:
                raise ValueError(f"Missing required production settings: {', '.join(missing)}")
            if any(not _is_exact_https_origin(origin) for origin in self.allowed_origins):
                raise ValueError("Production CORS origins must be exact HTTPS origins.")
            if self.product_name.strip() != self.product_name:
                raise ValueError("The product name cannot have surrounding whitespace.")
            if not _is_exact_https_origin(self.supabase_url):
                raise ValueError("The production Supabase URL must be an exact HTTPS origin.")
            if self.supabase_internal_url and not _is_exact_https_origin(
                self.supabase_internal_url
            ):
                raise ValueError(
                    "The production internal Supabase URL must be an exact HTTPS origin."
                )
            self.daily_hmac_keyring()
            validate_deployed_postgres_url(
                self.database_url,
                allow_placeholder=ci_validation,
            )
            redis_host = urlparse(self.redis_url or "").hostname
            if not self.redis_url or not self.redis_url.startswith("rediss://"):
                raise ValueError("Production Redis must use a TLS rediss URL.")
            if redis_host in {None, "localhost", "127.0.0.1", "::1"}:
                raise ValueError("Production Redis cannot use a local development host.")
            if len(self.supabase_service_role_key) < 32:
                raise ValueError("The production Supabase service credential is malformed.")
            if not ci_validation and (
                any(
                    _uses_placeholder_endpoint(endpoint)
                    for endpoint in (
                        self.database_url,
                        self.redis_url or "",
                        self.supabase_url,
                        self.supabase_internal_url,
                        self.error_reporting_url,
                        *self.allowed_origins,
                    )
                    if endpoint
                )
                or _uses_placeholder_service_key(self.supabase_service_role_key)
            ):
                raise ValueError(
                    "Deployed configuration cannot contain placeholder endpoints or credentials."
                )
            if self.release in {"", "development", "latest"}:
                raise ValueError("Production requires an immutable release identifier.")
            if len(self.public_identifier_hmac_key.encode()) < 32:
                raise ValueError("The public identifier HMAC key must contain at least 32 bytes.")
        return self

    @property
    def supabase_server_url(self) -> str:
        """Return the server-reachable provider URL without changing the JWT issuer."""

        return self.supabase_internal_url or self.supabase_url

    def secret_encryption_keyring(self) -> dict[str, bytes]:
        """Decode and validate every configured AES-GCM key version."""

        try:
            encoded_keys = json.loads(self.secret_encryption_keys)
        except json.JSONDecodeError as exc:
            raise ValueError("The secret encryption keyring is malformed.") from exc
        if not isinstance(encoded_keys, dict) or not encoded_keys:
            raise ValueError("The secret encryption keyring is malformed.")
        keys: dict[str, bytes] = {}
        try:
            for version, encoded_key in encoded_keys.items():
                if not isinstance(version, str) or not version or not isinstance(encoded_key, str):
                    raise ValueError
                keys[version] = base64.b64decode(encoded_key, validate=True)
        except (TypeError, ValueError) as exc:
            raise ValueError("The secret encryption keyring is malformed.") from exc
        if self.secret_active_key_version not in keys:
            raise ValueError("The active AES-GCM key version is absent from the keyring.")
        if any(len(key) not in {16, 24, 32} for key in keys.values()):
            raise ValueError("Every AES-GCM key must decode to 16, 24, or 32 bytes.")
        return keys

    def daily_hmac_keyring(self) -> dict[str, bytes]:
        """Return the versioned daily derivation key ring.

        ``daily_hmac_key`` remains a compatibility input for local environments and
        maps to the configured active version. Deployed environments should use the
        JSON key ring so an old version can overlap a rotation safely.
        """

        if self.daily_hmac_keys:
            try:
                decoded = json.loads(self.daily_hmac_keys)
            except json.JSONDecodeError as exc:
                raise ValueError("The daily HMAC keyring is malformed.") from exc
            if not isinstance(decoded, dict) or not decoded:
                raise ValueError("The daily HMAC keyring is malformed.")
            keys = {
                str(version): value.encode()
                for version, value in decoded.items()
                if isinstance(version, str) and isinstance(value, str)
            }
            if len(keys) != len(decoded):
                raise ValueError("The daily HMAC keyring is malformed.")
        elif self.daily_hmac_key:
            keys = {self.daily_hmac_active_key_version: self.daily_hmac_key.encode()}
        else:
            keys = {}
        if self.daily_hmac_active_key_version not in keys:
            raise ValueError("The active daily HMAC key version is absent from the keyring.")
        if any(len(key) < 32 for key in keys.values()):
            raise ValueError("Every daily HMAC key must contain at least 32 bytes.")
        return keys

    def daily_hmac_key_for_version(self, version: str) -> bytes:
        try:
            return self.daily_hmac_keyring()[version]
        except KeyError as exc:
            raise ValueError(f"Daily HMAC key version {version!r} is unavailable.") from exc


@lru_cache
def get_settings() -> Settings:
    return Settings()
