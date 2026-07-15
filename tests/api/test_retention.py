from __future__ import annotations

import asyncio
import os
import subprocess
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from mastermind_api.models import (
    FriendChallenge,
    GameAttempt,
    GameSession,
    MultiplayerEvent,
    MultiplayerMember,
    MultiplayerRoom,
    ProductEvent,
    Profile,
)
from mastermind_api.retention import game_expiry_for_mode, run_retention_batch
from mastermind_core import RULE_SET_VERSION, SCORING_VERSION, GameMode, get_preset
from sqlalchemy import delete, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .conftest import APIContext


@pytest.mark.parametrize(
    ("mode", "expected_lifetime"),
    [
        (GameMode.SOLO, timedelta(days=7)),
        (GameMode.DAILY, timedelta(days=1)),
        (GameMode.PRACTICE, timedelta(days=1)),
        (GameMode.PASS_AND_PLAY, timedelta(days=1)),
        (GameMode.FRIEND_CHALLENGE, timedelta(days=30)),
        (GameMode.DUEL, timedelta(hours=2)),
    ],
)
def test_game_expiry_is_mode_specific_and_fixed(
    mode: GameMode,
    expected_lifetime: timedelta,
) -> None:
    started_at = datetime(2026, 7, 16, 8, tzinfo=UTC)
    assert game_expiry_for_mode(mode, started_at) == started_at + expected_lifetime


def test_linked_game_expiry_never_outlives_its_parent() -> None:
    started_at = datetime(2026, 7, 16, 8, tzinfo=UTC)
    linked_expiry = started_at + timedelta(minutes=30)
    assert (
        game_expiry_for_mode(
            GameMode.DUEL,
            started_at,
            linked_expires_at=linked_expiry,
        )
        == linked_expiry
    )
    with pytest.raises(ValueError, match="must remain active"):
        game_expiry_for_mode(
            GameMode.FRIEND_CHALLENGE,
            started_at,
            linked_expires_at=started_at,
        )


async def test_attempt_after_deadline_durably_expires_game(api: APIContext) -> None:
    created = await api.client.post(
        "/v1/games",
        json={"mode": "solo", "difficulty": "easy"},
    )
    assert created.status_code == 201, created.text
    game_id = created.json()["id"]
    deadline = datetime.now(UTC)
    async with api.sessions() as session:
        game = await session.scalar(select(GameSession).where(GameSession.public_id == game_id))
        assert game is not None
        game.expires_at = deadline
        await session.commit()

    response = await api.client.post(
        f"/v1/games/{game_id}/attempts",
        json={"guess": list("RBGY"), "idempotencyKey": "expired-attempt-0001"},
    )
    assert response.status_code == 410
    assert response.json()["code"] == "GAME_EXPIRED"
    async with api.sessions() as session:
        game = await session.scalar(select(GameSession).where(GameSession.public_id == game_id))
        assert game is not None
        assert game.status == "expired"
        assert game.completed_at is not None
        assert game.completed_at.replace(tzinfo=UTC) == deadline
        assert game.final_score == 0
        assert game.score_breakdown is not None
        assert game.score_breakdown["total"] == 0
        assert await session.scalar(select(func.count(GameAttempt.id))) == 0


def _game(
    *,
    owner_id: uuid.UUID,
    now: datetime,
    mode: str = "solo",
    status: str = "won",
    completed_days_ago: int | None = None,
    ranked_eligibility: str = "unranked",
    friend_challenge_id: uuid.UUID | None = None,
    room_id: uuid.UUID | None = None,
) -> GameSession:
    completed_at = (
        now - timedelta(days=completed_days_ago) if completed_days_ago is not None else None
    )
    started_at = (completed_at or now) - timedelta(hours=1)
    config = get_preset("easy")
    return GameSession(
        public_id=uuid.uuid4().hex[:24],
        owner_id=owner_id,
        mode=mode,
        difficulty="easy",
        config=config.to_dict(),
        status=status,
        rule_set_version=RULE_SET_VERSION,
        scoring_version=SCORING_VERSION,
        encrypted_secret=b"ciphertext",
        secret_nonce=b"nonce",
        secret_key_version="v1",
        attempts_used=1,
        maximum_attempts=config.max_attempts,
        started_at=started_at,
        expires_at=started_at + timedelta(days=7),
        completed_at=completed_at,
        elapsed_seconds=60 if completed_at else None,
        final_score=0 if completed_at else None,
        score_breakdown={"attempts": 0, "difficulty": 0, "time": 0, "total": 0},
        ranked_eligibility=ranked_eligibility,
        friend_challenge_id=friend_challenge_id,
        room_id=room_id,
    )


def _challenge(owner_id: uuid.UUID, *, now: datetime, expires_days_ago: int) -> FriendChallenge:
    return FriendChallenge(
        share_code_hash=uuid.uuid4().hex + uuid.uuid4().hex,
        creator_id=owner_id,
        config=get_preset("easy").to_dict(),
        encrypted_secret=b"ciphertext",
        secret_nonce=b"nonce",
        secret_key_version="v1",
        expires_at=now - timedelta(days=expires_days_ago),
    )


def _room(owner_id: uuid.UUID, *, now: datetime, expires_days_ago: int) -> MultiplayerRoom:
    return MultiplayerRoom(
        room_code_hash=uuid.uuid4().hex + uuid.uuid4().hex,
        owner_id=owner_id,
        config=get_preset("easy").to_dict(),
        encrypted_secret=b"ciphertext",
        secret_nonce=b"nonce",
        secret_key_version="v1",
        status="active",
        expires_at=now - timedelta(days=expires_days_ago),
    )


async def test_retention_batch_is_bounded_resumable_and_deletes_in_dependency_order(
    api: APIContext,
) -> None:
    now = datetime.now(UTC)
    owner_id = api.current["principal"].user_id
    async with api.sessions() as session:
        session.add(Profile(id=owner_id, is_anonymous=False))

        expired_event = ProductEvent(
            client_event_id=uuid.uuid4(),
            event_name="game_started",
            anonymous=False,
            consent_version="privacy-v1",
            release="test",
            occurred_at=now - timedelta(days=397),
            expires_at=now - timedelta(days=1),
        )
        retained_event = ProductEvent(
            client_event_id=uuid.uuid4(),
            event_name="game_started",
            anonymous=False,
            consent_version="privacy-v1",
            release="test",
            occurred_at=now - timedelta(days=1),
            expires_at=now + timedelta(days=395),
        )
        session.add_all([expired_event, retained_event])

        unused_challenge = _challenge(owner_id, now=now, expires_days_ago=1)
        old_completed_challenge = _challenge(owner_id, now=now, expires_days_ago=100)
        recent_completed_challenge = _challenge(owner_id, now=now, expires_days_ago=40)
        session.add_all([unused_challenge, old_completed_challenge, recent_completed_challenge])
        await session.flush()
        old_challenge_game = _game(
            owner_id=owner_id,
            now=now,
            mode="friend_challenge",
            status="lost",
            completed_days_ago=91,
            friend_challenge_id=old_completed_challenge.id,
        )
        recent_challenge_game = _game(
            owner_id=owner_id,
            now=now,
            mode="friend_challenge",
            status="lost",
            completed_days_ago=20,
            friend_challenge_id=recent_completed_challenge.id,
        )

        old_room = _room(owner_id, now=now, expires_days_ago=31)
        session.add(old_room)
        await session.flush()
        session.add_all(
            [
                MultiplayerMember(room_id=old_room.id, user_id=owner_id),
                MultiplayerEvent(
                    room_id=old_room.id,
                    sequence=1,
                    event_type="room_started",
                    payload={},
                ),
            ]
        )

        due_active_game = _game(owner_id=owner_id, now=now, status="active")
        due_active_game.completed_at = None
        due_active_game.elapsed_seconds = None
        due_active_game.final_score = None
        due_active_game.expires_at = now - timedelta(minutes=30)
        old_unranked_game = _game(
            owner_id=owner_id,
            now=now,
            status="expired",
            completed_days_ago=366,
        )
        old_ranked_game = _game(
            owner_id=owner_id,
            now=now,
            status="won",
            completed_days_ago=731,
            ranked_eligibility="eligible",
        )
        retained_ranked_game = _game(
            owner_id=owner_id,
            now=now,
            status="won",
            completed_days_ago=400,
            ranked_eligibility="eligible",
        )
        session.add_all(
            [
                old_challenge_game,
                recent_challenge_game,
                due_active_game,
                old_unranked_game,
                old_ranked_game,
                retained_ranked_game,
            ]
        )
        await session.flush()
        for game in (old_unranked_game, old_ranked_game):
            session.add(
                GameAttempt(
                    game_id=game.id,
                    attempt_number=1,
                    guess=list("RBGY"),
                    black_pegs=0,
                    white_pegs=0,
                    idempotency_key=uuid.uuid4().hex,
                    request_id=uuid.uuid4().hex,
                )
            )
        await session.commit()

    async with api.sessions() as session:
        summary = await run_retention_batch(session, now=now, batch_size=10)
    assert summary.game_sessions_expired == 1
    assert summary.rooms_expired == 1
    assert summary.product_events_deleted == 1
    assert summary.friend_challenges_deleted == 2
    assert summary.rooms_deleted == 1
    assert summary.game_sessions_deleted == 2

    async with api.sessions() as session:
        assert await session.get(ProductEvent, retained_event.id) is not None
        assert await session.get(ProductEvent, expired_event.id) is None
        assert await session.get(FriendChallenge, unused_challenge.id) is None
        assert await session.get(FriendChallenge, old_completed_challenge.id) is None
        assert await session.get(FriendChallenge, recent_completed_challenge.id) is not None
        assert await session.get(MultiplayerRoom, old_room.id) is None
        assert (
            await session.scalar(
                select(func.count(MultiplayerEvent.id)).where(
                    MultiplayerEvent.room_id == old_room.id
                )
            )
            == 0
        )
        assert (
            await session.scalar(
                select(func.count(MultiplayerMember.id)).where(
                    MultiplayerMember.room_id == old_room.id
                )
            )
            == 0
        )
        due_game = await session.get(GameSession, due_active_game.id)
        assert due_game is not None and due_game.status == "expired"
        assert due_game.completed_at is not None
        assert due_game.completed_at.replace(tzinfo=UTC) == due_active_game.expires_at
        assert await session.get(GameSession, old_unranked_game.id) is None
        assert await session.get(GameSession, old_ranked_game.id) is None
        assert await session.get(GameSession, retained_ranked_game.id) is not None
        assert await session.scalar(select(func.count(GameAttempt.id))) == 0
        detached = await session.get(GameSession, old_challenge_game.id)
        assert detached is not None and detached.friend_challenge_id is None

    async with api.sessions() as session:
        empty = await run_retention_batch(session, now=now, batch_size=10)
    assert empty.records_changed == 0


@pytest.mark.postgres
@pytest.mark.skipif(
    not os.getenv("MASTERMIND_TEST_POSTGRES_URL"),
    reason="Set MASTERMIND_TEST_POSTGRES_URL to an isolated PostgreSQL database.",
)
async def test_postgres_retention_skips_locked_rows_and_resumes() -> None:
    url = os.environ["MASTERMIND_TEST_POSTGRES_URL"]
    bootstrap_engine = create_async_engine(url)
    async with bootstrap_engine.begin() as connection:
        await connection.execute(text("DROP SCHEMA public CASCADE"))
        await connection.execute(text("CREATE SCHEMA public"))
    await bootstrap_engine.dispose()
    environment = os.environ | {
        "MASTERMIND_ENVIRONMENT": "test",
        "MASTERMIND_DATABASE_URL": url,
    }
    migration = await asyncio.to_thread(
        subprocess.run,
        ["alembic", "-c", "apps/api/alembic.ini", "upgrade", "head"],
        cwd=Path(__file__).parents[2],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert migration.returncode == 0, migration.stderr
    engine = create_async_engine(url)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    now = datetime.now(UTC)
    first = ProductEvent(
        client_event_id=uuid.uuid4(),
        event_name="game_started",
        anonymous=False,
        consent_version="privacy-v1",
        release="test",
        occurred_at=now - timedelta(days=398),
        expires_at=now - timedelta(days=2),
    )
    second = ProductEvent(
        client_event_id=uuid.uuid4(),
        event_name="game_started",
        anonymous=False,
        consent_version="privacy-v1",
        release="test",
        occurred_at=now - timedelta(days=397),
        expires_at=now - timedelta(days=1),
    )
    async with sessions() as session:
        await session.execute(delete(ProductEvent))
        session.add_all([first, second])
        await session.commit()

    async with sessions() as locked_session:
        await locked_session.scalar(
            select(ProductEvent).where(ProductEvent.id == first.id).with_for_update()
        )
        async with sessions() as worker_session:
            summary = await run_retention_batch(worker_session, now=now, batch_size=1)
        assert summary.product_events_deleted == 1
        await locked_session.rollback()

    async with sessions() as worker_session:
        resumed = await run_retention_batch(worker_session, now=now, batch_size=1)
    assert resumed.product_events_deleted == 1
    async with sessions() as session:
        assert await session.scalar(select(func.count(ProductEvent.id))) == 0

    role_event = ProductEvent(
        client_event_id=uuid.uuid4(),
        event_name="game_started",
        anonymous=False,
        consent_version="privacy-v1",
        release="test",
        occurred_at=now - timedelta(days=397),
        expires_at=now - timedelta(days=1),
    )
    async with sessions() as session:
        session.add(role_event)
        await session.commit()
    async with engine.connect() as connection:
        await connection.execute(text("SET ROLE mastermind_retention"))
        role_session = AsyncSession(bind=connection, expire_on_commit=False)
        try:
            role_summary = await run_retention_batch(role_session, now=now, batch_size=1)
        finally:
            await role_session.close()
    assert role_summary.product_events_deleted == 1
    await engine.dispose()
