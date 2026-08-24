# Defers annotation evaluation so modern type hints remain safe at runtime.
from __future__ import annotations

# Imports `asyncio` because this module uses that dependency.
import asyncio

# Imports `base64` because this module uses that dependency.
import base64

# Imports `hashlib` because this module uses that dependency.
import hashlib

# Imports `hmac` because this module uses that dependency.
import hmac

# Imports `re` because this module uses that dependency.
import re

# Imports `secrets` because this module uses that dependency.
import secrets

# Imports `smtplib` because this module uses that dependency.
import smtplib

# Imports `struct` because this module uses that dependency.
import struct

# Imports `time` because this module uses that dependency.
import time

# Imports `urllib.parse` because this module uses that dependency.
import urllib.parse

# Imports `uuid` because this module uses that dependency.
import uuid

# Imports the required names from `datetime` for this module.
from datetime import UTC, datetime, timedelta

# Imports the required names from `email.message` for this module.
from email.message import EmailMessage

# Imports the required names from `fastapi` for this module.
from fastapi import APIRouter, Depends, Request, Response, status

# Imports the required names from `fastapi.responses` for this module.
from fastapi.responses import RedirectResponse

# Imports the required names from `pydantic` for this module.
from pydantic import Field, field_validator

# Imports the required names from `..auth` for this module.
from ..auth import (
    # Supplies this required nested value.
    AuthPrincipal,
    # Supplies this required nested value.
    IssuedSession,
    # Supplies this required nested value.
    create_auth_session,
    # Supplies this required nested value.
    get_current_user,
    # Supplies this required nested value.
    mint_access_token,
    # Supplies this required nested value.
    new_refresh_token,
    # Supplies this required nested value.
    revoke_user_sessions,
    # Supplies this required nested value.
    rotate_refresh_session,
    # Supplies this required nested value.
    token_hash,
    # Closes the multiline declaration, call, or collection opened above.
)

# Imports the required names from `..client_ip` for this module.
from ..client_ip import trusted_client_ip

# Imports the required names from `..config` for this module.
from ..config import Settings, get_settings

# Imports the required names from `..crypto` for this module.
from ..crypto import SecretCipher

# Imports the required names from `..database` for this module.
from ..database import MongoSession, get_session

# Imports the required names from `..dependencies` for this module.
from ..dependencies import get_cipher

# Imports the required names from `..errors` for this module.
from ..errors import APIError

# Imports the required names from `..models` for this module.
from ..models import AuthEmailToken, AuthSession, AuthUser

# Imports the required names from `..rate_limit` for this module.
from ..rate_limit import RateLimiter

# Imports the required names from `..schemas` for this module.
from ..schemas import APIModel

# Stores `router` because later steps depend on this value.
router = APIRouter(prefix='/v1/auth', tags=['auth'])
# Stores `_ALLOWED_NEXT` because later steps depend on this value.
_ALLOWED_NEXT = re.compile(r'^/(?:en|zh-Hant)(?:/[A-Za-z0-9_\-/]*)?$')


# Groups the state and behavior owned by `AuthUserResponse`.
class AuthUserResponse(APIModel):
    # Declares this typed field so the surrounding contract is explicit.
    id: uuid.UUID
    # Declares this typed field so the surrounding contract is explicit.
    email: str | None
    # Declares this typed field so the surrounding contract is explicit.
    is_anonymous: bool
    # Declares this typed field so the surrounding contract is explicit.
    mfa_enabled: bool


# Groups the state and behavior owned by `AuthSessionResponse`.
class AuthSessionResponse(APIModel):
    # Declares this typed field so the surrounding contract is explicit.
    access_token: str
    # Declares this typed field so the surrounding contract is explicit.
    expires_in: int
    # Declares this typed field so the surrounding contract is explicit.
    user: AuthUserResponse


# Groups the state and behavior owned by `EmailLinkRequest`.
class EmailLinkRequest(APIModel):
    # Stores `email` because later steps depend on this value.
    email: str = Field(min_length=3, max_length=254)
    # Stores `next` because later steps depend on this value.
    next: str = Field(default='/en/profile', max_length=200)

    # Applies this decorator to configure the declaration immediately below.
    @field_validator('email')
    # Applies this decorator to configure the declaration immediately below.
    @classmethod
    # Defines this callable to implement the operation described by its name.
    def validate_email(cls, value: str) -> str:
        # Stores `normalized` because later steps depend on this value.
        normalized = value.strip().casefold()
        # Guards the nested operation so it runs only when this condition is satisfied.
        if re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', normalized) is None:
            # Raises this error so invalid state cannot continue silently.
            raise ValueError('Enter a valid email address.')
        # Returns the computed result and ends the current callable.
        return normalized


# Groups the state and behavior owned by `EmailLinkAccepted`.
class EmailLinkAccepted(APIModel):
    # Stores `accepted` because later steps depend on this value.
    accepted: bool = True


# Groups the state and behavior owned by `TotpSetupResponse`.
class TotpSetupResponse(APIModel):
    # Declares this typed field so the surrounding contract is explicit.
    secret: str
    # Declares this typed field so the surrounding contract is explicit.
    uri: str


# Groups the state and behavior owned by `TotpVerifyRequest`.
class TotpVerifyRequest(APIModel):
    # Stores `code` because later steps depend on this value.
    code: str = Field(min_length=6, max_length=6, pattern=r'^\d{6}$')


# Groups the state and behavior owned by `AccessTokenResponse`.
class AccessTokenResponse(APIModel):
    # Declares this typed field so the surrounding contract is explicit.
    access_token: str
    # Declares this typed field so the surrounding contract is explicit.
    expires_in: int


# Defines this callable to implement the operation described by its name.
def _request_fingerprints(request: Request, settings: Settings) -> tuple[str | None, str | None]:
    # Stores `peer` because later steps depend on this value.
    peer = trusted_client_ip(
        # Supplies this required nested value.
        request.client.host if request.client else None,
        # Supplies this required nested value.
        request.headers.get('x-forwarded-for'),
        # Supplies this required nested value.
        settings.trusted_proxy_ips,
    # Closes the multiline declaration, call, or collection opened above.
    )
    # Stores `ip_hash` because later steps depend on this value.
    ip_hash = (
        # Supplies this required nested value.
        hmac.new(settings.auth_signing_key.encode(), peer.encode(), hashlib.sha256).hexdigest()
        # Guards the nested operation so it runs only when this condition is satisfied.
        if peer
        # Supplies this required nested value.
        else None
    # Closes the multiline declaration, call, or collection opened above.
    )
    # Stores `user_agent` because later steps depend on this value.
    user_agent = request.headers.get('user-agent', '')[:512]
    # Stores `user_agent_hash` because later steps depend on this value.
    user_agent_hash = hashlib.sha256(user_agent.encode()).hexdigest() if user_agent else None
    # Returns the computed result and ends the current callable.
    return ip_hash, user_agent_hash


# Defines this callable to implement the operation described by its name.
def _auth_user_response(user: AuthUser) -> AuthUserResponse:
    # Returns the computed result and ends the current callable.
    return AuthUserResponse(
        # Stores `id` because later steps depend on this value.
        id=user.id,
        # Stores `email` because later steps depend on this value.
        email=user.email,
        # Stores `is_anonymous` because later steps depend on this value.
        is_anonymous=user.is_anonymous,
        # Stores `mfa_enabled` because later steps depend on this value.
        mfa_enabled=user.totp_enabled_at is not None,
    # Closes the multiline declaration, call, or collection opened above.
    )


# Defines this callable to implement the operation described by its name.
def _session_response(issued: IssuedSession, user: AuthUser) -> AuthSessionResponse:
    # Returns the computed result and ends the current callable.
    return AuthSessionResponse(
        # Stores `access_token` because later steps depend on this value.
        access_token=issued.access_token,
        # Stores `expires_in` because later steps depend on this value.
        expires_in=issued.expires_in,
        # Stores `user` because later steps depend on this value.
        user=_auth_user_response(user),
    # Closes the multiline declaration, call, or collection opened above.
    )


# Defines this callable to implement the operation described by its name.
def _set_refresh_cookie(response: Response, refresh_token: str, settings: Settings) -> None:
    # Supplies this required nested value.
    response.set_cookie(
        # Supplies this required nested value.
        settings.auth_cookie_name,
        # Supplies this required nested value.
        refresh_token,
        # Stores `max_age` because later steps depend on this value.
        max_age=settings.auth_refresh_token_days * 24 * 60 * 60,
        # Stores `path` because later steps depend on this value.
        path='/v1/auth',
        # Stores `secure` because later steps depend on this value.
        secure=settings.auth_cookie_secure,
        # Stores `httponly` because later steps depend on this value.
        httponly=True,
        # Stores `samesite` because later steps depend on this value.
        samesite=settings.auth_cookie_samesite,
    # Closes the multiline declaration, call, or collection opened above.
    )


# Defines this callable to implement the operation described by its name.
def _clear_refresh_cookie(response: Response, settings: Settings) -> None:
    # Supplies this required nested value.
    response.delete_cookie(
        # Supplies this required nested value.
        settings.auth_cookie_name,
        # Stores `path` because later steps depend on this value.
        path='/v1/auth',
        # Stores `secure` because later steps depend on this value.
        secure=settings.auth_cookie_secure,
        # Stores `httponly` because later steps depend on this value.
        httponly=True,
        # Stores `samesite` because later steps depend on this value.
        samesite=settings.auth_cookie_samesite,
    # Closes the multiline declaration, call, or collection opened above.
    )


# Defines this callable to implement the operation described by its name.
async def _send_email(settings: Settings, recipient: str, link: str) -> None:
    # Stores `message` because later steps depend on this value.
    message = EmailMessage()
    # Supplies this required nested value.
    message['Subject'] = f'Sign in to {settings.product_name}'
    # Supplies this required nested value.
    message['From'] = settings.auth_email_sender
    # Supplies this required nested value.
    message['To'] = recipient
    # Supplies this required nested value.
    message.set_content(
        # Supplies this required nested value.
        f'Use this one-time link to sign in to {settings.product_name}:\n\n{link}\n\n'
        # Supplies this literal value to the surrounding declaration or call.
        'The link expires in 15 minutes. If you did not request it, ignore this message.'
    # Closes the multiline declaration, call, or collection opened above.
    )

    # Defines this callable to implement the operation described by its name.
    def deliver() -> None:
        # Scopes this resource so acquisition and cleanup remain paired.
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as client:
            # Guards the nested operation so it runs only when this condition is satisfied.
            if settings.smtp_starttls:
                # Supplies this required nested value.
                client.starttls()
            # Guards the nested operation so it runs only when this condition is satisfied.
            if settings.smtp_username:
                # Supplies this required nested value.
                client.login(settings.smtp_username, settings.smtp_password)
            # Supplies this required nested value.
            client.send_message(message)

    # Starts an operation whose expected failures are handled below.
    try:
        # Performs this required operation before the surrounding flow continues.
        await asyncio.to_thread(deliver)
    # Converts this expected failure into the controlled behavior below.
    except (OSError, smtplib.SMTPException) as exc:
        # Raises this error so invalid state cannot continue silently.
        raise APIError(
            # Supplies this required nested value.
            503, 'EMAIL_UNAVAILABLE', 'Sign-in email is temporarily unavailable.'
        # Closes the multiline declaration, call, or collection opened above.
        ) from exc


# Applies this decorator to configure the declaration immediately below.
@router.post('/guest', response_model=AuthSessionResponse, status_code=status.HTTP_201_CREATED)
# Defines this callable to implement the operation described by its name.
async def create_guest_session(
    # Declares this typed field so the surrounding contract is explicit.
    request: Request,
    # Declares this typed field so the surrounding contract is explicit.
    response: Response,
    # Stores `settings` because later steps depend on this value.
    settings: Settings = Depends(get_settings),
    # Stores `session` because later steps depend on this value.
    session: MongoSession = Depends(get_session),
# Closes the multiline declaration, call, or collection opened above.
) -> AuthSessionResponse:
    # Stores `limiter` because later steps depend on this value.
    limiter: RateLimiter = request.app.state.rate_limiter
    # Supplies this required nested value.
    ip_hash, user_agent_hash = _request_fingerprints(request, settings)
    # Performs this required operation before the surrounding flow continues.
    await limiter.check(f'auth-guest:{ip_hash or "unknown"}', weight=4)
    # Stores `user` because later steps depend on this value.
    user = AuthUser()
    # Supplies this required nested value.
    session.add(user)
    # Stores `issued` because later steps depend on this value.
    issued = await create_auth_session(
        # Supplies this required nested value.
        session,
        # Supplies this required nested value.
        user,
        # Supplies this required nested value.
        settings,
        # Stores `ip_hash` because later steps depend on this value.
        ip_hash=ip_hash,
        # Stores `user_agent_hash` because later steps depend on this value.
        user_agent_hash=user_agent_hash,
    # Closes the multiline declaration, call, or collection opened above.
    )
    # Supplies this required nested value.
    _set_refresh_cookie(response, issued.refresh_token, settings)
    # Returns the computed result and ends the current callable.
    return _session_response(issued, user)


# Applies this decorator to configure the declaration immediately below.
@router.post('/refresh', response_model=AuthSessionResponse)
# Defines this callable to implement the operation described by its name.
async def refresh_session(
    # Declares this typed field so the surrounding contract is explicit.
    request: Request,
    # Declares this typed field so the surrounding contract is explicit.
    response: Response,
    # Stores `settings` because later steps depend on this value.
    settings: Settings = Depends(get_settings),
    # Stores `session` because later steps depend on this value.
    session: MongoSession = Depends(get_session),
# Closes the multiline declaration, call, or collection opened above.
) -> AuthSessionResponse:
    # Stores `refresh_token` because later steps depend on this value.
    refresh_token = request.cookies.get(settings.auth_cookie_name)
    # Guards the nested operation so it runs only when this condition is satisfied.
    if not refresh_token:
        # Raises this error so invalid state cannot continue silently.
        raise APIError(401, 'INVALID_REFRESH_TOKEN', 'Your session has expired. Sign in again.')
    # Supplies this required nested value.
    ip_hash, user_agent_hash = _request_fingerprints(request, settings)
    # Stores `issued` because later steps depend on this value.
    issued = await rotate_refresh_session(
        # Supplies this required nested value.
        session,
        # Supplies this required nested value.
        refresh_token,
        # Supplies this required nested value.
        settings,
        # Stores `ip_hash` because later steps depend on this value.
        ip_hash=ip_hash,
        # Stores `user_agent_hash` because later steps depend on this value.
        user_agent_hash=user_agent_hash,
    # Closes the multiline declaration, call, or collection opened above.
    )
    # Stores `user` because later steps depend on this value.
    user = await session.get(AuthUser, issued.principal.user_id)
    # Performs this required operation before the surrounding flow continues.
    assert user is not None
    # Supplies this required nested value.
    _set_refresh_cookie(response, issued.refresh_token, settings)
    # Returns the computed result and ends the current callable.
    return _session_response(issued, user)


# Applies this decorator to configure the declaration immediately below.
@router.post('/logout', status_code=status.HTTP_204_NO_CONTENT)
# Defines this callable to implement the operation described by its name.
async def logout(
    # Declares this typed field so the surrounding contract is explicit.
    request: Request,
    # Declares this typed field so the surrounding contract is explicit.
    response: Response,
    # Stores `settings` because later steps depend on this value.
    settings: Settings = Depends(get_settings),
    # Stores `session` because later steps depend on this value.
    session: MongoSession = Depends(get_session),
# Closes the multiline declaration, call, or collection opened above.
) -> None:
    # Stores `refresh_token` because later steps depend on this value.
    refresh_token = request.cookies.get(settings.auth_cookie_name)
    # Guards the nested operation so it runs only when this condition is satisfied.
    if refresh_token:
        # Stores `auth_session` because later steps depend on this value.
        auth_session = await session.find_one(
            # Supplies this required nested value.
            AuthSession, {'refresh_token_hash': token_hash(refresh_token, settings)}
        # Closes the multiline declaration, call, or collection opened above.
        )
        # Guards the nested operation so it runs only when this condition is satisfied.
        if auth_session is not None:
            # Stores `auth_session.revoked_at` because later steps depend on this value.
            auth_session.revoked_at = datetime.now(UTC)
            # Performs this required operation before the surrounding flow continues.
            await session.commit()
    # Supplies this required nested value.
    _clear_refresh_cookie(response, settings)


# Applies this decorator to configure the declaration immediately below.
@router.post('/email', response_model=EmailLinkAccepted, status_code=status.HTTP_202_ACCEPTED)
# Defines this callable to implement the operation described by its name.
async def send_email_link(
    # Declares this typed field so the surrounding contract is explicit.
    payload: EmailLinkRequest,
    # Declares this typed field so the surrounding contract is explicit.
    request: Request,
    # Stores `principal` because later steps depend on this value.
    principal: AuthPrincipal = Depends(get_current_user),
    # Stores `settings` because later steps depend on this value.
    settings: Settings = Depends(get_settings),
    # Stores `session` because later steps depend on this value.
    session: MongoSession = Depends(get_session),
# Closes the multiline declaration, call, or collection opened above.
) -> EmailLinkAccepted:
    # Guards the nested operation so it runs only when this condition is satisfied.
    if not settings.feature_account_registration:
        # Raises this error so invalid state cannot continue silently.
        raise APIError(503, 'ACCOUNT_REGISTRATION_DISABLED', 'Account registration is unavailable.')
    # Stores `normalized_email` because later steps depend on this value.
    normalized_email = str(payload.email).strip().casefold()
    # Stores `limiter` because later steps depend on this value.
    limiter: RateLimiter = request.app.state.rate_limiter
    # Supplies this required nested value.
    ip_hash, _ = _request_fingerprints(request, settings)
    # Stores `email_hash` because later steps depend on this value.
    email_hash = hmac.new(
        # Supplies this required nested value.
        settings.auth_signing_key.encode(), normalized_email.encode(), hashlib.sha256
    # Closes the multiline declaration, call, or collection opened above.
    ).hexdigest()
    # Performs this required operation before the surrounding flow continues.
    await limiter.check(f'auth-email:{ip_hash or "unknown"}:{email_hash}', weight=12)
    # Stores `current_user` because later steps depend on this value.
    current_user = await session.get(AuthUser, principal.user_id)
    # Guards the nested operation so it runs only when this condition is satisfied.
    if current_user is None or current_user.deleted_at is not None:
        # Raises this error so invalid state cannot continue silently.
        raise APIError(401, 'INVALID_ACCESS_TOKEN', 'Your session is invalid or has expired.')
    # Stores `existing_user` because later steps depend on this value.
    existing_user = await session.find_one(AuthUser, {'normalized_email': normalized_email})
    # Stores `target_user` because later steps depend on this value.
    target_user = existing_user or current_user
    # Stores `purpose` because later steps depend on this value.
    purpose = 'signin' if existing_user is not None else 'upgrade'
    # Stores `raw_token` because later steps depend on this value.
    raw_token = new_refresh_token()
    # Stores `email_token` because later steps depend on this value.
    email_token = AuthEmailToken(
        # Stores `user_id` because later steps depend on this value.
        user_id=target_user.id,
        # Stores `normalized_email` because later steps depend on this value.
        normalized_email=normalized_email,
        # Stores `token_hash` because later steps depend on this value.
        token_hash=token_hash(raw_token, settings),
        # Stores `purpose` because later steps depend on this value.
        purpose=purpose,
        # Stores `expires_at` because later steps depend on this value.
        expires_at=datetime.now(UTC) + timedelta(seconds=settings.auth_email_token_seconds),
    # Closes the multiline declaration, call, or collection opened above.
    )
    # Supplies this required nested value.
    session.add(email_token)
    # Performs this required operation before the surrounding flow continues.
    await session.commit()
    # Stores `requested_next` because later steps depend on this value.
    requested_next = payload.next if _ALLOWED_NEXT.fullmatch(payload.next) else '/en/profile'
    # Stores `query` because later steps depend on this value.
    query = urllib.parse.urlencode({'token': raw_token, 'next': requested_next})
    # Stores `link` because later steps depend on this value.
    link = f'{settings.auth_issuer}/v1/auth/email/verify?{query}'
    # Performs this required operation before the surrounding flow continues.
    await _send_email(settings, normalized_email, link)
    # Returns the computed result and ends the current callable.
    return EmailLinkAccepted()


# Applies this decorator to configure the declaration immediately below.
@router.get('/email/verify')
# Defines this callable to implement the operation described by its name.
async def verify_email_link(
    # Declares this typed field so the surrounding contract is explicit.
    token: str,
    # Stores `next` because later steps depend on this value.
    next: str = '/en/profile',
    # Stores `settings` because later steps depend on this value.
    settings: Settings = Depends(get_settings),
    # Stores `session` because later steps depend on this value.
    session: MongoSession = Depends(get_session),
# Closes the multiline declaration, call, or collection opened above.
) -> RedirectResponse:
    # Stores `normalized_next` because later steps depend on this value.
    normalized_next = next if _ALLOWED_NEXT.fullmatch(next) else '/en/profile'
    # Stores `email_token` because later steps depend on this value.
    email_token = await session.find_one(
        # Supplies this required nested value.
        AuthEmailToken,
        # Supplies this required nested value.
        {
            # Supplies this literal value to the surrounding declaration or call.
            'token_hash': token_hash(token, settings),
            # Supplies this literal value to the surrounding declaration or call.
            'consumed_at': None,
            # Supplies this literal value to the surrounding declaration or call.
            'expires_at': {'$gt': datetime.now(UTC)},
        # Closes the multiline declaration, call, or collection opened above.
        },
    # Closes the multiline declaration, call, or collection opened above.
    )
    # Guards the nested operation so it runs only when this condition is satisfied.
    if email_token is None:
        # Returns the computed result and ends the current callable.
        return RedirectResponse(
            # Supplies this required nested value.
            f'{settings.product_origin}/en/auth?error=invalid_callback', status_code=303
        # Closes the multiline declaration, call, or collection opened above.
        )
    # Stores `user` because later steps depend on this value.
    user = await session.get(AuthUser, email_token.user_id)
    # Guards the nested operation so it runs only when this condition is satisfied.
    if user is None or user.deleted_at is not None:
        # Returns the computed result and ends the current callable.
        return RedirectResponse(
            # Supplies this required nested value.
            f'{settings.product_origin}/en/auth?error=invalid_callback', status_code=303
        # Closes the multiline declaration, call, or collection opened above.
        )
    # Stores `now` because later steps depend on this value.
    now = datetime.now(UTC)
    # Stores `email_token.consumed_at` because later steps depend on this value.
    email_token.consumed_at = now
    # Guards the nested operation so it runs only when this condition is satisfied.
    if email_token.purpose == 'upgrade':
        # Stores `user.email` because later steps depend on this value.
        user.email = email_token.normalized_email
        # Stores `user.normalized_email` because later steps depend on this value.
        user.normalized_email = email_token.normalized_email
        # Stores `user.email_verified_at` because later steps depend on this value.
        user.email_verified_at = now
        # Stores `user.is_anonymous` because later steps depend on this value.
        user.is_anonymous = False
    # Performs this required operation before the surrounding flow continues.
    await revoke_user_sessions(session, user.id)
    # Stores `ip_hash` because later steps depend on this value.
    ip_hash = None
    # Stores `user_agent_hash` because later steps depend on this value.
    user_agent_hash = None
    # Stores `issued` because later steps depend on this value.
    issued = await create_auth_session(
        # Supplies this required nested value.
        session,
        # Supplies this required nested value.
        user,
        # Supplies this required nested value.
        settings,
        # Stores `ip_hash` because later steps depend on this value.
        ip_hash=ip_hash,
        # Stores `user_agent_hash` because later steps depend on this value.
        user_agent_hash=user_agent_hash,
    # Closes the multiline declaration, call, or collection opened above.
    )
    # Stores `destination` because later steps depend on this value.
    destination = f'{settings.product_origin}{normalized_next}'
    # Stores `response` because later steps depend on this value.
    response = RedirectResponse(destination, status_code=303)
    # Supplies this required nested value.
    _set_refresh_cookie(response, issued.refresh_token, settings)
    # Returns the computed result and ends the current callable.
    return response


# Defines this callable to implement the operation described by its name.
def _totp(secret: bytes, counter: int) -> str:
    # Stores `digest` because later steps depend on this value.
    digest = hmac.new(secret, struct.pack('>Q', counter), hashlib.sha1).digest()
    # Stores `offset` because later steps depend on this value.
    offset = digest[-1] & 0x0F
    # Stores `value` because later steps depend on this value.
    value = (struct.unpack('>I', digest[offset : offset + 4])[0] & 0x7FFFFFFF) % 1_000_000
    # Returns the computed result and ends the current callable.
    return f'{value:06d}'


# Defines this callable to implement the operation described by its name.
def _valid_totp(secret: bytes, code: str, now: int | None = None) -> bool:
    # Stores `counter` because later steps depend on this value.
    counter = (now or int(time.time())) // 30
    # Returns the computed result and ends the current callable.
    return any(hmac.compare_digest(_totp(secret, counter + drift), code) for drift in (-1, 0, 1))


# Defines this callable to implement the operation described by its name.
def _totp_context(user_id: uuid.UUID) -> str:
    # Returns the computed result and ends the current callable.
    return f'auth-totp:{user_id}'


# Applies this decorator to configure the declaration immediately below.
@router.post('/mfa/totp/setup', response_model=TotpSetupResponse)
# Defines this callable to implement the operation described by its name.
async def setup_totp(
    # Stores `principal` because later steps depend on this value.
    principal: AuthPrincipal = Depends(get_current_user),
    # Stores `session` because later steps depend on this value.
    session: MongoSession = Depends(get_session),
    # Stores `cipher` because later steps depend on this value.
    cipher: SecretCipher = Depends(get_cipher),
    # Stores `settings` because later steps depend on this value.
    settings: Settings = Depends(get_settings),
# Closes the multiline declaration, call, or collection opened above.
) -> TotpSetupResponse:
    # Guards the nested operation so it runs only when this condition is satisfied.
    if principal.is_anonymous:
        # Raises this error so invalid state cannot continue silently.
        raise APIError(403, 'REGISTERED_ACCOUNT_REQUIRED', 'Register before enabling MFA.')
    # Stores `user` because later steps depend on this value.
    user = await session.get(AuthUser, principal.user_id)
    # Guards the nested operation so it runs only when this condition is satisfied.
    if user is None or not user.normalized_email:
        # Raises this error so invalid state cannot continue silently.
        raise APIError(404, 'ACCOUNT_NOT_FOUND', 'Account not found.')
    # Stores `secret` because later steps depend on this value.
    secret = secrets.token_bytes(20)
    # Stores `encoded_secret` because later steps depend on this value.
    encoded_secret = base64.b32encode(secret).decode().rstrip('=')
    # Stores `encrypted` because later steps depend on this value.
    encrypted = cipher.encrypt((encoded_secret,), context=_totp_context(user.id))
    # Stores `user.totp_secret_ciphertext` because later steps depend on this value.
    user.totp_secret_ciphertext = encrypted.ciphertext
    # Stores `user.totp_secret_nonce` because later steps depend on this value.
    user.totp_secret_nonce = encrypted.nonce
    # Stores `user.totp_secret_key_version` because later steps depend on this value.
    user.totp_secret_key_version = encrypted.key_version
    # Stores `user.totp_enabled_at` because later steps depend on this value.
    user.totp_enabled_at = None
    # Performs this required operation before the surrounding flow continues.
    await session.commit()
    # Stores `label` because later steps depend on this value.
    label = urllib.parse.quote(f'{settings.product_name}:{user.normalized_email}')
    # Stores `issuer` because later steps depend on this value.
    issuer = urllib.parse.quote(settings.product_name)
    # Stores `uri` because later steps depend on this value.
    uri = f'otpauth://totp/{label}?secret={encoded_secret}&issuer={issuer}&algorithm=SHA1&digits=6&period=30'
    # Returns the computed result and ends the current callable.
    return TotpSetupResponse(secret=encoded_secret, uri=uri)


# Applies this decorator to configure the declaration immediately below.
@router.post('/mfa/totp/verify', response_model=AccessTokenResponse)
# Defines this callable to implement the operation described by its name.
async def verify_totp(
    # Declares this typed field so the surrounding contract is explicit.
    payload: TotpVerifyRequest,
    # Declares this typed field so the surrounding contract is explicit.
    request: Request,
    # Stores `principal` because later steps depend on this value.
    principal: AuthPrincipal = Depends(get_current_user),
    # Stores `session` because later steps depend on this value.
    session: MongoSession = Depends(get_session),
    # Stores `cipher` because later steps depend on this value.
    cipher: SecretCipher = Depends(get_cipher),
    # Stores `settings` because later steps depend on this value.
    settings: Settings = Depends(get_settings),
# Closes the multiline declaration, call, or collection opened above.
) -> AccessTokenResponse:
    # Stores `limiter` because later steps depend on this value.
    limiter: RateLimiter = request.app.state.rate_limiter
    # Performs this required operation before the surrounding flow continues.
    await limiter.check(f'auth-totp:{principal.user_id}', weight=20)
    # Stores `user` because later steps depend on this value.
    user = await session.get(AuthUser, principal.user_id)
    # Stores `auth_session` because later steps depend on this value.
    auth_session = (
        # Performs this required operation before the surrounding flow continues.
        await session.get(AuthSession, uuid.UUID(principal.session_id))
        # Guards the nested operation so it runs only when this condition is satisfied.
        if principal.session_id
        # Supplies this required nested value.
        else None
    # Closes the multiline declaration, call, or collection opened above.
    )
    # Guards the nested operation so it runs only when this condition is satisfied.
    if (
        # Supplies this required nested value.
        user is None
        # Supplies this required nested value.
        or auth_session is None
        # Supplies this required nested value.
        or user.totp_secret_ciphertext is None
        # Supplies this required nested value.
        or user.totp_secret_nonce is None
        # Supplies this required nested value.
        or user.totp_secret_key_version is None
    # Closes the multiline declaration, call, or collection opened above.
    ):
        # Raises this error so invalid state cannot continue silently.
        raise APIError(409, 'MFA_NOT_CONFIGURED', 'Set up MFA before verifying a code.')
    # Stores `encoded_secret` because later steps depend on this value.
    encoded_secret = cipher.decrypt(
        # Supplies this required nested value.
        user.totp_secret_ciphertext,
        # Supplies this required nested value.
        user.totp_secret_nonce,
        # Supplies this required nested value.
        user.totp_secret_key_version,
        # Stores `context` because later steps depend on this value.
        context=_totp_context(user.id),
    # Closes the multiline declaration, call, or collection opened above.
    )[0]
    # Stores `padded` because later steps depend on this value.
    padded = encoded_secret + '=' * (-len(encoded_secret) % 8)
    # Stores `secret` because later steps depend on this value.
    secret = base64.b32decode(padded, casefold=True)
    # Guards the nested operation so it runs only when this condition is satisfied.
    if not _valid_totp(secret, payload.code):
        # Raises this error so invalid state cannot continue silently.
        raise APIError(401, 'INVALID_MFA_CODE', 'The authentication code is invalid.')
    # Stores `now` because later steps depend on this value.
    now = datetime.now(UTC)
    # Stores `user.totp_enabled_at` because later steps depend on this value.
    user.totp_enabled_at = user.totp_enabled_at or now
    # Stores `auth_session.assurance_level` because later steps depend on this value.
    auth_session.assurance_level = 'aal2'
    # Stores `auth_session.authenticated_at` because later steps depend on this value.
    auth_session.authenticated_at = now
    # Performs this required operation before the surrounding flow continues.
    await session.commit()
    # Supplies this required nested value.
    access_token, _ = mint_access_token(user, auth_session, settings)
    # Returns the computed result and ends the current callable.
    return AccessTokenResponse(
        # Stores `access_token` because later steps depend on this value.
        access_token=access_token, expires_in=settings.auth_access_token_seconds
    # Closes the multiline declaration, call, or collection opened above.
    )
