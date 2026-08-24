# Defers type-annotation evaluation to support modern hints safely.
from __future__ import annotations

# Imports `base64` so the module can use that dependency.
import base64

# Imports `ipaddress` so the module can use that dependency.
import ipaddress

# Imports `json` so the module can use that dependency.
import json

# Imports `os` so the module can use that dependency.
import os

# Imports `re` so the module can use that dependency.
import re

# Imports selected names from `functools` for use in this module.
from functools import lru_cache

# Imports selected names from `pathlib` for use in this module.
from pathlib import PurePosixPath

# Imports selected names from `typing` for use in this module.
from typing import Literal

# Imports selected names from `urllib.parse` for use in this module.
from urllib.parse import parse_qs, urlparse

# Imports selected names from `pydantic` for use in this module.
from pydantic import Field, field_validator, model_validator

# Imports selected names from `pydantic_settings` for use in this module.
from pydantic_settings import BaseSettings, SettingsConfigDict


# Defines the `postgres_verify_full_root_certificate` callable and its typed interface.
def postgres_verify_full_root_certificate(value: str) -> str:
    # Documents the purpose or contract of this module, class, or function.
    """Return the explicit CA source for a verify-full asyncpg URL."""

    # Computes and stores `parsed` for subsequent operations.
    parsed = urlparse(value)
    # Computes and stores `query` for subsequent operations.
    query = parse_qs(parsed.query, keep_blank_values=True)
    # Checks this condition before executing the nested branch.
    if query.get("ssl") != ["verify-full"]:
        # Raises this exception to report an invalid or failed operation.
        raise ValueError(
            # Executes this statement as the next step in the surrounding logic.
            "Production PostgreSQL must verify TLS with the URL option ssl=verify-full."
            # Closes the multiline call, declaration, or collection started above.
        )
    # Computes and stores `root_certificates` for subsequent operations.
    root_certificates = query.get("sslrootcert")
    # Checks this condition before executing the nested branch.
    if root_certificates is None or len(root_certificates) != 1:
        # Raises this exception to report an invalid or failed operation.
        raise ValueError("Production PostgreSQL must configure exactly one sslrootcert CA source.")
    # Computes and stores `root_certificate` for subsequent operations.
    root_certificate = root_certificates[0]
    # Checks this condition before executing the nested branch.
    if root_certificate != "system" and not PurePosixPath(root_certificate).is_absolute():
        # Raises this exception to report an invalid or failed operation.
        raise ValueError(
            # Executes this statement as the next step in the surrounding logic.
            "Production PostgreSQL sslrootcert must be 'system' or an absolute CA path."
            # Closes the multiline call, declaration, or collection started above.
        )
    # Returns this result to the caller and ends the current function.
    return root_certificate


# Defines the `validate_deployed_postgres_url` callable and its typed interface.
def validate_deployed_postgres_url(value: str, *, allow_placeholder: bool = False) -> None:
    # Documents the purpose or contract of this module, class, or function.
    """Require a remote asyncpg endpoint with an explicit verified CA source."""

    # Computes and stores `parsed` for subsequent operations.
    parsed = urlparse(value)
    # Checks this condition before executing the nested branch.
    if parsed.scheme != "postgresql+asyncpg":
        # Raises this exception to report an invalid or failed operation.
        raise ValueError("Production requires PostgreSQL through the asyncpg driver.")
    # Checks this condition before executing the nested branch.
    if parsed.hostname in {None, "localhost", "127.0.0.1", "::1"}:
        # Raises this exception to report an invalid or failed operation.
        raise ValueError("Production PostgreSQL cannot use a local development host.")
    # Calls `postgres_verify_full_root_certificate` with the supplied values.
    postgres_verify_full_root_certificate(value)
    # Checks this condition before executing the nested branch.
    if not allow_placeholder and _uses_placeholder_endpoint(value):
        # Raises this exception to report an invalid or failed operation.
        raise ValueError("Production PostgreSQL cannot use a placeholder endpoint.")


# Computes and stores `_PLACEHOLDER_HOSTS` for subsequent operations.
_PLACEHOLDER_HOSTS = {
    # Supplies this item to the surrounding call or collection.
    "example.com",
    # Supplies this item to the surrounding call or collection.
    "example.net",
    # Supplies this item to the surrounding call or collection.
    "example.org",
    # Supplies this item to the surrounding call or collection.
    "localhost",
    # Supplies this item to the surrounding call or collection.
    "project.supabase.co",
    # Supplies this item to the surrounding call or collection.
    "test.supabase.co",
    # Closes the multiline call, declaration, or collection started above.
}
# Computes and stores `_PLACEHOLDER_HOST_SUFFIXES` for subsequent operations.
_PLACEHOLDER_HOST_SUFFIXES = (
    # Supplies this item to the surrounding call or collection.
    ".example",
    # Supplies this item to the surrounding call or collection.
    ".example.com",
    # Supplies this item to the surrounding call or collection.
    ".example.net",
    # Supplies this item to the surrounding call or collection.
    ".example.org",
    # Supplies this item to the surrounding call or collection.
    ".invalid",
    # Supplies this item to the surrounding call or collection.
    ".localhost",
    # Supplies this item to the surrounding call or collection.
    ".test",
    # Closes the multiline call, declaration, or collection started above.
)
# Computes and stores `_PLACEHOLDER_SECRET_MARKERS` for subsequent operations.
_PLACEHOLDER_SECRET_MARKERS = (
    # Supplies this item to the surrounding call or collection.
    "change-me",
    # Supplies this item to the surrounding call or collection.
    "changeme",
    # Supplies this item to the surrounding call or collection.
    "ci-only",
    # Supplies this item to the surrounding call or collection.
    "dummy",
    # Supplies this item to the surrounding call or collection.
    "example",
    # Supplies this item to the surrounding call or collection.
    "placeholder",
    # Supplies this item to the surrounding call or collection.
    "replace-me",
    # Supplies this item to the surrounding call or collection.
    "server-only",
    # Supplies this item to the surrounding call or collection.
    "service-role-material",
    # Closes the multiline call, declaration, or collection started above.
)


# Defines the `_uses_placeholder_endpoint` callable and its typed interface.
def _uses_placeholder_endpoint(value: str) -> bool:
    # Computes and stores `hostname` for subsequent operations.
    hostname = (urlparse(value).hostname or "").lower().rstrip(".")
    # Starts a protected operation whose expected failures are handled below.
    try:
        # Computes and stores `address` for subsequent operations.
        address = ipaddress.ip_address(hostname)
    # Handles the listed exception so failure remains controlled.
    except ValueError:
        # Computes and stores `address` for subsequent operations.
        address = None
    # Returns this result to the caller and ends the current function.
    return bool(
        # Executes this statement as the next step in the surrounding logic.
        (address and (address.is_loopback or address.is_unspecified))
        # Executes this statement as the next step in the surrounding logic.
        or hostname in _PLACEHOLDER_HOSTS
        # Executes this statement as the next step in the surrounding logic.
        or hostname.endswith(_PLACEHOLDER_HOST_SUFFIXES)
        # Closes the multiline call, declaration, or collection started above.
    )


# Defines the `_is_exact_https_origin` callable and its typed interface.
def _is_exact_https_origin(value: str) -> bool:
    # Computes and stores `parsed` for subsequent operations.
    parsed = urlparse(value)
    # Returns this result to the caller and ends the current function.
    return bool(
        # Executes this statement as the next step in the surrounding logic.
        parsed.scheme == "https"
        # Executes this statement as the next step in the surrounding logic.
        and parsed.hostname
        # Executes this statement as the next step in the surrounding logic.
        and parsed.username is None
        # Executes this statement as the next step in the surrounding logic.
        and parsed.password is None
        # Executes this statement as the next step in the surrounding logic.
        and parsed.path in {"", "/"}
        # Executes this statement as the next step in the surrounding logic.
        and not parsed.params
        # Executes this statement as the next step in the surrounding logic.
        and not parsed.query
        # Executes this statement as the next step in the surrounding logic.
        and not parsed.fragment
        # Closes the multiline call, declaration, or collection started above.
    )


# Defines the `_uses_placeholder_service_key` callable and its typed interface.
def _uses_placeholder_service_key(value: str) -> bool:
    # Computes and stores `normalized` for subsequent operations.
    normalized = value.strip().lower()
    # Returns this result to the caller and ends the current function.
    return any(marker in normalized for marker in _PLACEHOLDER_SECRET_MARKERS) or (
        # Calls `bool` with the supplied values.
        bool(normalized) and len(set(normalized)) == 1
        # Closes the multiline call, declaration, or collection started above.
    )


# Defines the `Settings` class and its related behavior.
class Settings(BaseSettings):
    # Computes and stores `model_config` for subsequent operations.
    model_config = SettingsConfigDict(
        # Provides the `env_file` parameter or keyword argument.
        env_file=".env",
        # Provides the `env_prefix` parameter or keyword argument.
        env_prefix="MASTERMIND_",
        # Provides the `case_sensitive` parameter or keyword argument.
        case_sensitive=False,
        # Provides the `extra` parameter or keyword argument.
        extra="ignore",
        # Closes the multiline call, declaration, or collection started above.
    )

    # Computes and stores `environment` for subsequent operations.
    environment: Literal["development", "test", "staging", "production"] = "development"
    # Computes and stores `product_name` for subsequent operations.
    product_name: str = Field(default="Cipherboard", min_length=1, max_length=64)
    # Computes and stores `database_url` for subsequent operations.
    database_url: str = "postgresql+asyncpg://mastermind:mastermind@localhost:5432/mastermind"
    # Computes and stores `redis_url` for subsequent operations.
    redis_url: str | None = "redis://localhost:6379/0"
    # Computes and stores `allowed_origins` for subsequent operations.
    allowed_origins: tuple[str, ...] = ("http://localhost:3000",)
    # Computes and stores `supabase_url` for subsequent operations.
    supabase_url: str = ""
    # Computes and stores `supabase_service_role_key` for subsequent operations.
    supabase_service_role_key: str = ""
    # Computes and stores `supabase_jwt_audience` for subsequent operations.
    supabase_jwt_audience: str = "authenticated"
    # Computes and stores `secret_encryption_keys` for subsequent operations.
    secret_encryption_keys: str = ""
    # Computes and stores `secret_active_key_version` for subsequent operations.
    secret_active_key_version: str = "v1"
    # Computes and stores `daily_hmac_key` for subsequent operations.
    daily_hmac_key: str = ""
    # Computes and stores `daily_hmac_keys` for subsequent operations.
    daily_hmac_keys: str = ""
    # Computes and stores `daily_hmac_active_key_version` for subsequent operations.
    daily_hmac_active_key_version: str = "v1"
    # Computes and stores `public_identifier_hmac_key` for subsequent operations.
    public_identifier_hmac_key: str = ""
    # Computes and stores `trusted_proxy_ips` for subsequent operations.
    trusted_proxy_ips: tuple[str, ...] = ()
    # Computes and stores `admin_recent_auth_seconds` for subsequent operations.
    admin_recent_auth_seconds: int = Field(default=900, ge=60, le=3600)
    # Computes and stores `request_body_limit_bytes` for subsequent operations.
    request_body_limit_bytes: int = Field(default=65_536, ge=1024, le=1_048_576)
    # Computes and stores `request_timeout_seconds` for subsequent operations.
    request_timeout_seconds: int = Field(default=15, ge=1, le=120)
    # Computes and stores `rate_limit_per_minute` for subsequent operations.
    rate_limit_per_minute: int = Field(default=120, ge=10, le=10_000)
    # Computes and stores `room_tie_window_ms` for subsequent operations.
    room_tie_window_ms: int = Field(default=250, ge=50, le=2000)
    # Computes and stores `websocket_frame_limit_bytes` for subsequent operations.
    websocket_frame_limit_bytes: int = Field(default=4096, ge=1024, le=4096)
    # Computes and stores `websocket_user_connection_limit` for subsequent operations.
    websocket_user_connection_limit: int = Field(default=3, ge=1, le=20)
    # Computes and stores `websocket_ip_connection_limit` for subsequent operations.
    websocket_ip_connection_limit: int = Field(default=20, ge=1, le=200)
    # Computes and stores `websocket_connection_ttl_seconds` for subsequent operations.
    websocket_connection_ttl_seconds: int = Field(default=90, ge=60, le=300)
    # Computes and stores `config_scope` for subsequent operations.
    config_scope: Literal["application", "migration", "ci_validation"] = "application"
    # Computes and stores `release` for subsequent operations.
    release: str = "development"
    # Computes and stores `log_level` for subsequent operations.
    log_level: str = "INFO"
    # Computes and stores `metrics_enabled` for subsequent operations.
    metrics_enabled: bool = True
    # Computes and stores `error_reporting_url` for subsequent operations.
    error_reporting_url: str = ""
    # Computes and stores `error_reporting_token` for subsequent operations.
    error_reporting_token: str = ""
    # Computes and stores `feature_daily` for subsequent operations.
    feature_daily: bool = True
    # Computes and stores `feature_leaderboards` for subsequent operations.
    feature_leaderboards: bool = True
    # Computes and stores `feature_friend_challenges` for subsequent operations.
    feature_friend_challenges: bool = True
    # Computes and stores `feature_multiplayer` for subsequent operations.
    feature_multiplayer: bool = True
    # Computes and stores `feature_achievements` for subsequent operations.
    feature_achievements: bool = True
    # Computes and stores `feature_account_registration` for subsequent operations.
    feature_account_registration: bool = True
    # Computes and stores `feature_analytics` for subsequent operations.
    feature_analytics: bool = False

    # Applies `@field_validator("database_url")` to configure the declaration immediately below.
    @field_validator("database_url")
    # Applies `@classmethod` to configure the declaration immediately below.
    @classmethod
    # Defines the `normalize_database_scheme` callable and its typed interface.
    def normalize_database_scheme(cls, value: str) -> str:
        # Checks this condition before executing the nested branch.
        if value.startswith("postgres://"):
            # Returns this result to the caller and ends the current function.
            return value.replace("postgres://", "postgresql+asyncpg://", 1)
        # Checks this condition before executing the nested branch.
        if value.startswith("postgresql://"):
            # Returns this result to the caller and ends the current function.
            return value.replace("postgresql://", "postgresql+asyncpg://", 1)
        # Returns this result to the caller and ends the current function.
        return value

    # Applies `@model_validator(mode="after")` to configure the declaration immediately below.
    @model_validator(mode="after")
    # Defines the `validate_production` callable and its typed interface.
    def validate_production(self) -> Settings:
        # Checks this condition before executing the nested branch.
        if bool(self.error_reporting_url) != bool(self.error_reporting_token):
            # Raises this exception to report an invalid or failed operation.
            raise ValueError(
                # Executes this statement as the next step in the surrounding logic.
                "MASTERMIND_ERROR_REPORTING_URL and MASTERMIND_ERROR_REPORTING_TOKEN "
                # Executes this statement as the next step in the surrounding logic.
                "must be configured together."
                # Closes the multiline call, declaration, or collection started above.
            )
        # Checks this condition before executing the nested branch.
        if self.error_reporting_url and not self.error_reporting_url.startswith("https://"):
            # Raises this exception to report an invalid or failed operation.
            raise ValueError("The error-reporting endpoint must use HTTPS.")
        # Checks this condition before executing the nested branch.
        if self.secret_encryption_keys:
            # Computes and stores `encryption_keys` for subsequent operations.
            encryption_keys = self.secret_encryption_keyring()
            # Checks this condition before executing the nested branch.
            if self.environment in {"staging", "production"} and any(
                # Calls `len` with the supplied values.
                len(key) != 32
                # Continues the surrounding expression or operation.
                for key in encryption_keys.values()
                # Begins the nested block or multiline expression completed below.
            ):
                # Raises this exception to report an invalid or failed operation.
                raise ValueError("Every deployed AES-GCM key must decode to exactly 32 bytes.")
        # Checks this condition before executing the nested branch.
        if self.config_scope == "migration":
            # Checks this condition before executing the nested branch.
            if self.environment not in {"staging", "production"}:
                # Raises this exception to report an invalid or failed operation.
                raise ValueError(
                    # Executes this statement as the next step in the surrounding logic.
                    "Migration-only configuration is restricted to deployed environments."
                    # Closes the multiline call, declaration, or collection started above.
                )
            # Returns this result to the caller and ends the current function.
            return self
        # Executes this statement as the next step in the surrounding logic.
        ci_validation = self.config_scope == "ci_validation"
        # Checks this condition before executing the nested branch.
        if ci_validation and (
            # Executes this statement as the next step in the surrounding logic.
            self.environment != "production"
            # Executes this statement as the next step in the surrounding logic.
            or os.getenv("CI", "").lower() != "true"
            # Executes this statement as the next step in the surrounding logic.
            or os.getenv("GITHUB_ACTIONS", "").lower() != "true"
            # Executes this statement as the next step in the surrounding logic.
            or re.fullmatch(r"ci-[0-9a-f]{40}", self.release) is None
            # Begins the nested block or multiline expression completed below.
        ):
            # Raises this exception to report an invalid or failed operation.
            raise ValueError(
                # Executes this statement as the next step in the surrounding logic.
                "CI-only configuration validation requires GitHub Actions production validation "
                # Executes this statement as the next step in the surrounding logic.
                "and a full ci-* commit release."
                # Closes the multiline call, declaration, or collection started above.
            )
        # Checks this condition before executing the nested branch.
        if self.environment in {"staging", "production"}:
            # Computes and stores `missing` for subsequent operations.
            missing = [
                # Executes this statement as the next step in the surrounding logic.
                name
                # Iterates through the supplied values for the nested operation.
                for name, value in (
                    # Supplies this item to the surrounding call or collection.
                    ("MASTERMIND_SUPABASE_URL", self.supabase_url),
                    # Supplies this item to the surrounding call or collection.
                    ("MASTERMIND_SUPABASE_SERVICE_ROLE_KEY", self.supabase_service_role_key),
                    # Supplies this item to the surrounding call or collection.
                    ("MASTERMIND_SECRET_ENCRYPTION_KEYS", self.secret_encryption_keys),
                    # Begins the nested block or multiline expression completed below.
                    (
                        # Supplies this item to the surrounding call or collection.
                        "MASTERMIND_DAILY_HMAC_KEYS or MASTERMIND_DAILY_HMAC_KEY",
                        # Supplies this item to the surrounding call or collection.
                        self.daily_hmac_keys or self.daily_hmac_key,
                        # Closes the multiline call, declaration, or collection started above.
                    ),
                    # Supplies this item to the surrounding call or collection.
                    ("MASTERMIND_PUBLIC_IDENTIFIER_HMAC_KEY", self.public_identifier_hmac_key),
                    # Supplies this item to the surrounding call or collection.
                    ("MASTERMIND_REDIS_URL", self.redis_url),
                    # Closes the multiline call, declaration, or collection started above.
                )
                # Checks this condition before executing the nested branch.
                if not value
                # Closes the multiline call, declaration, or collection started above.
            ]
            # Checks this condition before executing the nested branch.
            if missing:
                # Raises this exception to report an invalid or failed operation.
                raise ValueError(f"Missing required production settings: {', '.join(missing)}")
            # Checks this condition before executing the nested branch.
            if any(not _is_exact_https_origin(origin) for origin in self.allowed_origins):
                # Raises this exception to report an invalid or failed operation.
                raise ValueError("Production CORS origins must be exact HTTPS origins.")
            # Checks this condition before executing the nested branch.
            if self.product_name.strip() != self.product_name:
                # Raises this exception to report an invalid or failed operation.
                raise ValueError("The product name cannot have surrounding whitespace.")
            # Checks this condition before executing the nested branch.
            if not _is_exact_https_origin(self.supabase_url):
                # Raises this exception to report an invalid or failed operation.
                raise ValueError("The production Supabase URL must be an exact HTTPS origin.")
            # Calls `self.daily_hmac_keyring` with the supplied values.
            self.daily_hmac_keyring()
            # Calls `validate_deployed_postgres_url` with the supplied values.
            validate_deployed_postgres_url(
                # Supplies this item to the surrounding call or collection.
                self.database_url,
                # Provides the `allow_placeholder` parameter or keyword argument.
                allow_placeholder=ci_validation,
                # Closes the multiline call, declaration, or collection started above.
            )
            # Computes and stores `redis_host` for subsequent operations.
            redis_host = urlparse(self.redis_url or "").hostname
            # Checks this condition before executing the nested branch.
            if not self.redis_url or not self.redis_url.startswith("rediss://"):
                # Raises this exception to report an invalid or failed operation.
                raise ValueError("Production Redis must use a TLS rediss URL.")
            # Checks this condition before executing the nested branch.
            if redis_host in {None, "localhost", "127.0.0.1", "::1"}:
                # Raises this exception to report an invalid or failed operation.
                raise ValueError("Production Redis cannot use a local development host.")
            # Checks this condition before executing the nested branch.
            if len(self.supabase_service_role_key) < 32:
                # Raises this exception to report an invalid or failed operation.
                raise ValueError("The production Supabase service credential is malformed.")
            # Checks this condition before executing the nested branch.
            if not ci_validation and (
                # Calls `any` with the supplied values.
                any(
                    # Calls `_uses_placeholder_endpoint` with the supplied values.
                    _uses_placeholder_endpoint(endpoint)
                    # Iterates through the supplied values for the nested operation.
                    for endpoint in (
                        # Supplies this item to the surrounding call or collection.
                        self.database_url,
                        # Supplies this item to the surrounding call or collection.
                        self.redis_url or "",
                        # Supplies this item to the surrounding call or collection.
                        self.supabase_url,
                        # Supplies this item to the surrounding call or collection.
                        self.error_reporting_url,
                        # Supplies this item to the surrounding call or collection.
                        *self.allowed_origins,
                        # Closes the multiline call, declaration, or collection started above.
                    )
                    # Checks this condition before executing the nested branch.
                    if endpoint
                    # Closes the multiline call, declaration, or collection started above.
                )
                # Executes this statement as the next step in the surrounding logic.
                or _uses_placeholder_service_key(self.supabase_service_role_key)
                # Begins the nested block or multiline expression completed below.
            ):
                # Raises this exception to report an invalid or failed operation.
                raise ValueError(
                    # Executes this statement as the next step in the surrounding logic.
                    "Deployed configuration cannot contain placeholder endpoints or credentials."
                    # Closes the multiline call, declaration, or collection started above.
                )
            # Checks this condition before executing the nested branch.
            if self.release in {"", "development", "latest"}:
                # Raises this exception to report an invalid or failed operation.
                raise ValueError("Production requires an immutable release identifier.")
            # Checks this condition before executing the nested branch.
            if len(self.public_identifier_hmac_key.encode()) < 32:
                # Raises this exception to report an invalid or failed operation.
                raise ValueError("The public identifier HMAC key must contain at least 32 bytes.")
        # Returns this result to the caller and ends the current function.
        return self

    # Defines the `secret_encryption_keyring` callable and its typed interface.
    def secret_encryption_keyring(self) -> dict[str, bytes]:
        # Documents the purpose or contract of this module, class, or function.
        """Decode and validate every configured AES-GCM key version."""

        # Starts a protected operation whose expected failures are handled below.
        try:
            # Computes and stores `encoded_keys` for subsequent operations.
            encoded_keys = json.loads(self.secret_encryption_keys)
        # Handles the listed exception so failure remains controlled.
        except json.JSONDecodeError as exc:
            # Raises this exception to report an invalid or failed operation.
            raise ValueError("The secret encryption keyring is malformed.") from exc
        # Checks this condition before executing the nested branch.
        if not isinstance(encoded_keys, dict) or not encoded_keys:
            # Raises this exception to report an invalid or failed operation.
            raise ValueError("The secret encryption keyring is malformed.")
        # Computes and stores `keys` for subsequent operations.
        keys: dict[str, bytes] = {}
        # Starts a protected operation whose expected failures are handled below.
        try:
            # Iterates through the supplied values for the nested operation.
            for version, encoded_key in encoded_keys.items():
                # Checks this condition before executing the nested branch.
                if not isinstance(version, str) or not version or not isinstance(encoded_key, str):
                    # Raises this exception to report an invalid or failed operation.
                    raise ValueError
                # Executes this statement as the next step in the surrounding logic.
                keys[version] = base64.b64decode(encoded_key, validate=True)
        # Handles the listed exception so failure remains controlled.
        except (TypeError, ValueError) as exc:
            # Raises this exception to report an invalid or failed operation.
            raise ValueError("The secret encryption keyring is malformed.") from exc
        # Checks this condition before executing the nested branch.
        if self.secret_active_key_version not in keys:
            # Raises this exception to report an invalid or failed operation.
            raise ValueError("The active AES-GCM key version is absent from the keyring.")
        # Checks this condition before executing the nested branch.
        if any(len(key) not in {16, 24, 32} for key in keys.values()):
            # Raises this exception to report an invalid or failed operation.
            raise ValueError("Every AES-GCM key must decode to 16, 24, or 32 bytes.")
        # Returns this result to the caller and ends the current function.
        return keys

    # Defines the `daily_hmac_keyring` callable and its typed interface.
    def daily_hmac_keyring(self) -> dict[str, bytes]:
        # Documents the purpose or contract of this module, class, or function.
        """Return the versioned daily derivation key ring.

        ``daily_hmac_key`` remains a compatibility input for local environments and
        maps to the configured active version. Deployed environments should use the
        JSON key ring so an old version can overlap a rotation safely.
        """

        # Checks this condition before executing the nested branch.
        if self.daily_hmac_keys:
            # Starts a protected operation whose expected failures are handled below.
            try:
                # Computes and stores `decoded` for subsequent operations.
                decoded = json.loads(self.daily_hmac_keys)
            # Handles the listed exception so failure remains controlled.
            except json.JSONDecodeError as exc:
                # Raises this exception to report an invalid or failed operation.
                raise ValueError("The daily HMAC keyring is malformed.") from exc
            # Checks this condition before executing the nested branch.
            if not isinstance(decoded, dict) or not decoded:
                # Raises this exception to report an invalid or failed operation.
                raise ValueError("The daily HMAC keyring is malformed.")
            # Computes and stores `keys` for subsequent operations.
            keys = {
                # Calls `str` with the supplied values.
                str(version): value.encode()
                # Iterates through the supplied values for the nested operation.
                for version, value in decoded.items()
                # Checks this condition before executing the nested branch.
                if isinstance(version, str) and isinstance(value, str)
                # Closes the multiline call, declaration, or collection started above.
            }
            # Checks this condition before executing the nested branch.
            if len(keys) != len(decoded):
                # Raises this exception to report an invalid or failed operation.
                raise ValueError("The daily HMAC keyring is malformed.")
        # Checks this alternative when previous conditions were false.
        elif self.daily_hmac_key:
            # Computes and stores `keys` for subsequent operations.
            keys = {self.daily_hmac_active_key_version: self.daily_hmac_key.encode()}
        # Handles the remaining case not matched by earlier branches.
        else:
            # Computes and stores `keys` for subsequent operations.
            keys = {}
        # Checks this condition before executing the nested branch.
        if self.daily_hmac_active_key_version not in keys:
            # Raises this exception to report an invalid or failed operation.
            raise ValueError("The active daily HMAC key version is absent from the keyring.")
        # Checks this condition before executing the nested branch.
        if any(len(key) < 32 for key in keys.values()):
            # Raises this exception to report an invalid or failed operation.
            raise ValueError("Every daily HMAC key must contain at least 32 bytes.")
        # Returns this result to the caller and ends the current function.
        return keys

    # Defines the `daily_hmac_key_for_version` callable and its typed interface.
    def daily_hmac_key_for_version(self, version: str) -> bytes:
        # Starts a protected operation whose expected failures are handled below.
        try:
            # Returns this result to the caller and ends the current function.
            return self.daily_hmac_keyring()[version]
        # Handles the listed exception so failure remains controlled.
        except KeyError as exc:
            # Raises this exception to report an invalid or failed operation.
            raise ValueError(f"Daily HMAC key version {version!r} is unavailable.") from exc


# Applies `@lru_cache` to configure the declaration immediately below.
@lru_cache
# Defines the `get_settings` callable and its typed interface.
def get_settings() -> Settings:
    # Returns this result to the caller and ends the current function.
    return Settings()
