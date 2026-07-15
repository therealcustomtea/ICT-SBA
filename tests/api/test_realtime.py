from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from mastermind_api.config import Settings
from mastermind_api.errors import APIError
from mastermind_api.models import (
    GameSession,
    MultiplayerMember,
    MultiplayerRoom,
    UserAchievement,
)
from mastermind_api.realtime import (
    InMemoryBroker,
    RedisBroker,
    UnavailableBroker,
    cleanup_stale_presence_once,
    finalize_due_rooms_once,
)
from mastermind_api.routers.rooms import (
    WEBSOCKET_SUBPROTOCOL,
    _ensure_realtime_available,
    _ticket_from_protocol_header,
)
from redis.exceptions import ConnectionError
from sqlalchemy import select

from .conftest import APIContext, principal


class RecoveringRedis:
    def __init__(self) -> None:
        self.available = False

    async def ping(self) -> bool:
        if not self.available:
            raise ConnectionError("temporarily unavailable")
        return True


def test_websocket_ticket_uses_subprotocol_and_rejects_query_style_absence() -> None:
    ticket = "safe_ticket-token_1234567890"
    assert _ticket_from_protocol_header(f"{WEBSOCKET_SUBPROTOCOL}, ticket.{ticket}") == ticket
    assert _ticket_from_protocol_header(f"ticket.{ticket}") is None
    assert _ticket_from_protocol_header(WEBSOCKET_SUBPROTOCOL) is None
    assert (
        _ticket_from_protocol_header(f"{WEBSOCKET_SUBPROTOCOL}, ticket.{ticket}, ticket.another")
        is None
    )
    assert _ticket_from_protocol_header(f"{WEBSOCKET_SUBPROTOCOL}, ticket.invalid/token") is None


async def test_realtime_probe_recovers_after_transient_redis_outage() -> None:
    redis = RecoveringRedis()
    state = SimpleNamespace(
        redis=redis,
        redis_ready=True,
        broker=UnavailableBroker(),
    )
    settings = Settings.model_construct(environment="production")

    with pytest.raises(APIError) as failure:
        await _ensure_realtime_available(state, settings)
    assert failure.value.code == "REALTIME_UNAVAILABLE"
    assert state.redis_ready is False

    redis.available = True
    assert await _ensure_realtime_available(state, settings) is redis
    assert state.redis_ready is True
    assert isinstance(state.broker, RedisBroker)


async def test_background_finalization_awards_duelist(api: APIContext) -> None:
    host = api.current["principal"]
    created = (await api.client.post("/v1/rooms", json={"difficulty": "easy"})).json()
    await api.client.post(f"/v1/rooms/{created['id']}/ready")
    guest = principal()
    api.current["principal"] = guest
    await api.client.post(f"/v1/rooms/{created['roomCode']}/join")
    started = await api.client.post(f"/v1/rooms/{created['id']}/ready")
    assert started.status_code == 200, started.text

    room_id = uuid.UUID(created["id"])
    now = datetime.now(UTC)
    async with api.sessions() as session:
        room = await session.get(MultiplayerRoom, room_id)
        winning_game = await session.scalar(
            select(GameSession).where(
                GameSession.room_id == room_id,
                GameSession.owner_id == host.user_id,
            )
        )
        losing_game = await session.scalar(
            select(GameSession).where(
                GameSession.room_id == room_id,
                GameSession.owner_id == guest.user_id,
            )
        )
        assert room is not None and winning_game is not None and losing_game is not None
        assert losing_game.status == "active"
        winning_game.status = "won"
        winning_game.completed_at = now - timedelta(seconds=1)
        room.winner_id = host.user_id
        room.winner_at = winning_game.completed_at
        room.tie_deadline = now - timedelta(milliseconds=1)
        await session.commit()

    broker = InMemoryBroker()
    assert await finalize_due_rooms_once(api.sessions, broker, now=now) == 1
    async with api.sessions() as session:
        duelist = await session.scalar(
            select(UserAchievement).where(
                UserAchievement.user_id == host.user_id,
                UserAchievement.achievement_key == "duelist",
            )
        )
        persisted_loser = await session.get(GameSession, losing_game.id)
    assert duelist is not None
    assert duelist.game_id == winning_game.id
    assert persisted_loser is not None
    assert persisted_loser.status == "lost"
    assert persisted_loser.completed_at is not None
    assert persisted_loser.completed_at.replace(tzinfo=UTC) == room.tie_deadline
    assert persisted_loser.final_score == 0
    assert persisted_loser.score_breakdown == {
        "attempts": 0,
        "difficulty": 0,
        "time": 0,
        "total": 0,
        "version": "score_v1",
    }
    assert persisted_loser.ranked_eligibility == "unranked"
    await broker.close()


async def test_stale_presence_is_cleared_and_published(api: APIContext) -> None:
    created = (await api.client.post("/v1/rooms", json={"difficulty": "easy"})).json()
    room_id = uuid.UUID(created["id"])
    stale_time = datetime.now(UTC) - timedelta(minutes=5)
    async with api.sessions() as session:
        member = await session.scalar(
            select(MultiplayerMember).where(MultiplayerMember.room_id == room_id)
        )
        assert member is not None
        member.connected = True
        member.last_seen_at = stale_time
        await session.commit()

    broker = InMemoryBroker()
    async with broker.subscribe(str(room_id)) as events:
        cleared = await cleanup_stale_presence_once(
            api.sessions,
            broker,
            now=datetime.now(UTC),
            stale_after_seconds=90,
        )
        event = await anext(events)

    assert cleared == 1
    assert event["type"] == "presence"
    assert event["payload"]["connected"] is False
    async with api.sessions() as session:
        member = await session.scalar(
            select(MultiplayerMember).where(MultiplayerMember.room_id == room_id)
        )
        assert member is not None and member.connected is False
    await broker.close()


async def test_in_memory_broker_marks_a_slow_consumer_for_resync() -> None:
    broker = InMemoryBroker()
    async with broker.subscribe("room") as events:
        for sequence in range(1, 102):
            await broker.publish("room", {"version": 1, "sequence": sequence, "type": "event"})
        event = await anext(events)

    assert event["type"] == "resync_required"
    assert event["payload"] == {"reason": "slow_consumer"}
    await broker.close()
