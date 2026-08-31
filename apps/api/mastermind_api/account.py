from __future__ import annotations

import asyncio
import uuid
from collections.abc import Awaitable, Callable
from datetime import timedelta
from functools import lru_cache

import httpx
import structlog
from fastapi import Depends
from sqlalchemy import or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .auth import AuthPrincipal
from .config import Settings, get_settings
from .errors import APIError
from .models import AccountDeletionRequest
from .services import delete_account, ensure_aware, utcnow


class IdentityProviderError(RuntimeError):
    pass


RETRY_LEASE_SECONDS = 30


class SupabaseAdminClient:
    def __init__(self, supabase_url: str, service_role_key: str) -> None:
        self._url = supabase_url.rstrip("/")
        self._service_role_key = service_role_key

    async def delete_user(self, user_id: uuid.UUID) -> None:
        if not self._url or not self._service_role_key:
            raise IdentityProviderError("provider_not_configured")
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
                response = await client.delete(
                    f"{self._url}/auth/v1/admin/users/{user_id}",
                    headers={
                        "apikey": self._service_role_key,
                        "Authorization": f"Bearer {self._service_role_key}",
                    },
                )
        except httpx.HTTPError as exc:
            raise IdentityProviderError("provider_unavailable") from exc
        if response.status_code not in {200, 204, 404}:
            raise IdentityProviderError("provider_rejected")

    async def revoke_sessions(self, access_token: str) -> None:
        if not self._url or not self._service_role_key:
            raise IdentityProviderError("provider_not_configured")
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
                response = await client.post(
                    f"{self._url}/auth/v1/logout?scope=global",
                    headers={
                        "apikey": self._service_role_key,
                        "Authorization": f"Bearer {access_token}",
                    },
                )
        except httpx.HTTPError as exc:
            raise IdentityProviderError("provider_unavailable") from exc
        if response.status_code not in {200, 204, 401, 404}:
            raise IdentityProviderError("provider_rejected")


@lru_cache
def _provider(supabase_url: str, service_role_key: str) -> SupabaseAdminClient:
    return SupabaseAdminClient(supabase_url, service_role_key)


def get_deletion_provider(settings: Settings = Depends(get_settings)) -> SupabaseAdminClient:
    return _provider(settings.supabase_server_url, settings.supabase_service_role_key)


async def process_account_deletion(
    session: AsyncSession,
    principal: AuthPrincipal,
    provider: SupabaseAdminClient,
    access_token: str,
) -> None:
    deletion = await session.scalar(
        select(AccountDeletionRequest).where(AccountDeletionRequest.user_id == principal.user_id)
    )
    if deletion and deletion.status == "completed":
        return
    if deletion is None:
        deletion = AccountDeletionRequest(user_id=principal.user_id)
        session.add(deletion)
        await session.flush()
    await delete_account(session, principal)
    deletion.status = "pending"
    deletion.provider_attempts += 1
    deletion.last_attempt_at = utcnow()
    await session.commit()
    try:
        await provider.revoke_sessions(access_token)
        await provider.delete_user(principal.user_id)
    except IdentityProviderError as exc:
        deletion.status = "provider_failed"
        deletion.last_error_code = str(exc)
        await session.commit()
        raise APIError(
            503,
            "ACCOUNT_DELETION_PENDING",
            "Account deletion is pending and will retry automatically.",
        ) from exc
    deletion.status = "completed"
    deletion.last_error_code = None
    deletion.completed_at = utcnow()
    await session.commit()


async def retry_pending_account_deletions(
    sessions: async_sessionmaker[AsyncSession],
    provider: SupabaseAdminClient,
    *,
    batch_size: int = 25,
) -> int:
    """Lease and retry a bounded batch without holding a transaction over HTTP."""
    retry_before = utcnow() - timedelta(seconds=RETRY_LEASE_SECONDS)
    async with sessions() as session:
        user_ids = list(
            await session.scalars(
                select(AccountDeletionRequest.user_id)
                .where(
                    AccountDeletionRequest.status.in_(["pending", "provider_failed"]),
                    or_(
                        AccountDeletionRequest.last_attempt_at.is_(None),
                        AccountDeletionRequest.last_attempt_at <= retry_before,
                    ),
                )
                .order_by(AccountDeletionRequest.requested_at)
                .limit(batch_size)
            )
        )
    completed = 0
    for user_id in user_ids:
        async with sessions() as session:
            deletion = await session.scalar(
                select(AccountDeletionRequest)
                .where(AccountDeletionRequest.user_id == user_id)
                .with_for_update(skip_locked=True)
            )
            if (
                deletion is None
                or deletion.status not in {"pending", "provider_failed"}
                or (
                    deletion.last_attempt_at is not None
                    and ensure_aware(deletion.last_attempt_at) > retry_before
                )
            ):
                continue
            deletion.provider_attempts += 1
            deletion.last_attempt_at = utcnow()
            await session.commit()
        try:
            await provider.delete_user(user_id)
        except IdentityProviderError as exc:
            async with sessions() as session:
                deletion = await session.scalar(
                    select(AccountDeletionRequest)
                    .where(AccountDeletionRequest.user_id == user_id)
                    .with_for_update()
                )
                if deletion is not None and deletion.status != "completed":
                    deletion.status = "provider_failed"
                    deletion.last_error_code = str(exc)
                    await session.commit()
        else:
            async with sessions() as session:
                deletion = await session.scalar(
                    select(AccountDeletionRequest)
                    .where(AccountDeletionRequest.user_id == user_id)
                    .with_for_update()
                )
                if deletion is None:
                    continue
                deletion.status = "completed"
                deletion.last_error_code = None
                deletion.completed_at = utcnow()
                await session.commit()
            completed += 1
    return completed


async def account_deletion_retry_worker(
    sessions: async_sessionmaker[AsyncSession],
    provider: SupabaseAdminClient,
    *,
    interval_seconds: float = 30,
    wait: Callable[[float], Awaitable[None]] = asyncio.sleep,
) -> None:
    while True:
        try:
            await retry_pending_account_deletions(sessions, provider)
        except SQLAlchemyError:
            structlog.get_logger().exception("account_deletion_retry_failed")
        await wait(interval_seconds)
