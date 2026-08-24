# Defers type-annotation evaluation to support modern hints safely.
from __future__ import annotations

# Imports `asyncio` so the module can use that dependency.
import asyncio

# Imports `uuid` so the module can use that dependency.
import uuid

# Imports selected names from `collections.abc` for use in this module.
from collections.abc import Awaitable, Callable

# Imports selected names from `datetime` for use in this module.
from datetime import timedelta

# Imports selected names from `functools` for use in this module.
from functools import lru_cache

# Imports `httpx` so the module can use that dependency.
import httpx

# Imports `structlog` so the module can use that dependency.
import structlog

# Imports selected names from `fastapi` for use in this module.
from fastapi import Depends

# Imports selected names from `sqlalchemy` for use in this module.
from sqlalchemy import or_, select

# Imports selected names from `sqlalchemy.exc` for use in this module.
from sqlalchemy.exc import SQLAlchemyError

# Imports selected names from `sqlalchemy.ext.asyncio` for use in this module.
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

# Imports selected names from `.auth` for use in this module.
from .auth import AuthPrincipal

# Imports selected names from `.config` for use in this module.
from .config import Settings, get_settings

# Imports selected names from `.errors` for use in this module.
from .errors import APIError

# Imports selected names from `.models` for use in this module.
from .models import AccountDeletionRequest

# Imports selected names from `.services` for use in this module.
from .services import delete_account, ensure_aware, utcnow


# Defines the `IdentityProviderError` class and its related behavior.
class IdentityProviderError(RuntimeError):
    # Provides the intentionally empty statement required by Python syntax.
    pass


# Computes and stores `RETRY_LEASE_SECONDS` for subsequent operations.
RETRY_LEASE_SECONDS = 30


# Defines the `SupabaseAdminClient` class and its related behavior.
class SupabaseAdminClient:
    # Defines the `__init__` callable and its typed interface.
    def __init__(self, supabase_url: str, service_role_key: str) -> None:
        # Computes and stores `self._url` for subsequent operations.
        self._url = supabase_url.rstrip("/")
        # Computes and stores `self._service_role_key` for subsequent operations.
        self._service_role_key = service_role_key

    # Defines the `delete_user` callable and its typed interface.
    async def delete_user(self, user_id: uuid.UUID) -> None:
        # Checks this condition before executing the nested branch.
        if not self._url or not self._service_role_key:
            # Raises this exception to report an invalid or failed operation.
            raise IdentityProviderError("provider_not_configured")
        # Starts a protected operation whose expected failures are handled below.
        try:
            # Acquires this asynchronous managed resource for the nested operation.
            async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
                # Computes and stores `response` for subsequent operations.
                response = await client.delete(
                    # Supplies this item to the surrounding call or collection.
                    f"{self._url}/auth/v1/admin/users/{user_id}",
                    # Computes and stores `headers` for subsequent operations.
                    headers={
                        # Associates the `apikey` key with its value.
                        "apikey": self._service_role_key,
                        # Associates the `Authorization` key with its value.
                        "Authorization": f"Bearer {self._service_role_key}",
                        # Closes the multiline call, declaration, or collection started above.
                    },
                    # Closes the multiline call, declaration, or collection started above.
                )
        # Handles the listed exception so failure remains controlled.
        except httpx.HTTPError as exc:
            # Raises this exception to report an invalid or failed operation.
            raise IdentityProviderError("provider_unavailable") from exc
        # Checks this condition before executing the nested branch.
        if response.status_code not in {200, 204, 404}:
            # Raises this exception to report an invalid or failed operation.
            raise IdentityProviderError("provider_rejected")

    # Defines the `revoke_sessions` callable and its typed interface.
    async def revoke_sessions(self, access_token: str) -> None:
        # Checks this condition before executing the nested branch.
        if not self._url or not self._service_role_key:
            # Raises this exception to report an invalid or failed operation.
            raise IdentityProviderError("provider_not_configured")
        # Starts a protected operation whose expected failures are handled below.
        try:
            # Acquires this asynchronous managed resource for the nested operation.
            async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
                # Computes and stores `response` for subsequent operations.
                response = await client.post(
                    # Supplies this item to the surrounding call or collection.
                    f"{self._url}/auth/v1/logout?scope=global",
                    # Computes and stores `headers` for subsequent operations.
                    headers={
                        # Associates the `apikey` key with its value.
                        "apikey": self._service_role_key,
                        # Associates the `Authorization` key with its value.
                        "Authorization": f"Bearer {access_token}",
                        # Closes the multiline call, declaration, or collection started above.
                    },
                    # Closes the multiline call, declaration, or collection started above.
                )
        # Handles the listed exception so failure remains controlled.
        except httpx.HTTPError as exc:
            # Raises this exception to report an invalid or failed operation.
            raise IdentityProviderError("provider_unavailable") from exc
        # Checks this condition before executing the nested branch.
        if response.status_code not in {200, 204, 401, 404}:
            # Raises this exception to report an invalid or failed operation.
            raise IdentityProviderError("provider_rejected")


# Applies `@lru_cache` to configure the declaration immediately below.
@lru_cache
# Defines the `_provider` callable and its typed interface.
def _provider(supabase_url: str, service_role_key: str) -> SupabaseAdminClient:
    # Returns this result to the caller and ends the current function.
    return SupabaseAdminClient(supabase_url, service_role_key)


# Defines the `get_deletion_provider` callable and its typed interface.
def get_deletion_provider(settings: Settings = Depends(get_settings)) -> SupabaseAdminClient:
    # Returns this result to the caller and ends the current function.
    return _provider(settings.supabase_url, settings.supabase_service_role_key)


# Defines the `process_account_deletion` callable and its typed interface.
async def process_account_deletion(
    # Declares the typed `session` data field.
    session: AsyncSession,
    # Declares the typed `principal` data field.
    principal: AuthPrincipal,
    # Declares the typed `provider` data field.
    provider: SupabaseAdminClient,
    # Declares the typed `access_token` data field.
    access_token: str,
    # Completes the signature and declares the callable return type.
) -> None:
    # Computes and stores `deletion` for subsequent operations.
    deletion = await session.scalar(
        # Calls `select` with the supplied values.
        select(AccountDeletionRequest).where(AccountDeletionRequest.user_id == principal.user_id)
        # Closes the multiline call, declaration, or collection started above.
    )
    # Checks this condition before executing the nested branch.
    if deletion and deletion.status == "completed":
        # Returns this result to the caller and ends the current function.
        return
    # Checks this condition before executing the nested branch.
    if deletion is None:
        # Computes and stores `deletion` for subsequent operations.
        deletion = AccountDeletionRequest(user_id=principal.user_id)
        # Calls `session.add` with the supplied values.
        session.add(deletion)
        # Waits for this asynchronous operation to complete.
        await session.flush()
    # Waits for this asynchronous operation to complete.
    await delete_account(session, principal)
    # Computes and stores `deletion.status` for subsequent operations.
    deletion.status = "pending"
    # Executes this statement as the next step in the surrounding logic.
    deletion.provider_attempts += 1
    # Computes and stores `deletion.last_attempt_at` for subsequent operations.
    deletion.last_attempt_at = utcnow()
    # Waits for this asynchronous operation to complete.
    await session.commit()
    # Starts a protected operation whose expected failures are handled below.
    try:
        # Waits for this asynchronous operation to complete.
        await provider.revoke_sessions(access_token)
        # Waits for this asynchronous operation to complete.
        await provider.delete_user(principal.user_id)
    # Handles the listed exception so failure remains controlled.
    except IdentityProviderError as exc:
        # Computes and stores `deletion.status` for subsequent operations.
        deletion.status = "provider_failed"
        # Computes and stores `deletion.last_error_code` for subsequent operations.
        deletion.last_error_code = str(exc)
        # Waits for this asynchronous operation to complete.
        await session.commit()
        # Raises this exception to report an invalid or failed operation.
        raise APIError(
            # Supplies this item to the surrounding call or collection.
            503,
            # Supplies this item to the surrounding call or collection.
            "ACCOUNT_DELETION_PENDING",
            # Supplies this item to the surrounding call or collection.
            "Account deletion is pending and will retry automatically.",
            # Executes this statement as the next step in the surrounding logic.
        ) from exc
    # Computes and stores `deletion.status` for subsequent operations.
    deletion.status = "completed"
    # Computes and stores `deletion.last_error_code` for subsequent operations.
    deletion.last_error_code = None
    # Computes and stores `deletion.completed_at` for subsequent operations.
    deletion.completed_at = utcnow()
    # Waits for this asynchronous operation to complete.
    await session.commit()


# Defines the `retry_pending_account_deletions` callable and its typed interface.
async def retry_pending_account_deletions(
    # Declares the typed `sessions` data field.
    sessions: async_sessionmaker[AsyncSession],
    # Declares the typed `provider` data field.
    provider: SupabaseAdminClient,
    # Makes the following parameters keyword-only for clear call sites.
    *,
    # Provides the `batch_size` parameter or keyword argument.
    batch_size: int = 25,
    # Completes the signature and declares the callable return type.
) -> int:
    # Documents the purpose or contract of this module, class, or function.
    """Lease and retry a bounded batch without holding a transaction over HTTP."""
    # Computes and stores `retry_before` for subsequent operations.
    retry_before = utcnow() - timedelta(seconds=RETRY_LEASE_SECONDS)
    # Acquires this asynchronous managed resource for the nested operation.
    async with sessions() as session:
        # Computes and stores `user_ids` for subsequent operations.
        user_ids = list(
            # Waits for this asynchronous operation to complete.
            await session.scalars(
                # Calls `select` with the supplied values.
                select(AccountDeletionRequest.user_id)
                # Begins the nested block or multiline expression completed below.
                .where(
                    # Calls `AccountDeletionRequest.status.in_` with the supplied values.
                    AccountDeletionRequest.status.in_(["pending", "provider_failed"]),
                    # Calls `or_` with the supplied values.
                    or_(
                        # Calls `AccountDeletionRequest.last_attempt_at.is_` with the supplied
                        # values.
                        AccountDeletionRequest.last_attempt_at.is_(None),
                        # Supplies this item to the surrounding call or collection.
                        AccountDeletionRequest.last_attempt_at <= retry_before,
                        # Closes the multiline call, declaration, or collection started above.
                    ),
                    # Closes the multiline call, declaration, or collection started above.
                )
                # Executes this statement as the next step in the surrounding logic.
                .order_by(AccountDeletionRequest.requested_at)
                # Executes this statement as the next step in the surrounding logic.
                .limit(batch_size)
                # Closes the multiline call, declaration, or collection started above.
            )
            # Closes the multiline call, declaration, or collection started above.
        )
    # Computes and stores `completed` for subsequent operations.
    completed = 0
    # Iterates through the supplied values for the nested operation.
    for user_id in user_ids:
        # Acquires this asynchronous managed resource for the nested operation.
        async with sessions() as session:
            # Computes and stores `deletion` for subsequent operations.
            deletion = await session.scalar(
                # Calls `select` with the supplied values.
                select(AccountDeletionRequest)
                # Executes this statement as the next step in the surrounding logic.
                .where(AccountDeletionRequest.user_id == user_id)
                # Executes this statement as the next step in the surrounding logic.
                .with_for_update(skip_locked=True)
                # Closes the multiline call, declaration, or collection started above.
            )
            # Checks this condition before executing the nested branch.
            if (
                # Executes this statement as the next step in the surrounding logic.
                deletion is None
                # Executes this statement as the next step in the surrounding logic.
                or deletion.status not in {"pending", "provider_failed"}
                # Begins the nested block or multiline expression completed below.
                or (
                    # Executes this statement as the next step in the surrounding logic.
                    deletion.last_attempt_at is not None
                    # Executes this statement as the next step in the surrounding logic.
                    and ensure_aware(deletion.last_attempt_at) > retry_before
                    # Closes the multiline call, declaration, or collection started above.
                )
                # Begins the nested block or multiline expression completed below.
            ):
                # Skips the remaining work and advances to the next iteration.
                continue
            # Executes this statement as the next step in the surrounding logic.
            deletion.provider_attempts += 1
            # Computes and stores `deletion.last_attempt_at` for subsequent operations.
            deletion.last_attempt_at = utcnow()
            # Waits for this asynchronous operation to complete.
            await session.commit()
        # Starts a protected operation whose expected failures are handled below.
        try:
            # Waits for this asynchronous operation to complete.
            await provider.delete_user(user_id)
        # Handles the listed exception so failure remains controlled.
        except IdentityProviderError as exc:
            # Acquires this asynchronous managed resource for the nested operation.
            async with sessions() as session:
                # Computes and stores `deletion` for subsequent operations.
                deletion = await session.scalar(
                    # Calls `select` with the supplied values.
                    select(AccountDeletionRequest)
                    # Executes this statement as the next step in the surrounding logic.
                    .where(AccountDeletionRequest.user_id == user_id)
                    # Executes this statement as the next step in the surrounding logic.
                    .with_for_update()
                    # Closes the multiline call, declaration, or collection started above.
                )
                # Checks this condition before executing the nested branch.
                if deletion is not None and deletion.status != "completed":
                    # Computes and stores `deletion.status` for subsequent operations.
                    deletion.status = "provider_failed"
                    # Computes and stores `deletion.last_error_code` for subsequent operations.
                    deletion.last_error_code = str(exc)
                    # Waits for this asynchronous operation to complete.
                    await session.commit()
        # Handles the remaining case not matched by earlier branches.
        else:
            # Acquires this asynchronous managed resource for the nested operation.
            async with sessions() as session:
                # Computes and stores `deletion` for subsequent operations.
                deletion = await session.scalar(
                    # Calls `select` with the supplied values.
                    select(AccountDeletionRequest)
                    # Executes this statement as the next step in the surrounding logic.
                    .where(AccountDeletionRequest.user_id == user_id)
                    # Executes this statement as the next step in the surrounding logic.
                    .with_for_update()
                    # Closes the multiline call, declaration, or collection started above.
                )
                # Checks this condition before executing the nested branch.
                if deletion is None:
                    # Skips the remaining work and advances to the next iteration.
                    continue
                # Computes and stores `deletion.status` for subsequent operations.
                deletion.status = "completed"
                # Computes and stores `deletion.last_error_code` for subsequent operations.
                deletion.last_error_code = None
                # Computes and stores `deletion.completed_at` for subsequent operations.
                deletion.completed_at = utcnow()
                # Waits for this asynchronous operation to complete.
                await session.commit()
            # Executes this statement as the next step in the surrounding logic.
            completed += 1
    # Returns this result to the caller and ends the current function.
    return completed


# Defines the `account_deletion_retry_worker` callable and its typed interface.
async def account_deletion_retry_worker(
    # Declares the typed `sessions` data field.
    sessions: async_sessionmaker[AsyncSession],
    # Declares the typed `provider` data field.
    provider: SupabaseAdminClient,
    # Makes the following parameters keyword-only for clear call sites.
    *,
    # Provides the `interval_seconds` parameter or keyword argument.
    interval_seconds: float = 30,
    # Provides the `wait` parameter or keyword argument.
    wait: Callable[[float], Awaitable[None]] = asyncio.sleep,
    # Completes the signature and declares the callable return type.
) -> None:
    # Repeats the nested block while this condition remains true.
    while True:
        # Starts a protected operation whose expected failures are handled below.
        try:
            # Waits for this asynchronous operation to complete.
            await retry_pending_account_deletions(sessions, provider)
        # Handles the listed exception so failure remains controlled.
        except SQLAlchemyError:
            # Calls `structlog.get_logger` with the supplied values.
            structlog.get_logger().exception("account_deletion_retry_failed")
        # Waits for this asynchronous operation to complete.
        await wait(interval_seconds)
