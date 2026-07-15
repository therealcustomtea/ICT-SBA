from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from collections.abc import AsyncIterator
from contextlib import AbstractAsyncContextManager, asynccontextmanager, suppress
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol

from mastermind_core import GameConfig, GameStatus, LeaderboardEligibility, calculate_score
from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .config import get_settings
from .features import feature_enabled
from .models import (
    GameSession,
    MultiplayerEvent,
    MultiplayerMember,
    MultiplayerRoom,
    Profile,
    UserAchievement,
)


class Broker(Protocol):
    available: bool

    async def publish(self, room_id: str, event: dict[str, Any]) -> None: ...

    def subscribe(
        self, room_id: str
    ) -> AbstractAsyncContextManager[AsyncIterator[dict[str, Any]]]: ...

    async def close(self) -> None: ...


class InMemoryBroker:
    """Development/test broker. Production uses Redis for horizontal fan-out."""

    available = True

    def __init__(self) -> None:
        self._subscribers: dict[str, set[asyncio.Queue[dict[str, Any]]]] = defaultdict(set)

    async def publish(self, room_id: str, event: dict[str, Any]) -> None:
        for queue in tuple(self._subscribers[room_id]):
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                while not queue.empty():
                    queue.get_nowait()
                queue.put_nowait(
                    {
                        "version": 1,
                        "sequence": event.get("sequence"),
                        "type": "resync_required",
                        "payload": {"reason": "slow_consumer"},
                    }
                )

    @asynccontextmanager
    async def subscribe(self, room_id: str) -> AsyncIterator[AsyncIterator[dict[str, Any]]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=100)
        self._subscribers[room_id].add(queue)

        async def events() -> AsyncIterator[dict[str, Any]]:
            while True:
                yield await queue.get()

        try:
            yield events()
        finally:
            self._subscribers[room_id].discard(queue)

    async def close(self) -> None:
        self._subscribers.clear()


class RedisBroker:
    available = True

    def __init__(self, client: Redis) -> None:
        self._client = client

    async def publish(self, room_id: str, event: dict[str, Any]) -> None:
        await self._client.publish(f"mastermind:room:{room_id}", json.dumps(event))

    @asynccontextmanager
    async def subscribe(self, room_id: str) -> AsyncIterator[AsyncIterator[dict[str, Any]]]:
        pubsub = self._client.pubsub()
        await pubsub.subscribe(f"mastermind:room:{room_id}")
        queue: asyncio.Queue[dict[str, Any] | Exception] = asyncio.Queue(maxsize=100)

        async def pump() -> None:
            try:
                async for message in pubsub.listen():
                    if message["type"] != "message":
                        continue
                    value = json.loads(message["data"])
                    if not isinstance(value, dict):
                        continue
                    try:
                        queue.put_nowait(value)
                    except asyncio.QueueFull:
                        while not queue.empty():
                            queue.get_nowait()
                        queue.put_nowait(
                            {
                                "version": 1,
                                "sequence": value.get("sequence"),
                                "type": "resync_required",
                                "payload": {"reason": "slow_consumer"},
                            }
                        )
            except (RedisError, RuntimeError, json.JSONDecodeError) as exc:
                while not queue.empty():
                    queue.get_nowait()
                queue.put_nowait(exc)

        pump_task = asyncio.create_task(pump())

        async def events() -> AsyncIterator[dict[str, Any]]:
            while True:
                value = await queue.get()
                if isinstance(value, Exception):
                    raise value
                yield value

        try:
            yield events()
        finally:
            pump_task.cancel()
            with suppress(asyncio.CancelledError):
                await pump_task
            await pubsub.unsubscribe(f"mastermind:room:{room_id}")
            await pubsub.aclose()  # type: ignore[no-untyped-call]

    async def close(self) -> None:
        await self._client.aclose()


class UnavailableBroker:
    available = False

    async def publish(self, room_id: str, event: dict[str, Any]) -> None:
        raise RuntimeError("Realtime broker is unavailable.")

    @asynccontextmanager
    async def subscribe(self, room_id: str) -> AsyncIterator[AsyncIterator[dict[str, Any]]]:
        yield _empty_events()

    async def close(self) -> None:
        return None


async def _empty_events() -> AsyncIterator[dict[str, Any]]:
    if False:
        yield {}


def _event_envelope(
    event_type: str,
    payload: dict[str, Any],
    sequence: int,
) -> dict[str, Any]:
    return {"version": 1, "sequence": sequence, "type": event_type, "payload": payload}


async def record_room_event(
    session: AsyncSession,
    room: MultiplayerRoom,
    event_type: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Append a safe room event while the caller holds the room transaction."""

    room.event_sequence += 1
    event = MultiplayerEvent(
        room_id=room.id,
        sequence=room.event_sequence,
        event_type=event_type,
        payload=payload,
    )
    session.add(event)
    return _event_envelope(event_type, payload, event.sequence)


async def award_duelist_if_eligible(
    session: AsyncSession,
    room: MultiplayerRoom,
) -> None:
    """Persist Duelist even when a background worker finalizes the room."""

    if room.winner_id is None or room.is_tie:
        return
    profile = await session.get(Profile, room.winner_id)
    if (
        profile is None
        or profile.is_anonymous
        or not await feature_enabled(session, get_settings(), "achievements")
    ):
        return
    game_id = await session.scalar(
        select(GameSession.id).where(
            GameSession.room_id == room.id,
            GameSession.owner_id == room.winner_id,
            GameSession.status == "won",
        )
    )
    if game_id is None:
        return
    try:
        async with session.begin_nested():
            session.add(
                UserAchievement(
                    user_id=room.winner_id,
                    achievement_key="duelist",
                    game_id=game_id,
                )
            )
            await session.flush()
    except IntegrityError:
        pass


def _aware_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


async def finalize_active_room_games(
    session: AsyncSession,
    room: MultiplayerRoom,
) -> None:
    """Close every remaining game when the authoritative room becomes terminal."""

    active_games = (
        await session.scalars(
            select(GameSession)
            .where(
                GameSession.room_id == room.id,
                GameSession.status == GameStatus.ACTIVE.value,
            )
            .order_by(GameSession.id)
            .with_for_update()
        )
    ).all()
    if not active_games:
        return
    now = datetime.now(UTC)
    candidate = room.tie_deadline or room.winner_at or now
    completed_at = min(_aware_utc(candidate), now)
    for game in active_games:
        status = (
            GameStatus.LOST
            if room.status == "completed"
            and room.winner_id is not None
            and game.owner_id != room.winner_id
            else GameStatus.ABANDONED
        )
        game.status = status.value
        game.completed_at = completed_at
        game.elapsed_seconds = max(
            0,
            int((completed_at - _aware_utc(game.started_at)).total_seconds()),
        )
        game.final_score = 0
        game.score_breakdown = calculate_score(
            GameConfig.from_dict(game.config),
            status=status,
            attempts_used=game.attempts_used,
            elapsed_seconds=game.elapsed_seconds,
        ).to_dict()
        game.ranked_eligibility = LeaderboardEligibility.UNRANKED.value


async def record_room_completion(
    session: AsyncSession,
    room: MultiplayerRoom,
    reason: str,
) -> dict[str, Any] | None:
    await finalize_active_room_games(session, room)
    await award_duelist_if_eligible(session, room)
    existing = await session.scalar(
        select(MultiplayerEvent.id).where(
            MultiplayerEvent.room_id == room.id,
            MultiplayerEvent.event_type == "room_completed",
        )
    )
    if existing is not None:
        return None
    return await record_room_event(
        session,
        room,
        "room_completed",
        {
            "winnerId": str(room.winner_id) if room.winner_id else None,
            "isTie": room.is_tie,
            "reason": reason,
        },
    )


async def finalize_due_rooms_once(
    session_factory: async_sessionmaker[AsyncSession],
    broker: Broker,
    *,
    now: datetime | None = None,
    limit: int = 100,
) -> int:
    """Finalize expired tie windows from durable state and publish after commit."""

    effective_now = now or datetime.now(UTC)
    events: list[tuple[str, dict[str, Any]]] = []
    async with session_factory() as session:
        rooms = (
            await session.scalars(
                select(MultiplayerRoom)
                .where(
                    MultiplayerRoom.status == "active",
                    MultiplayerRoom.winner_id.is_not(None),
                    MultiplayerRoom.tie_deadline.is_not(None),
                    MultiplayerRoom.tie_deadline <= effective_now,
                )
                .order_by(MultiplayerRoom.tie_deadline, MultiplayerRoom.id)
                .limit(limit)
                .with_for_update(skip_locked=True)
            )
        ).all()
        for room in rooms:
            room.status = "completed"
            event = await record_room_completion(session, room, "tie_window_elapsed")
            if event is not None:
                events.append((str(room.id), event))
        await session.commit()
    for room_id, event in events:
        with suppress(RedisError, RuntimeError):
            await broker.publish(room_id, event)
    return len(events)


async def cleanup_stale_presence_once(
    session_factory: async_sessionmaker[AsyncSession],
    broker: Broker,
    *,
    now: datetime | None = None,
    stale_after_seconds: int,
    limit: int = 100,
) -> int:
    """Clear durable presence left behind by a crashed process or lost socket."""

    effective_now = now or datetime.now(UTC)
    stale_before = effective_now - timedelta(seconds=stale_after_seconds)
    events: list[tuple[str, dict[str, Any]]] = []
    async with session_factory() as session:
        rows = (
            await session.execute(
                select(MultiplayerMember, MultiplayerRoom)
                .join(MultiplayerRoom, MultiplayerRoom.id == MultiplayerMember.room_id)
                .where(
                    MultiplayerMember.connected.is_(True),
                    MultiplayerMember.last_seen_at <= stale_before,
                    MultiplayerRoom.status.in_(["waiting", "active"]),
                )
                .order_by(MultiplayerMember.last_seen_at, MultiplayerMember.id)
                .limit(limit)
                .with_for_update(skip_locked=True)
            )
        ).all()
        for member, room in rows:
            member.connected = False
            event = await record_room_event(
                session,
                room,
                "presence",
                {"userId": str(member.user_id), "connected": False},
            )
            events.append((str(room.id), event))
        await session.commit()
    for room_id, event in events:
        with suppress(RedisError, RuntimeError):
            await broker.publish(room_id, event)
    return len(events)


async def room_finalization_worker(
    session_factory: async_sessionmaker[AsyncSession],
    broker: Broker,
    *,
    interval_seconds: float = 1.0,
) -> None:
    settings = get_settings()
    while True:
        with suppress(SQLAlchemyError, RedisError, RuntimeError):
            await finalize_due_rooms_once(session_factory, broker)
            await cleanup_stale_presence_once(
                session_factory,
                broker,
                stale_after_seconds=settings.websocket_connection_ttl_seconds,
            )
        await asyncio.sleep(interval_seconds)
