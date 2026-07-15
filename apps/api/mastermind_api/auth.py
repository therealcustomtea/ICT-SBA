from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import lru_cache
from typing import Any

import jwt
from fastapi import Depends, Header, Request
from jwt import PyJWKClient
from jwt.exceptions import InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession

from .config import Settings, get_settings
from .database import get_session
from .errors import APIError
from .models import AdminGrant, Profile

# Bound tolerance for small clock differences between the identity provider and API hosts.
JWT_CLOCK_SKEW_SECONDS = 30


@dataclass(frozen=True, slots=True)
class AuthPrincipal:
    user_id: uuid.UUID
    is_anonymous: bool
    session_id: str | None
    issued_at: datetime
    authenticated_at: datetime | None
    assurance_level: str | None


class SupabaseJWTVerifier:
    def __init__(self, settings: Settings) -> None:
        if not settings.supabase_url:
            raise RuntimeError("MASTERMIND_SUPABASE_URL is required for authentication.")
        self.issuer = f"{settings.supabase_url.rstrip('/')}/auth/v1"
        self.audience = settings.supabase_jwt_audience
        self.jwks = PyJWKClient(
            f"{self.issuer}/.well-known/jwks.json",
            cache_jwk_set=True,
            lifespan=600,
            cache_keys=True,
            max_cached_keys=16,
        )

    def verify(self, token: str) -> AuthPrincipal:
        try:
            signing_key = self.jwks.get_signing_key_from_jwt(token)
            claims: dict[str, Any] = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256", "ES256"],
                audience=self.audience,
                issuer=self.issuer,
                leeway=JWT_CLOCK_SKEW_SECONDS,
                options={"require": ["exp", "iat", "iss", "aud", "sub"]},
            )
            user_id = uuid.UUID(str(claims["sub"]))
            authentication_times = [
                int(item["timestamp"])
                for item in claims.get("amr", [])
                if isinstance(item, dict) and isinstance(item.get("timestamp"), int | float)
            ]
            authenticated_at = (
                datetime.fromtimestamp(max(authentication_times), tz=UTC)
                if authentication_times
                else None
            )
            return AuthPrincipal(
                user_id=user_id,
                is_anonymous=bool(claims.get("is_anonymous", False)),
                session_id=claims.get("session_id")
                if isinstance(claims.get("session_id"), str)
                else None,
                issued_at=datetime.fromtimestamp(int(claims["iat"]), tz=UTC),
                authenticated_at=authenticated_at,
                assurance_level=(claims.get("aal") if isinstance(claims.get("aal"), str) else None),
            )
        except (InvalidTokenError, ValueError, KeyError) as exc:
            raise APIError(
                401, "INVALID_ACCESS_TOKEN", "Your session is invalid or has expired."
            ) from exc


@lru_cache
def _cached_verifier(supabase_url: str, audience: str) -> SupabaseJWTVerifier:
    return SupabaseJWTVerifier(
        Settings(environment="test", supabase_url=supabase_url, supabase_jwt_audience=audience)
    )


def get_verifier(settings: Settings = Depends(get_settings)) -> SupabaseJWTVerifier:
    return _cached_verifier(settings.supabase_url, settings.supabase_jwt_audience)


def get_current_user(
    request: Request,
    authorization: str | None = Header(default=None),
    verifier: SupabaseJWTVerifier = Depends(get_verifier),
) -> AuthPrincipal:
    if not authorization or not authorization.startswith("Bearer "):
        raise APIError(401, "AUTHENTICATION_REQUIRED", "Sign in or continue as a guest to play.")
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise APIError(401, "AUTHENTICATION_REQUIRED", "Sign in or continue as a guest to play.")
    principal = verifier.verify(token)
    request.state.principal_id = str(principal.user_id)
    return principal


async def require_admin(
    principal: AuthPrincipal = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> AuthPrincipal:
    settings = get_settings()
    if principal.is_anonymous:
        raise APIError(403, "ADMIN_REQUIRED", "Administrator access is required.")
    if not principal.session_id:
        raise APIError(401, "SESSION_REQUIRED", "Sign in again before using administrator tools.")
    if principal.assurance_level != "aal2":
        raise APIError(
            401,
            "MFA_REQUIRED",
            "Complete multi-factor authentication before using administrator tools.",
        )
    if (
        principal.authenticated_at is None
        or (datetime.now(UTC) - principal.authenticated_at).total_seconds()
        > settings.admin_recent_auth_seconds
    ):
        raise APIError(
            401, "RECENT_AUTH_REQUIRED", "Sign in again before using administrator tools."
        )
    grant = await session.get(AdminGrant, principal.user_id)
    profile = await session.get(Profile, principal.user_id)
    if (
        grant is None
        or grant.revoked_at is not None
        or profile is None
        or profile.deleted_at is not None
        or profile.is_banned
    ):
        raise APIError(403, "ADMIN_REQUIRED", "Administrator access is required.")
    return principal
