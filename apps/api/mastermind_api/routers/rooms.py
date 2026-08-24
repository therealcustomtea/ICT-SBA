# Defers type-annotation evaluation to support modern hints safely.
from __future__ import annotations

# Imports `asyncio` so the module can use that dependency.
import asyncio

# Imports `hashlib` so the module can use that dependency.
import hashlib

# Imports `json` so the module can use that dependency.
import json

# Imports `secrets` so the module can use that dependency.
import secrets

# Imports `time` so the module can use that dependency.
import time

# Imports `uuid` so the module can use that dependency.
import uuid

# Imports selected names from `contextlib` for use in this module.
from contextlib import suppress

# Imports selected names from `dataclasses` for use in this module.
from dataclasses import dataclass

# Imports selected names from `datetime` for use in this module.
from datetime import datetime, timedelta

# Imports selected names from `typing` for use in this module.
from typing import Any

# Imports selected names from `fastapi` for use in this module.
from fastapi import APIRouter, Depends, Request, WebSocket, WebSocketDisconnect, status

# Imports selected names from `mastermind_core` for use in this module.
from mastermind_core import DomainError

# Imports selected names from `pydantic` for use in this module.
from pydantic import ValidationError

# Imports selected names from `redis.exceptions` for use in this module.
from redis.exceptions import RedisError

# Imports selected names from `sqlalchemy` for use in this module.
from sqlalchemy import select

# Imports selected names from `sqlalchemy.ext.asyncio` for use in this module.
from sqlalchemy.ext.asyncio import AsyncSession

# Imports selected names from `sqlalchemy.orm` for use in this module.
from sqlalchemy.orm import selectinload

# Imports selected names from `..auth` for use in this module.
from ..auth import AuthPrincipal, get_current_user

# Imports selected names from `..client_ip` for use in this module.
from ..client_ip import trusted_client_ip

# Imports selected names from `..config` for use in this module.
from ..config import Settings, get_settings

# Imports selected names from `..crypto` for use in this module.
from ..crypto import SecretCipher

# Imports selected names from `..database` for use in this module.
from ..database import SessionFactory, get_session

# Imports selected names from `..dependencies` for use in this module.
from ..dependencies import get_cipher

# Imports selected names from `..errors` for use in this module.
from ..errors import APIError

# Imports selected names from `..features` for use in this module.
from ..features import feature_enabled

# Imports selected names from `..metrics` for use in this module.
from ..metrics import WEBSOCKET_CONNECTIONS, WEBSOCKET_RECONNECTS

# Imports selected names from `..models` for use in this module.
from ..models import (
    # Supplies this item to the surrounding call or collection.
    GameAttempt,
    # Supplies this item to the surrounding call or collection.
    GameSession,
    # Supplies this item to the surrounding call or collection.
    MultiplayerEvent,
    # Supplies this item to the surrounding call or collection.
    MultiplayerMember,
    # Supplies this item to the surrounding call or collection.
    MultiplayerRoom,
    # Closes the multiline call, declaration, or collection started above.
)

# Imports selected names from `..rate_limit` for use in this module.
from ..rate_limit import enforce_action_limit

# Imports selected names from `..realtime` for use in this module.
from ..realtime import (
    # Supplies this item to the surrounding call or collection.
    Broker,
    # Supplies this item to the surrounding call or collection.
    RedisBroker,
    # Supplies this item to the surrounding call or collection.
    UnavailableBroker,
    # Supplies this item to the surrounding call or collection.
    record_room_completion,
    # Supplies this item to the surrounding call or collection.
    record_room_event,
    # Closes the multiline call, declaration, or collection started above.
)

# Imports selected names from `..schemas` for use in this module.
from ..schemas import (
    # Supplies this item to the surrounding call or collection.
    CreateRoomRequest,
    # Supplies this item to the surrounding call or collection.
    RoomClientMessage,
    # Supplies this item to the surrounding call or collection.
    RoomResponse,
    # Supplies this item to the surrounding call or collection.
    WebSocketTicketResponse,
    # Closes the multiline call, declaration, or collection started above.
)

# Imports selected names from `..services` for use in this module.
from ..services import (
    # Supplies this item to the surrounding call or collection.
    create_room,
    # Supplies this item to the surrounding call or collection.
    ensure_aware,
    # Supplies this item to the surrounding call or collection.
    join_room,
    # Supplies this item to the surrounding call or collection.
    load_room_for_member,
    # Supplies this item to the surrounding call or collection.
    ready_room,
    # Supplies this item to the surrounding call or collection.
    room_response,
    # Supplies this item to the surrounding call or collection.
    submit_attempt,
    # Supplies this item to the surrounding call or collection.
    utcnow,
    # Closes the multiline call, declaration, or collection started above.
)

# Computes and stores `router` for subsequent operations.
router = APIRouter(prefix="/v1/rooms", tags=["multiplayer"])

# Computes and stores `WEBSOCKET_PROTOCOL_VERSION` for subsequent operations.
WEBSOCKET_PROTOCOL_VERSION = 1
# Computes and stores `WEBSOCKET_SUBPROTOCOL` for subsequent operations.
WEBSOCKET_SUBPROTOCOL = "cipherboard-v1"
# Computes and stores `MAX_REPLAY_EVENTS` for subsequent operations.
MAX_REPLAY_EVENTS = 200


# Defines the `DuelRoomFinalized` class and its related behavior.
class DuelRoomFinalized(Exception):
    # Defines the `__init__` callable and its typed interface.
    def __init__(self, event: dict[str, Any] | None) -> None:
        # Calls `super` with the supplied values.
        super().__init__("The duel tie window elapsed before this command was accepted.")
        # Computes and stores `self.event` for subsequent operations.
        self.event = event


# Applies `@dataclass(slots=True)` to configure the declaration immediately below.
@dataclass(slots=True)
# Defines the `DuelAttemptOutcome` class and its related behavior.
class DuelAttemptOutcome:
    # Declares the typed `game` data field.
    game: GameSession
    # Declares the typed `attempt` data field.
    attempt: GameAttempt
    # Declares the typed `safe_event` data field.
    safe_event: dict[str, Any] | None
    # Declares the typed `completion_event` data field.
    completion_event: dict[str, Any] | None
    # Declares the typed `finalization_deadline` data field.
    finalization_deadline: datetime | None
    # Computes and stores `duplicate` for subsequent operations.
    duplicate: bool = False


# Defines the `_server_event` callable and its typed interface.
def _server_event(
    # Declares the typed `event_type` data field.
    event_type: str,
    # Declares the typed `payload` data field.
    payload: dict[str, Any],
    # Makes the following parameters keyword-only for clear call sites.
    *,
    # Provides the `sequence` parameter or keyword argument.
    sequence: int | None = None,
    # Completes the signature and declares the callable return type.
) -> dict[str, Any]:
    # Returns this result to the caller and ends the current function.
    return {
        # Associates the `version` key with its value.
        "version": WEBSOCKET_PROTOCOL_VERSION,
        # Associates the `sequence` key with its value.
        "sequence": sequence,
        # Associates the `type` key with its value.
        "type": event_type,
        # Associates the `payload` key with its value.
        "payload": payload,
        # Closes the multiline call, declaration, or collection started above.
    }


# Defines the `_claim_connection` callable and its typed interface.
async def _claim_connection(
    # Declares the typed `redis` data field.
    redis: Any,
    # Declares the typed `principal` data field.
    principal: AuthPrincipal,
    # Declares the typed `peer` data field.
    peer: str,
    # Declares the typed `token` data field.
    token: str,
    # Declares the typed `settings` data field.
    settings: Settings,
    # Completes the signature and declares the callable return type.
) -> tuple[bool, int, str, str]:
    # Computes and stores `user_digest` for subsequent operations.
    user_digest = hashlib.sha256(f"ws-user:{principal.user_id}".encode()).hexdigest()
    # Computes and stores `ip_digest` for subsequent operations.
    ip_digest = hashlib.sha256(f"ws-peer:{peer}".encode()).hexdigest()
    # Computes and stores `user_key` for subsequent operations.
    user_key = f"mastermind:ws-connections:user:{user_digest}"
    # Computes and stores `ip_key` for subsequent operations.
    ip_key = f"mastermind:ws-connections:ip:{ip_digest}"
    # Computes and stores `now` for subsequent operations.
    now = int(time.time())
    # Computes and stores `script` for subsequent operations.
    script = """
    local now = tonumber(ARGV[1])
    local ttl = tonumber(ARGV[2])
    local cutoff = now - ttl
    redis.call('ZREMRANGEBYSCORE', KEYS[1], '-inf', cutoff)
    redis.call('ZREMRANGEBYSCORE', KEYS[2], '-inf', cutoff)
    local user_count = redis.call('ZCARD', KEYS[1])
    local ip_count = redis.call('ZCARD', KEYS[2])
    if user_count >= tonumber(ARGV[3]) or ip_count >= tonumber(ARGV[4]) then
      return {0, user_count}
    end
    redis.call('ZADD', KEYS[1], now, ARGV[5])
    redis.call('ZADD', KEYS[2], now, ARGV[5])
    redis.call('EXPIRE', KEYS[1], ttl)
    redis.call('EXPIRE', KEYS[2], ttl)
    return {1, user_count + 1}
    """
    # Begins the nested block or multiline expression completed below.
    allowed, user_count = await redis.eval(
        # Supplies this item to the surrounding call or collection.
        script,
        # Supplies this item to the surrounding call or collection.
        2,
        # Supplies this item to the surrounding call or collection.
        user_key,
        # Supplies this item to the surrounding call or collection.
        ip_key,
        # Supplies this item to the surrounding call or collection.
        now,
        # Supplies this item to the surrounding call or collection.
        settings.websocket_connection_ttl_seconds,
        # Supplies this item to the surrounding call or collection.
        settings.websocket_user_connection_limit,
        # Supplies this item to the surrounding call or collection.
        settings.websocket_ip_connection_limit,
        # Supplies this item to the surrounding call or collection.
        token,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Returns this result to the caller and ends the current function.
    return bool(allowed), int(user_count), user_key, ip_key


# Defines the `_refresh_connection` callable and its typed interface.
async def _refresh_connection(
    # Declares the typed `redis` data field.
    redis: Any,
    # Declares the typed `user_key` data field.
    user_key: str,
    # Declares the typed `ip_key` data field.
    ip_key: str,
    # Declares the typed `token` data field.
    token: str,
    # Declares the typed `settings` data field.
    settings: Settings,
    # Completes the signature and declares the callable return type.
) -> None:
    # Computes and stores `now` for subsequent operations.
    now = int(time.time())
    # Computes and stores `pipeline` for subsequent operations.
    pipeline = redis.pipeline(transaction=True)
    # Calls `pipeline.zadd` with the supplied values.
    pipeline.zadd(user_key, {token: now}, xx=True)
    # Calls `pipeline.zadd` with the supplied values.
    pipeline.zadd(ip_key, {token: now}, xx=True)
    # Calls `pipeline.expire` with the supplied values.
    pipeline.expire(user_key, settings.websocket_connection_ttl_seconds)
    # Calls `pipeline.expire` with the supplied values.
    pipeline.expire(ip_key, settings.websocket_connection_ttl_seconds)
    # Waits for this asynchronous operation to complete.
    await pipeline.execute()


# Defines the `_release_connection` callable and its typed interface.
async def _release_connection(
    # Declares the typed `redis` data field.
    redis: Any,
    # Declares the typed `user_key` data field.
    user_key: str,
    # Declares the typed `ip_key` data field.
    ip_key: str,
    # Declares the typed `token` data field.
    token: str,
    # Completes the signature and declares the callable return type.
) -> int:
    # Computes and stores `script` for subsequent operations.
    script = """
    redis.call('ZREM', KEYS[1], ARGV[1])
    redis.call('ZREM', KEYS[2], ARGV[1])
    return redis.call('ZCARD', KEYS[1])
    """
    # Returns this result to the caller and ends the current function.
    return int(await redis.eval(script, 2, user_key, ip_key, token))


# Defines the `require_rooms` callable and its typed interface.
async def require_rooms(session: AsyncSession, settings: Settings) -> None:
    # Checks this condition before executing the nested branch.
    if not await feature_enabled(session, settings, "multiplayer"):
        # Raises this exception to report an invalid or failed operation.
        raise APIError(503, "FEATURE_DISABLED", "Private duels are temporarily unavailable.")


# Defines the `_ensure_realtime_available` callable and its typed interface.
async def _ensure_realtime_available(
    # Declares the typed `state` data field.
    state: Any,
    # Declares the typed `settings` data field.
    settings: Settings,
    # Makes the following parameters keyword-only for clear call sites.
    *,
    # Provides the `require_ticket_store` parameter or keyword argument.
    require_ticket_store: bool = False,
    # Completes the signature and declares the callable return type.
) -> Any | None:
    # Documents the purpose or contract of this module, class, or function.
    """Probe Redis at realtime boundaries so a startup outage can recover."""

    # Computes and stores `redis` for subsequent operations.
    redis = state.redis
    # Checks this condition before executing the nested branch.
    if redis is None:
        # Computes and stores `state.redis_ready` for subsequent operations.
        state.redis_ready = False
        # Checks this condition before executing the nested branch.
        if settings.environment in {"production", "staging"} or require_ticket_store:
            # Raises this exception to report an invalid or failed operation.
            raise APIError(503, "REALTIME_UNAVAILABLE", "Realtime play is temporarily unavailable.")
        # Checks this condition before executing the nested branch.
        if not state.broker.available:
            # Raises this exception to report an invalid or failed operation.
            raise APIError(503, "REALTIME_UNAVAILABLE", "Realtime play is temporarily unavailable.")
        # Returns this result to the caller and ends the current function.
        return None
    # Starts a protected operation whose expected failures are handled below.
    try:
        # Acquires this asynchronous managed resource for the nested operation.
        async with asyncio.timeout(2):
            # Waits for this asynchronous operation to complete.
            await redis.ping()
    # Handles the listed exception so failure remains controlled.
    except (RedisError, TimeoutError):
        # Computes and stores `state.redis_ready` for subsequent operations.
        state.redis_ready = False
        # Checks this condition before executing the nested branch.
        if settings.environment in {"production", "staging"}:
            # Computes and stores `state.broker` for subsequent operations.
            state.broker = UnavailableBroker()
        # Raises this exception to report an invalid or failed operation.
        raise APIError(
            # Executes this statement as the next step in the surrounding logic.
            503,
            # Supplies this string to the surrounding call or collection.
            "REALTIME_UNAVAILABLE",
            # Supplies this string to the surrounding call or collection.
            "Realtime play is temporarily unavailable.",
            # Executes this statement as the next step in the surrounding logic.
        ) from None
    # Computes and stores `state.redis_ready` for subsequent operations.
    state.redis_ready = True
    # Checks this condition before executing the nested branch.
    if settings.environment in {"production", "staging"} and not isinstance(
        # Executes this statement as the next step in the surrounding logic.
        state.broker,
        # Supplies this item to the surrounding call or collection.
        RedisBroker,
        # Begins the nested block or multiline expression completed below.
    ):
        # Computes and stores `state.broker` for subsequent operations.
        state.broker = RedisBroker(redis)
    # Returns this result to the caller and ends the current function.
    return redis


# Defines the `_ticket_from_protocol_header` callable and its typed interface.
def _ticket_from_protocol_header(header: str) -> str | None:
    # Computes and stores `offered` for subsequent operations.
    offered = {protocol.strip() for protocol in header.split(",") if protocol.strip()}
    # Computes and stores `tickets` for subsequent operations.
    tickets = [
        # Calls `protocol.removeprefix` with the supplied values.
        protocol.removeprefix("ticket.")
        # Continues the surrounding expression or operation.
        for protocol in offered
        # Checks this condition before running the nested branch.
        if protocol.startswith("ticket.")
        # Closes the multiline call, declaration, or collection started above.
    ]
    # Checks this condition before executing the nested branch.
    if WEBSOCKET_SUBPROTOCOL not in offered or len(tickets) != 1:
        # Returns this result to the caller and ends the current function.
        return None
    # Computes and stores `ticket` for subsequent operations.
    ticket = tickets[0]
    # Computes and stores `allowed_characters` for subsequent operations.
    allowed_characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
    # Checks this condition before executing the nested branch.
    if (
        # Executes this statement as the next step in the surrounding logic.
        not ticket
        # Executes this statement as the next step in the surrounding logic.
        or len(ticket) > 128
        # Executes this statement as the next step in the surrounding logic.
        or not all(character in allowed_characters for character in ticket)
        # Begins the nested block or multiline expression completed below.
    ):
        # Returns this result to the caller and ends the current function.
        return None
    # Returns this result to the caller and ends the current function.
    return ticket


# Defines the `_websocket_ticket` callable and its typed interface.
def _websocket_ticket(websocket: WebSocket) -> str | None:
    # Returns this result to the caller and ends the current function.
    return _ticket_from_protocol_header(websocket.headers.get("sec-websocket-protocol", ""))


# Applies `@router.post("/{room_id}/ws-ticket", response_model=WebSocketTicketResponse)` to
# configure the declaration immediately below.
@router.post("/{room_id}/ws-ticket", response_model=WebSocketTicketResponse)
# Defines the `create_websocket_ticket_route` callable and its typed interface.
async def create_websocket_ticket_route(
    # Declares the typed `room_id` data field.
    room_id: uuid.UUID,
    # Declares the typed `request` data field.
    request: Request,
    # Provides the `principal` parameter or keyword argument.
    principal: AuthPrincipal = Depends(get_current_user),
    # Provides the `session` parameter or keyword argument.
    session: AsyncSession = Depends(get_session),
    # Provides the `settings` parameter or keyword argument.
    settings: Settings = Depends(get_settings),
    # Completes the signature and declares the callable return type.
) -> WebSocketTicketResponse:
    # Waits for this asynchronous operation to complete.
    await require_rooms(session, settings)
    # Waits for this asynchronous operation to complete.
    await enforce_action_limit(
        # Supplies this item to the surrounding call or collection.
        request,
        # Provides the `action` parameter or keyword argument.
        action="room.ws_ticket",
        # Provides the `subject` parameter or keyword argument.
        subject=principal.user_id,
        # Provides the `resource` parameter or keyword argument.
        resource=room_id,
        # Provides the `weight` parameter or keyword argument.
        weight=8,
        # Provides the `integrity_required` parameter or keyword argument.
        integrity_required=True,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Waits for this asynchronous operation to complete.
    await load_room_for_member(session, room_id, principal)
    # Computes and stores `redis` for subsequent operations.
    redis = await _ensure_realtime_available(request.app.state, settings, require_ticket_store=True)
    # Asserts this invariant so an unexpected test state fails immediately.
    assert redis is not None
    # Computes and stores `ticket` for subsequent operations.
    ticket = secrets.token_urlsafe(32)
    # Computes and stores `ticket_hash` for subsequent operations.
    ticket_hash = hashlib.sha256(ticket.encode()).hexdigest()
    # Computes and stores `expires_at` for subsequent operations.
    expires_at = utcnow() + timedelta(seconds=60)
    # Computes and stores `value` for subsequent operations.
    value = json.dumps(
        # Begins the nested block or multiline expression completed below.
        {
            # Associates the `roomId` key with its value.
            "roomId": str(room_id),
            # Associates the `userId` key with its value.
            "userId": str(principal.user_id),
            # Associates the `isAnonymous` key with its value.
            "isAnonymous": principal.is_anonymous,
            # Associates the `expiresAt` key with its value.
            "expiresAt": expires_at.isoformat(),
            # Closes the multiline call, declaration, or collection started above.
        }
        # Closes the multiline call, declaration, or collection started above.
    )
    # Starts a protected operation whose expected failures are handled below.
    try:
        # Acquires this asynchronous managed resource for the nested operation.
        async with asyncio.timeout(2):
            # Waits for this asynchronous operation to complete.
            await redis.setex(f"mastermind:ws-ticket:{ticket_hash}", 60, value)
    # Handles the listed exception so failure remains controlled.
    except (RedisError, TimeoutError):
        # Computes and stores `request.app.state.redis_ready` for subsequent operations.
        request.app.state.redis_ready = False
        # Raises this exception to report an invalid or failed operation.
        raise APIError(
            # Executes this statement as the next step in the surrounding logic.
            503,
            # Supplies this string to the surrounding call or collection.
            "REALTIME_UNAVAILABLE",
            # Supplies this string to the surrounding call or collection.
            "Realtime play is temporarily unavailable.",
            # Executes this statement as the next step in the surrounding logic.
        ) from None
    # Returns this result to the caller and ends the current function.
    return WebSocketTicketResponse(ticket=ticket, expires_at=expires_at)


# Applies `@router.post("", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)` to
# configure the declaration immediately below.
@router.post("", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
# Defines the `create_room_route` callable and its typed interface.
async def create_room_route(
    # Declares the typed `payload` data field.
    payload: CreateRoomRequest,
    # Declares the typed `request` data field.
    request: Request,
    # Provides the `principal` parameter or keyword argument.
    principal: AuthPrincipal = Depends(get_current_user),
    # Provides the `session` parameter or keyword argument.
    session: AsyncSession = Depends(get_session),
    # Provides the `cipher` parameter or keyword argument.
    cipher: SecretCipher = Depends(get_cipher),
    # Provides the `settings` parameter or keyword argument.
    settings: Settings = Depends(get_settings),
    # Completes the signature and declares the callable return type.
) -> RoomResponse:
    # Waits for this asynchronous operation to complete.
    await require_rooms(session, settings)
    # Waits for this asynchronous operation to complete.
    await enforce_action_limit(
        # Supplies this item to the surrounding call or collection.
        request,
        # Provides the `action` parameter or keyword argument.
        action="room.create",
        # Provides the `subject` parameter or keyword argument.
        subject=principal.user_id,
        # Provides the `weight` parameter or keyword argument.
        weight=10,
        # Provides the `integrity_required` parameter or keyword argument.
        integrity_required=True,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Waits for this asynchronous operation to complete.
    await _ensure_realtime_available(request.app.state, settings)
    # Begins the nested block or multiline expression completed below.
    room, room_code = await create_room(
        # Supplies this item to the surrounding call or collection.
        session,
        # Supplies this item to the surrounding call or collection.
        principal,
        # Supplies this item to the surrounding call or collection.
        payload.difficulty,
        # Supplies this item to the surrounding call or collection.
        cipher,
        # Supplies this item to the surrounding call or collection.
        settings,
        # Supplies this item to the surrounding call or collection.
        payload.idempotency_key,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Returns this result to the caller and ends the current function.
    return await room_response(session, room, room_code, principal.user_id)


# Applies `@router.post("/{room_code}/join", response_model=RoomResponse)` to configure the
# declaration immediately below.
@router.post("/{room_code}/join", response_model=RoomResponse)
# Defines the `join_room_route` callable and its typed interface.
async def join_room_route(
    # Declares the typed `room_code` data field.
    room_code: str,
    # Declares the typed `request` data field.
    request: Request,
    # Provides the `principal` parameter or keyword argument.
    principal: AuthPrincipal = Depends(get_current_user),
    # Provides the `session` parameter or keyword argument.
    session: AsyncSession = Depends(get_session),
    # Provides the `cipher` parameter or keyword argument.
    cipher: SecretCipher = Depends(get_cipher),
    # Provides the `settings` parameter or keyword argument.
    settings: Settings = Depends(get_settings),
    # Completes the signature and declares the callable return type.
) -> RoomResponse:
    # Waits for this asynchronous operation to complete.
    await require_rooms(session, settings)
    # Waits for this asynchronous operation to complete.
    await enforce_action_limit(
        # Supplies this item to the surrounding call or collection.
        request,
        # Provides the `action` parameter or keyword argument.
        action="room.join",
        # Provides the `subject` parameter or keyword argument.
        subject=principal.user_id,
        # Provides the `resource` parameter or keyword argument.
        resource=room_code,
        # Provides the `weight` parameter or keyword argument.
        weight=10,
        # Provides the `integrity_required` parameter or keyword argument.
        integrity_required=True,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Waits for this asynchronous operation to complete.
    await _ensure_realtime_available(request.app.state, settings)
    # Computes and stores `room` for subsequent operations.
    room = await join_room(session, principal, room_code, cipher, settings)
    # Returns this result to the caller and ends the current function.
    return await room_response(session, room, viewer_id=principal.user_id)


# Applies `@router.post("/{room_id}/ready", response_model=RoomResponse)` to configure the
# declaration immediately below.
@router.post("/{room_id}/ready", response_model=RoomResponse)
# Defines the `ready_room_route` callable and its typed interface.
async def ready_room_route(
    # Declares the typed `room_id` data field.
    room_id: uuid.UUID,
    # Declares the typed `request` data field.
    request: Request,
    # Provides the `principal` parameter or keyword argument.
    principal: AuthPrincipal = Depends(get_current_user),
    # Provides the `session` parameter or keyword argument.
    session: AsyncSession = Depends(get_session),
    # Provides the `cipher` parameter or keyword argument.
    cipher: SecretCipher = Depends(get_cipher),
    # Provides the `settings` parameter or keyword argument.
    settings: Settings = Depends(get_settings),
    # Completes the signature and declares the callable return type.
) -> RoomResponse:
    # Waits for this asynchronous operation to complete.
    await require_rooms(session, settings)
    # Waits for this asynchronous operation to complete.
    await enforce_action_limit(
        # Supplies this item to the surrounding call or collection.
        request,
        # Provides the `action` parameter or keyword argument.
        action="room.ready",
        # Provides the `subject` parameter or keyword argument.
        subject=principal.user_id,
        # Provides the `resource` parameter or keyword argument.
        resource=room_id,
        # Provides the `weight` parameter or keyword argument.
        weight=6,
        # Provides the `integrity_required` parameter or keyword argument.
        integrity_required=True,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Waits for this asynchronous operation to complete.
    await _ensure_realtime_available(request.app.state, settings)
    # Executes this statement as the next step in the surrounding logic.
    room, events = await ready_room(session, principal, room_id, cipher)
    # Computes and stores `broker` for subsequent operations.
    broker: Broker = request.app.state.broker
    # Iterates through the supplied values for the nested operation.
    for event in events:
        # Acquires this managed resource and guarantees cleanup afterward.
        with suppress(RedisError, RuntimeError):
            # Waits for this asynchronous operation to complete.
            await broker.publish(str(room.id), event)
    # Returns this result to the caller and ends the current function.
    return await room_response(session, room, viewer_id=principal.user_id)


# Applies `@router.get("/{room_id}", response_model=RoomResponse)` to configure the declaration
# immediately below.
@router.get("/{room_id}", response_model=RoomResponse)
# Defines the `get_room_route` callable and its typed interface.
async def get_room_route(
    # Declares the typed `room_id` data field.
    room_id: uuid.UUID,
    # Provides the `principal` parameter or keyword argument.
    principal: AuthPrincipal = Depends(get_current_user),
    # Provides the `session` parameter or keyword argument.
    session: AsyncSession = Depends(get_session),
    # Provides the `settings` parameter or keyword argument.
    settings: Settings = Depends(get_settings),
    # Completes the signature and declares the callable return type.
) -> RoomResponse:
    # Waits for this asynchronous operation to complete.
    await require_rooms(session, settings)
    # Computes and stores `room` for subsequent operations.
    room = await load_room_for_member(session, room_id, principal)
    # Waits for this asynchronous operation to complete.
    await session.commit()
    # Returns this result to the caller and ends the current function.
    return await room_response(session, room, viewer_id=principal.user_id)


# Defines the `_record_event` callable and its typed interface.
async def _record_event(
    # Declares the typed `session` data field.
    session: AsyncSession,
    # Declares the typed `room` data field.
    room: MultiplayerRoom,
    # Declares the typed `event_type` data field.
    event_type: str,
    # Declares the typed `payload` data field.
    payload: dict[str, Any],
    # Completes the signature and declares the callable return type.
) -> dict[str, Any]:
    # Returns this result to the caller and ends the current function.
    return await record_room_event(session, room, event_type, payload)


# Defines the `_room_completion_event` callable and its typed interface.
async def _room_completion_event(
    # Declares the typed `session` data field.
    session: AsyncSession,
    # Declares the typed `room` data field.
    room: MultiplayerRoom,
    # Declares the typed `reason` data field.
    reason: str,
    # Completes the signature and declares the callable return type.
) -> dict[str, Any] | None:
    # Returns this result to the caller and ends the current function.
    return await record_room_completion(session, room, reason)


# Defines the `_lock_duel_attempt_state` callable and its typed interface.
async def _lock_duel_attempt_state(
    # Declares the typed `session` data field.
    session: AsyncSession,
    # Declares the typed `room_id` data field.
    room_id: uuid.UUID,
    # Declares the typed `principal` data field.
    principal: AuthPrincipal,
    # Completes the signature and declares the callable return type.
) -> tuple[MultiplayerRoom, GameSession]:
    # Documents the purpose or contract of this module, class, or function.
    """Lock a duel in the single room -> ordered games acquisition order."""

    # Computes and stores `room` for subsequent operations.
    room = await load_room_for_member(session, room_id, principal, for_update=True)
    # Checks this condition before executing the nested branch.
    if (
        # Executes this statement as the next step in the surrounding logic.
        room.status == "active"
        # Executes this statement as the next step in the surrounding logic.
        and room.winner_id is not None
        # Executes this statement as the next step in the surrounding logic.
        and room.tie_deadline is not None
        # Executes this statement as the next step in the surrounding logic.
        and ensure_aware(room.tie_deadline) <= utcnow()
        # Begins the nested block or multiline expression completed below.
    ):
        # Computes and stores `room.status` for subsequent operations.
        room.status = "completed"
        # Computes and stores `event` for subsequent operations.
        event = await _room_completion_event(session, room, "tie_window_elapsed")
        # Waits for this asynchronous operation to complete.
        await session.commit()
        # Raises this exception to report an invalid or failed operation.
        raise DuelRoomFinalized(event)
    # Checks this condition before executing the nested branch.
    if room.status != "active":
        # Raises this exception to report an invalid or failed operation.
        raise APIError(409, "ROOM_NOT_ACTIVE", "This room is not accepting guesses.")
    # Computes and stores `game` for subsequent operations.
    game = await session.scalar(
        # Calls `select` with the supplied values.
        select(GameSession)
        # Executes this statement as the next step in the surrounding logic.
        .options(selectinload(GameSession.attempts))
        # Begins the nested block or multiline expression completed below.
        .where(
            # Supplies this item to the surrounding call or collection.
            GameSession.room_id == room_id,
            # Supplies this item to the surrounding call or collection.
            GameSession.owner_id == principal.user_id,
            # Closes the multiline call, declaration, or collection started above.
        )
        # Closes the multiline call, declaration, or collection started above.
    )
    # Checks this condition before executing the nested branch.
    if game is None:
        # Raises this exception to report an invalid or failed operation.
        raise APIError(404, "GAME_NOT_FOUND", "Your duel game was not found.")
    # Returns this result to the caller and ends the current function.
    return room, game


# Defines the `_submit_duel_attempt_transaction` callable and its typed interface.
async def _submit_duel_attempt_transaction(
    # Declares the typed `session` data field.
    session: AsyncSession,
    # Declares the typed `room_id` data field.
    room_id: uuid.UUID,
    # Declares the typed `principal` data field.
    principal: AuthPrincipal,
    # Declares the typed `guess` data field.
    guess: list[str],
    # Declares the typed `idempotency_key` data field.
    idempotency_key: str,
    # Declares the typed `request_id` data field.
    request_id: str,
    # Declares the typed `cipher` data field.
    cipher: SecretCipher,
    # Declares the typed `settings` data field.
    settings: Settings,
    # Completes the signature and declares the callable return type.
) -> DuelAttemptOutcome:
    # Documents the purpose or contract of this module, class, or function.
    """Apply one duel command under the authoritative lock order and commit it."""

    # Executes this statement as the next step in the surrounding logic.
    room, game = await _lock_duel_attempt_state(session, room_id, principal)
    # Computes and stores `previous` for subsequent operations.
    previous = next(
        # Supplies this item to the surrounding call or collection.
        (attempt for attempt in game.attempts if attempt.idempotency_key == idempotency_key),
        # Supplies this item to the surrounding call or collection.
        None,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Checks this condition before executing the nested branch.
    if previous and previous.guess == [peg.upper() for peg in guess]:
        # Waits for this asynchronous operation to complete.
        await session.commit()
        # Returns this result to the caller and ends the current function.
        return DuelAttemptOutcome(game, previous, None, None, None, duplicate=True)

    # Computes and stores `game` for subsequent operations.
    game = await submit_attempt(
        # Supplies this item to the surrounding call or collection.
        session,
        # Supplies this item to the surrounding call or collection.
        principal,
        # Supplies this item to the surrounding call or collection.
        game.public_id,
        # Supplies this item to the surrounding call or collection.
        guess,
        # Supplies this item to the surrounding call or collection.
        idempotency_key,
        # Supplies this item to the surrounding call or collection.
        request_id,
        # Supplies this item to the surrounding call or collection.
        cipher,
        # Provides the `commit` parameter or keyword argument.
        commit=False,
        # Provides the `allow_duel` parameter or keyword argument.
        allow_duel=True,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Executes this statement as the next step in the surrounding logic.
    just_completed = game.status == "won"
    # Computes and stores `finalization_deadline` for subsequent operations.
    finalization_deadline = None
    # Checks this condition before executing the nested branch.
    if just_completed and room.winner_id is None:
        # Computes and stores `room.winner_id` for subsequent operations.
        room.winner_id = principal.user_id
        # Computes and stores `room.winner_at` for subsequent operations.
        room.winner_at = utcnow()
        # Computes and stores `room.tie_deadline` for subsequent operations.
        room.tie_deadline = room.winner_at + timedelta(milliseconds=settings.room_tie_window_ms)
        # Computes and stores `finalization_deadline` for subsequent operations.
        finalization_deadline = room.tie_deadline
    # Checks this alternative when previous conditions were false.
    elif (
        # Executes this statement as the next step in the surrounding logic.
        just_completed
        # Executes this statement as the next step in the surrounding logic.
        and room.winner_id != principal.user_id
        # Executes this statement as the next step in the surrounding logic.
        and room.tie_deadline
        # Executes this statement as the next step in the surrounding logic.
        and utcnow() <= room.tie_deadline
        # Begins the nested block or multiline expression completed below.
    ):
        # Computes and stores `room.is_tie` for subsequent operations.
        room.is_tie = True
        # Computes and stores `room.winner_id` for subsequent operations.
        room.winner_id = None
        # Computes and stores `room.status` for subsequent operations.
        room.status = "completed"
    # Computes and stores `game_states` for subsequent operations.
    game_states = (
        # Waits for this asynchronous operation to complete.
        await session.execute(
            # Calls `select` with the supplied values.
            select(GameSession.owner_id, GameSession.status).where(GameSession.room_id == room_id)
            # Closes the multiline call, declaration, or collection started above.
        )
        # Executes this statement as the next step in the surrounding logic.
    ).all()
    # Computes and stores `terminal_statuses` for subsequent operations.
    terminal_statuses = {"won", "lost", "abandoned", "expired"}
    # Computes and stores `completed_reason` for subsequent operations.
    completed_reason = None
    # Checks this condition before executing the nested branch.
    if game_states and all(status_value in terminal_statuses for _, status_value in game_states):
        # Executes this statement as the next step in the surrounding logic.
        winners = [owner_id for owner_id, status_value in game_states if status_value == "won"]
        # Checks this condition before executing the nested branch.
        if not winners:
            # Computes and stores `room.status` for subsequent operations.
            room.status = "completed"
            # Computes and stores `room.winner_id` for subsequent operations.
            room.winner_id = None
            # Computes and stores `room.is_tie` for subsequent operations.
            room.is_tie = True
            # Computes and stores `completed_reason` for subsequent operations.
            completed_reason = "both_lost"
        # Checks this alternative when previous conditions were false.
        elif room.status == "completed":
            # Computes and stores `completed_reason` for subsequent operations.
            completed_reason = "tie_window" if room.is_tie else "winner"
    # Computes and stores `safe_event` for subsequent operations.
    safe_event = await _record_event(
        # Supplies this item to the surrounding call or collection.
        session,
        # Supplies this item to the surrounding call or collection.
        room,
        # Supplies this item to the surrounding call or collection.
        "opponent_progress",
        # Begins the nested block or multiline expression completed below.
        {
            # Associates the `userId` key with its value.
            "userId": str(principal.user_id),
            # Associates the `attemptsUsed` key with its value.
            "attemptsUsed": game.attempts_used,
            # Associates the `completed` key with its value.
            "completed": game.status in {"won", "lost"},
            # Closes the multiline call, declaration, or collection started above.
        },
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `completion_event` for subsequent operations.
    completion_event = (
        # Waits for this asynchronous operation to complete.
        await _room_completion_event(session, room, completed_reason)
        # Checks this condition before executing the nested branch.
        if completed_reason is not None
        # Executes this statement as the next step in the surrounding logic.
        else None
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `latest` for subsequent operations.
    latest = game.attempts[-1]
    # Waits for this asynchronous operation to complete.
    await session.commit()
    # Returns this result to the caller and ends the current function.
    return DuelAttemptOutcome(
        # Supplies this item to the surrounding call or collection.
        game,
        # Supplies this item to the surrounding call or collection.
        latest,
        # Supplies this item to the surrounding call or collection.
        safe_event,
        # Supplies this item to the surrounding call or collection.
        completion_event,
        # Supplies this item to the surrounding call or collection.
        finalization_deadline,
        # Closes the multiline call, declaration, or collection started above.
    )


# Defines the `_finalize_room_after_tie_window` callable and its typed interface.
async def _finalize_room_after_tie_window(
    # Declares the typed `room_id` data field.
    room_id: uuid.UUID,
    # Declares the typed `deadline` data field.
    deadline: datetime,
    # Declares the typed `broker` data field.
    broker: Broker,
    # Completes the signature and declares the callable return type.
) -> None:
    # Computes and stores `delay` for subsequent operations.
    delay = max(0.0, (deadline - utcnow()).total_seconds())
    # Waits for this asynchronous operation to complete.
    await asyncio.sleep(delay)
    # Computes and stores `completion_event` for subsequent operations.
    completion_event = None
    # Acquires this asynchronous managed resource for the nested operation.
    async with SessionFactory() as session:
        # Computes and stores `room` for subsequent operations.
        room = await session.scalar(
            # Calls `select` with the supplied values.
            select(MultiplayerRoom).where(MultiplayerRoom.id == room_id).with_for_update()
            # Closes the multiline call, declaration, or collection started above.
        )
        # Checks this condition before executing the nested branch.
        if (
            # Executes this statement as the next step in the surrounding logic.
            room is not None
            # Executes this statement as the next step in the surrounding logic.
            and room.status == "active"
            # Executes this statement as the next step in the surrounding logic.
            and room.winner_id is not None
            # Executes this statement as the next step in the surrounding logic.
            and room.tie_deadline is not None
            # Executes this statement as the next step in the surrounding logic.
            and ensure_aware(room.tie_deadline) <= utcnow()
            # Begins the nested block or multiline expression completed below.
        ):
            # Computes and stores `room.status` for subsequent operations.
            room.status = "completed"
            # Computes and stores `completion_event` for subsequent operations.
            completion_event = await _room_completion_event(session, room, "tie_window_elapsed")
            # Waits for this asynchronous operation to complete.
            await session.commit()
    # Checks this condition before executing the nested branch.
    if completion_event is not None:
        # Acquires this managed resource and guarantees cleanup afterward.
        with suppress(RedisError, RuntimeError):
            # Waits for this asynchronous operation to complete.
            await broker.publish(str(room_id), completion_event)


# Defines the `_schedule_room_finalization` callable and its typed interface.
def _schedule_room_finalization(
    # Declares the typed `websocket` data field.
    websocket: WebSocket,
    # Declares the typed `room_id` data field.
    room_id: uuid.UUID,
    # Declares the typed `deadline` data field.
    deadline: datetime,
    # Declares the typed `broker` data field.
    broker: Broker,
    # Completes the signature and declares the callable return type.
) -> None:
    # Computes and stores `tasks` for subsequent operations.
    tasks: set[asyncio.Task[None]] = getattr(websocket.app.state, "room_finalization_tasks", set())
    # Computes and stores `websocket.app.state.room_finalization_tasks` for subsequent operations.
    websocket.app.state.room_finalization_tasks = tasks
    # Computes and stores `task` for subsequent operations.
    task = asyncio.create_task(_finalize_room_after_tie_window(room_id, deadline, broker))
    # Calls `tasks.add` with the supplied values.
    tasks.add(task)
    # Calls `task.add_done_callback` with the supplied values.
    task.add_done_callback(tasks.discard)


# Applies `@router.websocket("/{room_id}/events")` to configure the declaration immediately below.
@router.websocket("/{room_id}/events")
# Defines the `room_events` callable and its typed interface.
async def room_events(websocket: WebSocket, room_id: uuid.UUID) -> None:
    # Computes and stores `settings` for subsequent operations.
    settings = get_settings()
    # Checks this condition before executing the nested branch.
    if not settings.feature_multiplayer:
        # Waits for this asynchronous operation to complete.
        await websocket.close(code=1013, reason="Private duels are unavailable.")
        # Returns this result to the caller and ends the current function.
        return
    # Computes and stores `ticket` for subsequent operations.
    ticket = _websocket_ticket(websocket)
    # Checks this condition before executing the nested branch.
    if not ticket:
        # Waits for this asynchronous operation to complete.
        await websocket.close(code=4401, reason="Authentication required.")
        # Returns this result to the caller and ends the current function.
        return
    # Starts a protected operation whose expected failures are handled below.
    try:
        # Computes and stores `redis` for subsequent operations.
        redis = await _ensure_realtime_available(
            # Executes this statement as the next step in the surrounding logic.
            websocket.app.state,
            # Supplies this item to the surrounding call or collection.
            settings,
            # Provides the `require_ticket_store` value to the surrounding call.
            require_ticket_store=True,
            # Closes the multiline call, declaration, or collection started above.
        )
    # Handles the listed exception so failure remains controlled.
    except APIError:
        # Waits for this asynchronous operation to complete.
        await websocket.close(code=1013, reason="Realtime authentication is unavailable.")
        # Returns this result to the caller and ends the current function.
        return
    # Asserts this invariant so an unexpected test state fails immediately.
    assert redis is not None
    # Starts a protected operation whose expected failures are handled below.
    try:
        # Computes and stores `ticket_hash` for subsequent operations.
        ticket_hash = hashlib.sha256(ticket.encode()).hexdigest()
        # Acquires this asynchronous managed resource for the nested operation.
        async with asyncio.timeout(2):
            # Computes and stores `stored` for subsequent operations.
            stored = await redis.getdel(f"mastermind:ws-ticket:{ticket_hash}")
        # Computes and stores `ticket_data` for subsequent operations.
        ticket_data = json.loads(stored) if stored else None
        # Checks this condition before executing the nested branch.
        if (
            # Executes this statement as the next step in the surrounding logic.
            not isinstance(ticket_data, dict)
            # Executes this statement as the next step in the surrounding logic.
            or ticket_data.get("roomId") != str(room_id)
            # Executes this statement as the next step in the surrounding logic.
            or datetime.fromisoformat(str(ticket_data.get("expiresAt"))) <= utcnow()
            # Begins the nested block or multiline expression completed below.
        ):
            # Raises this exception to report an invalid or failed operation.
            raise ValueError("invalid ticket")
        # Computes and stores `principal` for subsequent operations.
        principal = AuthPrincipal(
            # Provides the `user_id` parameter or keyword argument.
            user_id=uuid.UUID(str(ticket_data["userId"])),
            # Provides the `is_anonymous` parameter or keyword argument.
            is_anonymous=bool(ticket_data.get("isAnonymous", True)),
            # Provides the `session_id` parameter or keyword argument.
            session_id=None,
            # Provides the `issued_at` parameter or keyword argument.
            issued_at=utcnow(),
            # Provides the `authenticated_at` parameter or keyword argument.
            authenticated_at=None,
            # Provides the `assurance_level` parameter or keyword argument.
            assurance_level=None,
            # Closes the multiline call, declaration, or collection started above.
        )
    # Handles the listed exception so failure remains controlled.
    except (RedisError, TimeoutError):
        # Waits for this asynchronous operation to complete.
        await websocket.close(code=1013, reason="Realtime authentication is unavailable.")
        # Returns this result to the caller and ends the current function.
        return
    # Handles the listed exception so failure remains controlled.
    except (ValueError, TypeError, json.JSONDecodeError):
        # Waits for this asynchronous operation to complete.
        await websocket.close(code=4401, reason="Invalid or expired realtime ticket.")
        # Returns this result to the caller and ends the current function.
        return
    # Computes and stores `broker` for subsequent operations.
    broker: Broker = websocket.app.state.broker
    # Checks this condition before executing the nested branch.
    if not broker.available:
        # Waits for this asynchronous operation to complete.
        await websocket.close(code=1013, reason="Realtime service unavailable.")
        # Returns this result to the caller and ends the current function.
        return
    # Acquires this asynchronous managed resource for the nested operation.
    async with SessionFactory() as session:
        # Checks this condition before executing the nested branch.
        if not await feature_enabled(session, settings, "multiplayer"):
            # Waits for this asynchronous operation to complete.
            await websocket.close(code=1013, reason="Private duels are unavailable.")
            # Returns this result to the caller and ends the current function.
            return
        # Starts a protected operation whose expected failures are handled below.
        try:
            # Computes and stores `room` for subsequent operations.
            room = await load_room_for_member(session, room_id, principal)
        # Handles the listed exception so failure remains controlled.
        except APIError:
            # Waits for this asynchronous operation to complete.
            await websocket.close(code=4403, reason="Room access denied.")
            # Returns this result to the caller and ends the current function.
            return
        # Checks this condition before executing the nested branch.
        if room.status == "expired":
            # Waits for this asynchronous operation to complete.
            await websocket.close(code=4408, reason="Room expired.")
            # Returns this result to the caller and ends the current function.
            return
        # Computes and stores `member_exists` for subsequent operations.
        member_exists = await session.scalar(
            # Calls `select` with the supplied values.
            select(MultiplayerMember).where(
                # Supplies this item to the surrounding call or collection.
                MultiplayerMember.room_id == room.id,
                # Supplies this item to the surrounding call or collection.
                MultiplayerMember.user_id == principal.user_id,
                # Closes the multiline call, declaration, or collection started above.
            )
            # Closes the multiline call, declaration, or collection started above.
        )
        # Checks this condition before executing the nested branch.
        if member_exists is None:
            # Waits for this asynchronous operation to complete.
            await websocket.close(code=4403, reason="Room access denied.")
            # Returns this result to the caller and ends the current function.
            return

    # Computes and stores `subscription_ready` for subsequent operations.
    subscription_ready = asyncio.Event()
    # Computes and stores `subscription_failed` for subsequent operations.
    subscription_failed = asyncio.Event()
    # Computes and stores `begin_forwarding` for subsequent operations.
    begin_forwarding = asyncio.Event()

    # Defines the `forward_events` callable and its typed interface.
    async def forward_events() -> None:
        # Starts a protected operation whose expected failures are handled below.
        try:
            # Acquires this asynchronous managed resource for the nested operation.
            async with broker.subscribe(str(room_id)) as events:
                # Calls `subscription_ready.set` with the supplied values.
                subscription_ready.set()
                # Waits for this asynchronous operation to complete.
                await begin_forwarding.wait()
                # Iterates asynchronously through the supplied values.
                async for event in events:
                    # Calls `event.setdefault` with the supplied values.
                    event.setdefault("version", WEBSOCKET_PROTOCOL_VERSION)
                    # Waits for this asynchronous operation to complete.
                    await websocket.send_json(event)
        # Handles the listed exception so failure remains controlled.
        except (RedisError, RuntimeError, json.JSONDecodeError):
            # Calls `subscription_failed.set` with the supplied values.
            subscription_failed.set()
            # Calls `subscription_ready.set` with the supplied values.
            subscription_ready.set()
            # Checks this condition before executing the nested branch.
            if begin_forwarding.is_set():
                # Waits for this asynchronous operation to complete.
                await websocket.close(code=1013, reason="Realtime broker interrupted.")

    # Computes and stores `forward_task` for subsequent operations.
    forward_task = asyncio.create_task(forward_events())
    # Waits for this asynchronous operation to complete.
    await subscription_ready.wait()
    # Checks this condition before executing the nested branch.
    if subscription_failed.is_set():
        # Waits for this asynchronous operation to complete.
        await websocket.close(code=1013, reason="Realtime broker unavailable.")
        # Returns this result to the caller and ends the current function.
        return
    # Computes and stores `peer` for subsequent operations.
    peer = trusted_client_ip(
        # Supplies this item to the surrounding call or collection.
        websocket.client.host if websocket.client else None,
        # Calls `websocket.headers.get` with the supplied values.
        websocket.headers.get("x-forwarded-for"),
        # Supplies this item to the surrounding call or collection.
        settings.trusted_proxy_ips,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `connection_token` for subsequent operations.
    connection_token = uuid.uuid4().hex
    # Starts a protected operation whose expected failures are handled below.
    try:
        # Begins the nested block or multiline expression completed below.
        (
            # Supplies this item to the surrounding call or collection.
            allowed,
            # Supplies this item to the surrounding call or collection.
            user_connection_count,
            # Supplies this item to the surrounding call or collection.
            user_connection_key,
            # Supplies this item to the surrounding call or collection.
            ip_connection_key,
            # Executes this statement as the next step in the surrounding logic.
        ) = await _claim_connection(redis, principal, peer, connection_token, settings)
    # Handles the listed exception so failure remains controlled.
    except RedisError:
        # Calls `forward_task.cancel` with the supplied values.
        forward_task.cancel()
        # Acquires this managed resource and guarantees cleanup afterward.
        with suppress(asyncio.CancelledError):
            # Waits for this asynchronous operation to complete.
            await forward_task
        # Waits for this asynchronous operation to complete.
        await websocket.close(code=1013, reason="Realtime admission is unavailable.")
        # Returns this result to the caller and ends the current function.
        return
    # Checks this condition before executing the nested branch.
    if not allowed:
        # Calls `forward_task.cancel` with the supplied values.
        forward_task.cancel()
        # Acquires this managed resource and guarantees cleanup afterward.
        with suppress(asyncio.CancelledError):
            # Waits for this asynchronous operation to complete.
            await forward_task
        # Waits for this asynchronous operation to complete.
        await websocket.close(code=4429, reason="Realtime connection limit exceeded.")
        # Returns this result to the caller and ends the current function.
        return
    # Starts a protected operation whose expected failures are handled below.
    try:
        # Computes and stores `after` for subsequent operations.
        after = int(websocket.query_params.get("after", "0"))
        # Checks this condition before executing the nested branch.
        if after < 0:
            # Raises this exception to report an invalid or failed operation.
            raise ValueError("negative sequence")
    # Handles the listed exception so failure remains controlled.
    except ValueError:
        # Calls `forward_task.cancel` with the supplied values.
        forward_task.cancel()
        # Acquires this managed resource and guarantees cleanup afterward.
        with suppress(asyncio.CancelledError):
            # Waits for this asynchronous operation to complete.
            await forward_task
        # Acquires this managed resource and guarantees cleanup afterward.
        with suppress(RedisError):
            # Waits for this asynchronous operation to complete.
            await _release_connection(
                # Executes this statement as the next step in the surrounding logic.
                redis,
                # Supplies this item to the surrounding call or collection.
                user_connection_key,
                # Supplies this item to the surrounding call or collection.
                ip_connection_key,
                # Supplies this item to the surrounding call or collection.
                connection_token,
                # Closes the multiline call, declaration, or collection started above.
            )
        # Waits for this asynchronous operation to complete.
        await websocket.close(code=4400, reason="Invalid replay sequence.")
        # Returns this result to the caller and ends the current function.
        return
    # Acquires this asynchronous managed resource for the nested operation.
    async with SessionFactory() as presence_session:
        # Starts a protected operation whose expected failures are handled below.
        try:
            # Computes and stores `room` for subsequent operations.
            room = await load_room_for_member(presence_session, room_id, principal, for_update=True)
        # Handles the listed exception so failure remains controlled.
        except APIError:
            # Calls `forward_task.cancel` with the supplied values.
            forward_task.cancel()
            # Acquires this managed resource and guarantees cleanup afterward.
            with suppress(asyncio.CancelledError):
                # Waits for this asynchronous operation to complete.
                await forward_task
            # Acquires this managed resource and guarantees cleanup afterward.
            with suppress(RedisError):
                # Waits for this asynchronous operation to complete.
                await _release_connection(
                    # Executes this statement as the next step in the surrounding logic.
                    redis,
                    # Supplies this item to the surrounding call or collection.
                    user_connection_key,
                    # Supplies this item to the surrounding call or collection.
                    ip_connection_key,
                    # Supplies this item to the surrounding call or collection.
                    connection_token,
                    # Closes the multiline call, declaration, or collection started above.
                )
            # Waits for this asynchronous operation to complete.
            await websocket.close(code=4403, reason="Room access denied.")
            # Returns this result to the caller and ends the current function.
            return
        # Computes and stores `member` for subsequent operations.
        member = await presence_session.scalar(
            # Calls `select` with the supplied values.
            select(MultiplayerMember).where(
                # Supplies this item to the surrounding call or collection.
                MultiplayerMember.room_id == room.id,
                # Supplies this item to the surrounding call or collection.
                MultiplayerMember.user_id == principal.user_id,
                # Closes the multiline call, declaration, or collection started above.
            )
            # Closes the multiline call, declaration, or collection started above.
        )
        # Checks this condition before executing the nested branch.
        if member is None:
            # Calls `forward_task.cancel` with the supplied values.
            forward_task.cancel()
            # Acquires this managed resource and guarantees cleanup afterward.
            with suppress(asyncio.CancelledError):
                # Waits for this asynchronous operation to complete.
                await forward_task
            # Acquires this managed resource and guarantees cleanup afterward.
            with suppress(RedisError):
                # Waits for this asynchronous operation to complete.
                await _release_connection(
                    # Executes this statement as the next step in the surrounding logic.
                    redis,
                    # Supplies this item to the surrounding call or collection.
                    user_connection_key,
                    # Supplies this item to the surrounding call or collection.
                    ip_connection_key,
                    # Supplies this item to the surrounding call or collection.
                    connection_token,
                    # Closes the multiline call, declaration, or collection started above.
                )
            # Waits for this asynchronous operation to complete.
            await websocket.close(code=4403, reason="Room access denied.")
            # Returns this result to the caller and ends the current function.
            return
        # Computes and stores `member.connected` for subsequent operations.
        member.connected = True
        # Computes and stores `member.last_seen_at` for subsequent operations.
        member.last_seen_at = utcnow()
        # Computes and stores `connected` for subsequent operations.
        connected = None
        # Checks this condition before executing the nested branch.
        if user_connection_count == 1:
            # Computes and stores `connected` for subsequent operations.
            connected = await _record_event(
                # Supplies this item to the surrounding call or collection.
                presence_session,
                # Supplies this item to the surrounding call or collection.
                room,
                # Supplies this item to the surrounding call or collection.
                "presence",
                # Supplies this item to the surrounding call or collection.
                {"userId": str(principal.user_id), "connected": True},
                # Closes the multiline call, declaration, or collection started above.
            )
        # Waits for this asynchronous operation to complete.
        await presence_session.commit()
        # Computes and stores `snapshot` for subsequent operations.
        snapshot = await room_response(presence_session, room, viewer_id=principal.user_id)
        # Computes and stores `snapshot_sequence` for subsequent operations.
        snapshot_sequence = room.event_sequence

    # Computes and stores `replay_events` for subsequent operations.
    replay_events: list[MultiplayerEvent] = []
    # Computes and stores `replay_gap` for subsequent operations.
    replay_gap = after > snapshot_sequence
    # Checks this condition before executing the nested branch.
    if after > 0:
        # Acquires this asynchronous managed resource for the nested operation.
        async with SessionFactory() as replay_session:
            # Computes and stores `replay_events` for subsequent operations.
            replay_events = list(
                # Waits for this asynchronous operation to complete.
                await replay_session.scalars(
                    # Calls `select` with the supplied values.
                    select(MultiplayerEvent)
                    # Begins the nested block or multiline expression completed below.
                    .where(
                        # Supplies this item to the surrounding call or collection.
                        MultiplayerEvent.room_id == room_id,
                        # Supplies this item to the surrounding call or collection.
                        MultiplayerEvent.sequence > after,
                        # Supplies this item to the surrounding call or collection.
                        MultiplayerEvent.sequence <= snapshot_sequence,
                        # Closes the multiline call, declaration, or collection started above.
                    )
                    # Executes this statement as the next step in the surrounding logic.
                    .order_by(MultiplayerEvent.sequence)
                    # Executes this statement as the next step in the surrounding logic.
                    .limit(MAX_REPLAY_EVENTS + 1)
                    # Closes the multiline call, declaration, or collection started above.
                )
                # Closes the multiline call, declaration, or collection started above.
            )
            # Computes and stores `replay_gap` for subsequent operations.
            replay_gap = replay_gap or len(replay_events) > MAX_REPLAY_EVENTS

    # Waits for this asynchronous operation to complete.
    await websocket.accept(subprotocol=WEBSOCKET_SUBPROTOCOL)
    # Checks this condition before executing the nested branch.
    if not replay_gap:
        # Iterates through the supplied values for the nested operation.
        for replay_event in replay_events:
            # Waits for this asynchronous operation to complete.
            await websocket.send_json(
                # Calls `_server_event` with the supplied values.
                _server_event(
                    # Supplies this item to the surrounding call or collection.
                    replay_event.event_type,
                    # Supplies this item to the surrounding call or collection.
                    replay_event.payload,
                    # Provides the `sequence` parameter or keyword argument.
                    sequence=replay_event.sequence,
                    # Closes the multiline call, declaration, or collection started above.
                )
                # Closes the multiline call, declaration, or collection started above.
            )
    # Waits for this asynchronous operation to complete.
    await websocket.send_json(
        # Calls `_server_event` with the supplied values.
        _server_event(
            # Supplies this item to the surrounding call or collection.
            "snapshot",
            # Calls `snapshot.model_dump` with the supplied values.
            snapshot.model_dump(by_alias=True, mode="json"),
            # Provides the `sequence` parameter or keyword argument.
            sequence=snapshot_sequence,
            # Closes the multiline call, declaration, or collection started above.
        )
        # Closes the multiline call, declaration, or collection started above.
    )
    # Checks this condition before executing the nested branch.
    if replay_gap:
        # Waits for this asynchronous operation to complete.
        await websocket.send_json(
            # Calls `_server_event` with the supplied values.
            _server_event(
                # Supplies this item to the surrounding call or collection.
                "resync_required",
                # Begins the nested block or multiline expression completed below.
                {
                    # Associates the `after` key with its value.
                    "after": after,
                    # Associates the `snapshotSequence` key with its value.
                    "snapshotSequence": snapshot_sequence,
                    # Associates the `reason` key with its value.
                    "reason": "replay_gap",
                    # Closes the multiline call, declaration, or collection started above.
                },
                # Provides the `sequence` parameter or keyword argument.
                sequence=snapshot_sequence,
                # Closes the multiline call, declaration, or collection started above.
            )
            # Closes the multiline call, declaration, or collection started above.
        )
    # Calls `begin_forwarding.set` with the supplied values.
    begin_forwarding.set()
    # Checks this condition before executing the nested branch.
    if connected is not None:
        # Waits for this asynchronous operation to complete.
        await broker.publish(str(room_id), connected)
    # Checks this condition before executing the nested branch.
    if after > 0:
        # Calls `WEBSOCKET_RECONNECTS.inc` with the supplied values.
        WEBSOCKET_RECONNECTS.inc()
    # Computes and stores `limiter` for subsequent operations.
    limiter = websocket.app.state.rate_limiter
    # Computes and stores `subject_rate_key` for subsequent operations.
    subject_rate_key = hashlib.sha256(f"ws-sub:{principal.user_id}".encode()).hexdigest()
    # Computes and stores `ip_rate_key` for subsequent operations.
    ip_rate_key = hashlib.sha256(f"ws-ip:{peer}".encode()).hexdigest()
    # Calls `WEBSOCKET_CONNECTIONS.inc` with the supplied values.
    WEBSOCKET_CONNECTIONS.inc()
    # Starts a protected operation whose expected failures are handled below.
    try:
        # Repeats the nested block while this condition remains true.
        while True:
            # Starts a protected operation whose expected failures are handled below.
            try:
                # Computes and stores `frame` for subsequent operations.
                frame = await asyncio.wait_for(websocket.receive(), timeout=40)
            # Handles the listed exception so failure remains controlled.
            except TimeoutError:
                # Waits for this asynchronous operation to complete.
                await websocket.close(code=4408, reason="Heartbeat timed out.")
                # Stops the nearest loop after reaching its terminating case.
                break
            # Checks this condition before executing the nested branch.
            if frame["type"] == "websocket.disconnect":
                # Raises this exception to report an invalid or failed operation.
                raise WebSocketDisconnect(frame.get("code", 1000))
            # Computes and stores `frame_value` for subsequent operations.
            frame_value = frame.get("bytes")
            # Checks this condition before executing the nested branch.
            if frame_value is None:
                # Computes and stores `frame_value` for subsequent operations.
                frame_value = str(frame.get("text") or "").encode()
            # Checks this condition before executing the nested branch.
            if len(frame_value) > settings.websocket_frame_limit_bytes:
                # Waits for this asynchronous operation to complete.
                await websocket.close(code=1009, reason="Realtime frame exceeds 4 KiB.")
                # Stops the nearest loop after reaching its terminating case.
                break
            # Starts a protected operation whose expected failures are handled below.
            try:
                # Waits for this asynchronous operation to complete.
                await limiter.check(subject_rate_key)
                # Waits for this asynchronous operation to complete.
                await limiter.check(ip_rate_key)
            # Handles the listed exception so failure remains controlled.
            except APIError as exc:
                # Waits for this asynchronous operation to complete.
                await websocket.send_json(
                    # Calls `_server_event` with the supplied values.
                    _server_event("error", {"code": exc.code, "message": exc.message})
                    # Closes the multiline call, declaration, or collection started above.
                )
                # Waits for this asynchronous operation to complete.
                await websocket.close(code=4429, reason="Realtime message rate exceeded.")
                # Stops the nearest loop after reaching its terminating case.
                break
            # Starts a protected operation whose expected failures are handled below.
            try:
                # Computes and stores `raw` for subsequent operations.
                raw = json.loads(frame_value)
                # Computes and stores `message` for subsequent operations.
                message = RoomClientMessage.model_validate(raw)
            # Handles the listed exception so failure remains controlled.
            except (json.JSONDecodeError, UnicodeDecodeError, ValidationError):
                # Waits for this asynchronous operation to complete.
                await websocket.send_json(
                    # Calls `_server_event` with the supplied values.
                    _server_event(
                        # Supplies this item to the surrounding call or collection.
                        "error",
                        # Begins the nested block or multiline expression completed below.
                        {
                            # Associates the `code` key with its value.
                            "code": "INVALID_EVENT",
                            # Associates the `message` key with its value.
                            "message": "The room event is invalid.",
                            # Closes the multiline call, declaration, or collection started above.
                        },
                        # Closes the multiline call, declaration, or collection started above.
                    )
                    # Closes the multiline call, declaration, or collection started above.
                )
                # Skips the remaining work and advances to the next iteration.
                continue
            # Checks this condition before executing the nested branch.
            if message.type == "heartbeat":
                # Starts a protected operation whose expected failures are handled below.
                try:
                    # Waits for this asynchronous operation to complete.
                    await _refresh_connection(
                        # Supplies this item to the surrounding call or collection.
                        redis,
                        # Supplies this item to the surrounding call or collection.
                        user_connection_key,
                        # Supplies this item to the surrounding call or collection.
                        ip_connection_key,
                        # Supplies this item to the surrounding call or collection.
                        connection_token,
                        # Supplies this item to the surrounding call or collection.
                        settings,
                        # Closes the multiline call, declaration, or collection started above.
                    )
                # Handles the listed exception so failure remains controlled.
                except RedisError:
                    # Waits for this asynchronous operation to complete.
                    await websocket.close(code=1013, reason="Realtime presence is unavailable.")
                    # Stops the nearest loop after reaching its terminating case.
                    break
                # Acquires this asynchronous managed resource for the nested operation.
                async with SessionFactory() as heartbeat_session:
                    # Computes and stores `heartbeat_member` for subsequent operations.
                    heartbeat_member = await heartbeat_session.scalar(
                        # Calls `select` with the supplied values.
                        select(MultiplayerMember).where(
                            # Supplies this item to the surrounding call or collection.
                            MultiplayerMember.room_id == room_id,
                            # Supplies this item to the surrounding call or collection.
                            MultiplayerMember.user_id == principal.user_id,
                            # Closes the multiline call, declaration, or collection started above.
                        )
                        # Closes the multiline call, declaration, or collection started above.
                    )
                    # Checks this condition before executing the nested branch.
                    if heartbeat_member:
                        # Computes and stores `heartbeat_member.last_seen_at` for subsequent
                        # operations.
                        heartbeat_member.last_seen_at = utcnow()
                        # Waits for this asynchronous operation to complete.
                        await heartbeat_session.commit()
                # Waits for this asynchronous operation to complete.
                await websocket.send_json(
                    # Calls `_server_event` with the supplied values.
                    _server_event("heartbeat_ack", {"serverTime": utcnow().isoformat()})
                    # Closes the multiline call, declaration, or collection started above.
                )
                # Skips the remaining work and advances to the next iteration.
                continue
            # Asserts this invariant so an unexpected test state fails immediately.
            assert message.guess is not None and message.idempotency_key is not None
            # Acquires this asynchronous managed resource for the nested operation.
            async with SessionFactory() as attempt_session:
                # Starts a protected operation whose expected failures are handled below.
                try:
                    # Computes and stores `outcome` for subsequent operations.
                    outcome = await _submit_duel_attempt_transaction(
                        # Supplies this item to the surrounding call or collection.
                        attempt_session,
                        # Supplies this item to the surrounding call or collection.
                        room_id,
                        # Supplies this item to the surrounding call or collection.
                        principal,
                        # Supplies this item to the surrounding call or collection.
                        message.guess,
                        # Supplies this item to the surrounding call or collection.
                        message.idempotency_key,
                        # Supplies this item to the surrounding call or collection.
                        f"ws:{uuid.uuid4()}",
                        # Calls `get_cipher` with the supplied values.
                        get_cipher(settings),
                        # Supplies this item to the surrounding call or collection.
                        settings,
                        # Closes the multiline call, declaration, or collection started above.
                    )
                # Handles the listed exception so failure remains controlled.
                except DuelRoomFinalized as finalized:
                    # Checks this condition before executing the nested branch.
                    if finalized.event is not None:
                        # Acquires this managed resource and guarantees cleanup afterward.
                        with suppress(RedisError, RuntimeError):
                            # Waits for this asynchronous operation to complete.
                            await broker.publish(str(room_id), finalized.event)
                    # Waits for this asynchronous operation to complete.
                    await websocket.send_json(
                        # Calls `_server_event` with the supplied values.
                        _server_event(
                            # Supplies this item to the surrounding call or collection.
                            "error",
                            # Begins the nested block or multiline expression completed below.
                            {
                                # Associates the `code` key with its value.
                                "code": "ROOM_NOT_ACTIVE",
                                # Associates the `message` key with its value.
                                "message": "This room is not accepting guesses.",
                                # Closes the multiline call, declaration, or collection started
                                # above.
                            },
                            # Closes the multiline call, declaration, or collection started above.
                        )
                        # Closes the multiline call, declaration, or collection started above.
                    )
                    # Skips the remaining work and advances to the next iteration.
                    continue
                # Handles the listed exception so failure remains controlled.
                except APIError as exc:
                    # Waits for this asynchronous operation to complete.
                    await attempt_session.rollback()
                    # Waits for this asynchronous operation to complete.
                    await websocket.send_json(
                        # Calls `_server_event` with the supplied values.
                        _server_event(
                            # Supplies this item to the surrounding call or collection.
                            "error",
                            # Supplies this item to the surrounding call or collection.
                            {"code": exc.code, "message": exc.message},
                            # Closes the multiline call, declaration, or collection started above.
                        )
                        # Closes the multiline call, declaration, or collection started above.
                    )
                    # Skips the remaining work and advances to the next iteration.
                    continue
                # Handles the listed exception so failure remains controlled.
                except DomainError as exc:
                    # Waits for this asynchronous operation to complete.
                    await attempt_session.rollback()
                    # Waits for this asynchronous operation to complete.
                    await websocket.send_json(
                        # Calls `_server_event` with the supplied values.
                        _server_event("error", {"code": exc.code, "message": exc.message})
                        # Closes the multiline call, declaration, or collection started above.
                    )
                    # Skips the remaining work and advances to the next iteration.
                    continue
                # Checks this condition before executing the nested branch.
                if outcome.duplicate:
                    # Waits for this asynchronous operation to complete.
                    await websocket.send_json(
                        # Calls `_server_event` with the supplied values.
                        _server_event(
                            # Supplies this item to the surrounding call or collection.
                            "attempt_result",
                            # Begins the nested block or multiline expression completed below.
                            {
                                # Associates the `number` key with its value.
                                "number": outcome.attempt.attempt_number,
                                # Associates the `guess` key with its value.
                                "guess": outcome.attempt.guess,
                                # Associates the `feedback` key with its value.
                                "feedback": {
                                    # Associates the `black` key with its value.
                                    "black": outcome.attempt.black_pegs,
                                    # Associates the `white` key with its value.
                                    "white": outcome.attempt.white_pegs,
                                    # Closes the multiline call, declaration, or collection started
                                    # above.
                                },
                                # Associates the `status` key with its value.
                                "status": outcome.game.status,
                                # Associates the `duplicate` key with its value.
                                "duplicate": True,
                                # Closes the multiline call, declaration, or collection started
                                # above.
                            },
                            # Closes the multiline call, declaration, or collection started above.
                        )
                        # Closes the multiline call, declaration, or collection started above.
                    )
                    # Skips the remaining work and advances to the next iteration.
                    continue
                # Asserts this invariant so an unexpected test state fails immediately.
                assert outcome.safe_event is not None
                # Waits for this asynchronous operation to complete.
                await websocket.send_json(
                    # Calls `_server_event` with the supplied values.
                    _server_event(
                        # Supplies this item to the surrounding call or collection.
                        "attempt_result",
                        # Begins the nested block or multiline expression completed below.
                        {
                            # Associates the `number` key with its value.
                            "number": outcome.attempt.attempt_number,
                            # Associates the `guess` key with its value.
                            "guess": outcome.attempt.guess,
                            # Associates the `feedback` key with its value.
                            "feedback": {
                                # Associates the `black` key with its value.
                                "black": outcome.attempt.black_pegs,
                                # Associates the `white` key with its value.
                                "white": outcome.attempt.white_pegs,
                                # Closes the multiline call, declaration, or collection started
                                # above.
                            },
                            # Associates the `status` key with its value.
                            "status": outcome.game.status,
                            # Closes the multiline call, declaration, or collection started above.
                        },
                        # Provides the `sequence` parameter or keyword argument.
                        sequence=outcome.safe_event["sequence"],
                        # Closes the multiline call, declaration, or collection started above.
                    )
                    # Closes the multiline call, declaration, or collection started above.
                )
                # Waits for this asynchronous operation to complete.
                await broker.publish(str(room_id), outcome.safe_event)
                # Checks this condition before executing the nested branch.
                if outcome.completion_event is not None:
                    # Waits for this asynchronous operation to complete.
                    await broker.publish(str(room_id), outcome.completion_event)
                # Checks this alternative when previous conditions were false.
                elif outcome.finalization_deadline is not None:
                    # Calls `_schedule_room_finalization` with the supplied values.
                    _schedule_room_finalization(
                        # Executes this statement as the next step in the surrounding logic.
                        websocket,
                        # Supplies this item to the surrounding call or collection.
                        room_id,
                        # Supplies this item to the surrounding call or collection.
                        outcome.finalization_deadline,
                        # Supplies this item to the surrounding call or collection.
                        broker,
                        # Closes the multiline call, declaration, or collection started above.
                    )
    # Handles the listed exception so failure remains controlled.
    except WebSocketDisconnect:
        # Provides the intentionally empty statement required by Python syntax.
        pass
    # Runs this cleanup block regardless of the protected result.
    finally:
        # Calls `WEBSOCKET_CONNECTIONS.dec` with the supplied values.
        WEBSOCKET_CONNECTIONS.dec()
        # Calls `forward_task.cancel` with the supplied values.
        forward_task.cancel()
        # Acquires this managed resource and guarantees cleanup afterward.
        with suppress(asyncio.CancelledError):
            # Waits for this asynchronous operation to complete.
            await forward_task
        # Computes and stores `remaining_connections` for subsequent operations.
        remaining_connections: int | None = None
        # Acquires this managed resource and guarantees cleanup afterward.
        with suppress(RedisError):
            # Computes and stores `remaining_connections` for subsequent operations.
            remaining_connections = await _release_connection(
                # Executes this statement as the next step in the surrounding logic.
                redis,
                # Supplies this item to the surrounding call or collection.
                user_connection_key,
                # Supplies this item to the surrounding call or collection.
                ip_connection_key,
                # Supplies this item to the surrounding call or collection.
                connection_token,
                # Closes the multiline call, declaration, or collection started above.
            )
        # Checks this condition before executing the nested branch.
        if remaining_connections == 0:
            # Acquires this asynchronous managed resource for the nested operation.
            async with SessionFactory() as close_session:
                # Declares the typed `closing_room` data field.
                closing_room: MultiplayerRoom | None
                # Starts a protected operation whose expected failures are handled below.
                try:
                    # Computes and stores `closing_room` for subsequent operations.
                    closing_room = await load_room_for_member(
                        # Executes this statement as the next step in the surrounding logic.
                        close_session,
                        # Supplies this item to the surrounding call or collection.
                        room_id,
                        # Supplies this item to the surrounding call or collection.
                        principal,
                        # Provides the `for_update` value to the surrounding call.
                        for_update=True,
                        # Closes the multiline call, declaration, or collection started above.
                    )
                # Handles the listed exception so failure remains controlled.
                except APIError:
                    # Computes and stores `closing_room` for subsequent operations.
                    closing_room = None
                # Checks this condition before executing the nested branch.
                if closing_room is not None:
                    # Computes and stores `close_member` for subsequent operations.
                    close_member = await close_session.scalar(
                        # Calls `select` with the supplied values.
                        select(MultiplayerMember).where(
                            # Supplies this item to the surrounding call or collection.
                            MultiplayerMember.room_id == room_id,
                            # Supplies this item to the surrounding call or collection.
                            MultiplayerMember.user_id == principal.user_id,
                            # Closes the multiline call, declaration, or collection started above.
                        )
                        # Closes the multiline call, declaration, or collection started above.
                    )
                    # Checks this condition before executing the nested branch.
                    if close_member:
                        # Computes and stores `close_member.connected` for subsequent operations.
                        close_member.connected = False
                        # Computes and stores `close_member.last_seen_at` for subsequent operations.
                        close_member.last_seen_at = utcnow()
                    # Computes and stores `disconnect_event` for subsequent operations.
                    disconnect_event = await _record_event(
                        # Supplies this item to the surrounding call or collection.
                        close_session,
                        # Supplies this item to the surrounding call or collection.
                        closing_room,
                        # Supplies this item to the surrounding call or collection.
                        "presence",
                        # Supplies this item to the surrounding call or collection.
                        {"userId": str(principal.user_id), "connected": False},
                        # Closes the multiline call, declaration, or collection started above.
                    )
                    # Waits for this asynchronous operation to complete.
                    await close_session.commit()
                    # Acquires this managed resource and guarantees cleanup afterward.
                    with suppress(RedisError, RuntimeError):
                        # Waits for this asynchronous operation to complete.
                        await broker.publish(str(room_id), disconnect_event)
