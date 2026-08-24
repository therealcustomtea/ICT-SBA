# Defers type-annotation evaluation to support modern hints safely.
from __future__ import annotations

# Imports `uuid` so the module can use that dependency.
import uuid

# Imports selected names from `dataclasses` for use in this module.
from dataclasses import dataclass

# Imports selected names from `datetime` for use in this module.
from datetime import UTC, datetime

# Imports selected names from `functools` for use in this module.
from functools import lru_cache

# Imports selected names from `typing` for use in this module.
from typing import Any

# Imports `jwt` so the module can use that dependency.
import jwt

# Imports selected names from `fastapi` for use in this module.
from fastapi import Depends, Header, Request

# Imports selected names from `jwt` for use in this module.
from jwt import PyJWKClient

# Imports selected names from `jwt.exceptions` for use in this module.
from jwt.exceptions import InvalidTokenError

# Imports selected names from `sqlalchemy.ext.asyncio` for use in this module.
from sqlalchemy.ext.asyncio import AsyncSession

# Imports selected names from `.config` for use in this module.
from .config import Settings, get_settings

# Imports selected names from `.database` for use in this module.
from .database import get_session

# Imports selected names from `.errors` for use in this module.
from .errors import APIError

# Imports selected names from `.models` for use in this module.
from .models import AdminGrant, Profile

# Bound tolerance for small clock differences between the identity provider and API hosts.
# Computes and stores `JWT_CLOCK_SKEW_SECONDS` for subsequent operations.
JWT_CLOCK_SKEW_SECONDS = 30


# Applies `@dataclass(frozen=True, slots=True)` to configure the declaration immediately below.
@dataclass(frozen=True, slots=True)
# Defines the `AuthPrincipal` class and its related behavior.
class AuthPrincipal:
    # Declares the typed `user_id` data field.
    user_id: uuid.UUID
    # Declares the typed `is_anonymous` data field.
    is_anonymous: bool
    # Declares the typed `session_id` data field.
    session_id: str | None
    # Declares the typed `issued_at` data field.
    issued_at: datetime
    # Declares the typed `authenticated_at` data field.
    authenticated_at: datetime | None
    # Declares the typed `assurance_level` data field.
    assurance_level: str | None


# Defines the `SupabaseJWTVerifier` class and its related behavior.
class SupabaseJWTVerifier:
    # Defines the `__init__` callable and its typed interface.
    def __init__(self, settings: Settings) -> None:
        # Checks this condition before executing the nested branch.
        if not settings.supabase_url:
            # Raises this exception to report an invalid or failed operation.
            raise RuntimeError("MASTERMIND_SUPABASE_URL is required for authentication.")
        # Computes and stores `self.issuer` for subsequent operations.
        self.issuer = f"{settings.supabase_url.rstrip('/')}/auth/v1"
        # Computes and stores `self.audience` for subsequent operations.
        self.audience = settings.supabase_jwt_audience
        # Computes and stores `self.jwks` for subsequent operations.
        self.jwks = PyJWKClient(
            # Supplies this item to the surrounding call or collection.
            f"{self.issuer}/.well-known/jwks.json",
            # Provides the `cache_jwk_set` parameter or keyword argument.
            cache_jwk_set=True,
            # Provides the `lifespan` parameter or keyword argument.
            lifespan=600,
            # Provides the `cache_keys` parameter or keyword argument.
            cache_keys=True,
            # Provides the `max_cached_keys` parameter or keyword argument.
            max_cached_keys=16,
            # Closes the multiline call, declaration, or collection started above.
        )

    # Defines the `verify` callable and its typed interface.
    def verify(self, token: str) -> AuthPrincipal:
        # Starts a protected operation whose expected failures are handled below.
        try:
            # Computes and stores `signing_key` for subsequent operations.
            signing_key = self.jwks.get_signing_key_from_jwt(token)
            # Computes and stores `claims` for subsequent operations.
            claims: dict[str, Any] = jwt.decode(
                # Supplies this item to the surrounding call or collection.
                token,
                # Supplies this item to the surrounding call or collection.
                signing_key.key,
                # Provides the `algorithms` parameter or keyword argument.
                algorithms=["RS256", "ES256"],
                # Provides the `audience` parameter or keyword argument.
                audience=self.audience,
                # Provides the `issuer` parameter or keyword argument.
                issuer=self.issuer,
                # Provides the `leeway` parameter or keyword argument.
                leeway=JWT_CLOCK_SKEW_SECONDS,
                # Provides the `options` parameter or keyword argument.
                options={"require": ["exp", "iat", "iss", "aud", "sub"]},
                # Closes the multiline call, declaration, or collection started above.
            )
            # Computes and stores `user_id` for subsequent operations.
            user_id = uuid.UUID(str(claims["sub"]))
            # Computes and stores `authentication_times` for subsequent operations.
            authentication_times = [
                # Calls `int` with the supplied values.
                int(item["timestamp"])
                # Iterates through the supplied values for the nested operation.
                for item in claims.get("amr", [])
                # Checks this condition before executing the nested branch.
                if isinstance(item, dict) and isinstance(item.get("timestamp"), int | float)
                # Closes the multiline call, declaration, or collection started above.
            ]
            # Computes and stores `authenticated_at` for subsequent operations.
            authenticated_at = (
                # Calls `datetime.fromtimestamp` with the supplied values.
                datetime.fromtimestamp(max(authentication_times), tz=UTC)
                # Checks this condition before executing the nested branch.
                if authentication_times
                # Executes this statement as the next step in the surrounding logic.
                else None
                # Closes the multiline call, declaration, or collection started above.
            )
            # Returns this result to the caller and ends the current function.
            return AuthPrincipal(
                # Provides the `user_id` parameter or keyword argument.
                user_id=user_id,
                # Provides the `is_anonymous` parameter or keyword argument.
                is_anonymous=bool(claims.get("is_anonymous", False)),
                # Computes and stores `session_id` for subsequent operations.
                session_id=claims.get("session_id")
                # Checks this condition before executing the nested branch.
                if isinstance(claims.get("session_id"), str)
                # Supplies this item to the surrounding call or collection.
                else None,
                # Provides the `issued_at` parameter or keyword argument.
                issued_at=datetime.fromtimestamp(int(claims["iat"]), tz=UTC),
                # Provides the `authenticated_at` parameter or keyword argument.
                authenticated_at=authenticated_at,
                # Provides the `assurance_level` parameter or keyword argument.
                assurance_level=(claims.get("aal") if isinstance(claims.get("aal"), str) else None),
                # Closes the multiline call, declaration, or collection started above.
            )
        # Handles the listed exception so failure remains controlled.
        except (InvalidTokenError, ValueError, KeyError) as exc:
            # Raises this exception to report an invalid or failed operation.
            raise APIError(
                # Executes this statement as the next step in the surrounding logic.
                401,
                # Supplies this string to the surrounding call or collection.
                "INVALID_ACCESS_TOKEN",
                # Supplies this string to the surrounding call or collection.
                "Your session is invalid or has expired.",
                # Executes this statement as the next step in the surrounding logic.
            ) from exc


# Applies `@lru_cache` to configure the declaration immediately below.
@lru_cache
# Defines the `_cached_verifier` callable and its typed interface.
def _cached_verifier(supabase_url: str, audience: str) -> SupabaseJWTVerifier:
    # Returns this result to the caller and ends the current function.
    return SupabaseJWTVerifier(
        # Calls `Settings` with the supplied values.
        Settings(environment="test", supabase_url=supabase_url, supabase_jwt_audience=audience)
        # Closes the multiline call, declaration, or collection started above.
    )


# Defines the `get_verifier` callable and its typed interface.
def get_verifier(settings: Settings = Depends(get_settings)) -> SupabaseJWTVerifier:
    # Returns this result to the caller and ends the current function.
    return _cached_verifier(settings.supabase_url, settings.supabase_jwt_audience)


# Defines the `get_current_user` callable and its typed interface.
def get_current_user(
    # Declares the typed `request` data field.
    request: Request,
    # Provides the `authorization` parameter or keyword argument.
    authorization: str | None = Header(default=None),
    # Provides the `verifier` parameter or keyword argument.
    verifier: SupabaseJWTVerifier = Depends(get_verifier),
    # Completes the signature and declares the callable return type.
) -> AuthPrincipal:
    # Checks this condition before executing the nested branch.
    if not authorization or not authorization.startswith("Bearer "):
        # Raises this exception to report an invalid or failed operation.
        raise APIError(401, "AUTHENTICATION_REQUIRED", "Sign in or continue as a guest to play.")
    # Computes and stores `token` for subsequent operations.
    token = authorization.removeprefix("Bearer ").strip()
    # Checks this condition before executing the nested branch.
    if not token:
        # Raises this exception to report an invalid or failed operation.
        raise APIError(401, "AUTHENTICATION_REQUIRED", "Sign in or continue as a guest to play.")
    # Computes and stores `principal` for subsequent operations.
    principal = verifier.verify(token)
    # Computes and stores `request.state.principal_id` for subsequent operations.
    request.state.principal_id = str(principal.user_id)
    # Returns this result to the caller and ends the current function.
    return principal


# Defines the `require_admin` callable and its typed interface.
async def require_admin(
    # Provides the `principal` parameter or keyword argument.
    principal: AuthPrincipal = Depends(get_current_user),
    # Provides the `session` parameter or keyword argument.
    session: AsyncSession = Depends(get_session),
    # Completes the signature and declares the callable return type.
) -> AuthPrincipal:
    # Computes and stores `settings` for subsequent operations.
    settings = get_settings()
    # Checks this condition before executing the nested branch.
    if principal.is_anonymous:
        # Raises this exception to report an invalid or failed operation.
        raise APIError(403, "ADMIN_REQUIRED", "Administrator access is required.")
    # Checks this condition before executing the nested branch.
    if not principal.session_id:
        # Raises this exception to report an invalid or failed operation.
        raise APIError(401, "SESSION_REQUIRED", "Sign in again before using administrator tools.")
    # Checks this condition before executing the nested branch.
    if principal.assurance_level != "aal2":
        # Raises this exception to report an invalid or failed operation.
        raise APIError(
            # Supplies this item to the surrounding call or collection.
            401,
            # Supplies this item to the surrounding call or collection.
            "MFA_REQUIRED",
            # Supplies this item to the surrounding call or collection.
            "Complete multi-factor authentication before using administrator tools.",
            # Closes the multiline call, declaration, or collection started above.
        )
    # Checks this condition before executing the nested branch.
    if (
        # Executes this statement as the next step in the surrounding logic.
        principal.authenticated_at is None
        # Executes this statement as the next step in the surrounding logic.
        or (datetime.now(UTC) - principal.authenticated_at).total_seconds()
        # Executes this statement as the next step in the surrounding logic.
        > settings.admin_recent_auth_seconds
        # Begins the nested block or multiline expression completed below.
    ):
        # Raises this exception to report an invalid or failed operation.
        raise APIError(
            # Executes this statement as the next step in the surrounding logic.
            401,
            # Supplies this string to the surrounding call or collection.
            "RECENT_AUTH_REQUIRED",
            # Supplies this string to the surrounding call or collection.
            "Sign in again before using administrator tools.",
            # Closes the multiline call, declaration, or collection started above.
        )
    # Computes and stores `grant` for subsequent operations.
    grant = await session.get(AdminGrant, principal.user_id)
    # Computes and stores `profile` for subsequent operations.
    profile = await session.get(Profile, principal.user_id)
    # Checks this condition before executing the nested branch.
    if (
        # Executes this statement as the next step in the surrounding logic.
        grant is None
        # Executes this statement as the next step in the surrounding logic.
        or grant.revoked_at is not None
        # Executes this statement as the next step in the surrounding logic.
        or profile is None
        # Executes this statement as the next step in the surrounding logic.
        or profile.deleted_at is not None
        # Executes this statement as the next step in the surrounding logic.
        or profile.is_banned
        # Begins the nested block or multiline expression completed below.
    ):
        # Raises this exception to report an invalid or failed operation.
        raise APIError(403, "ADMIN_REQUIRED", "Administrator access is required.")
    # Returns this result to the caller and ends the current function.
    return principal
