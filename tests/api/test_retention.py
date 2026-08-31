# Defers annotation evaluation so modern type hints remain safe at runtime.
from __future__ import annotations

# Imports `uuid` because this module uses that dependency.
import uuid

# Imports the required names from `datetime` for this module.
from datetime import UTC, datetime, timedelta

# Imports the required names from `mastermind_api.models` for this module.
from mastermind_api.models import GameSession, ProductEvent

# Imports the required names from `mastermind_api.retention` for this module.
from mastermind_api.retention import (
    # Supplies this required nested value.
    DAILY_ACTIVE_LIFETIME,
    # Supplies this required nested value.
    DUEL_ACTIVE_LIFETIME,
    # Supplies this required nested value.
    expire_game_record,
    # Supplies this required nested value.
    game_expiry_for_mode,
    # Supplies this required nested value.
    run_retention_batch,
    # Closes the multiline declaration, call, or collection opened above.
)

# Imports the required names from `mastermind_core` for this module.
from mastermind_core import RULE_SET_VERSION, SCORING_VERSION, get_preset

# Imports the required names from `.conftest` for this module.
from .conftest import APIContext


# Defines this callable to implement the operation described by its name.
def make_game(*, started_at: datetime, expires_at: datetime) -> GameSession:
    # Stores `config` because later steps depend on this value.
    config = get_preset("easy")
    # Returns the computed result and ends the current callable.
    return GameSession(
        # Stores `public_id` because later steps depend on this value.
        public_id=f"game-{uuid.uuid4().hex}",
        # Stores `owner_id` because later steps depend on this value.
        owner_id=uuid.uuid4(),
        # Stores `mode` because later steps depend on this value.
        mode="solo",
        # Stores `config` because later steps depend on this value.
        config=config.to_dict(),
        # Stores `status` because later steps depend on this value.
        status="active",
        # Stores `rule_set_version` because later steps depend on this value.
        rule_set_version=RULE_SET_VERSION,
        # Stores `scoring_version` because later steps depend on this value.
        scoring_version=SCORING_VERSION,
        # Stores `encrypted_secret` because later steps depend on this value.
        encrypted_secret=b"ciphertext",
        # Stores `secret_nonce` because later steps depend on this value.
        secret_nonce=b"nonce",
        # Stores `secret_key_version` because later steps depend on this value.
        secret_key_version="v1",
        # Stores `maximum_attempts` because later steps depend on this value.
        maximum_attempts=config.max_attempts,
        # Stores `started_at` because later steps depend on this value.
        started_at=started_at,
        # Stores `expires_at` because later steps depend on this value.
        expires_at=expires_at,
        # Stores `ranked_eligibility` because later steps depend on this value.
        ranked_eligibility="eligible",
        # Closes the multiline declaration, call, or collection opened above.
    )


# Defines this callable to implement the operation described by its name.
def test_game_expiry_uses_mode_and_linked_deadline() -> None:
    # Stores `started_at` because later steps depend on this value.
    started_at = datetime(2026, 1, 1, tzinfo=UTC)
    # Performs this required operation before the surrounding flow continues.
    assert game_expiry_for_mode("daily", started_at) == started_at + DAILY_ACTIVE_LIFETIME
    # Stores `linked` because later steps depend on this value.
    linked = started_at + timedelta(minutes=30)
    # Performs this required operation before the surrounding flow continues.
    assert game_expiry_for_mode("duel", started_at, linked_expires_at=linked) == linked
    # Performs this required operation before the surrounding flow continues.
    assert game_expiry_for_mode("duel", started_at) == started_at + DUEL_ACTIVE_LIFETIME


# Defines this callable to implement the operation described by its name.
def test_expire_game_record_is_idempotent() -> None:
    # Stores `now` because later steps depend on this value.
    now = datetime(2026, 1, 8, tzinfo=UTC)
    # Stores `game` because later steps depend on this value.
    game = make_game(started_at=now - timedelta(days=8), expires_at=now - timedelta(days=1))

    # Performs this required operation before the surrounding flow continues.
    assert expire_game_record(game, now=now) is True
    # Performs this required operation before the surrounding flow continues.
    assert game.status == "expired"
    # Performs this required operation before the surrounding flow continues.
    assert game.final_score == 0
    # Performs this required operation before the surrounding flow continues.
    assert game.ranked_eligibility == "unranked"
    # Performs this required operation before the surrounding flow continues.
    assert expire_game_record(game, now=now) is False


# Defines this callable to implement the operation described by its name.
async def test_retention_expires_games_and_deletes_events(api: APIContext) -> None:
    # Stores `now` because later steps depend on this value.
    now = datetime.now(UTC)
    # Stores `game` because later steps depend on this value.
    game = make_game(started_at=now - timedelta(days=8), expires_at=now - timedelta(days=1))
    # Stores `event` because later steps depend on this value.
    event = ProductEvent(
        # Stores `client_event_id` because later steps depend on this value.
        client_event_id=uuid.uuid4(),
        # Stores `event_name` because later steps depend on this value.
        event_name="game_started",
        # Stores `anonymous` because later steps depend on this value.
        anonymous=True,
        # Stores `consent_version` because later steps depend on this value.
        consent_version="v1",
        # Stores `release` because later steps depend on this value.
        release="test",
        # Stores `expires_at` because later steps depend on this value.
        expires_at=now - timedelta(seconds=1),
        # Closes the multiline declaration, call, or collection opened above.
    )
    # Scopes this resource so acquisition and cleanup remain paired.
    async with api.sessions() as session:
        # Supplies this required nested value.
        session.add_all([game, event])
        # Performs this required operation before the surrounding flow continues.
        await session.commit()
        # Stores `summary` because later steps depend on this value.
        summary = await run_retention_batch(session, now=now)

    # Performs this required operation before the surrounding flow continues.
    assert summary.game_sessions_expired == 1
    # Performs this required operation before the surrounding flow continues.
    assert summary.product_events_deleted == 1
    # Scopes this resource so acquisition and cleanup remain paired.
    async with api.sessions() as session:
        # Stores `stored_game` because later steps depend on this value.
        stored_game = await session.get(GameSession, game.id)
        # Stores `stored_event` because later steps depend on this value.
        stored_event = await session.get(ProductEvent, event.id)
    # Performs this required operation before the surrounding flow continues.
    assert stored_game is not None
    # Performs this required operation before the surrounding flow continues.
    assert stored_game.status == "expired"
    # Performs this required operation before the surrounding flow continues.
    assert stored_event is None
