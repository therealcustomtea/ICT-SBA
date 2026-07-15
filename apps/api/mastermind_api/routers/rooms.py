from __future__ import annotations

import asyncio
import hashlib
import json
import secrets
import time
import uuid
from contextlib import suppress
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, Request, WebSocket, WebSocketDisconnect, status
from mastermind_core import DomainError
from pydantic import ValidationError
from redis.exceptions import RedisError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..auth import AuthPrincipal, get_current_user
from ..client_ip import trusted_client_ip
from ..config import Settings, get_settings
from ..crypto import SecretCipher
from ..database import SessionFactory, get_session
from ..dependencies import get_cipher
from ..errors import APIError
from ..features import feature_enabled
from ..metrics import WEBSOCKET_CONNECTIONS, WEBSOCKET_RECONNECTS
from ..models import (
    GameAttempt,
    GameSession,
    MultiplayerEvent,
    MultiplayerMember,
    MultiplayerRoom,
)
from ..rate_limit import enforce_action_limit
from ..realtime import (
    Broker,
    RedisBroker,
    UnavailableBroker,
    record_room_completion,
    record_room_event,
)
from ..schemas import (
    CreateRoomRequest,
    RoomClientMessage,
    RoomResponse,
    WebSocketTicketResponse,
)
from ..services import (
    create_room,
    ensure_aware,
    join_room,
    load_room_for_member,
    ready_room,
    room_response,
    submit_attempt,
    utcnow,
)

router = APIRouter(prefix="/v1/rooms", tags=["multiplayer"])

WEBSOCKET_PROTOCOL_VERSION = 1
WEBSOCKET_SUBPROTOCOL = "cipherboard-v1"
MAX_REPLAY_EVENTS = 200


class DuelRoomFinalized(Exception):
    def __init__(self, event: dict[str, Any] | None) -> None:
        super().__init__("The duel tie window elapsed before this command was accepted.")
        self.event = event


@dataclass(slots=True)
class DuelAttemptOutcome:
    game: GameSession
    attempt: GameAttempt
    safe_event: dict[str, Any] | None
    completion_event: dict[str, Any] | None
    finalization_deadline: datetime | None
    duplicate: bool = False


def _server_event(
    event_type: str,
    payload: dict[str, Any],
    *,
    sequence: int | None = None,
) -> dict[str, Any]:
    return {
        "version": WEBSOCKET_PROTOCOL_VERSION,
        "sequence": sequence,
        "type": event_type,
        "payload": payload,
    }


async def _claim_connection(
    redis: Any,
    principal: AuthPrincipal,
    peer: str,
    token: str,
    settings: Settings,
) -> tuple[bool, int, str, str]:
    user_digest = hashlib.sha256(f"ws-user:{principal.user_id}".encode()).hexdigest()
    ip_digest = hashlib.sha256(f"ws-peer:{peer}".encode()).hexdigest()
    user_key = f"mastermind:ws-connections:user:{user_digest}"
    ip_key = f"mastermind:ws-connections:ip:{ip_digest}"
    now = int(time.time())
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
    allowed, user_count = await redis.eval(
        script,
        2,
        user_key,
        ip_key,
        now,
        settings.websocket_connection_ttl_seconds,
        settings.websocket_user_connection_limit,
        settings.websocket_ip_connection_limit,
        token,
    )
    return bool(allowed), int(user_count), user_key, ip_key


async def _refresh_connection(
    redis: Any,
    user_key: str,
    ip_key: str,
    token: str,
    settings: Settings,
) -> None:
    now = int(time.time())
    pipeline = redis.pipeline(transaction=True)
    pipeline.zadd(user_key, {token: now}, xx=True)
    pipeline.zadd(ip_key, {token: now}, xx=True)
    pipeline.expire(user_key, settings.websocket_connection_ttl_seconds)
    pipeline.expire(ip_key, settings.websocket_connection_ttl_seconds)
    await pipeline.execute()


async def _release_connection(
    redis: Any,
    user_key: str,
    ip_key: str,
    token: str,
) -> int:
    script = """
    redis.call('ZREM', KEYS[1], ARGV[1])
    redis.call('ZREM', KEYS[2], ARGV[1])
    return redis.call('ZCARD', KEYS[1])
    """
    return int(await redis.eval(script, 2, user_key, ip_key, token))


async def require_rooms(session: AsyncSession, settings: Settings) -> None:
    if not await feature_enabled(session, settings, "multiplayer"):
        raise APIError(503, "FEATURE_DISABLED", "Private duels are temporarily unavailable.")


async def _ensure_realtime_available(
    state: Any,
    settings: Settings,
    *,
    require_ticket_store: bool = False,
) -> Any | None:
    """Probe Redis at realtime boundaries so a startup outage can recover."""

    redis = state.redis
    if redis is None:
        state.redis_ready = False
        if settings.environment in {"production", "staging"} or require_ticket_store:
            raise APIError(503, "REALTIME_UNAVAILABLE", "Realtime play is temporarily unavailable.")
        if not state.broker.available:
            raise APIError(503, "REALTIME_UNAVAILABLE", "Realtime play is temporarily unavailable.")
        return None
    try:
        async with asyncio.timeout(2):
            await redis.ping()
    except (RedisError, TimeoutError):
        state.redis_ready = False
        if settings.environment in {"production", "staging"}:
            state.broker = UnavailableBroker()
        raise APIError(
            503, "REALTIME_UNAVAILABLE", "Realtime play is temporarily unavailable."
        ) from None
    state.redis_ready = True
    if settings.environment in {"production", "staging"} and not isinstance(
        state.broker, RedisBroker
    ):
        state.broker = RedisBroker(redis)
    return redis


def _ticket_from_protocol_header(header: str) -> str | None:
    offered = {protocol.strip() for protocol in header.split(",") if protocol.strip()}
    tickets = [
        protocol.removeprefix("ticket.") for protocol in offered if protocol.startswith("ticket.")
    ]
    if WEBSOCKET_SUBPROTOCOL not in offered or len(tickets) != 1:
        return None
    ticket = tickets[0]
    allowed_characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
    if (
        not ticket
        or len(ticket) > 128
        or not all(character in allowed_characters for character in ticket)
    ):
        return None
    return ticket


def _websocket_ticket(websocket: WebSocket) -> str | None:
    return _ticket_from_protocol_header(websocket.headers.get("sec-websocket-protocol", ""))


@router.post("/{room_id}/ws-ticket", response_model=WebSocketTicketResponse)
async def create_websocket_ticket_route(
    room_id: uuid.UUID,
    request: Request,
    principal: AuthPrincipal = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> WebSocketTicketResponse:
    await require_rooms(session, settings)
    await enforce_action_limit(
        request,
        action="room.ws_ticket",
        subject=principal.user_id,
        resource=room_id,
        weight=8,
        integrity_required=True,
    )
    await load_room_for_member(session, room_id, principal)
    redis = await _ensure_realtime_available(request.app.state, settings, require_ticket_store=True)
    assert redis is not None
    ticket = secrets.token_urlsafe(32)
    ticket_hash = hashlib.sha256(ticket.encode()).hexdigest()
    expires_at = utcnow() + timedelta(seconds=60)
    value = json.dumps(
        {
            "roomId": str(room_id),
            "userId": str(principal.user_id),
            "isAnonymous": principal.is_anonymous,
            "expiresAt": expires_at.isoformat(),
        }
    )
    try:
        async with asyncio.timeout(2):
            await redis.setex(f"mastermind:ws-ticket:{ticket_hash}", 60, value)
    except (RedisError, TimeoutError):
        request.app.state.redis_ready = False
        raise APIError(
            503, "REALTIME_UNAVAILABLE", "Realtime play is temporarily unavailable."
        ) from None
    return WebSocketTicketResponse(ticket=ticket, expires_at=expires_at)


@router.post("", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
async def create_room_route(
    payload: CreateRoomRequest,
    request: Request,
    principal: AuthPrincipal = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    cipher: SecretCipher = Depends(get_cipher),
    settings: Settings = Depends(get_settings),
) -> RoomResponse:
    await require_rooms(session, settings)
    await enforce_action_limit(
        request,
        action="room.create",
        subject=principal.user_id,
        weight=10,
        integrity_required=True,
    )
    await _ensure_realtime_available(request.app.state, settings)
    room, room_code = await create_room(
        session,
        principal,
        payload.difficulty,
        cipher,
        settings,
        payload.idempotency_key,
    )
    return await room_response(session, room, room_code, principal.user_id)


@router.post("/{room_code}/join", response_model=RoomResponse)
async def join_room_route(
    room_code: str,
    request: Request,
    principal: AuthPrincipal = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    cipher: SecretCipher = Depends(get_cipher),
    settings: Settings = Depends(get_settings),
) -> RoomResponse:
    await require_rooms(session, settings)
    await enforce_action_limit(
        request,
        action="room.join",
        subject=principal.user_id,
        resource=room_code,
        weight=10,
        integrity_required=True,
    )
    await _ensure_realtime_available(request.app.state, settings)
    room = await join_room(session, principal, room_code, cipher, settings)
    return await room_response(session, room, viewer_id=principal.user_id)


@router.post("/{room_id}/ready", response_model=RoomResponse)
async def ready_room_route(
    room_id: uuid.UUID,
    request: Request,
    principal: AuthPrincipal = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    cipher: SecretCipher = Depends(get_cipher),
    settings: Settings = Depends(get_settings),
) -> RoomResponse:
    await require_rooms(session, settings)
    await enforce_action_limit(
        request,
        action="room.ready",
        subject=principal.user_id,
        resource=room_id,
        weight=6,
        integrity_required=True,
    )
    await _ensure_realtime_available(request.app.state, settings)
    room, events = await ready_room(session, principal, room_id, cipher)
    broker: Broker = request.app.state.broker
    for event in events:
        with suppress(RedisError, RuntimeError):
            await broker.publish(str(room.id), event)
    return await room_response(session, room, viewer_id=principal.user_id)


@router.get("/{room_id}", response_model=RoomResponse)
async def get_room_route(
    room_id: uuid.UUID,
    principal: AuthPrincipal = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> RoomResponse:
    await require_rooms(session, settings)
    room = await load_room_for_member(session, room_id, principal)
    await session.commit()
    return await room_response(session, room, viewer_id=principal.user_id)


async def _record_event(
    session: AsyncSession,
    room: MultiplayerRoom,
    event_type: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    return await record_room_event(session, room, event_type, payload)


async def _room_completion_event(
    session: AsyncSession,
    room: MultiplayerRoom,
    reason: str,
) -> dict[str, Any] | None:
    return await record_room_completion(session, room, reason)


async def _lock_duel_attempt_state(
    session: AsyncSession,
    room_id: uuid.UUID,
    principal: AuthPrincipal,
) -> tuple[MultiplayerRoom, GameSession]:
    """Lock a duel in the single room -> ordered games acquisition order."""

    room = await load_room_for_member(session, room_id, principal, for_update=True)
    if (
        room.status == "active"
        and room.winner_id is not None
        and room.tie_deadline is not None
        and ensure_aware(room.tie_deadline) <= utcnow()
    ):
        room.status = "completed"
        event = await _room_completion_event(session, room, "tie_window_elapsed")
        await session.commit()
        raise DuelRoomFinalized(event)
    if room.status != "active":
        raise APIError(409, "ROOM_NOT_ACTIVE", "This room is not accepting guesses.")
    game = await session.scalar(
        select(GameSession)
        .options(selectinload(GameSession.attempts))
        .where(
            GameSession.room_id == room_id,
            GameSession.owner_id == principal.user_id,
        )
    )
    if game is None:
        raise APIError(404, "GAME_NOT_FOUND", "Your duel game was not found.")
    return room, game


async def _submit_duel_attempt_transaction(
    session: AsyncSession,
    room_id: uuid.UUID,
    principal: AuthPrincipal,
    guess: list[str],
    idempotency_key: str,
    request_id: str,
    cipher: SecretCipher,
    settings: Settings,
) -> DuelAttemptOutcome:
    """Apply one duel command under the authoritative lock order and commit it."""

    room, game = await _lock_duel_attempt_state(session, room_id, principal)
    previous = next(
        (attempt for attempt in game.attempts if attempt.idempotency_key == idempotency_key),
        None,
    )
    if previous and previous.guess == [peg.upper() for peg in guess]:
        await session.commit()
        return DuelAttemptOutcome(game, previous, None, None, None, duplicate=True)

    game = await submit_attempt(
        session,
        principal,
        game.public_id,
        guess,
        idempotency_key,
        request_id,
        cipher,
        commit=False,
        allow_duel=True,
    )
    just_completed = game.status == "won"
    finalization_deadline = None
    if just_completed and room.winner_id is None:
        room.winner_id = principal.user_id
        room.winner_at = utcnow()
        room.tie_deadline = room.winner_at + timedelta(milliseconds=settings.room_tie_window_ms)
        finalization_deadline = room.tie_deadline
    elif (
        just_completed
        and room.winner_id != principal.user_id
        and room.tie_deadline
        and utcnow() <= room.tie_deadline
    ):
        room.is_tie = True
        room.winner_id = None
        room.status = "completed"
    game_states = (
        await session.execute(
            select(GameSession.owner_id, GameSession.status).where(GameSession.room_id == room_id)
        )
    ).all()
    terminal_statuses = {"won", "lost", "abandoned", "expired"}
    completed_reason = None
    if game_states and all(status_value in terminal_statuses for _, status_value in game_states):
        winners = [owner_id for owner_id, status_value in game_states if status_value == "won"]
        if not winners:
            room.status = "completed"
            room.winner_id = None
            room.is_tie = True
            completed_reason = "both_lost"
        elif room.status == "completed":
            completed_reason = "tie_window" if room.is_tie else "winner"
    safe_event = await _record_event(
        session,
        room,
        "opponent_progress",
        {
            "userId": str(principal.user_id),
            "attemptsUsed": game.attempts_used,
            "completed": game.status in {"won", "lost"},
        },
    )
    completion_event = (
        await _room_completion_event(session, room, completed_reason)
        if completed_reason is not None
        else None
    )
    latest = game.attempts[-1]
    await session.commit()
    return DuelAttemptOutcome(
        game,
        latest,
        safe_event,
        completion_event,
        finalization_deadline,
    )


async def _finalize_room_after_tie_window(
    room_id: uuid.UUID,
    deadline: datetime,
    broker: Broker,
) -> None:
    delay = max(0.0, (deadline - utcnow()).total_seconds())
    await asyncio.sleep(delay)
    completion_event = None
    async with SessionFactory() as session:
        room = await session.scalar(
            select(MultiplayerRoom).where(MultiplayerRoom.id == room_id).with_for_update()
        )
        if (
            room is not None
            and room.status == "active"
            and room.winner_id is not None
            and room.tie_deadline is not None
            and ensure_aware(room.tie_deadline) <= utcnow()
        ):
            room.status = "completed"
            completion_event = await _room_completion_event(session, room, "tie_window_elapsed")
            await session.commit()
    if completion_event is not None:
        with suppress(RedisError, RuntimeError):
            await broker.publish(str(room_id), completion_event)


def _schedule_room_finalization(
    websocket: WebSocket,
    room_id: uuid.UUID,
    deadline: datetime,
    broker: Broker,
) -> None:
    tasks: set[asyncio.Task[None]] = getattr(websocket.app.state, "room_finalization_tasks", set())
    websocket.app.state.room_finalization_tasks = tasks
    task = asyncio.create_task(_finalize_room_after_tie_window(room_id, deadline, broker))
    tasks.add(task)
    task.add_done_callback(tasks.discard)


@router.websocket("/{room_id}/events")
async def room_events(websocket: WebSocket, room_id: uuid.UUID) -> None:
    settings = get_settings()
    if not settings.feature_multiplayer:
        await websocket.close(code=1013, reason="Private duels are unavailable.")
        return
    ticket = _websocket_ticket(websocket)
    if not ticket:
        await websocket.close(code=4401, reason="Authentication required.")
        return
    try:
        redis = await _ensure_realtime_available(
            websocket.app.state, settings, require_ticket_store=True
        )
    except APIError:
        await websocket.close(code=1013, reason="Realtime authentication is unavailable.")
        return
    assert redis is not None
    try:
        ticket_hash = hashlib.sha256(ticket.encode()).hexdigest()
        async with asyncio.timeout(2):
            stored = await redis.getdel(f"mastermind:ws-ticket:{ticket_hash}")
        ticket_data = json.loads(stored) if stored else None
        if (
            not isinstance(ticket_data, dict)
            or ticket_data.get("roomId") != str(room_id)
            or datetime.fromisoformat(str(ticket_data.get("expiresAt"))) <= utcnow()
        ):
            raise ValueError("invalid ticket")
        principal = AuthPrincipal(
            user_id=uuid.UUID(str(ticket_data["userId"])),
            is_anonymous=bool(ticket_data.get("isAnonymous", True)),
            session_id=None,
            issued_at=utcnow(),
            authenticated_at=None,
            assurance_level=None,
        )
    except (RedisError, TimeoutError):
        await websocket.close(code=1013, reason="Realtime authentication is unavailable.")
        return
    except (ValueError, TypeError, json.JSONDecodeError):
        await websocket.close(code=4401, reason="Invalid or expired realtime ticket.")
        return
    broker: Broker = websocket.app.state.broker
    if not broker.available:
        await websocket.close(code=1013, reason="Realtime service unavailable.")
        return
    async with SessionFactory() as session:
        if not await feature_enabled(session, settings, "multiplayer"):
            await websocket.close(code=1013, reason="Private duels are unavailable.")
            return
        try:
            room = await load_room_for_member(session, room_id, principal)
        except APIError:
            await websocket.close(code=4403, reason="Room access denied.")
            return
        if room.status == "expired":
            await websocket.close(code=4408, reason="Room expired.")
            return
        member_exists = await session.scalar(
            select(MultiplayerMember).where(
                MultiplayerMember.room_id == room.id,
                MultiplayerMember.user_id == principal.user_id,
            )
        )
        if member_exists is None:
            await websocket.close(code=4403, reason="Room access denied.")
            return

    subscription_ready = asyncio.Event()
    subscription_failed = asyncio.Event()
    begin_forwarding = asyncio.Event()

    async def forward_events() -> None:
        try:
            async with broker.subscribe(str(room_id)) as events:
                subscription_ready.set()
                await begin_forwarding.wait()
                async for event in events:
                    event.setdefault("version", WEBSOCKET_PROTOCOL_VERSION)
                    await websocket.send_json(event)
        except (RedisError, RuntimeError, json.JSONDecodeError):
            subscription_failed.set()
            subscription_ready.set()
            if begin_forwarding.is_set():
                await websocket.close(code=1013, reason="Realtime broker interrupted.")

    forward_task = asyncio.create_task(forward_events())
    await subscription_ready.wait()
    if subscription_failed.is_set():
        await websocket.close(code=1013, reason="Realtime broker unavailable.")
        return
    peer = trusted_client_ip(
        websocket.client.host if websocket.client else None,
        websocket.headers.get("x-forwarded-for"),
        settings.trusted_proxy_ips,
    )
    connection_token = uuid.uuid4().hex
    try:
        (
            allowed,
            user_connection_count,
            user_connection_key,
            ip_connection_key,
        ) = await _claim_connection(redis, principal, peer, connection_token, settings)
    except RedisError:
        forward_task.cancel()
        with suppress(asyncio.CancelledError):
            await forward_task
        await websocket.close(code=1013, reason="Realtime admission is unavailable.")
        return
    if not allowed:
        forward_task.cancel()
        with suppress(asyncio.CancelledError):
            await forward_task
        await websocket.close(code=4429, reason="Realtime connection limit exceeded.")
        return
    try:
        after = int(websocket.query_params.get("after", "0"))
        if after < 0:
            raise ValueError("negative sequence")
    except ValueError:
        forward_task.cancel()
        with suppress(asyncio.CancelledError):
            await forward_task
        with suppress(RedisError):
            await _release_connection(
                redis, user_connection_key, ip_connection_key, connection_token
            )
        await websocket.close(code=4400, reason="Invalid replay sequence.")
        return
    async with SessionFactory() as presence_session:
        try:
            room = await load_room_for_member(presence_session, room_id, principal, for_update=True)
        except APIError:
            forward_task.cancel()
            with suppress(asyncio.CancelledError):
                await forward_task
            with suppress(RedisError):
                await _release_connection(
                    redis, user_connection_key, ip_connection_key, connection_token
                )
            await websocket.close(code=4403, reason="Room access denied.")
            return
        member = await presence_session.scalar(
            select(MultiplayerMember).where(
                MultiplayerMember.room_id == room.id,
                MultiplayerMember.user_id == principal.user_id,
            )
        )
        if member is None:
            forward_task.cancel()
            with suppress(asyncio.CancelledError):
                await forward_task
            with suppress(RedisError):
                await _release_connection(
                    redis, user_connection_key, ip_connection_key, connection_token
                )
            await websocket.close(code=4403, reason="Room access denied.")
            return
        member.connected = True
        member.last_seen_at = utcnow()
        connected = None
        if user_connection_count == 1:
            connected = await _record_event(
                presence_session,
                room,
                "presence",
                {"userId": str(principal.user_id), "connected": True},
            )
        await presence_session.commit()
        snapshot = await room_response(presence_session, room, viewer_id=principal.user_id)
        snapshot_sequence = room.event_sequence

    replay_events: list[MultiplayerEvent] = []
    replay_gap = after > snapshot_sequence
    if after > 0:
        async with SessionFactory() as replay_session:
            replay_events = list(
                await replay_session.scalars(
                    select(MultiplayerEvent)
                    .where(
                        MultiplayerEvent.room_id == room_id,
                        MultiplayerEvent.sequence > after,
                        MultiplayerEvent.sequence <= snapshot_sequence,
                    )
                    .order_by(MultiplayerEvent.sequence)
                    .limit(MAX_REPLAY_EVENTS + 1)
                )
            )
            replay_gap = replay_gap or len(replay_events) > MAX_REPLAY_EVENTS

    await websocket.accept(subprotocol=WEBSOCKET_SUBPROTOCOL)
    if not replay_gap:
        for replay_event in replay_events:
            await websocket.send_json(
                _server_event(
                    replay_event.event_type,
                    replay_event.payload,
                    sequence=replay_event.sequence,
                )
            )
    await websocket.send_json(
        _server_event(
            "snapshot",
            snapshot.model_dump(by_alias=True, mode="json"),
            sequence=snapshot_sequence,
        )
    )
    if replay_gap:
        await websocket.send_json(
            _server_event(
                "resync_required",
                {
                    "after": after,
                    "snapshotSequence": snapshot_sequence,
                    "reason": "replay_gap",
                },
                sequence=snapshot_sequence,
            )
        )
    begin_forwarding.set()
    if connected is not None:
        await broker.publish(str(room_id), connected)
    if after > 0:
        WEBSOCKET_RECONNECTS.inc()
    limiter = websocket.app.state.rate_limiter
    subject_rate_key = hashlib.sha256(f"ws-sub:{principal.user_id}".encode()).hexdigest()
    ip_rate_key = hashlib.sha256(f"ws-ip:{peer}".encode()).hexdigest()
    WEBSOCKET_CONNECTIONS.inc()
    try:
        while True:
            try:
                frame = await asyncio.wait_for(websocket.receive(), timeout=40)
            except TimeoutError:
                await websocket.close(code=4408, reason="Heartbeat timed out.")
                break
            if frame["type"] == "websocket.disconnect":
                raise WebSocketDisconnect(frame.get("code", 1000))
            frame_value = frame.get("bytes")
            if frame_value is None:
                frame_value = str(frame.get("text") or "").encode()
            if len(frame_value) > settings.websocket_frame_limit_bytes:
                await websocket.close(code=1009, reason="Realtime frame exceeds 4 KiB.")
                break
            try:
                await limiter.check(subject_rate_key)
                await limiter.check(ip_rate_key)
            except APIError as exc:
                await websocket.send_json(
                    _server_event("error", {"code": exc.code, "message": exc.message})
                )
                await websocket.close(code=4429, reason="Realtime message rate exceeded.")
                break
            try:
                raw = json.loads(frame_value)
                message = RoomClientMessage.model_validate(raw)
            except (json.JSONDecodeError, UnicodeDecodeError, ValidationError):
                await websocket.send_json(
                    _server_event(
                        "error",
                        {
                            "code": "INVALID_EVENT",
                            "message": "The room event is invalid.",
                        },
                    )
                )
                continue
            if message.type == "heartbeat":
                try:
                    await _refresh_connection(
                        redis,
                        user_connection_key,
                        ip_connection_key,
                        connection_token,
                        settings,
                    )
                except RedisError:
                    await websocket.close(code=1013, reason="Realtime presence is unavailable.")
                    break
                async with SessionFactory() as heartbeat_session:
                    heartbeat_member = await heartbeat_session.scalar(
                        select(MultiplayerMember).where(
                            MultiplayerMember.room_id == room_id,
                            MultiplayerMember.user_id == principal.user_id,
                        )
                    )
                    if heartbeat_member:
                        heartbeat_member.last_seen_at = utcnow()
                        await heartbeat_session.commit()
                await websocket.send_json(
                    _server_event("heartbeat_ack", {"serverTime": utcnow().isoformat()})
                )
                continue
            assert message.guess is not None and message.idempotency_key is not None
            async with SessionFactory() as attempt_session:
                try:
                    outcome = await _submit_duel_attempt_transaction(
                        attempt_session,
                        room_id,
                        principal,
                        message.guess,
                        message.idempotency_key,
                        f"ws:{uuid.uuid4()}",
                        get_cipher(settings),
                        settings,
                    )
                except DuelRoomFinalized as finalized:
                    if finalized.event is not None:
                        with suppress(RedisError, RuntimeError):
                            await broker.publish(str(room_id), finalized.event)
                    await websocket.send_json(
                        _server_event(
                            "error",
                            {
                                "code": "ROOM_NOT_ACTIVE",
                                "message": "This room is not accepting guesses.",
                            },
                        )
                    )
                    continue
                except APIError as exc:
                    await attempt_session.rollback()
                    await websocket.send_json(
                        _server_event(
                            "error",
                            {"code": exc.code, "message": exc.message},
                        )
                    )
                    continue
                except DomainError as exc:
                    await attempt_session.rollback()
                    await websocket.send_json(
                        _server_event("error", {"code": exc.code, "message": exc.message})
                    )
                    continue
                if outcome.duplicate:
                    await websocket.send_json(
                        _server_event(
                            "attempt_result",
                            {
                                "number": outcome.attempt.attempt_number,
                                "guess": outcome.attempt.guess,
                                "feedback": {
                                    "black": outcome.attempt.black_pegs,
                                    "white": outcome.attempt.white_pegs,
                                },
                                "status": outcome.game.status,
                                "duplicate": True,
                            },
                        )
                    )
                    continue
                assert outcome.safe_event is not None
                await websocket.send_json(
                    _server_event(
                        "attempt_result",
                        {
                            "number": outcome.attempt.attempt_number,
                            "guess": outcome.attempt.guess,
                            "feedback": {
                                "black": outcome.attempt.black_pegs,
                                "white": outcome.attempt.white_pegs,
                            },
                            "status": outcome.game.status,
                        },
                        sequence=outcome.safe_event["sequence"],
                    )
                )
                await broker.publish(str(room_id), outcome.safe_event)
                if outcome.completion_event is not None:
                    await broker.publish(str(room_id), outcome.completion_event)
                elif outcome.finalization_deadline is not None:
                    _schedule_room_finalization(
                        websocket, room_id, outcome.finalization_deadline, broker
                    )
    except WebSocketDisconnect:
        pass
    finally:
        WEBSOCKET_CONNECTIONS.dec()
        forward_task.cancel()
        with suppress(asyncio.CancelledError):
            await forward_task
        remaining_connections: int | None = None
        with suppress(RedisError):
            remaining_connections = await _release_connection(
                redis, user_connection_key, ip_connection_key, connection_token
            )
        if remaining_connections == 0:
            async with SessionFactory() as close_session:
                closing_room: MultiplayerRoom | None
                try:
                    closing_room = await load_room_for_member(
                        close_session, room_id, principal, for_update=True
                    )
                except APIError:
                    closing_room = None
                if closing_room is not None:
                    close_member = await close_session.scalar(
                        select(MultiplayerMember).where(
                            MultiplayerMember.room_id == room_id,
                            MultiplayerMember.user_id == principal.user_id,
                        )
                    )
                    if close_member:
                        close_member.connected = False
                        close_member.last_seen_at = utcnow()
                    disconnect_event = await _record_event(
                        close_session,
                        closing_room,
                        "presence",
                        {"userId": str(principal.user_id), "connected": False},
                    )
                    await close_session.commit()
                    with suppress(RedisError, RuntimeError):
                        await broker.publish(str(room_id), disconnect_event)
