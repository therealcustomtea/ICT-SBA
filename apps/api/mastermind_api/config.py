# Defers annotation evaluation so modern type hints remain safe at runtime.
from __future__ import annotations

# Imports `base64` because this module uses that dependency.
import base64

# Imports `json` because this module uses that dependency.
import json

# Imports `os` because this module uses that dependency.
import os

# Imports `re` because this module uses that dependency.
import re

# Imports the required names from `functools` for this module.
from functools import lru_cache

# Imports the required names from `typing` for this module.
from typing import Literal

# Imports the required names from `urllib.parse` for this module.
from urllib.parse import urlparse

# Imports the required names from `pydantic` for this module.
from pydantic import Field, field_validator, model_validator

# Imports the required names from `pydantic_settings` for this module.
from pydantic_settings import BaseSettings, SettingsConfigDict

# Stores `_PLACEHOLDER_MARKERS` because later steps depend on this value.
_PLACEHOLDER_MARKERS = (
    # Supplies this literal value to the surrounding declaration or call.
    "change-me",
    # Supplies this literal value to the surrounding declaration or call.
    "changeme",
    # Supplies this literal value to the surrounding declaration or call.
    "dummy",
    # Supplies this literal value to the surrounding declaration or call.
    "example",
    # Supplies this literal value to the surrounding declaration or call.
    "placeholder",
    # Supplies this literal value to the surrounding declaration or call.
    "replace-me",
    # Closes the multiline declaration, call, or collection opened above.
)


# Defines this callable to implement the operation described by its name.
def _is_exact_https_origin(value: str) -> bool:
    # Stores `parsed` because later steps depend on this value.
    parsed = urlparse(value)
    # Returns the computed result and ends the current callable.
    return bool(
        # Stores `parsed.scheme` because later steps depend on this value.
        parsed.scheme == "https"
        # Supplies this required nested value.
        and parsed.hostname
        # Supplies this required nested value.
        and parsed.username is None
        # Supplies this required nested value.
        and parsed.password is None
        # Supplies this required nested value.
        and parsed.path in {"", "/"}
        # Supplies this required nested value.
        and not parsed.params
        # Supplies this required nested value.
        and not parsed.query
        # Supplies this required nested value.
        and not parsed.fragment
        # Closes the multiline declaration, call, or collection opened above.
    )


# Defines this callable to implement the operation described by its name.
def _looks_placeholder(value: str) -> bool:
    # Stores `normalized` because later steps depend on this value.
    normalized = value.strip().lower()
    # Returns the computed result and ends the current callable.
    return any(marker in normalized for marker in _PLACEHOLDER_MARKERS) or (
        # Supplies this required nested value.
        bool(normalized) and len(set(normalized)) == 1
        # Closes the multiline declaration, call, or collection opened above.
    )


# Groups the state and behavior owned by `Settings`.
class Settings(BaseSettings):
    # Stores `model_config` because later steps depend on this value.
    model_config = SettingsConfigDict(
        # Stores `env_file` because later steps depend on this value.
        env_file=".env",
        # Stores `env_prefix` because later steps depend on this value.
        env_prefix="MASTERMIND_",
        # Stores `case_sensitive` because later steps depend on this value.
        case_sensitive=False,
        # Stores `extra` because later steps depend on this value.
        extra="ignore",
        # Closes the multiline declaration, call, or collection opened above.
    )

    # Stores `environment` because later steps depend on this value.
    environment: Literal["development", "test", "staging", "production"] = "development"
    # Stores `product_name` because later steps depend on this value.
    product_name: str = Field(default="Cipherboard", min_length=1, max_length=64)
    # Stores `release` because later steps depend on this value.
    release: str = "development"

    # Stores `mongodb_url` because later steps depend on this value.
    mongodb_url: str = "mongodb://localhost:27017/?replicaSet=rs0"
    # Stores `mongodb_database` because later steps depend on this value.
    mongodb_database: str = "mastermind"
    # Stores `redis_url` because later steps depend on this value.
    redis_url: str | None = "redis://localhost:6379/0"
    # Stores `allowed_origins` because later steps depend on this value.
    allowed_origins: tuple[str, ...] = ("http://localhost:3000",)
    # Stores `product_origin` because later steps depend on this value.
    product_origin: str = "http://localhost:3000"
    # Stores `trusted_proxy_ips` because later steps depend on this value.
    trusted_proxy_ips: tuple[str, ...] = ()

    # Stores `auth_issuer` because later steps depend on this value.
    auth_issuer: str = "http://localhost:8000"
    # Stores `auth_audience` because later steps depend on this value.
    auth_audience: str = "cipherboard-web"
    # Stores `auth_signing_key` because later steps depend on this value.
    auth_signing_key: str = ""
    # Stores `auth_access_token_seconds` because later steps depend on this value.
    auth_access_token_seconds: int = Field(default=600, ge=300, le=3600)
    # Stores `auth_refresh_token_days` because later steps depend on this value.
    auth_refresh_token_days: int = Field(default=30, ge=1, le=90)
    # Stores `auth_email_token_seconds` because later steps depend on this value.
    auth_email_token_seconds: int = Field(default=900, ge=300, le=3600)
    # Stores `auth_cookie_name` because later steps depend on this value.
    auth_cookie_name: str = "cipherboard_refresh"
    # Stores `auth_cookie_secure` because later steps depend on this value.
    auth_cookie_secure: bool = False
    # Stores `auth_cookie_samesite` because later steps depend on this value.
    auth_cookie_samesite: Literal["lax", "strict", "none"] = "lax"
    # Stores `auth_email_sender` because later steps depend on this value.
    auth_email_sender: str = "Cipherboard <noreply@localhost.invalid>"
    # Stores `smtp_host` because later steps depend on this value.
    smtp_host: str = "localhost"
    # Stores `smtp_port` because later steps depend on this value.
    smtp_port: int = Field(default=1025, ge=1, le=65535)
    # Stores `smtp_username` because later steps depend on this value.
    smtp_username: str = ""
    # Stores `smtp_password` because later steps depend on this value.
    smtp_password: str = ""
    # Stores `smtp_starttls` because later steps depend on this value.
    smtp_starttls: bool = False

    # Stores `secret_encryption_keys` because later steps depend on this value.
    secret_encryption_keys: str = ""
    # Stores `secret_active_key_version` because later steps depend on this value.
    secret_active_key_version: str = "v1"
    # Stores `daily_hmac_key` because later steps depend on this value.
    daily_hmac_key: str = ""
    # Stores `daily_hmac_keys` because later steps depend on this value.
    daily_hmac_keys: str = ""
    # Stores `daily_hmac_active_key_version` because later steps depend on this value.
    daily_hmac_active_key_version: str = "v1"
    # Stores `public_identifier_hmac_key` because later steps depend on this value.
    public_identifier_hmac_key: str = ""

    # Stores `admin_recent_auth_seconds` because later steps depend on this value.
    admin_recent_auth_seconds: int = Field(default=900, ge=60, le=3600)
    # Stores `request_body_limit_bytes` because later steps depend on this value.
    request_body_limit_bytes: int = Field(default=65_536, ge=1024, le=1_048_576)
    # Stores `request_timeout_seconds` because later steps depend on this value.
    request_timeout_seconds: int = Field(default=15, ge=1, le=120)
    # Stores `rate_limit_per_minute` because later steps depend on this value.
    rate_limit_per_minute: int = Field(default=120, ge=10, le=10_000)
    # Stores `room_tie_window_ms` because later steps depend on this value.
    room_tie_window_ms: int = Field(default=250, ge=50, le=2000)
    # Stores `websocket_frame_limit_bytes` because later steps depend on this value.
    websocket_frame_limit_bytes: int = Field(default=4096, ge=1024, le=4096)
    # Stores `websocket_user_connection_limit` because later steps depend on this value.
    websocket_user_connection_limit: int = Field(default=3, ge=1, le=20)
    # Stores `websocket_ip_connection_limit` because later steps depend on this value.
    websocket_ip_connection_limit: int = Field(default=20, ge=1, le=200)
    # Stores `websocket_connection_ttl_seconds` because later steps depend on this value.
    websocket_connection_ttl_seconds: int = Field(default=90, ge=60, le=300)
    # Stores `log_level` because later steps depend on this value.
    log_level: str = "INFO"
    # Stores `metrics_enabled` because later steps depend on this value.
    metrics_enabled: bool = True
    # Stores `error_reporting_url` because later steps depend on this value.
    error_reporting_url: str = ""
    # Stores `error_reporting_token` because later steps depend on this value.
    error_reporting_token: str = ""
    # Stores `feature_daily` because later steps depend on this value.
    feature_daily: bool = True
    # Stores `feature_leaderboards` because later steps depend on this value.
    feature_leaderboards: bool = True
    # Stores `feature_friend_challenges` because later steps depend on this value.
    feature_friend_challenges: bool = True
    # Stores `feature_multiplayer` because later steps depend on this value.
    feature_multiplayer: bool = True
    # Stores `feature_achievements` because later steps depend on this value.
    feature_achievements: bool = True
    # Stores `feature_account_registration` because later steps depend on this value.
    feature_account_registration: bool = True
    # Stores `feature_analytics` because later steps depend on this value.
    feature_analytics: bool = False

    # Applies this decorator to configure the declaration immediately below.
    @field_validator("auth_issuer")
    # Applies this decorator to configure the declaration immediately below.
    @classmethod
    # Defines this callable to implement the operation described by its name.
    def normalize_auth_issuer(cls, value: str) -> str:
        # Returns the computed result and ends the current callable.
        return value.rstrip("/")

    # Applies this decorator to configure the declaration immediately below.
    @model_validator(mode="after")
    # Defines this callable to implement the operation described by its name.
    def validate_configuration(self) -> Settings:
        # Guards the nested operation so it runs only when this condition is satisfied.
        if bool(self.error_reporting_url) != bool(self.error_reporting_token):
            # Raises this error so invalid state cannot continue silently.
            raise ValueError(
                # Supplies this literal value to the surrounding declaration or call.
                "MASTERMIND_ERROR_REPORTING_URL and MASTERMIND_ERROR_REPORTING_TOKEN "
                # Supplies this literal value to the surrounding declaration or call.
                "must be configured together."
                # Closes the multiline declaration, call, or collection opened above.
            )
        # Guards the nested operation so it runs only when this condition is satisfied.
        if self.error_reporting_url and not self.error_reporting_url.startswith("https://"):
            # Raises this error so invalid state cannot continue silently.
            raise ValueError("The error-reporting endpoint must use HTTPS.")
        # Guards the nested operation so it runs only when this condition is satisfied.
        if self.auth_cookie_samesite == "none" and not self.auth_cookie_secure:
            # Raises this error so invalid state cannot continue silently.
            raise ValueError("SameSite=None authentication cookies must be Secure.")
        # Guards the nested operation so it runs only when this condition is satisfied.
        if self.secret_encryption_keys:
            # Supplies this required nested value.
            self.secret_encryption_keyring()
        # Guards the nested operation so it runs only when this condition is satisfied.
        if self.environment in {"staging", "production"}:
            # Stores `required` because later steps depend on this value.
            required = (
                # Supplies this required nested value.
                ("MASTERMIND_MONGODB_URL", self.mongodb_url),
                # Supplies this required nested value.
                ("MASTERMIND_REDIS_URL", self.redis_url or ""),
                # Supplies this required nested value.
                ("MASTERMIND_AUTH_SIGNING_KEY", self.auth_signing_key),
                # Supplies this required nested value.
                ("MASTERMIND_SECRET_ENCRYPTION_KEYS", self.secret_encryption_keys),
                # Supplies this required nested value.
                (
                    # Supplies this literal value to the surrounding declaration or call.
                    "MASTERMIND_DAILY_HMAC_KEYS or MASTERMIND_DAILY_HMAC_KEY",
                    # Supplies this required nested value.
                    self.daily_hmac_keys or self.daily_hmac_key,
                    # Closes the multiline declaration, call, or collection opened above.
                ),
                # Supplies this required nested value.
                ("MASTERMIND_PUBLIC_IDENTIFIER_HMAC_KEY", self.public_identifier_hmac_key),
                # Supplies this required nested value.
                ("MASTERMIND_SMTP_HOST", self.smtp_host),
                # Closes the multiline declaration, call, or collection opened above.
            )
            # Stores `missing` because later steps depend on this value.
            missing = [name for name, value in required if not value]
            # Guards the nested operation so it runs only when this condition is satisfied.
            if missing:
                # Raises this error so invalid state cannot continue silently.
                raise ValueError(f"Missing required production settings: {', '.join(missing)}")
            # Stores `parsed_mongo` because later steps depend on this value.
            parsed_mongo = urlparse(self.mongodb_url)
            # Stores `mongo_host` because later steps depend on this value.
            mongo_host = (parsed_mongo.hostname or "").lower()
            # Guards the nested operation so it runs only when this condition is satisfied.
            if parsed_mongo.scheme not in {"mongodb", "mongodb+srv"}:
                # Raises this error so invalid state cannot continue silently.
                raise ValueError("Production MongoDB must use a MongoDB connection string.")
            # Guards the nested operation so it runs only when this condition is satisfied.
            if mongo_host in {"", "localhost", "127.0.0.1", "::1"}:
                # Raises this error so invalid state cannot continue silently.
                raise ValueError("Production MongoDB cannot use a local host.")
            # Guards the nested operation so it runs only when this condition is satisfied.
            if parsed_mongo.scheme == "mongodb" and "tls=true" not in self.mongodb_url.lower():
                # Raises this error so invalid state cannot continue silently.
                raise ValueError("Production MongoDB connections must enable TLS.")
            # Guards the nested operation so it runs only when this condition is satisfied.
            if not self.redis_url or not self.redis_url.startswith("rediss://"):
                # Raises this error so invalid state cannot continue silently.
                raise ValueError("Production Redis must use TLS.")
            # Guards the nested operation so it runs only when this condition is satisfied.
            if any(not _is_exact_https_origin(origin) for origin in self.allowed_origins):
                # Raises this error so invalid state cannot continue silently.
                raise ValueError("Production CORS origins must be exact HTTPS origins.")
            # Guards the nested operation so it runs only when this condition is satisfied.
            if not _is_exact_https_origin(self.auth_issuer):
                # Raises this error so invalid state cannot continue silently.
                raise ValueError("Production auth issuer must be an exact HTTPS origin.")
            # Guards the nested operation so it runs only when this condition is satisfied.
            if len(self.auth_signing_key.encode()) < 32 or _looks_placeholder(
                # Supplies this required nested value.
                self.auth_signing_key
                # Closes the multiline declaration, call, or collection opened above.
            ):
                # Raises this error so invalid state cannot continue silently.
                raise ValueError(
                    # Supplies this literal value to the surrounding declaration or call.
                    "Production auth signing key must contain at least 32 random bytes."
                    # Closes the multiline declaration, call, or collection opened above.
                )
            # Guards the nested operation so it runs only when this condition is satisfied.
            if len(self.public_identifier_hmac_key.encode()) < 32:
                # Raises this error so invalid state cannot continue silently.
                raise ValueError("The public identifier HMAC key must contain at least 32 bytes.")
            # Guards the nested operation so it runs only when this condition is satisfied.
            if not self.auth_cookie_secure:
                # Raises this error so invalid state cannot continue silently.
                raise ValueError("Production authentication cookies must be Secure.")
            # Guards the nested operation so it runs only when this condition is satisfied.
            if self.release in {"", "development", "latest"}:
                # Raises this error so invalid state cannot continue silently.
                raise ValueError("Production requires an immutable release identifier.")
        # Returns the computed result and ends the current callable.
        return self

    # Defines this callable to implement the operation described by its name.
    def secret_encryption_keyring(self) -> dict[str, bytes]:
        # Starts an operation whose expected failures are handled below.
        try:
            # Stores `encoded_keys` because later steps depend on this value.
            encoded_keys = json.loads(self.secret_encryption_keys)
        # Converts this expected failure into the controlled behavior below.
        except json.JSONDecodeError as exc:
            # Raises this error so invalid state cannot continue silently.
            raise ValueError("The secret encryption keyring is malformed.") from exc
        # Guards the nested operation so it runs only when this condition is satisfied.
        if not isinstance(encoded_keys, dict) or not encoded_keys:
            # Raises this error so invalid state cannot continue silently.
            raise ValueError("The secret encryption keyring is malformed.")
        # Stores `keys` because later steps depend on this value.
        keys: dict[str, bytes] = {}
        # Starts an operation whose expected failures are handled below.
        try:
            # Iterates over these values so each item receives the same processing.
            for version, encoded_key in encoded_keys.items():
                # Guards the nested operation so it runs only when this condition is satisfied.
                if not isinstance(version, str) or not version or not isinstance(encoded_key, str):
                    # Raises this error so invalid state cannot continue silently.
                    raise ValueError
                # Supplies this required nested value.
                keys[version] = base64.b64decode(encoded_key, validate=True)
        # Converts this expected failure into the controlled behavior below.
        except (TypeError, ValueError) as exc:
            # Raises this error so invalid state cannot continue silently.
            raise ValueError("The secret encryption keyring is malformed.") from exc
        # Guards the nested operation so it runs only when this condition is satisfied.
        if self.secret_active_key_version not in keys:
            # Raises this error so invalid state cannot continue silently.
            raise ValueError("The active AES-GCM key version is absent from the keyring.")
        # Stores `expected_lengths` because later steps depend on this value.
        expected_lengths = {32} if self.environment in {"staging", "production"} else {16, 24, 32}
        # Guards the nested operation so it runs only when this condition is satisfied.
        if any(len(key) not in expected_lengths for key in keys.values()):
            # Raises this error so invalid state cannot continue silently.
            raise ValueError("Every AES-GCM key has an invalid length.")
        # Returns the computed result and ends the current callable.
        return keys

    # Defines this callable to implement the operation described by its name.
    def daily_hmac_keyring(self) -> dict[str, bytes]:
        # Guards the nested operation so it runs only when this condition is satisfied.
        if self.daily_hmac_keys:
            # Starts an operation whose expected failures are handled below.
            try:
                # Stores `decoded` because later steps depend on this value.
                decoded = json.loads(self.daily_hmac_keys)
            # Converts this expected failure into the controlled behavior below.
            except json.JSONDecodeError as exc:
                # Raises this error so invalid state cannot continue silently.
                raise ValueError("The daily HMAC keyring is malformed.") from exc
            # Guards the nested operation so it runs only when this condition is satisfied.
            if not isinstance(decoded, dict) or not decoded:
                # Raises this error so invalid state cannot continue silently.
                raise ValueError("The daily HMAC keyring is malformed.")
            # Stores `keys` because later steps depend on this value.
            keys = {
                # Supplies this required nested value.
                str(version): value.encode()
                # Iterates over these values so each item receives the same processing.
                for version, value in decoded.items()
                # Guards the nested operation so it runs only when this condition is satisfied.
                if isinstance(version, str) and isinstance(value, str)
                # Closes the multiline declaration, call, or collection opened above.
            }
            # Guards the nested operation so it runs only when this condition is satisfied.
            if len(keys) != len(decoded):
                # Raises this error so invalid state cannot continue silently.
                raise ValueError("The daily HMAC keyring is malformed.")
        # Handles this alternative only when the earlier conditions did not match.
        elif self.daily_hmac_key:
            # Stores `keys` because later steps depend on this value.
            keys = {self.daily_hmac_active_key_version: self.daily_hmac_key.encode()}
        # Provides the fallback path when the preceding conditions do not match.
        else:
            # Stores `keys` because later steps depend on this value.
            keys = {}
        # Guards the nested operation so it runs only when this condition is satisfied.
        if self.daily_hmac_active_key_version not in keys:
            # Raises this error so invalid state cannot continue silently.
            raise ValueError("The active daily HMAC key version is absent from the keyring.")
        # Guards the nested operation so it runs only when this condition is satisfied.
        if any(len(key) < 32 for key in keys.values()):
            # Raises this error so invalid state cannot continue silently.
            raise ValueError("Every daily HMAC key must contain at least 32 bytes.")
        # Returns the computed result and ends the current callable.
        return keys

    # Defines this callable to implement the operation described by its name.
    def daily_hmac_key_for_version(self, version: str) -> bytes:
        # Starts an operation whose expected failures are handled below.
        try:
            # Returns the computed result and ends the current callable.
            return self.daily_hmac_keyring()[version]
        # Converts this expected failure into the controlled behavior below.
        except KeyError as exc:
            # Raises this error so invalid state cannot continue silently.
            raise ValueError(f"Daily HMAC key version {version!r} is unavailable.") from exc


# Applies this decorator to configure the declaration immediately below.
@lru_cache
# Defines this callable to implement the operation described by its name.
def get_settings() -> Settings:
    # Returns the computed result and ends the current callable.
    return Settings()


# Defines this callable to implement the operation described by its name.
def reset_settings_cache() -> None:
    # Supplies this required nested value.
    get_settings.cache_clear()


# Defines this callable to implement the operation described by its name.
def ci_environment() -> bool:
    # Returns the computed result and ends the current callable.
    return (
        # Supplies this required nested value.
        os.getenv("CI", "").lower() == "true"
        # Supplies this required nested value.
        and os.getenv("GITHUB_ACTIONS", "").lower() == "true"
        # Closes the multiline declaration, call, or collection opened above.
    )


# Defines this callable to implement the operation described by its name.
def immutable_ci_release(value: str) -> bool:
    # Returns the computed result and ends the current callable.
    return re.fullmatch(r"ci-[0-9a-f]{40}", value) is not None
