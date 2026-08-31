# Defers annotation evaluation so modern type hints remain safe at runtime.
from __future__ import annotations

# Imports `hashlib` because this module uses that dependency.
import hashlib

# Imports `hmac` because this module uses that dependency.
import hmac

# Imports `secrets` because this module uses that dependency.
import secrets

# Imports `uuid` because this module uses that dependency.
import uuid

# Imports the required names from `dataclasses` for this module.
from dataclasses import dataclass

# Imports the required names from `datetime` for this module.
from datetime import UTC, datetime, timedelta

# Imports the required names from `functools` for this module.
from functools import lru_cache

# Imports the required names from `typing` for this module.
from typing import Any

# Imports `jwt` because this module uses that dependency.
import jwt

# Imports the required names from `fastapi` for this module.
from fastapi import Depends, Header, Request

# Imports the required names from `jwt.exceptions` for this module.
from jwt.exceptions import InvalidTokenError

# Imports the required names from `.config` for this module.
from .config import Settings, get_settings

# Imports the required names from `.database` for this module.
from .database import MongoSession, get_session

# Imports the required names from `.errors` for this module.
from .errors import APIError

# Imports the required names from `.models` for this module.
from .models import AdminGrant, AuthSession, AuthUser, Profile

# Stores `JWT_CLOCK_SKEW_SECONDS` because later steps depend on this value.
JWT_CLOCK_SKEW_SECONDS = 30


# Applies this decorator to configure the declaration immediately below.
@dataclass(frozen=True, slots=True)
# Groups the state and behavior owned by `AuthPrincipal`.
class AuthPrincipal:
    # Declares this typed field so the surrounding contract is explicit.
    user_id: uuid.UUID
    # Declares this typed field so the surrounding contract is explicit.
    is_anonymous: bool
    # Declares this typed field so the surrounding contract is explicit.
    session_id: str | None
    # Declares this typed field so the surrounding contract is explicit.
    issued_at: datetime
    # Declares this typed field so the surrounding contract is explicit.
    authenticated_at: datetime | None
    # Declares this typed field so the surrounding contract is explicit.
    assurance_level: str | None


# Applies this decorator to configure the declaration immediately below.
@dataclass(frozen=True, slots=True)
# Groups the state and behavior owned by `IssuedSession`.
class IssuedSession:
    # Declares this typed field so the surrounding contract is explicit.
    access_token: str
    # Declares this typed field so the surrounding contract is explicit.
    refresh_token: str
    # Declares this typed field so the surrounding contract is explicit.
    expires_in: int
    # Declares this typed field so the surrounding contract is explicit.
    principal: AuthPrincipal


# Groups the state and behavior owned by `AccessTokenVerifier`.
class AccessTokenVerifier:
    # Defines this callable to implement the operation described by its name.
    def __init__(self, settings: Settings) -> None:
        # Guards the nested operation so it runs only when this condition is satisfied.
        if len(settings.auth_signing_key.encode()) < 32:
            # Raises this error so invalid state cannot continue silently.
            raise RuntimeError("MASTERMIND_AUTH_SIGNING_KEY is required for authentication.")
        # Stores `self.key` because later steps depend on this value.
        self.key = settings.auth_signing_key
        # Stores `self.issuer` because later steps depend on this value.
        self.issuer = settings.auth_issuer
        # Stores `self.audience` because later steps depend on this value.
        self.audience = settings.auth_audience

    # Defines this callable to implement the operation described by its name.
    def verify(self, token: str) -> AuthPrincipal:
        # Starts an operation whose expected failures are handled below.
        try:
            # Stores `claims` because later steps depend on this value.
            claims: dict[str, Any] = jwt.decode(
                # Supplies this required nested value.
                token,
                # Supplies this required nested value.
                self.key,
                # Stores `algorithms` because later steps depend on this value.
                algorithms=["HS256"],
                # Stores `audience` because later steps depend on this value.
                audience=self.audience,
                # Stores `issuer` because later steps depend on this value.
                issuer=self.issuer,
                # Stores `leeway` because later steps depend on this value.
                leeway=JWT_CLOCK_SKEW_SECONDS,
                # Stores `options` because later steps depend on this value.
                options={"require": ["exp", "iat", "iss", "aud", "sub", "session_id"]},
                # Closes the multiline declaration, call, or collection opened above.
            )
            # Stores `user_id` because later steps depend on this value.
            user_id = uuid.UUID(str(claims["sub"]))
            # Stores `session_id` because later steps depend on this value.
            session_id = str(uuid.UUID(str(claims["session_id"])))
            # Stores `authenticated_at_value` because later steps depend on this value.
            authenticated_at_value = claims.get("auth_time")
            # Stores `authenticated_at` because later steps depend on this value.
            authenticated_at = (
                # Supplies this required nested value.
                datetime.fromtimestamp(int(authenticated_at_value), tz=UTC)
                # Guards the nested operation so it runs only when this condition is satisfied.
                if isinstance(authenticated_at_value, int | float)
                # Supplies this required nested value.
                else None
                # Closes the multiline declaration, call, or collection opened above.
            )
            # Returns the computed result and ends the current callable.
            return AuthPrincipal(
                # Stores `user_id` because later steps depend on this value.
                user_id=user_id,
                # Stores `is_anonymous` because later steps depend on this value.
                is_anonymous=bool(claims.get("is_anonymous", False)),
                # Stores `session_id` because later steps depend on this value.
                session_id=session_id,
                # Stores `issued_at` because later steps depend on this value.
                issued_at=datetime.fromtimestamp(int(claims["iat"]), tz=UTC),
                # Stores `authenticated_at` because later steps depend on this value.
                authenticated_at=authenticated_at,
                # Stores `assurance_level` because later steps depend on this value.
                assurance_level=str(claims.get("aal", "aal1")),
                # Closes the multiline declaration, call, or collection opened above.
            )
        # Converts this expected failure into the controlled behavior below.
        except (InvalidTokenError, ValueError, KeyError) as exc:
            # Raises this error so invalid state cannot continue silently.
            raise APIError(
                # Supplies this required nested value.
                401,
                # Supplies this literal value to the surrounding declaration or call.
                "INVALID_ACCESS_TOKEN",
                # Supplies this literal value to the surrounding declaration or call.
                "Your session is invalid or has expired.",
                # Closes the multiline declaration, call, or collection opened above.
            ) from exc


# Applies this decorator to configure the declaration immediately below.
@lru_cache
# Defines this callable to implement the operation described by its name.
def _cached_verifier(signing_key: str, issuer: str, audience: str) -> AccessTokenVerifier:
    # Returns the computed result and ends the current callable.
    return AccessTokenVerifier(
        # Supplies this required nested value.
        Settings(
            # Stores `environment` because later steps depend on this value.
            environment="test",
            # Stores `auth_signing_key` because later steps depend on this value.
            auth_signing_key=signing_key,
            # Stores `auth_issuer` because later steps depend on this value.
            auth_issuer=issuer,
            # Stores `auth_audience` because later steps depend on this value.
            auth_audience=audience,
            # Closes the multiline declaration, call, or collection opened above.
        )
        # Closes the multiline declaration, call, or collection opened above.
    )


# Defines this callable to implement the operation described by its name.
def get_verifier(settings: Settings = Depends(get_settings)) -> AccessTokenVerifier:
    # Returns the computed result and ends the current callable.
    return _cached_verifier(settings.auth_signing_key, settings.auth_issuer, settings.auth_audience)


# Defines this callable to implement the operation described by its name.
def token_hash(token: str, settings: Settings) -> str:
    # Returns the computed result and ends the current callable.
    return hmac.new(settings.auth_signing_key.encode(), token.encode(), hashlib.sha256).hexdigest()


# Defines this callable to implement the operation described by its name.
def new_refresh_token() -> str:
    # Returns the computed result and ends the current callable.
    return secrets.token_urlsafe(48)


# Defines this callable to implement the operation described by its name.
def mint_access_token(
    # Declares this typed field so the surrounding contract is explicit.
    user: AuthUser,
    auth_session: AuthSession,
    settings: Settings,
    # Closes the multiline declaration, call, or collection opened above.
) -> tuple[str, AuthPrincipal]:
    # Stores `now` because later steps depend on this value.
    now = datetime.now(UTC)
    # Stores `principal` because later steps depend on this value.
    principal = AuthPrincipal(
        # Stores `user_id` because later steps depend on this value.
        user_id=user.id,
        # Stores `is_anonymous` because later steps depend on this value.
        is_anonymous=user.is_anonymous,
        # Stores `session_id` because later steps depend on this value.
        session_id=str(auth_session.id),
        # Stores `issued_at` because later steps depend on this value.
        issued_at=now,
        # Stores `authenticated_at` because later steps depend on this value.
        authenticated_at=auth_session.authenticated_at,
        # Stores `assurance_level` because later steps depend on this value.
        assurance_level=auth_session.assurance_level,
        # Closes the multiline declaration, call, or collection opened above.
    )
    # Stores `payload` because later steps depend on this value.
    payload = {
        # Supplies this literal value to the surrounding declaration or call.
        "iss": settings.auth_issuer,
        # Supplies this literal value to the surrounding declaration or call.
        "aud": settings.auth_audience,
        # Supplies this literal value to the surrounding declaration or call.
        "sub": str(user.id),
        # Supplies this literal value to the surrounding declaration or call.
        "session_id": str(auth_session.id),
        # Supplies this literal value to the surrounding declaration or call.
        "is_anonymous": user.is_anonymous,
        # Supplies this literal value to the surrounding declaration or call.
        "aal": auth_session.assurance_level,
        # Supplies this literal value to the surrounding declaration or call.
        "auth_time": int(auth_session.authenticated_at.timestamp()),
        # Supplies this literal value to the surrounding declaration or call.
        "iat": int(now.timestamp()),
        # Supplies this literal value to the surrounding declaration or call.
        "exp": int((now + timedelta(seconds=settings.auth_access_token_seconds)).timestamp()),
        # Supplies this literal value to the surrounding declaration or call.
        "jti": uuid.uuid4().hex,
        # Closes the multiline declaration, call, or collection opened above.
    }
    # Returns the computed result and ends the current callable.
    return jwt.encode(payload, settings.auth_signing_key, algorithm="HS256"), principal


# Defines this callable to implement the operation described by its name.
async def create_auth_session(
    # Declares this typed field so the surrounding contract is explicit.
    session: MongoSession,
    # Declares this typed field so the surrounding contract is explicit.
    user: AuthUser,
    # Declares this typed field so the surrounding contract is explicit.
    settings: Settings,
    # Supplies this required nested value.
    *,
    # Stores `assurance_level` because later steps depend on this value.
    assurance_level: str = "aal1",
    # Stores `ip_hash` because later steps depend on this value.
    ip_hash: str | None = None,
    # Stores `user_agent_hash` because later steps depend on this value.
    user_agent_hash: str | None = None,
    # Closes the multiline declaration, call, or collection opened above.
) -> IssuedSession:
    # Stores `refresh_token` because later steps depend on this value.
    refresh_token = new_refresh_token()
    # Stores `now` because later steps depend on this value.
    now = datetime.now(UTC)
    # Stores `auth_session` because later steps depend on this value.
    auth_session = AuthSession(
        # Stores `user_id` because later steps depend on this value.
        user_id=user.id,
        # Stores `refresh_token_hash` because later steps depend on this value.
        refresh_token_hash=token_hash(refresh_token, settings),
        # Stores `created_at` because later steps depend on this value.
        created_at=now,
        # Stores `updated_at` because later steps depend on this value.
        updated_at=now,
        # Stores `authenticated_at` because later steps depend on this value.
        authenticated_at=now,
        # Stores `expires_at` because later steps depend on this value.
        expires_at=now + timedelta(days=settings.auth_refresh_token_days),
        # Stores `assurance_level` because later steps depend on this value.
        assurance_level=assurance_level,
        # Stores `last_ip_hash` because later steps depend on this value.
        last_ip_hash=ip_hash,
        # Stores `user_agent_hash` because later steps depend on this value.
        user_agent_hash=user_agent_hash,
        # Closes the multiline declaration, call, or collection opened above.
    )
    # Supplies this required nested value.
    session.add(auth_session)
    # Performs this required operation before the surrounding flow continues.
    await session.commit()
    # Supplies this required nested value.
    access_token, principal = mint_access_token(user, auth_session, settings)
    # Returns the computed result and ends the current callable.
    return IssuedSession(
        # Stores `access_token` because later steps depend on this value.
        access_token=access_token,
        # Stores `refresh_token` because later steps depend on this value.
        refresh_token=refresh_token,
        # Stores `expires_in` because later steps depend on this value.
        expires_in=settings.auth_access_token_seconds,
        # Stores `principal` because later steps depend on this value.
        principal=principal,
        # Closes the multiline declaration, call, or collection opened above.
    )


# Defines this callable to implement the operation described by its name.
async def revoke_user_sessions(session: MongoSession, user_id: uuid.UUID) -> None:
    # Performs this required operation before the surrounding flow continues.
    await session.update_many(
        # Supplies this required nested value.
        AuthSession,
        # Supplies this required nested value.
        {"user_id": user_id, "revoked_at": None},
        # Supplies this required nested value.
        {"$set": {"revoked_at": datetime.now(UTC), "updated_at": datetime.now(UTC)}},
        # Closes the multiline declaration, call, or collection opened above.
    )


# Defines this callable to implement the operation described by its name.
async def rotate_refresh_session(
    # Declares this typed field so the surrounding contract is explicit.
    session: MongoSession,
    # Declares this typed field so the surrounding contract is explicit.
    refresh_token: str,
    # Declares this typed field so the surrounding contract is explicit.
    settings: Settings,
    # Supplies this required nested value.
    *,
    # Stores `ip_hash` because later steps depend on this value.
    ip_hash: str | None = None,
    # Stores `user_agent_hash` because later steps depend on this value.
    user_agent_hash: str | None = None,
    # Closes the multiline declaration, call, or collection opened above.
) -> IssuedSession:
    # Stores `presented_hash` because later steps depend on this value.
    presented_hash = token_hash(refresh_token, settings)
    # Stores `auth_session` because later steps depend on this value.
    auth_session = await session.find_one(AuthSession, {"refresh_token_hash": presented_hash})
    # Guards the nested operation so it runs only when this condition is satisfied.
    if auth_session is None:
        # Stores `reused` because later steps depend on this value.
        reused = await session.find_one(
            # Supplies this required nested value.
            AuthSession,
            {"previous_refresh_token_hash": presented_hash},
            # Closes the multiline declaration, call, or collection opened above.
        )
        # Guards the nested operation so it runs only when this condition is satisfied.
        if reused is not None:
            # Performs this required operation before the surrounding flow continues.
            await revoke_user_sessions(session, reused.user_id)
            # Performs this required operation before the surrounding flow continues.
            await session.commit()
        # Raises this error so invalid state cannot continue silently.
        raise APIError(401, "INVALID_REFRESH_TOKEN", "Your session has expired. Sign in again.")
    # Stores `now` because later steps depend on this value.
    now = datetime.now(UTC)
    # Guards the nested operation so it runs only when this condition is satisfied.
    if auth_session.revoked_at is not None or auth_session.expires_at <= now:
        # Raises this error so invalid state cannot continue silently.
        raise APIError(401, "INVALID_REFRESH_TOKEN", "Your session has expired. Sign in again.")
    # Stores `user` because later steps depend on this value.
    user = await session.get(AuthUser, auth_session.user_id)
    # Guards the nested operation so it runs only when this condition is satisfied.
    if user is None or user.deleted_at is not None:
        # Stores `auth_session.revoked_at` because later steps depend on this value.
        auth_session.revoked_at = now
        # Performs this required operation before the surrounding flow continues.
        await session.commit()
        # Raises this error so invalid state cannot continue silently.
        raise APIError(401, "INVALID_REFRESH_TOKEN", "Your session has expired. Sign in again.")
    # Stores `replacement` because later steps depend on this value.
    replacement = new_refresh_token()
    # Stores `auth_session.previous_refresh_token_hash` because later steps depend on this value.
    auth_session.previous_refresh_token_hash = auth_session.refresh_token_hash
    # Stores `auth_session.refresh_token_hash` because later steps depend on this value.
    auth_session.refresh_token_hash = token_hash(replacement, settings)
    # Stores `auth_session.updated_at` because later steps depend on this value.
    auth_session.updated_at = now
    # Stores `auth_session.last_ip_hash` because later steps depend on this value.
    auth_session.last_ip_hash = ip_hash
    # Stores `auth_session.user_agent_hash` because later steps depend on this value.
    auth_session.user_agent_hash = user_agent_hash
    # Performs this required operation before the surrounding flow continues.
    await session.commit()
    # Supplies this required nested value.
    access_token, principal = mint_access_token(user, auth_session, settings)
    # Returns the computed result and ends the current callable.
    return IssuedSession(
        # Stores `access_token` because later steps depend on this value.
        access_token=access_token,
        # Stores `refresh_token` because later steps depend on this value.
        refresh_token=replacement,
        # Stores `expires_in` because later steps depend on this value.
        expires_in=settings.auth_access_token_seconds,
        # Stores `principal` because later steps depend on this value.
        principal=principal,
        # Closes the multiline declaration, call, or collection opened above.
    )


# Defines this callable to implement the operation described by its name.
async def get_current_user(
    # Declares this typed field so the surrounding contract is explicit.
    request: Request,
    # Stores `authorization` because later steps depend on this value.
    authorization: str | None = Header(default=None),
    # Stores `verifier` because later steps depend on this value.
    verifier: AccessTokenVerifier = Depends(get_verifier),
    # Stores `session` because later steps depend on this value.
    session: MongoSession = Depends(get_session),
    # Closes the multiline declaration, call, or collection opened above.
) -> AuthPrincipal:
    # Guards the nested operation so it runs only when this condition is satisfied.
    if not authorization or not authorization.startswith("Bearer "):
        # Raises this error so invalid state cannot continue silently.
        raise APIError(401, "AUTHENTICATION_REQUIRED", "Sign in or continue as a guest to play.")
    # Stores `token` because later steps depend on this value.
    token = authorization.removeprefix("Bearer ").strip()
    # Guards the nested operation so it runs only when this condition is satisfied.
    if not token:
        # Raises this error so invalid state cannot continue silently.
        raise APIError(401, "AUTHENTICATION_REQUIRED", "Sign in or continue as a guest to play.")
    # Stores `token_principal` because later steps depend on this value.
    token_principal = verifier.verify(token)
    # Performs this required operation before the surrounding flow continues.
    assert token_principal.session_id is not None
    # Stores `auth_session` because later steps depend on this value.
    auth_session = await session.get(AuthSession, uuid.UUID(token_principal.session_id))
    # Stores `user` because later steps depend on this value.
    user = await session.get(AuthUser, token_principal.user_id)
    # Stores `now` because later steps depend on this value.
    now = datetime.now(UTC)
    # Guards the nested operation so it runs only when this condition is satisfied.
    if (
        # Supplies this required nested value.
        auth_session is None
        # Supplies this required nested value.
        or user is None
        # Supplies this required nested value.
        or auth_session.user_id != token_principal.user_id
        # Supplies this required nested value.
        or auth_session.revoked_at is not None
        # Supplies this required nested value.
        or auth_session.expires_at <= now
        # Supplies this required nested value.
        or user.deleted_at is not None
        # Closes the multiline declaration, call, or collection opened above.
    ):
        # Raises this error so invalid state cannot continue silently.
        raise APIError(401, "INVALID_ACCESS_TOKEN", "Your session is invalid or has expired.")
    # Stores `principal` because later steps depend on this value.
    principal = AuthPrincipal(
        # Stores `user_id` because later steps depend on this value.
        user_id=user.id,
        # Stores `is_anonymous` because later steps depend on this value.
        is_anonymous=user.is_anonymous,
        # Stores `session_id` because later steps depend on this value.
        session_id=str(auth_session.id),
        # Stores `issued_at` because later steps depend on this value.
        issued_at=token_principal.issued_at,
        # Stores `authenticated_at` because later steps depend on this value.
        authenticated_at=auth_session.authenticated_at,
        # Stores `assurance_level` because later steps depend on this value.
        assurance_level=auth_session.assurance_level,
        # Closes the multiline declaration, call, or collection opened above.
    )
    # Stores `request.state.principal_id` because later steps depend on this value.
    request.state.principal_id = str(principal.user_id)
    # Returns the computed result and ends the current callable.
    return principal


# Defines this callable to implement the operation described by its name.
async def require_admin(
    # Stores `principal` because later steps depend on this value.
    principal: AuthPrincipal = Depends(get_current_user),
    # Stores `session` because later steps depend on this value.
    session: MongoSession = Depends(get_session),
    # Closes the multiline declaration, call, or collection opened above.
) -> AuthPrincipal:
    # Stores `settings` because later steps depend on this value.
    settings = get_settings()
    # Guards the nested operation so it runs only when this condition is satisfied.
    if principal.is_anonymous:
        # Raises this error so invalid state cannot continue silently.
        raise APIError(403, "ADMIN_REQUIRED", "Administrator access is required.")
    # Guards the nested operation so it runs only when this condition is satisfied.
    if not principal.session_id:
        # Raises this error so invalid state cannot continue silently.
        raise APIError(401, "SESSION_REQUIRED", "Sign in again before using administrator tools.")
    # Guards the nested operation so it runs only when this condition is satisfied.
    if principal.assurance_level != "aal2":
        # Raises this error so invalid state cannot continue silently.
        raise APIError(
            # Supplies this required nested value.
            401,
            # Supplies this literal value to the surrounding declaration or call.
            "MFA_REQUIRED",
            # Supplies this literal value to the surrounding declaration or call.
            "Complete multi-factor authentication before using administrator tools.",
            # Closes the multiline declaration, call, or collection opened above.
        )
    # Guards the nested operation so it runs only when this condition is satisfied.
    if (
        # Supplies this required nested value.
        principal.authenticated_at is None
        # Supplies this required nested value.
        or (datetime.now(UTC) - principal.authenticated_at).total_seconds()
        # Supplies this required nested value.
        > settings.admin_recent_auth_seconds
        # Closes the multiline declaration, call, or collection opened above.
    ):
        # Raises this error so invalid state cannot continue silently.
        raise APIError(
            # Supplies this required nested value.
            401,
            # Supplies this literal value to the surrounding declaration or call.
            "RECENT_AUTH_REQUIRED",
            # Supplies this literal value to the surrounding declaration or call.
            "Sign in again before using administrator tools.",
            # Closes the multiline declaration, call, or collection opened above.
        )
    # Stores `grant` because later steps depend on this value.
    grant = await session.get(AdminGrant, principal.user_id)
    # Stores `profile` because later steps depend on this value.
    profile = await session.get(Profile, principal.user_id)
    # Guards the nested operation so it runs only when this condition is satisfied.
    if (
        # Supplies this required nested value.
        grant is None
        # Supplies this required nested value.
        or grant.revoked_at is not None
        # Supplies this required nested value.
        or profile is None
        # Supplies this required nested value.
        or profile.deleted_at is not None
        # Supplies this required nested value.
        or profile.is_banned
        # Closes the multiline declaration, call, or collection opened above.
    ):
        # Raises this error so invalid state cannot continue silently.
        raise APIError(403, "ADMIN_REQUIRED", "Administrator access is required.")
    # Returns the computed result and ends the current callable.
    return principal
