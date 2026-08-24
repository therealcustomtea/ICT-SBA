# Defers type-annotation evaluation to support modern hints safely.
from __future__ import annotations

# Imports `asyncio` so broker polling can be exercised without real time delays.
import asyncio

# Imports `uuid` so the module can use that dependency.
import uuid

# Imports selected names from `datetime` for use in this module.
from datetime import UTC, datetime, timedelta

# Imports selected names from `types` for use in this module.
from types import SimpleNamespace

# Imports `pytest` so the module can use that dependency.
import pytest

# Imports selected names from `mastermind_api.config` for use in this module.
from mastermind_api.config import Settings

# Imports selected names from `mastermind_api.errors` for use in this module.
from mastermind_api.errors import APIError

# Imports selected names from `mastermind_api.models` for use in this module.
from mastermind_api.models import (
    # Supplies this item to the surrounding call or collection.
    GameSession,
    # Supplies this item to the surrounding call or collection.
    MultiplayerMember,
    # Supplies this item to the surrounding call or collection.
    MultiplayerRoom,
    # Supplies this item to the surrounding call or collection.
    UserAchievement,
    # Closes the multiline call, declaration, or collection started above.
)

# Imports selected names from `mastermind_api.realtime` for use in this module.
from mastermind_api.realtime import (
    # Supplies this item to the surrounding call or collection.
    InMemoryBroker,
    # Supplies this item to the surrounding call or collection.
    RedisBroker,
    # Supplies this item to the surrounding call or collection.
    UnavailableBroker,
    # Supplies this item to the surrounding call or collection.
    cleanup_stale_presence_once,
    # Supplies this item to the surrounding call or collection.
    finalize_due_rooms_once,
    # Closes the multiline call, declaration, or collection started above.
)

# Imports selected names from `mastermind_api.routers.rooms` for use in this module.
from mastermind_api.routers.rooms import (
    # Supplies this item to the surrounding call or collection.
    WEBSOCKET_SUBPROTOCOL,
    # Supplies this item to the surrounding call or collection.
    _ensure_realtime_available,
    # Supplies this item to the surrounding call or collection.
    _refresh_connection,
    # Supplies this item to the surrounding call or collection.
    _release_connection,
    # Supplies this item to the surrounding call or collection.
    _ticket_from_protocol_header,
    # Closes the multiline call, declaration, or collection started above.
)

# Imports selected names from `redis.exceptions` for use in this module.
from redis.exceptions import ConnectionError

# Imports selected names from `.conftest` for use in this module.
from .conftest import APIContext, principal


# Defines the `RecoveringRedis` class and its related behavior.
class RecoveringRedis:
    # Defines the `__init__` callable and its typed interface.
    def __init__(self) -> None:
        # Computes and stores `self.available` for subsequent operations.
        self.available = False

    # Defines the `ping` callable and its typed interface.
    async def ping(self) -> bool:
        # Checks this condition before executing the nested branch.
        if not self.available:
            # Raises this exception to report an invalid or failed operation.
            raise ConnectionError("temporarily unavailable")
        # Returns this result to the caller and ends the current function.
        return True


# Verifies that abandoned connection tokens cannot keep presence stuck online or offline.
async def test_connection_bookkeeping_removes_abandoned_socket_tokens(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class SortedSetRedis:
        def __init__(self) -> None:
            self.sets: dict[str, dict[str, int]] = {
                "user": {"abandoned": 900, "current": 995},
                "ip": {"abandoned": 900, "current": 995},
            }

        def pipeline(self, *, transaction: bool) -> SortedSetRedis:
            assert transaction is True
            return self

        def zremrangebyscore(self, key: str, _minimum: str, maximum: int) -> SortedSetRedis:
            self.sets[key] = {
                token: score for token, score in self.sets[key].items() if score > maximum
            }
            return self

        def zadd(self, key: str, values: dict[str, int], *, xx: bool) -> SortedSetRedis:
            for token, score in values.items():
                if not xx or token in self.sets[key]:
                    self.sets[key][token] = score
            return self

        def expire(self, _key: str, _seconds: int) -> SortedSetRedis:
            return self

        async def execute(self) -> list[object]:
            return []

        async def eval(
            self, script: str, key_count: int, user_key: str, ip_key: str, token: str, cutoff: int
        ) -> int:
            assert key_count == 2
            assert "ZREMRANGEBYSCORE" in script
            for key in (user_key, ip_key):
                self.zremrangebyscore(key, "-inf", cutoff)
                self.sets[key].pop(token, None)
            return len(self.sets[user_key])

    monkeypatch.setattr("mastermind_api.routers.rooms.time.time", lambda: 1000)
    redis = SortedSetRedis()
    settings = Settings.model_construct(websocket_connection_ttl_seconds=90)

    await _refresh_connection(redis, "user", "ip", "current", settings)

    assert redis.sets == {"user": {"current": 1000}, "ip": {"current": 1000}}

    redis.sets["user"]["abandoned"] = 900
    redis.sets["ip"]["abandoned"] = 900
    remaining = await _release_connection(redis, "user", "ip", "current", settings)

    assert remaining == 0
    assert redis.sets == {"user": {}, "ip": {}}


# Defines the `test_websocket_ticket_uses_subprotocol_and_rejects_query_style_absence` callable and
# its typed interface.
def test_websocket_ticket_uses_subprotocol_and_rejects_query_style_absence() -> None:
    # Computes and stores `ticket` for subsequent operations.
    ticket = "safe_ticket-token_1234567890"
    # Asserts this invariant so an unexpected test state fails immediately.
    assert _ticket_from_protocol_header(f"{WEBSOCKET_SUBPROTOCOL}, ticket.{ticket}") == ticket
    # Asserts this invariant so an unexpected test state fails immediately.
    assert _ticket_from_protocol_header(f"ticket.{ticket}") is None
    # Asserts this invariant so an unexpected test state fails immediately.
    assert _ticket_from_protocol_header(WEBSOCKET_SUBPROTOCOL) is None
    # Asserts this invariant so an unexpected test state fails immediately.
    assert (
        # Calls `_ticket_from_protocol_header` with the supplied values.
        _ticket_from_protocol_header(f"{WEBSOCKET_SUBPROTOCOL}, ticket.{ticket}, ticket.another")
        # Executes this statement as the next step in the surrounding logic.
        is None
        # Closes the multiline call, declaration, or collection started above.
    )
    # Asserts this invariant so an unexpected test state fails immediately.
    assert _ticket_from_protocol_header(f"{WEBSOCKET_SUBPROTOCOL}, ticket.invalid/token") is None


# Defines the `test_realtime_probe_recovers_after_transient_redis_outage` callable and its typed
# interface.
async def test_realtime_probe_recovers_after_transient_redis_outage() -> None:
    # Computes and stores `redis` for subsequent operations.
    redis = RecoveringRedis()
    # Computes and stores `state` for subsequent operations.
    state = SimpleNamespace(
        # Provides the `redis` parameter or keyword argument.
        redis=redis,
        # Provides the `redis_ready` parameter or keyword argument.
        redis_ready=True,
        # Provides the `broker` parameter or keyword argument.
        broker=UnavailableBroker(),
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `settings` for subsequent operations.
    settings = Settings.model_construct(environment="production")

    # Acquires this managed resource and guarantees cleanup afterward.
    with pytest.raises(APIError) as failure:
        # Waits for this asynchronous operation to complete.
        await _ensure_realtime_available(state, settings)
    # Asserts this invariant so an unexpected test state fails immediately.
    assert failure.value.code == "REALTIME_UNAVAILABLE"
    # Asserts this invariant so an unexpected test state fails immediately.
    assert state.redis_ready is False

    # Computes and stores `redis.available` for subsequent operations.
    redis.available = True
    # Asserts this invariant so an unexpected test state fails immediately.
    assert await _ensure_realtime_available(state, settings) is redis
    # Asserts this invariant so an unexpected test state fails immediately.
    assert state.redis_ready is True
    # Asserts this invariant so an unexpected test state fails immediately.
    assert isinstance(state.broker, RedisBroker)


# Defines the `test_background_finalization_awards_duelist` callable and its typed interface.
async def test_background_finalization_awards_duelist(api: APIContext) -> None:
    # Computes and stores `host` for subsequent operations.
    host = api.current["principal"]
    # Computes and stores `created` for subsequent operations.
    created = (await api.client.post("/v1/rooms", json={"difficulty": "easy"})).json()
    # Waits for this asynchronous operation to complete.
    await api.client.post(f"/v1/rooms/{created['id']}/ready")
    # Computes and stores `guest` for subsequent operations.
    guest = principal()
    # Executes this statement as the next step in the surrounding logic.
    api.current["principal"] = guest
    # Waits for this asynchronous operation to complete.
    await api.client.post(f"/v1/rooms/{created['roomCode']}/join")
    # Computes and stores `started` for subsequent operations.
    started = await api.client.post(f"/v1/rooms/{created['id']}/ready")
    # Asserts this invariant so an unexpected test state fails immediately.
    assert started.status_code == 200, started.text

    # Computes and stores `room_id` for subsequent operations.
    room_id = uuid.UUID(created["id"])
    # Computes and stores `now` for subsequent operations.
    now = datetime.now(UTC)
    # Acquires this asynchronous managed resource for the nested operation.
    async with api.sessions() as session:
        # Computes and stores `room` for subsequent operations.
        room = await session.get(MultiplayerRoom, room_id)
        # Computes and stores `winning_game` for subsequent operations.
        winning_game = await session.find_one(
            # Supplies this required nested value.
            GameSession,
            {"room_id": room_id, "owner_id": host.user_id},
            # Closes the multiline declaration, call, or collection opened above.
        )
        # Computes and stores `losing_game` for subsequent operations.
        losing_game = await session.find_one(
            # Supplies this required nested value.
            GameSession,
            {"room_id": room_id, "owner_id": guest.user_id},
            # Closes the multiline declaration, call, or collection opened above.
        )
        # Asserts this invariant so an unexpected test state fails immediately.
        assert room is not None and winning_game is not None and losing_game is not None
        # Asserts this invariant so an unexpected test state fails immediately.
        assert losing_game.status == "active"
        # Computes and stores `winning_game.status` for subsequent operations.
        winning_game.status = "won"
        # Computes and stores `winning_game.completed_at` for subsequent operations.
        winning_game.completed_at = now - timedelta(seconds=1)
        # Computes and stores `room.winner_id` for subsequent operations.
        room.winner_id = host.user_id
        # Computes and stores `room.winner_at` for subsequent operations.
        room.winner_at = winning_game.completed_at
        # Computes and stores `room.tie_deadline` for subsequent operations.
        room.tie_deadline = now - timedelta(milliseconds=1)
        # Waits for this asynchronous operation to complete.
        await session.commit()

    # Computes and stores `broker` for subsequent operations.
    broker = InMemoryBroker()
    # Asserts this invariant so an unexpected test state fails immediately.
    assert await finalize_due_rooms_once(api.sessions, broker, now=now) == 1
    # Acquires this asynchronous managed resource for the nested operation.
    async with api.sessions() as session:
        # Computes and stores `duelist` for subsequent operations.
        duelist = await session.find_one(
            # Supplies this required nested value.
            UserAchievement,
            # Supplies this required nested value.
            {"user_id": host.user_id, "achievement_key": "duelist"},
            # Closes the multiline declaration, call, or collection opened above.
        )
        # Computes and stores `persisted_loser` for subsequent operations.
        persisted_loser = await session.get(GameSession, losing_game.id)
    # Asserts this invariant so an unexpected test state fails immediately.
    assert duelist is not None
    # Asserts this invariant so an unexpected test state fails immediately.
    assert duelist.game_id == winning_game.id
    # Asserts this invariant so an unexpected test state fails immediately.
    assert persisted_loser is not None
    # Asserts this invariant so an unexpected test state fails immediately.
    assert persisted_loser.status == "lost"
    # Asserts this invariant so an unexpected test state fails immediately.
    assert persisted_loser.completed_at is not None
    # Asserts this invariant so an unexpected test state fails immediately.
    assert persisted_loser.completed_at.replace(tzinfo=UTC) == room.tie_deadline
    # Asserts this invariant so an unexpected test state fails immediately.
    assert persisted_loser.final_score == 0
    # Asserts this invariant so an unexpected test state fails immediately.
    assert persisted_loser.score_breakdown == {
        # Associates the `attempts` key with its value.
        "attempts": 0,
        # Associates the `difficulty` key with its value.
        "difficulty": 0,
        # Associates the `time` key with its value.
        "time": 0,
        # Associates the `total` key with its value.
        "total": 0,
        # Associates the `version` key with its value.
        "version": "score_v1",
        # Closes the multiline call, declaration, or collection started above.
    }
    # Asserts this invariant so an unexpected test state fails immediately.
    assert persisted_loser.ranked_eligibility == "unranked"
    # Waits for this asynchronous operation to complete.
    await broker.close()


# Defines the `test_stale_presence_is_cleared_and_published` callable and its typed interface.
async def test_stale_presence_is_cleared_and_published(api: APIContext) -> None:
    # Computes and stores `created` for subsequent operations.
    created = (await api.client.post("/v1/rooms", json={"difficulty": "easy"})).json()
    # Computes and stores `room_id` for subsequent operations.
    room_id = uuid.UUID(created["id"])
    # Computes and stores `stale_time` for subsequent operations.
    stale_time = datetime.now(UTC) - timedelta(minutes=5)
    # Acquires this asynchronous managed resource for the nested operation.
    async with api.sessions() as session:
        # Computes and stores `member` for subsequent operations.
        member = await session.find_one(MultiplayerMember, {"room_id": room_id})
        # Asserts this invariant so an unexpected test state fails immediately.
        assert member is not None
        # Computes and stores `member.connected` for subsequent operations.
        member.connected = True
        # Computes and stores `member.last_seen_at` for subsequent operations.
        member.last_seen_at = stale_time
        # Waits for this asynchronous operation to complete.
        await session.commit()

    # Computes and stores `broker` for subsequent operations.
    broker = InMemoryBroker()
    # Acquires this asynchronous managed resource for the nested operation.
    async with broker.subscribe(str(room_id)) as events:
        # Computes and stores `cleared` for subsequent operations.
        cleared = await cleanup_stale_presence_once(
            # Supplies this item to the surrounding call or collection.
            api.sessions,
            # Supplies this item to the surrounding call or collection.
            broker,
            # Provides the `now` parameter or keyword argument.
            now=datetime.now(UTC),
            # Provides the `stale_after_seconds` parameter or keyword argument.
            stale_after_seconds=90,
            # Closes the multiline call, declaration, or collection started above.
        )
        # Computes and stores `event` for subsequent operations.
        event = await anext(events)

    # Asserts this invariant so an unexpected test state fails immediately.
    assert cleared == 1
    # Asserts this invariant so an unexpected test state fails immediately.
    assert event["type"] == "presence"
    # Asserts this invariant so an unexpected test state fails immediately.
    assert event["payload"]["connected"] is False
    # Acquires this asynchronous managed resource for the nested operation.
    async with api.sessions() as session:
        # Computes and stores `member` for subsequent operations.
        member = await session.find_one(MultiplayerMember, {"room_id": room_id})
        # Asserts this invariant so an unexpected test state fails immediately.
        assert member is not None and member.connected is False
    # Waits for this asynchronous operation to complete.
    await broker.close()


# Defines the `test_in_memory_broker_marks_a_slow_consumer_for_resync` callable and its typed
# interface.
async def test_in_memory_broker_marks_a_slow_consumer_for_resync() -> None:
    # Computes and stores `broker` for subsequent operations.
    broker = InMemoryBroker()
    # Acquires this asynchronous managed resource for the nested operation.
    async with broker.subscribe("room") as events:
        # Iterates through the supplied values for the nested operation.
        for sequence in range(1, 102):
            # Waits for this asynchronous operation to complete.
            await broker.publish("room", {"version": 1, "sequence": sequence, "type": "event"})
        # Computes and stores `event` for subsequent operations.
        event = await anext(events)

    # Asserts this invariant so an unexpected test state fails immediately.
    assert event["type"] == "resync_required"
    # Asserts this invariant so an unexpected test state fails immediately.
    assert event["payload"] == {"reason": "slow_consumer"}
    # Waits for this asynchronous operation to complete.
    await broker.close()


# Defines the regression coverage for idle Redis subscriptions.
async def test_redis_broker_keeps_polling_after_an_idle_read() -> None:
    # Implements the subset of Redis Pub/Sub used by `RedisBroker`.
    class IdlePubSub:
        def __init__(self) -> None:
            self.polls = 0
            self.poll_arguments: list[tuple[bool, float]] = []

        async def subscribe(self, _channel: str) -> None:
            return None

        async def get_message(self, **options: bool | float) -> dict[str, str] | None:
            ignore_subscribe_messages = bool(options["ignore_subscribe_messages"])
            timeout = float(options["timeout"])
            self.polls += 1
            self.poll_arguments.append((ignore_subscribe_messages, timeout))
            await asyncio.sleep(0)
            if self.polls == 2:
                return {"data": '{"version":1,"sequence":1,"type":"presence","payload":{}}'}
            return None

        async def unsubscribe(self, _channel: str) -> None:
            return None

        async def aclose(self) -> None:
            return None

    # Implements the subset of the Redis client used by `RedisBroker`.
    class IdleRedis:
        def __init__(self) -> None:
            self.pubsub_client = IdlePubSub()

        def pubsub(self) -> IdlePubSub:
            return self.pubsub_client

        async def aclose(self) -> None:
            return None

    redis = IdleRedis()
    broker = RedisBroker(redis)  # type: ignore[arg-type]

    async with broker.subscribe("room") as events:
        event = await asyncio.wait_for(anext(events), timeout=1)

    assert event["type"] == "presence"
    assert redis.pubsub_client.polls >= 2
    assert redis.pubsub_client.poll_arguments[:2] == [(True, 1.0), (True, 1.0)]
    await broker.close()
