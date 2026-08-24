# Defers type-annotation evaluation to support modern hints safely.
from __future__ import annotations

# Imports `asyncio` so the module can use that dependency.
import asyncio

# Imports `json` so the module can use that dependency.
import json

# Imports selected names from `collections` for use in this module.
from collections import defaultdict

# Imports selected names from `collections.abc` for use in this module.
from collections.abc import AsyncIterator

# Imports selected names from `contextlib` for use in this module.
from contextlib import AbstractAsyncContextManager, asynccontextmanager, suppress

# Imports selected names from `datetime` for use in this module.
from datetime import UTC, datetime, timedelta

# Imports selected names from `typing` for use in this module.
from typing import Any, Protocol

# Imports selected names from `mastermind_core` for use in this module.
from mastermind_core import GameConfig, GameStatus, LeaderboardEligibility, calculate_score

# Imports the required names from `pymongo.errors` for this module.
from pymongo.errors import PyMongoError

# Imports selected names from `redis.asyncio` for use in this module.
from redis.asyncio import Redis

# Imports selected names from `redis.exceptions` for use in this module.
from redis.exceptions import RedisError

# Imports selected names from `.config` for use in this module.
from .config import get_settings

# Imports the required names from `.database` for this module.
from .database import MongoSession, MongoSessionFactory

# Imports selected names from `.features` for use in this module.
from .features import feature_enabled

# Imports selected names from `.models` for use in this module.
from .models import (
    # Supplies this item to the surrounding call or collection.
    GameSession,
    # Supplies this item to the surrounding call or collection.
    MultiplayerEvent,
    # Supplies this item to the surrounding call or collection.
    MultiplayerMember,
    # Supplies this item to the surrounding call or collection.
    MultiplayerRoom,
    # Supplies this item to the surrounding call or collection.
    Profile,
    # Supplies this item to the surrounding call or collection.
    UserAchievement,
    # Closes the multiline call, declaration, or collection started above.
)


# Defines the `Broker` class and its related behavior.
class Broker(Protocol):
    # Declares the typed `available` data field.
    available: bool

    # Defines the `publish` callable and its typed interface.
    async def publish(self, room_id: str, event: dict[str, Any]) -> None: ...

    # Defines the `subscribe` callable and its typed interface.
    def subscribe(
        # Executes this statement as the next step in the surrounding logic.
        self,
        # Supplies this item to the surrounding call or collection.
        room_id: str,
        # Executes this statement as the next step in the surrounding logic.
    ) -> AbstractAsyncContextManager[AsyncIterator[dict[str, Any]]]: ...

    # Defines the `close` callable and its typed interface.
    async def close(self) -> None: ...


# Defines the `InMemoryBroker` class and its related behavior.
class InMemoryBroker:
    # Documents the purpose or contract of this module, class, or function.
    """Development/test broker. Production uses Redis for horizontal fan-out."""

    # Computes and stores `available` for subsequent operations.
    available = True

    # Defines the `__init__` callable and its typed interface.
    def __init__(self) -> None:
        # Computes and stores `self._subscribers` for subsequent operations.
        self._subscribers: dict[str, set[asyncio.Queue[dict[str, Any]]]] = defaultdict(set)

    # Defines the `publish` callable and its typed interface.
    async def publish(self, room_id: str, event: dict[str, Any]) -> None:
        # Iterates through the supplied values for the nested operation.
        for queue in tuple(self._subscribers[room_id]):
            # Starts a protected operation whose expected failures are handled below.
            try:
                # Calls `queue.put_nowait` with the supplied values.
                queue.put_nowait(event)
            # Handles the listed exception so failure remains controlled.
            except asyncio.QueueFull:
                # Repeats the nested block while this condition remains true.
                while not queue.empty():
                    # Calls `queue.get_nowait` with the supplied values.
                    queue.get_nowait()
                # Calls `queue.put_nowait` with the supplied values.
                queue.put_nowait(
                    # Begins the nested block or multiline expression completed below.
                    {
                        # Associates the `version` key with its value.
                        "version": 1,
                        # Associates the `sequence` key with its value.
                        "sequence": event.get("sequence"),
                        # Associates the `type` key with its value.
                        "type": "resync_required",
                        # Associates the `payload` key with its value.
                        "payload": {"reason": "slow_consumer"},
                        # Closes the multiline call, declaration, or collection started above.
                    }
                    # Closes the multiline call, declaration, or collection started above.
                )

    # Applies `@asynccontextmanager` to configure the declaration immediately below.
    @asynccontextmanager
    # Defines the `subscribe` callable and its typed interface.
    async def subscribe(self, room_id: str) -> AsyncIterator[AsyncIterator[dict[str, Any]]]:
        # Computes and stores `queue` for subsequent operations.
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=100)
        # Executes this statement as the next step in the surrounding logic.
        self._subscribers[room_id].add(queue)

        # Defines the `events` callable and its typed interface.
        async def events() -> AsyncIterator[dict[str, Any]]:
            # Repeats the nested block while this condition remains true.
            while True:
                # Yields this value to the generator consumer without ending iteration.
                yield await queue.get()

        # Starts a protected operation whose expected failures are handled below.
        try:
            # Yields this value to the generator consumer without ending iteration.
            yield events()
        # Runs this cleanup block regardless of the protected result.
        finally:
            # Executes this statement as the next step in the surrounding logic.
            self._subscribers[room_id].discard(queue)

    # Defines the `close` callable and its typed interface.
    async def close(self) -> None:
        # Calls `self._subscribers.clear` with the supplied values.
        self._subscribers.clear()


# Defines the `RedisBroker` class and its related behavior.
class RedisBroker:
    # Computes and stores `available` for subsequent operations.
    available = True

    # Defines the `__init__` callable and its typed interface.
    def __init__(self, client: Redis) -> None:
        # Computes and stores `self._client` for subsequent operations.
        self._client = client

    # Defines the `publish` callable and its typed interface.
    async def publish(self, room_id: str, event: dict[str, Any]) -> None:
        # Waits for this asynchronous operation to complete.
        await self._client.publish(f"mastermind:room:{room_id}", json.dumps(event))

    # Applies `@asynccontextmanager` to configure the declaration immediately below.
    @asynccontextmanager
    # Defines the `subscribe` callable and its typed interface.
    async def subscribe(self, room_id: str) -> AsyncIterator[AsyncIterator[dict[str, Any]]]:
        # Computes and stores `pubsub` for subsequent operations.
        pubsub = self._client.pubsub()
        # Waits for this asynchronous operation to complete.
        await pubsub.subscribe(f"mastermind:room:{room_id}")
        # Computes and stores `queue` for subsequent operations.
        queue: asyncio.Queue[dict[str, Any] | Exception] = asyncio.Queue(maxsize=100)

        # Defines the `pump` callable and its typed interface.
        async def pump() -> None:
            # Starts a protected operation whose expected failures are handled below.
            try:
                # Poll below the shared Redis socket timeout so an idle room remains connected.
                while True:
                    # Polls Redis for the next room event without blocking indefinitely.
                    message = await pubsub.get_message(
                        # Skips subscription acknowledgements so callers receive room events.
                        ignore_subscribe_messages=True,
                        # Bounds each poll so cancellation and connection cleanup remain responsive.
                        timeout=1.0,
                        # Closes the bounded Redis polling call opened above.
                    )
                    # Skips empty polls so the subscription can continue waiting for an event.
                    if message is None:
                        # Returns to the polling boundary without attempting to decode absent data.
                        continue
                    # Computes and stores `value` for subsequent operations.
                    value = json.loads(message["data"])
                    # Checks this condition before executing the nested branch.
                    if not isinstance(value, dict):
                        # Skips the remaining work and advances to the next iteration.
                        continue
                    # Starts a protected operation whose expected failures are handled below.
                    try:
                        # Calls `queue.put_nowait` with the supplied values.
                        queue.put_nowait(value)
                    # Handles the listed exception so failure remains controlled.
                    except asyncio.QueueFull:
                        # Repeats the nested block while this condition remains true.
                        while not queue.empty():
                            # Calls `queue.get_nowait` with the supplied values.
                            queue.get_nowait()
                        # Calls `queue.put_nowait` with the supplied values.
                        queue.put_nowait(
                            # Begins the nested block or multiline expression completed below.
                            {
                                # Associates the `version` key with its value.
                                "version": 1,
                                # Associates the `sequence` key with its value.
                                "sequence": value.get("sequence"),
                                # Associates the `type` key with its value.
                                "type": "resync_required",
                                # Associates the `payload` key with its value.
                                "payload": {"reason": "slow_consumer"},
                                # Closes the multiline call, declaration, or collection started
                                # above.
                            }
                            # Closes the multiline call, declaration, or collection started above.
                        )
            # Handles the listed exception so failure remains controlled.
            except (RedisError, RuntimeError, json.JSONDecodeError) as exc:
                # Repeats the nested block while this condition remains true.
                while not queue.empty():
                    # Calls `queue.get_nowait` with the supplied values.
                    queue.get_nowait()
                # Calls `queue.put_nowait` with the supplied values.
                queue.put_nowait(exc)

        # Computes and stores `pump_task` for subsequent operations.
        pump_task = asyncio.create_task(pump())

        # Defines the `events` callable and its typed interface.
        async def events() -> AsyncIterator[dict[str, Any]]:
            # Repeats the nested block while this condition remains true.
            while True:
                # Computes and stores `value` for subsequent operations.
                value = await queue.get()
                # Checks this condition before executing the nested branch.
                if isinstance(value, Exception):
                    # Raises this exception to report an invalid or failed operation.
                    raise value
                # Yields this value to the generator consumer without ending iteration.
                yield value

        # Starts a protected operation whose expected failures are handled below.
        try:
            # Yields this value to the generator consumer without ending iteration.
            yield events()
        # Runs this cleanup block regardless of the protected result.
        finally:
            # Calls `pump_task.cancel` with the supplied values.
            pump_task.cancel()
            # Acquires this managed resource and guarantees cleanup afterward.
            with suppress(asyncio.CancelledError):
                # Waits for this asynchronous operation to complete.
                await pump_task
            # Waits for this asynchronous operation to complete.
            await pubsub.unsubscribe(f"mastermind:room:{room_id}")
            # Waits for this asynchronous operation to complete.
            await pubsub.aclose()  # type: ignore[no-untyped-call]

    # Defines the `close` callable and its typed interface.
    async def close(self) -> None:
        # Waits for this asynchronous operation to complete.
        await self._client.aclose()


# Defines the `UnavailableBroker` class and its related behavior.
class UnavailableBroker:
    # Computes and stores `available` for subsequent operations.
    available = False

    # Defines the `publish` callable and its typed interface.
    async def publish(self, room_id: str, event: dict[str, Any]) -> None:
        # Raises this exception to report an invalid or failed operation.
        raise RuntimeError("Realtime broker is unavailable.")

    # Applies `@asynccontextmanager` to configure the declaration immediately below.
    @asynccontextmanager
    # Defines the `subscribe` callable and its typed interface.
    async def subscribe(self, room_id: str) -> AsyncIterator[AsyncIterator[dict[str, Any]]]:
        # Yields this value to the generator consumer without ending iteration.
        yield _empty_events()

    # Defines the `close` callable and its typed interface.
    async def close(self) -> None:
        # Returns this result to the caller and ends the current function.
        return None


# Defines the `_empty_events` callable and its typed interface.
async def _empty_events() -> AsyncIterator[dict[str, Any]]:
    # Checks this condition before executing the nested branch.
    if False:
        # Yields this value to the generator consumer without ending iteration.
        yield {}


# Defines the `_event_envelope` callable and its typed interface.
def _event_envelope(
    # Declares the typed `event_type` data field.
    event_type: str,
    # Declares the typed `payload` data field.
    payload: dict[str, Any],
    # Declares the typed `sequence` data field.
    sequence: int,
    # Completes the signature and declares the callable return type.
) -> dict[str, Any]:
    # Returns this result to the caller and ends the current function.
    return {"version": 1, "sequence": sequence, "type": event_type, "payload": payload}


# Defines the `record_room_event` callable and its typed interface.
async def record_room_event(
    # Declares the typed `session` data field.
    session: MongoSession,
    # Declares the typed `room` data field.
    room: MultiplayerRoom,
    # Declares the typed `event_type` data field.
    event_type: str,
    # Declares the typed `payload` data field.
    payload: dict[str, Any],
    # Completes the signature and declares the callable return type.
) -> dict[str, Any]:
    # Documents the purpose or contract of this module, class, or function.
    """Append a safe room event while the caller holds the room transaction."""

    # Executes this statement as the next step in the surrounding logic.
    room.event_sequence += 1
    # Computes and stores `event` for subsequent operations.
    event = MultiplayerEvent(
        # Provides the `room_id` parameter or keyword argument.
        room_id=room.id,
        # Provides the `sequence` parameter or keyword argument.
        sequence=room.event_sequence,
        # Provides the `event_type` parameter or keyword argument.
        event_type=event_type,
        # Provides the `payload` parameter or keyword argument.
        payload=payload,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Calls `session.add` with the supplied values.
    session.add(event)
    # Returns this result to the caller and ends the current function.
    return _event_envelope(event_type, payload, event.sequence)


# Defines the `award_duelist_if_eligible` callable and its typed interface.
async def award_duelist_if_eligible(
    # Declares the typed `session` data field.
    session: MongoSession,
    # Declares the typed `room` data field.
    room: MultiplayerRoom,
    # Completes the signature and declares the callable return type.
) -> None:
    # Documents the purpose or contract of this module, class, or function.
    """Persist Duelist even when a background worker finalizes the room."""

    # Checks this condition before executing the nested branch.
    if room.winner_id is None or room.is_tie:
        # Returns this result to the caller and ends the current function.
        return
    # Computes and stores `profile` for subsequent operations.
    profile = await session.get(Profile, room.winner_id)
    # Checks this condition before executing the nested branch.
    if (
        # Executes this statement as the next step in the surrounding logic.
        profile is None
        # Executes this statement as the next step in the surrounding logic.
        or profile.is_anonymous
        # Executes this statement as the next step in the surrounding logic.
        or not await feature_enabled(session, get_settings(), "achievements")
        # Begins the nested block or multiline expression completed below.
    ):
        # Returns this result to the caller and ends the current function.
        return
    # Computes and stores `game_id` for subsequent operations.
    game = await session.find_one(
        # Supplies this required nested value.
        GameSession,
        # Supplies this required nested value.
        {'room_id': room.id, 'owner_id': room.winner_id, 'status': 'won'},
    # Closes the multiline declaration, call, or collection opened above.
    )
    # Guards the nested operation so it runs only when this condition is satisfied.
    if game is None:
        # Returns this result to the caller and ends the current function.
        return
    # Stores `existing` because later steps depend on this value.
    existing = await session.find_one(
        # Supplies this required nested value.
        UserAchievement,
        # Supplies this required nested value.
        {'user_id': room.winner_id, 'achievement_key': 'duelist'},
    # Closes the multiline declaration, call, or collection opened above.
    )
    # Guards the nested operation so it runs only when this condition is satisfied.
    if existing is None:
        # Supplies this required nested value.
        session.add(
            # Supplies this required nested value.
            UserAchievement(
                # Stores `user_id` because later steps depend on this value.
                user_id=room.winner_id,
                # Stores `achievement_key` because later steps depend on this value.
                achievement_key='duelist',
                # Stores `game_id` because later steps depend on this value.
                game_id=game.id,
            # Closes the multiline declaration, call, or collection opened above.
            )
        # Closes the multiline declaration, call, or collection opened above.
        )


# Defines the `_aware_utc` callable and its typed interface.
def _aware_utc(value: datetime) -> datetime:
    # Returns this result to the caller and ends the current function.
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


# Defines the `finalize_active_room_games` callable and its typed interface.
async def finalize_active_room_games(
    # Declares the typed `session` data field.
    session: MongoSession,
    # Declares the typed `room` data field.
    room: MultiplayerRoom,
    # Completes the signature and declares the callable return type.
) -> None:
    # Documents the purpose or contract of this module, class, or function.
    """Close every remaining game when the authoritative room becomes terminal."""

    # Computes and stores `active_games` for subsequent operations.
    active_games = await session.find_many(
        # Supplies this required nested value.
        GameSession,
        # Supplies this required nested value.
        {'room_id': room.id, 'status': GameStatus.ACTIVE.value},
        # Stores `sort` because later steps depend on this value.
        sort=[('_id', 1)],
    # Closes the multiline declaration, call, or collection opened above.
    )
    # Checks this condition before executing the nested branch.
    if not active_games:
        # Returns this result to the caller and ends the current function.
        return
    # Computes and stores `now` for subsequent operations.
    now = datetime.now(UTC)
    # Computes and stores `candidate` for subsequent operations.
    candidate = room.tie_deadline or room.winner_at or now
    # Computes and stores `completed_at` for subsequent operations.
    completed_at = min(_aware_utc(candidate), now)
    # Iterates through the supplied values for the nested operation.
    for game in active_games:
        # Computes and stores `status` for subsequent operations.
        status = (
            # Executes this statement as the next step in the surrounding logic.
            GameStatus.LOST
            # Checks this condition before executing the nested branch.
            if room.status == "completed"
            # Executes this statement as the next step in the surrounding logic.
            and room.winner_id is not None
            # Executes this statement as the next step in the surrounding logic.
            and game.owner_id != room.winner_id
            # Executes this statement as the next step in the surrounding logic.
            else GameStatus.ABANDONED
            # Closes the multiline call, declaration, or collection started above.
        )
        # Computes and stores `game.status` for subsequent operations.
        game.status = status.value
        # Computes and stores `game.completed_at` for subsequent operations.
        game.completed_at = completed_at
        # Computes and stores `game.elapsed_seconds` for subsequent operations.
        game.elapsed_seconds = max(
            # Supplies this item to the surrounding call or collection.
            0,
            # Calls `int` with the supplied values.
            int((completed_at - _aware_utc(game.started_at)).total_seconds()),
            # Closes the multiline call, declaration, or collection started above.
        )
        # Computes and stores `game.final_score` for subsequent operations.
        game.final_score = 0
        # Computes and stores `game.score_breakdown` for subsequent operations.
        game.score_breakdown = calculate_score(
            # Calls `GameConfig.from_dict` with the supplied values.
            GameConfig.from_dict(game.config),
            # Provides the `status` parameter or keyword argument.
            status=status,
            # Provides the `attempts_used` parameter or keyword argument.
            attempts_used=game.attempts_used,
            # Provides the `elapsed_seconds` parameter or keyword argument.
            elapsed_seconds=game.elapsed_seconds,
            # Executes this statement as the next step in the surrounding logic.
        ).to_dict()
        # Computes and stores `game.ranked_eligibility` for subsequent operations.
        game.ranked_eligibility = LeaderboardEligibility.UNRANKED.value


# Defines the `record_room_completion` callable and its typed interface.
async def record_room_completion(
    # Declares the typed `session` data field.
    session: MongoSession,
    # Declares the typed `room` data field.
    room: MultiplayerRoom,
    # Declares the typed `reason` data field.
    reason: str,
    # Completes the signature and declares the callable return type.
) -> dict[str, Any] | None:
    # Waits for this asynchronous operation to complete.
    await finalize_active_room_games(session, room)
    # Waits for this asynchronous operation to complete.
    await award_duelist_if_eligible(session, room)
    # Computes and stores `existing` for subsequent operations.
    existing = await session.find_one(
        # Supplies this required nested value.
        MultiplayerEvent, {'room_id': room.id, 'event_type': 'room_completed'}
    # Closes the multiline declaration, call, or collection opened above.
    )
    # Checks this condition before executing the nested branch.
    if existing is not None:
        # Returns this result to the caller and ends the current function.
        return None
    # Returns this result to the caller and ends the current function.
    return await record_room_event(
        # Supplies this item to the surrounding call or collection.
        session,
        # Supplies this item to the surrounding call or collection.
        room,
        # Supplies this item to the surrounding call or collection.
        "room_completed",
        # Begins the nested block or multiline expression completed below.
        {
            # Associates the `winnerId` key with its value.
            "winnerId": str(room.winner_id) if room.winner_id else None,
            # Associates the `isTie` key with its value.
            "isTie": room.is_tie,
            # Associates the `reason` key with its value.
            "reason": reason,
            # Closes the multiline call, declaration, or collection started above.
        },
        # Closes the multiline call, declaration, or collection started above.
    )


# Defines the `finalize_due_rooms_once` callable and its typed interface.
async def finalize_due_rooms_once(
    # Declares the typed `session_factory` data field.
    session_factory: MongoSessionFactory,
    # Declares the typed `broker` data field.
    broker: Broker,
    # Makes the following parameters keyword-only for clear call sites.
    *,
    # Provides the `now` parameter or keyword argument.
    now: datetime | None = None,
    # Provides the `limit` parameter or keyword argument.
    limit: int = 100,
    # Completes the signature and declares the callable return type.
) -> int:
    # Documents the purpose or contract of this module, class, or function.
    """Finalize expired tie windows from durable state and publish after commit."""

    # Computes and stores `effective_now` for subsequent operations.
    effective_now = now or datetime.now(UTC)
    # Computes and stores `events` for subsequent operations.
    events: list[tuple[str, dict[str, Any]]] = []
    # Acquires this asynchronous managed resource for the nested operation.
    async with session_factory() as session:
        # Computes and stores `rooms` for subsequent operations.
        rooms = await session.find_many(
            # Supplies this required nested value.
            MultiplayerRoom,
            # Supplies this required nested value.
            {
                # Supplies this literal value to the surrounding declaration or call.
                'status': 'active',
                # Supplies this literal value to the surrounding declaration or call.
                'winner_id': {'$ne': None},
                # Supplies this literal value to the surrounding declaration or call.
                'tie_deadline': {'$ne': None, '$lte': effective_now},
            # Closes the multiline declaration, call, or collection opened above.
            },
            # Stores `sort` because later steps depend on this value.
            sort=[('tie_deadline', 1), ('_id', 1)],
            # Stores `limit` because later steps depend on this value.
            limit=limit,
        # Closes the multiline declaration, call, or collection opened above.
        )
        # Iterates through the supplied values for the nested operation.
        for room in rooms:
            # Computes and stores `room.status` for subsequent operations.
            room.status = "completed"
            # Computes and stores `event` for subsequent operations.
            event = await record_room_completion(session, room, "tie_window_elapsed")
            # Checks this condition before executing the nested branch.
            if event is not None:
                # Calls `events.append` with the supplied values.
                events.append((str(room.id), event))
        # Waits for this asynchronous operation to complete.
        await session.commit()
    # Iterates through the supplied values for the nested operation.
    for room_id, event in events:
        # Acquires this managed resource and guarantees cleanup afterward.
        with suppress(RedisError, RuntimeError):
            # Waits for this asynchronous operation to complete.
            await broker.publish(room_id, event)
    # Returns this result to the caller and ends the current function.
    return len(events)


# Defines the `cleanup_stale_presence_once` callable and its typed interface.
async def cleanup_stale_presence_once(
    # Declares the typed `session_factory` data field.
    session_factory: MongoSessionFactory,
    # Declares the typed `broker` data field.
    broker: Broker,
    # Makes the following parameters keyword-only for clear call sites.
    *,
    # Provides the `now` parameter or keyword argument.
    now: datetime | None = None,
    # Declares the typed `stale_after_seconds` data field.
    stale_after_seconds: int,
    # Provides the `limit` parameter or keyword argument.
    limit: int = 100,
    # Completes the signature and declares the callable return type.
) -> int:
    # Documents the purpose or contract of this module, class, or function.
    """Clear durable presence left behind by a crashed process or lost socket."""

    # Computes and stores `effective_now` for subsequent operations.
    effective_now = now or datetime.now(UTC)
    # Computes and stores `stale_before` for subsequent operations.
    stale_before = effective_now - timedelta(seconds=stale_after_seconds)
    # Computes and stores `events` for subsequent operations.
    events: list[tuple[str, dict[str, Any]]] = []
    # Acquires this asynchronous managed resource for the nested operation.
    async with session_factory() as session:
        # Computes and stores `rows` for subsequent operations.
        members = await session.find_many(
            # Supplies this required nested value.
            MultiplayerMember,
            # Supplies this required nested value.
            {'connected': True, 'last_seen_at': {'$lte': stale_before}},
            # Stores `sort` because later steps depend on this value.
            sort=[('last_seen_at', 1), ('_id', 1)],
            # Stores `limit` because later steps depend on this value.
            limit=limit,
        # Closes the multiline declaration, call, or collection opened above.
        )
        # Stores `rows` because later steps depend on this value.
        rows = []
        # Iterates over these values so each item receives the same processing.
        for member in members:
            # Stores `room` because later steps depend on this value.
            room = await session.get(MultiplayerRoom, member.room_id)
            # Guards the nested operation so it runs only when this condition is satisfied.
            if room is not None and room.status in {'waiting', 'active'}:
                # Supplies this required nested value.
                rows.append((member, room))
        # Iterates through the supplied values for the nested operation.
        for member, room in rows:
            # Computes and stores `member.connected` for subsequent operations.
            member.connected = False
            # Computes and stores `event` for subsequent operations.
            event = await record_room_event(
                # Supplies this item to the surrounding call or collection.
                session,
                # Supplies this item to the surrounding call or collection.
                room,
                # Supplies this item to the surrounding call or collection.
                "presence",
                # Supplies this item to the surrounding call or collection.
                {"userId": str(member.user_id), "connected": False},
                # Closes the multiline call, declaration, or collection started above.
            )
            # Calls `events.append` with the supplied values.
            events.append((str(room.id), event))
        # Waits for this asynchronous operation to complete.
        await session.commit()
    # Iterates through the supplied values for the nested operation.
    for room_id, event in events:
        # Acquires this managed resource and guarantees cleanup afterward.
        with suppress(RedisError, RuntimeError):
            # Waits for this asynchronous operation to complete.
            await broker.publish(room_id, event)
    # Returns this result to the caller and ends the current function.
    return len(events)


# Defines the `room_finalization_worker` callable and its typed interface.
async def room_finalization_worker(
    # Declares the typed `session_factory` data field.
    session_factory: MongoSessionFactory,
    # Declares the typed `broker` data field.
    broker: Broker,
    # Makes the following parameters keyword-only for clear call sites.
    *,
    # Provides the `interval_seconds` parameter or keyword argument.
    interval_seconds: float = 1.0,
    # Completes the signature and declares the callable return type.
) -> None:
    # Computes and stores `settings` for subsequent operations.
    settings = get_settings()
    # Repeats the nested block while this condition remains true.
    while True:
        # Acquires this managed resource and guarantees cleanup afterward.
        with suppress(PyMongoError, RedisError, RuntimeError):
            # Waits for this asynchronous operation to complete.
            await finalize_due_rooms_once(session_factory, broker)
            # Waits for this asynchronous operation to complete.
            await cleanup_stale_presence_once(
                # Supplies this item to the surrounding call or collection.
                session_factory,
                # Supplies this item to the surrounding call or collection.
                broker,
                # Provides the `stale_after_seconds` parameter or keyword argument.
                stale_after_seconds=settings.websocket_connection_ttl_seconds,
                # Closes the multiline call, declaration, or collection started above.
            )
        # Waits for this asynchronous operation to complete.
        await asyncio.sleep(interval_seconds)
