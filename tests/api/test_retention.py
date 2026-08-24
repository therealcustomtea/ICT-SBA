# Defers type-annotation evaluation to support modern hints safely.
from __future__ import annotations

# Imports `asyncio` so the module can use that dependency.
import asyncio

# Imports `os` so the module can use that dependency.
import os

# Imports `subprocess` so the module can use that dependency.
import subprocess

# Imports `uuid` so the module can use that dependency.
import uuid

# Imports selected names from `datetime` for use in this module.
from datetime import UTC, datetime, timedelta

# Imports selected names from `pathlib` for use in this module.
from pathlib import Path

# Imports `pytest` so the module can use that dependency.
import pytest

# Imports selected names from `mastermind_api.models` for use in this module.
from mastermind_api.models import (
    # Supplies this item to the surrounding call or collection.
    FriendChallenge,
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
    # Supplies this item to the surrounding call or collection.
    ProductEvent,
    # Supplies this item to the surrounding call or collection.
    Profile,
    # Closes the multiline call, declaration, or collection started above.
)

# Imports selected names from `mastermind_api.retention` for use in this module.
from mastermind_api.retention import game_expiry_for_mode, run_retention_batch

# Imports selected names from `mastermind_core` for use in this module.
from mastermind_core import RULE_SET_VERSION, SCORING_VERSION, GameMode, get_preset

# Imports selected names from `sqlalchemy` for use in this module.
from sqlalchemy import delete, func, select, text

# Imports selected names from `sqlalchemy.ext.asyncio` for use in this module.
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Imports selected names from `.conftest` for use in this module.
from .conftest import APIContext


# Applies `@pytest.mark.parametrize(` to configure the declaration immediately below.
@pytest.mark.parametrize(
    # Supplies this item to the surrounding call or collection.
    ("mode", "expected_lifetime"),
    # Begins the nested block or multiline expression completed below.
    [
        # Supplies this item to the surrounding call or collection.
        (GameMode.SOLO, timedelta(days=7)),
        # Supplies this item to the surrounding call or collection.
        (GameMode.DAILY, timedelta(days=1)),
        # Supplies this item to the surrounding call or collection.
        (GameMode.PRACTICE, timedelta(days=1)),
        # Supplies this item to the surrounding call or collection.
        (GameMode.PASS_AND_PLAY, timedelta(days=1)),
        # Supplies this item to the surrounding call or collection.
        (GameMode.FRIEND_CHALLENGE, timedelta(days=30)),
        # Supplies this item to the surrounding call or collection.
        (GameMode.DUEL, timedelta(hours=2)),
        # Closes the multiline call, declaration, or collection started above.
    ],
    # Closes the multiline call, declaration, or collection started above.
)
# Defines the `test_game_expiry_is_mode_specific_and_fixed` callable and its typed interface.
def test_game_expiry_is_mode_specific_and_fixed(
    # Declares the typed `mode` data field.
    mode: GameMode,
    # Declares the typed `expected_lifetime` data field.
    expected_lifetime: timedelta,
    # Completes the signature and declares the callable return type.
) -> None:
    # Computes and stores `started_at` for subsequent operations.
    started_at = datetime(2026, 7, 16, 8, tzinfo=UTC)
    # Asserts this invariant so an unexpected test state fails immediately.
    assert game_expiry_for_mode(mode, started_at) == started_at + expected_lifetime


# Defines the `test_linked_game_expiry_never_outlives_its_parent` callable and its typed interface.
def test_linked_game_expiry_never_outlives_its_parent() -> None:
    # Computes and stores `started_at` for subsequent operations.
    started_at = datetime(2026, 7, 16, 8, tzinfo=UTC)
    # Computes and stores `linked_expiry` for subsequent operations.
    linked_expiry = started_at + timedelta(minutes=30)
    # Asserts this invariant so an unexpected test state fails immediately.
    assert (
        # Calls `game_expiry_for_mode` with the supplied values.
        game_expiry_for_mode(
            # Supplies this item to the surrounding call or collection.
            GameMode.DUEL,
            # Supplies this item to the surrounding call or collection.
            started_at,
            # Provides the `linked_expires_at` parameter or keyword argument.
            linked_expires_at=linked_expiry,
            # Closes the multiline call, declaration, or collection started above.
        )
        # Executes this statement as the next step in the surrounding logic.
        == linked_expiry
        # Closes the multiline call, declaration, or collection started above.
    )
    # Acquires this managed resource and guarantees cleanup afterward.
    with pytest.raises(ValueError, match="must remain active"):
        # Calls `game_expiry_for_mode` with the supplied values.
        game_expiry_for_mode(
            # Supplies this item to the surrounding call or collection.
            GameMode.FRIEND_CHALLENGE,
            # Supplies this item to the surrounding call or collection.
            started_at,
            # Provides the `linked_expires_at` parameter or keyword argument.
            linked_expires_at=started_at,
            # Closes the multiline call, declaration, or collection started above.
        )


# Defines the `test_attempt_after_deadline_durably_expires_game` callable and its typed interface.
async def test_attempt_after_deadline_durably_expires_game(api: APIContext) -> None:
    # Computes and stores `created` for subsequent operations.
    created = await api.client.post(
        # Supplies this item to the surrounding call or collection.
        "/v1/games",
        # Provides the `json` parameter or keyword argument.
        json={"mode": "solo", "difficulty": "easy"},
        # Closes the multiline call, declaration, or collection started above.
    )
    # Asserts this invariant so an unexpected test state fails immediately.
    assert created.status_code == 201, created.text
    # Computes and stores `game_id` for subsequent operations.
    game_id = created.json()["id"]
    # Computes and stores `deadline` for subsequent operations.
    deadline = datetime.now(UTC)
    # Acquires this asynchronous managed resource for the nested operation.
    async with api.sessions() as session:
        # Executes this statement as the next step in the surrounding logic.
        game = await session.scalar(select(GameSession).where(GameSession.public_id == game_id))
        # Asserts this invariant so an unexpected test state fails immediately.
        assert game is not None
        # Computes and stores `game.expires_at` for subsequent operations.
        game.expires_at = deadline
        # Waits for this asynchronous operation to complete.
        await session.commit()

    # Computes and stores `response` for subsequent operations.
    response = await api.client.post(
        # Supplies this item to the surrounding call or collection.
        f"/v1/games/{game_id}/attempts",
        # Provides the `json` parameter or keyword argument.
        json={"guess": list("RBGY"), "idempotencyKey": "expired-attempt-0001"},
        # Closes the multiline call, declaration, or collection started above.
    )
    # Asserts this invariant so an unexpected test state fails immediately.
    assert response.status_code == 410
    # Asserts this invariant so an unexpected test state fails immediately.
    assert response.json()["code"] == "GAME_EXPIRED"
    # Acquires this asynchronous managed resource for the nested operation.
    async with api.sessions() as session:
        # Executes this statement as the next step in the surrounding logic.
        game = await session.scalar(select(GameSession).where(GameSession.public_id == game_id))
        # Asserts this invariant so an unexpected test state fails immediately.
        assert game is not None
        # Asserts this invariant so an unexpected test state fails immediately.
        assert game.status == "expired"
        # Asserts this invariant so an unexpected test state fails immediately.
        assert game.completed_at is not None
        # Asserts this invariant so an unexpected test state fails immediately.
        assert game.completed_at.replace(tzinfo=UTC) == deadline
        # Asserts this invariant so an unexpected test state fails immediately.
        assert game.final_score == 0
        # Asserts this invariant so an unexpected test state fails immediately.
        assert game.score_breakdown is not None
        # Asserts this invariant so an unexpected test state fails immediately.
        assert game.score_breakdown["total"] == 0
        # Asserts this invariant so an unexpected test state fails immediately.
        assert await session.scalar(select(func.count(GameAttempt.id))) == 0


# Defines the `_game` callable and its typed interface.
def _game(
    # Makes the following parameters keyword-only for clear call sites.
    *,
    # Declares the typed `owner_id` data field.
    owner_id: uuid.UUID,
    # Declares the typed `now` data field.
    now: datetime,
    # Provides the `mode` parameter or keyword argument.
    mode: str = "solo",
    # Provides the `status` parameter or keyword argument.
    status: str = "won",
    # Provides the `completed_days_ago` parameter or keyword argument.
    completed_days_ago: int | None = None,
    # Provides the `ranked_eligibility` parameter or keyword argument.
    ranked_eligibility: str = "unranked",
    # Provides the `friend_challenge_id` parameter or keyword argument.
    friend_challenge_id: uuid.UUID | None = None,
    # Provides the `room_id` parameter or keyword argument.
    room_id: uuid.UUID | None = None,
    # Completes the signature and declares the callable return type.
) -> GameSession:
    # Computes and stores `completed_at` for subsequent operations.
    completed_at = (
        # Executes this statement as the next step in the surrounding logic.
        now - timedelta(days=completed_days_ago) if completed_days_ago is not None else None
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `started_at` for subsequent operations.
    started_at = (completed_at or now) - timedelta(hours=1)
    # Computes and stores `config` for subsequent operations.
    config = get_preset("easy")
    # Returns this result to the caller and ends the current function.
    return GameSession(
        # Provides the `public_id` parameter or keyword argument.
        public_id=uuid.uuid4().hex[:24],
        # Provides the `owner_id` parameter or keyword argument.
        owner_id=owner_id,
        # Provides the `mode` parameter or keyword argument.
        mode=mode,
        # Provides the `difficulty` parameter or keyword argument.
        difficulty="easy",
        # Provides the `config` parameter or keyword argument.
        config=config.to_dict(),
        # Provides the `status` parameter or keyword argument.
        status=status,
        # Provides the `rule_set_version` parameter or keyword argument.
        rule_set_version=RULE_SET_VERSION,
        # Provides the `scoring_version` parameter or keyword argument.
        scoring_version=SCORING_VERSION,
        # Provides the `encrypted_secret` parameter or keyword argument.
        encrypted_secret=b"ciphertext",
        # Provides the `secret_nonce` parameter or keyword argument.
        secret_nonce=b"nonce",
        # Provides the `secret_key_version` parameter or keyword argument.
        secret_key_version="v1",
        # Provides the `attempts_used` parameter or keyword argument.
        attempts_used=1,
        # Provides the `maximum_attempts` parameter or keyword argument.
        maximum_attempts=config.max_attempts,
        # Provides the `started_at` parameter or keyword argument.
        started_at=started_at,
        # Provides the `expires_at` parameter or keyword argument.
        expires_at=started_at + timedelta(days=7),
        # Provides the `completed_at` parameter or keyword argument.
        completed_at=completed_at,
        # Provides the `elapsed_seconds` parameter or keyword argument.
        elapsed_seconds=60 if completed_at else None,
        # Provides the `final_score` parameter or keyword argument.
        final_score=0 if completed_at else None,
        # Provides the `score_breakdown` parameter or keyword argument.
        score_breakdown={"attempts": 0, "difficulty": 0, "time": 0, "total": 0},
        # Provides the `ranked_eligibility` parameter or keyword argument.
        ranked_eligibility=ranked_eligibility,
        # Provides the `friend_challenge_id` parameter or keyword argument.
        friend_challenge_id=friend_challenge_id,
        # Provides the `room_id` parameter or keyword argument.
        room_id=room_id,
        # Closes the multiline call, declaration, or collection started above.
    )


# Defines the `_challenge` callable and its typed interface.
def _challenge(owner_id: uuid.UUID, *, now: datetime, expires_days_ago: int) -> FriendChallenge:
    # Returns this result to the caller and ends the current function.
    return FriendChallenge(
        # Provides the `share_code_hash` parameter or keyword argument.
        share_code_hash=uuid.uuid4().hex + uuid.uuid4().hex,
        # Provides the `creator_id` parameter or keyword argument.
        creator_id=owner_id,
        # Provides the `config` parameter or keyword argument.
        config=get_preset("easy").to_dict(),
        # Provides the `encrypted_secret` parameter or keyword argument.
        encrypted_secret=b"ciphertext",
        # Provides the `secret_nonce` parameter or keyword argument.
        secret_nonce=b"nonce",
        # Provides the `secret_key_version` parameter or keyword argument.
        secret_key_version="v1",
        # Provides the `expires_at` parameter or keyword argument.
        expires_at=now - timedelta(days=expires_days_ago),
        # Closes the multiline call, declaration, or collection started above.
    )


# Defines the `_room` callable and its typed interface.
def _room(owner_id: uuid.UUID, *, now: datetime, expires_days_ago: int) -> MultiplayerRoom:
    # Returns this result to the caller and ends the current function.
    return MultiplayerRoom(
        # Provides the `room_code_hash` parameter or keyword argument.
        room_code_hash=uuid.uuid4().hex + uuid.uuid4().hex,
        # Provides the `owner_id` parameter or keyword argument.
        owner_id=owner_id,
        # Provides the `config` parameter or keyword argument.
        config=get_preset("easy").to_dict(),
        # Provides the `encrypted_secret` parameter or keyword argument.
        encrypted_secret=b"ciphertext",
        # Provides the `secret_nonce` parameter or keyword argument.
        secret_nonce=b"nonce",
        # Provides the `secret_key_version` parameter or keyword argument.
        secret_key_version="v1",
        # Provides the `status` parameter or keyword argument.
        status="active",
        # Provides the `expires_at` parameter or keyword argument.
        expires_at=now - timedelta(days=expires_days_ago),
        # Closes the multiline call, declaration, or collection started above.
    )


# Defines the `test_retention_batch_is_bounded_resumable_and_deletes_in_dependency_order` callable
# and its typed interface.
async def test_retention_batch_is_bounded_resumable_and_deletes_in_dependency_order(
    # Declares the typed `api` data field.
    api: APIContext,
    # Completes the signature and declares the callable return type.
) -> None:
    # Computes and stores `now` for subsequent operations.
    now = datetime.now(UTC)
    # Computes and stores `owner_id` for subsequent operations.
    owner_id = api.current["principal"].user_id
    # Acquires this asynchronous managed resource for the nested operation.
    async with api.sessions() as session:
        # Calls `session.add` with the supplied values.
        session.add(Profile(id=owner_id, is_anonymous=False))

        # Computes and stores `expired_event` for subsequent operations.
        expired_event = ProductEvent(
            # Provides the `client_event_id` parameter or keyword argument.
            client_event_id=uuid.uuid4(),
            # Provides the `event_name` parameter or keyword argument.
            event_name="game_started",
            # Provides the `anonymous` parameter or keyword argument.
            anonymous=False,
            # Provides the `consent_version` parameter or keyword argument.
            consent_version="privacy-v1",
            # Provides the `release` parameter or keyword argument.
            release="test",
            # Provides the `occurred_at` parameter or keyword argument.
            occurred_at=now - timedelta(days=397),
            # Provides the `expires_at` parameter or keyword argument.
            expires_at=now - timedelta(days=1),
            # Closes the multiline call, declaration, or collection started above.
        )
        # Computes and stores `retained_event` for subsequent operations.
        retained_event = ProductEvent(
            # Provides the `client_event_id` parameter or keyword argument.
            client_event_id=uuid.uuid4(),
            # Provides the `event_name` parameter or keyword argument.
            event_name="game_started",
            # Provides the `anonymous` parameter or keyword argument.
            anonymous=False,
            # Provides the `consent_version` parameter or keyword argument.
            consent_version="privacy-v1",
            # Provides the `release` parameter or keyword argument.
            release="test",
            # Provides the `occurred_at` parameter or keyword argument.
            occurred_at=now - timedelta(days=1),
            # Provides the `expires_at` parameter or keyword argument.
            expires_at=now + timedelta(days=395),
            # Closes the multiline call, declaration, or collection started above.
        )
        # Calls `session.add_all` with the supplied values.
        session.add_all([expired_event, retained_event])

        # Computes and stores `unused_challenge` for subsequent operations.
        unused_challenge = _challenge(owner_id, now=now, expires_days_ago=1)
        # Computes and stores `old_completed_challenge` for subsequent operations.
        old_completed_challenge = _challenge(owner_id, now=now, expires_days_ago=100)
        # Computes and stores `recent_completed_challenge` for subsequent operations.
        recent_completed_challenge = _challenge(owner_id, now=now, expires_days_ago=40)
        # Calls `session.add_all` with the supplied values.
        session.add_all([unused_challenge, old_completed_challenge, recent_completed_challenge])
        # Waits for this asynchronous operation to complete.
        await session.flush()
        # Computes and stores `old_challenge_game` for subsequent operations.
        old_challenge_game = _game(
            # Provides the `owner_id` parameter or keyword argument.
            owner_id=owner_id,
            # Provides the `now` parameter or keyword argument.
            now=now,
            # Provides the `mode` parameter or keyword argument.
            mode="friend_challenge",
            # Provides the `status` parameter or keyword argument.
            status="lost",
            # Provides the `completed_days_ago` parameter or keyword argument.
            completed_days_ago=91,
            # Provides the `friend_challenge_id` parameter or keyword argument.
            friend_challenge_id=old_completed_challenge.id,
            # Closes the multiline call, declaration, or collection started above.
        )
        # Computes and stores `recent_challenge_game` for subsequent operations.
        recent_challenge_game = _game(
            # Provides the `owner_id` parameter or keyword argument.
            owner_id=owner_id,
            # Provides the `now` parameter or keyword argument.
            now=now,
            # Provides the `mode` parameter or keyword argument.
            mode="friend_challenge",
            # Provides the `status` parameter or keyword argument.
            status="lost",
            # Provides the `completed_days_ago` parameter or keyword argument.
            completed_days_ago=20,
            # Provides the `friend_challenge_id` parameter or keyword argument.
            friend_challenge_id=recent_completed_challenge.id,
            # Closes the multiline call, declaration, or collection started above.
        )

        # Computes and stores `old_room` for subsequent operations.
        old_room = _room(owner_id, now=now, expires_days_ago=31)
        # Calls `session.add` with the supplied values.
        session.add(old_room)
        # Waits for this asynchronous operation to complete.
        await session.flush()
        # Calls `session.add_all` with the supplied values.
        session.add_all(
            # Begins the nested block or multiline expression completed below.
            [
                # Calls `MultiplayerMember` with the supplied values.
                MultiplayerMember(room_id=old_room.id, user_id=owner_id),
                # Calls `MultiplayerEvent` with the supplied values.
                MultiplayerEvent(
                    # Provides the `room_id` parameter or keyword argument.
                    room_id=old_room.id,
                    # Provides the `sequence` parameter or keyword argument.
                    sequence=1,
                    # Provides the `event_type` parameter or keyword argument.
                    event_type="room_started",
                    # Provides the `payload` parameter or keyword argument.
                    payload={},
                    # Closes the multiline call, declaration, or collection started above.
                ),
                # Closes the multiline call, declaration, or collection started above.
            ]
            # Closes the multiline call, declaration, or collection started above.
        )

        # Computes and stores `due_active_game` for subsequent operations.
        due_active_game = _game(owner_id=owner_id, now=now, status="active")
        # Computes and stores `due_active_game.completed_at` for subsequent operations.
        due_active_game.completed_at = None
        # Computes and stores `due_active_game.elapsed_seconds` for subsequent operations.
        due_active_game.elapsed_seconds = None
        # Computes and stores `due_active_game.final_score` for subsequent operations.
        due_active_game.final_score = None
        # Computes and stores `due_active_game.expires_at` for subsequent operations.
        due_active_game.expires_at = now - timedelta(minutes=30)
        # Computes and stores `old_unranked_game` for subsequent operations.
        old_unranked_game = _game(
            # Provides the `owner_id` parameter or keyword argument.
            owner_id=owner_id,
            # Provides the `now` parameter or keyword argument.
            now=now,
            # Provides the `status` parameter or keyword argument.
            status="expired",
            # Provides the `completed_days_ago` parameter or keyword argument.
            completed_days_ago=366,
            # Closes the multiline call, declaration, or collection started above.
        )
        # Computes and stores `old_ranked_game` for subsequent operations.
        old_ranked_game = _game(
            # Provides the `owner_id` parameter or keyword argument.
            owner_id=owner_id,
            # Provides the `now` parameter or keyword argument.
            now=now,
            # Provides the `status` parameter or keyword argument.
            status="won",
            # Provides the `completed_days_ago` parameter or keyword argument.
            completed_days_ago=731,
            # Provides the `ranked_eligibility` parameter or keyword argument.
            ranked_eligibility="eligible",
            # Closes the multiline call, declaration, or collection started above.
        )
        # Computes and stores `retained_ranked_game` for subsequent operations.
        retained_ranked_game = _game(
            # Provides the `owner_id` parameter or keyword argument.
            owner_id=owner_id,
            # Provides the `now` parameter or keyword argument.
            now=now,
            # Provides the `status` parameter or keyword argument.
            status="won",
            # Provides the `completed_days_ago` parameter or keyword argument.
            completed_days_ago=400,
            # Provides the `ranked_eligibility` parameter or keyword argument.
            ranked_eligibility="eligible",
            # Closes the multiline call, declaration, or collection started above.
        )
        # Calls `session.add_all` with the supplied values.
        session.add_all(
            # Begins the nested block or multiline expression completed below.
            [
                # Supplies this item to the surrounding call or collection.
                old_challenge_game,
                # Supplies this item to the surrounding call or collection.
                recent_challenge_game,
                # Supplies this item to the surrounding call or collection.
                due_active_game,
                # Supplies this item to the surrounding call or collection.
                old_unranked_game,
                # Supplies this item to the surrounding call or collection.
                old_ranked_game,
                # Supplies this item to the surrounding call or collection.
                retained_ranked_game,
                # Closes the multiline call, declaration, or collection started above.
            ]
            # Closes the multiline call, declaration, or collection started above.
        )
        # Waits for this asynchronous operation to complete.
        await session.flush()
        # Iterates through the supplied values for the nested operation.
        for game in (old_unranked_game, old_ranked_game):
            # Calls `session.add` with the supplied values.
            session.add(
                # Calls `GameAttempt` with the supplied values.
                GameAttempt(
                    # Provides the `game_id` parameter or keyword argument.
                    game_id=game.id,
                    # Provides the `attempt_number` parameter or keyword argument.
                    attempt_number=1,
                    # Provides the `guess` parameter or keyword argument.
                    guess=list("RBGY"),
                    # Provides the `black_pegs` parameter or keyword argument.
                    black_pegs=0,
                    # Provides the `white_pegs` parameter or keyword argument.
                    white_pegs=0,
                    # Provides the `idempotency_key` parameter or keyword argument.
                    idempotency_key=uuid.uuid4().hex,
                    # Provides the `request_id` parameter or keyword argument.
                    request_id=uuid.uuid4().hex,
                    # Closes the multiline call, declaration, or collection started above.
                )
                # Closes the multiline call, declaration, or collection started above.
            )
        # Waits for this asynchronous operation to complete.
        await session.commit()

    # Acquires this asynchronous managed resource for the nested operation.
    async with api.sessions() as session:
        # Computes and stores `summary` for subsequent operations.
        summary = await run_retention_batch(session, now=now, batch_size=10)
    # Asserts this invariant so an unexpected test state fails immediately.
    assert summary.game_sessions_expired == 1
    # Asserts this invariant so an unexpected test state fails immediately.
    assert summary.rooms_expired == 1
    # Asserts this invariant so an unexpected test state fails immediately.
    assert summary.product_events_deleted == 1
    # Asserts this invariant so an unexpected test state fails immediately.
    assert summary.friend_challenges_deleted == 2
    # Asserts this invariant so an unexpected test state fails immediately.
    assert summary.rooms_deleted == 1
    # Asserts this invariant so an unexpected test state fails immediately.
    assert summary.game_sessions_deleted == 2

    # Acquires this asynchronous managed resource for the nested operation.
    async with api.sessions() as session:
        # Asserts this invariant so an unexpected test state fails immediately.
        assert await session.get(ProductEvent, retained_event.id) is not None
        # Asserts this invariant so an unexpected test state fails immediately.
        assert await session.get(ProductEvent, expired_event.id) is None
        # Asserts this invariant so an unexpected test state fails immediately.
        assert await session.get(FriendChallenge, unused_challenge.id) is None
        # Asserts this invariant so an unexpected test state fails immediately.
        assert await session.get(FriendChallenge, old_completed_challenge.id) is None
        # Asserts this invariant so an unexpected test state fails immediately.
        assert await session.get(FriendChallenge, recent_completed_challenge.id) is not None
        # Asserts this invariant so an unexpected test state fails immediately.
        assert await session.get(MultiplayerRoom, old_room.id) is None
        # Asserts this invariant so an unexpected test state fails immediately.
        assert (
            # Waits for this asynchronous operation to complete.
            await session.scalar(
                # Calls `select` with the supplied values.
                select(func.count(MultiplayerEvent.id)).where(
                    # Executes this statement as the next step in the surrounding logic.
                    MultiplayerEvent.room_id == old_room.id
                    # Closes the multiline call, declaration, or collection started above.
                )
                # Closes the multiline call, declaration, or collection started above.
            )
            # Executes this statement as the next step in the surrounding logic.
            == 0
            # Closes the multiline call, declaration, or collection started above.
        )
        # Asserts this invariant so an unexpected test state fails immediately.
        assert (
            # Waits for this asynchronous operation to complete.
            await session.scalar(
                # Calls `select` with the supplied values.
                select(func.count(MultiplayerMember.id)).where(
                    # Executes this statement as the next step in the surrounding logic.
                    MultiplayerMember.room_id == old_room.id
                    # Closes the multiline call, declaration, or collection started above.
                )
                # Closes the multiline call, declaration, or collection started above.
            )
            # Executes this statement as the next step in the surrounding logic.
            == 0
            # Closes the multiline call, declaration, or collection started above.
        )
        # Computes and stores `due_game` for subsequent operations.
        due_game = await session.get(GameSession, due_active_game.id)
        # Asserts this invariant so an unexpected test state fails immediately.
        assert due_game is not None and due_game.status == "expired"
        # Asserts this invariant so an unexpected test state fails immediately.
        assert due_game.completed_at is not None
        # Asserts this invariant so an unexpected test state fails immediately.
        assert due_game.completed_at.replace(tzinfo=UTC) == due_active_game.expires_at
        # Asserts this invariant so an unexpected test state fails immediately.
        assert await session.get(GameSession, old_unranked_game.id) is None
        # Asserts this invariant so an unexpected test state fails immediately.
        assert await session.get(GameSession, old_ranked_game.id) is None
        # Asserts this invariant so an unexpected test state fails immediately.
        assert await session.get(GameSession, retained_ranked_game.id) is not None
        # Asserts this invariant so an unexpected test state fails immediately.
        assert await session.scalar(select(func.count(GameAttempt.id))) == 0
        # Computes and stores `detached` for subsequent operations.
        detached = await session.get(GameSession, old_challenge_game.id)
        # Asserts this invariant so an unexpected test state fails immediately.
        assert detached is not None and detached.friend_challenge_id is None

    # Acquires this asynchronous managed resource for the nested operation.
    async with api.sessions() as session:
        # Computes and stores `empty` for subsequent operations.
        empty = await run_retention_batch(session, now=now, batch_size=10)
    # Asserts this invariant so an unexpected test state fails immediately.
    assert empty.records_changed == 0


# Applies `@pytest.mark.postgres` to configure the declaration immediately below.
@pytest.mark.postgres
# Applies `@pytest.mark.skipif(` to configure the declaration immediately below.
@pytest.mark.skipif(
    # Supplies this item to the surrounding call or collection.
    not os.getenv("MASTERMIND_TEST_POSTGRES_URL"),
    # Provides the `reason` parameter or keyword argument.
    reason="Set MASTERMIND_TEST_POSTGRES_URL to an isolated PostgreSQL database.",
    # Closes the multiline call, declaration, or collection started above.
)
# Defines the `test_postgres_retention_skips_locked_rows_and_resumes` callable and its typed
# interface.
async def test_postgres_retention_skips_locked_rows_and_resumes() -> None:
    # Computes and stores `url` for subsequent operations.
    url = os.environ["MASTERMIND_TEST_POSTGRES_URL"]
    # Computes and stores `bootstrap_engine` for subsequent operations.
    bootstrap_engine = create_async_engine(url)
    # Acquires this asynchronous managed resource for the nested operation.
    async with bootstrap_engine.begin() as connection:
        # Waits for this asynchronous operation to complete.
        await connection.execute(text("DROP SCHEMA public CASCADE"))
        # Waits for this asynchronous operation to complete.
        await connection.execute(text("CREATE SCHEMA public"))
    # Waits for this asynchronous operation to complete.
    await bootstrap_engine.dispose()
    # Computes and stores `environment` for subsequent operations.
    environment = os.environ | {
        # Associates the `MASTERMIND_ENVIRONMENT` key with its value.
        "MASTERMIND_ENVIRONMENT": "test",
        # Associates the `MASTERMIND_DATABASE_URL` key with its value.
        "MASTERMIND_DATABASE_URL": url,
        # Closes the multiline call, declaration, or collection started above.
    }
    # Computes and stores `migration` for subsequent operations.
    migration = await asyncio.to_thread(
        # Supplies this item to the surrounding call or collection.
        subprocess.run,
        # Supplies this item to the surrounding call or collection.
        ["alembic", "-c", "apps/api/alembic.ini", "upgrade", "head"],
        # Provides the `cwd` parameter or keyword argument.
        cwd=Path(__file__).parents[2],
        # Provides the `env` parameter or keyword argument.
        env=environment,
        # Provides the `capture_output` parameter or keyword argument.
        capture_output=True,
        # Provides the `text` parameter or keyword argument.
        text=True,
        # Provides the `check` parameter or keyword argument.
        check=False,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Asserts this invariant so an unexpected test state fails immediately.
    assert migration.returncode == 0, migration.stderr
    # Computes and stores `engine` for subsequent operations.
    engine = create_async_engine(url)
    # Computes and stores `sessions` for subsequent operations.
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    # Computes and stores `now` for subsequent operations.
    now = datetime.now(UTC)
    # Computes and stores `first` for subsequent operations.
    first = ProductEvent(
        # Provides the `client_event_id` parameter or keyword argument.
        client_event_id=uuid.uuid4(),
        # Provides the `event_name` parameter or keyword argument.
        event_name="game_started",
        # Provides the `anonymous` parameter or keyword argument.
        anonymous=False,
        # Provides the `consent_version` parameter or keyword argument.
        consent_version="privacy-v1",
        # Provides the `release` parameter or keyword argument.
        release="test",
        # Provides the `occurred_at` parameter or keyword argument.
        occurred_at=now - timedelta(days=398),
        # Provides the `expires_at` parameter or keyword argument.
        expires_at=now - timedelta(days=2),
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `second` for subsequent operations.
    second = ProductEvent(
        # Provides the `client_event_id` parameter or keyword argument.
        client_event_id=uuid.uuid4(),
        # Provides the `event_name` parameter or keyword argument.
        event_name="game_started",
        # Provides the `anonymous` parameter or keyword argument.
        anonymous=False,
        # Provides the `consent_version` parameter or keyword argument.
        consent_version="privacy-v1",
        # Provides the `release` parameter or keyword argument.
        release="test",
        # Provides the `occurred_at` parameter or keyword argument.
        occurred_at=now - timedelta(days=397),
        # Provides the `expires_at` parameter or keyword argument.
        expires_at=now - timedelta(days=1),
        # Closes the multiline call, declaration, or collection started above.
    )
    # Acquires this asynchronous managed resource for the nested operation.
    async with sessions() as session:
        # Waits for this asynchronous operation to complete.
        await session.execute(delete(ProductEvent))
        # Calls `session.add_all` with the supplied values.
        session.add_all([first, second])
        # Waits for this asynchronous operation to complete.
        await session.commit()

    # Acquires this asynchronous managed resource for the nested operation.
    async with sessions() as locked_session:
        # Waits for this asynchronous operation to complete.
        await locked_session.scalar(
            # Calls `select` with the supplied values.
            select(ProductEvent).where(ProductEvent.id == first.id).with_for_update()
            # Closes the multiline call, declaration, or collection started above.
        )
        # Acquires this asynchronous managed resource for the nested operation.
        async with sessions() as worker_session:
            # Computes and stores `summary` for subsequent operations.
            summary = await run_retention_batch(worker_session, now=now, batch_size=1)
        # Asserts this invariant so an unexpected test state fails immediately.
        assert summary.product_events_deleted == 1
        # Waits for this asynchronous operation to complete.
        await locked_session.rollback()

    # Acquires this asynchronous managed resource for the nested operation.
    async with sessions() as worker_session:
        # Computes and stores `resumed` for subsequent operations.
        resumed = await run_retention_batch(worker_session, now=now, batch_size=1)
    # Asserts this invariant so an unexpected test state fails immediately.
    assert resumed.product_events_deleted == 1
    # Acquires this asynchronous managed resource for the nested operation.
    async with sessions() as session:
        # Asserts this invariant so an unexpected test state fails immediately.
        assert await session.scalar(select(func.count(ProductEvent.id))) == 0

    # Computes and stores `role_event` for subsequent operations.
    role_event = ProductEvent(
        # Provides the `client_event_id` parameter or keyword argument.
        client_event_id=uuid.uuid4(),
        # Provides the `event_name` parameter or keyword argument.
        event_name="game_started",
        # Provides the `anonymous` parameter or keyword argument.
        anonymous=False,
        # Provides the `consent_version` parameter or keyword argument.
        consent_version="privacy-v1",
        # Provides the `release` parameter or keyword argument.
        release="test",
        # Provides the `occurred_at` parameter or keyword argument.
        occurred_at=now - timedelta(days=397),
        # Provides the `expires_at` parameter or keyword argument.
        expires_at=now - timedelta(days=1),
        # Closes the multiline call, declaration, or collection started above.
    )
    # Acquires this asynchronous managed resource for the nested operation.
    async with sessions() as session:
        # Calls `session.add` with the supplied values.
        session.add(role_event)
        # Waits for this asynchronous operation to complete.
        await session.commit()
    # Acquires this asynchronous managed resource for the nested operation.
    async with engine.connect() as connection:
        # Waits for this asynchronous operation to complete.
        await connection.execute(text("SET ROLE mastermind_retention"))
        # Computes and stores `role_session` for subsequent operations.
        role_session = AsyncSession(bind=connection, expire_on_commit=False)
        # Starts a protected operation whose expected failures are handled below.
        try:
            # Computes and stores `role_summary` for subsequent operations.
            role_summary = await run_retention_batch(role_session, now=now, batch_size=1)
        # Runs this cleanup block regardless of the protected result.
        finally:
            # Waits for this asynchronous operation to complete.
            await role_session.close()
    # Asserts this invariant so an unexpected test state fails immediately.
    assert role_summary.product_events_deleted == 1
    # Waits for this asynchronous operation to complete.
    await engine.dispose()
