# Defers type-annotation evaluation to support modern hints safely.
from __future__ import annotations

# Imports `asyncio` so the module can use that dependency.
import asyncio

# Imports `base64` so the module can use that dependency.
import base64

# Imports `json` so the module can use that dependency.
import json

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

# Imports selected names from `mastermind_api.auth` for use in this module.
from mastermind_api.auth import AuthPrincipal

# Imports selected names from `mastermind_api.config` for use in this module.
from mastermind_api.config import Settings

# Imports selected names from `mastermind_api.crypto` for use in this module.
from mastermind_api.crypto import SecretCipher

# Imports selected names from `mastermind_api.database` for use in this module.
from mastermind_api.database import Base

# Imports selected names from `mastermind_api.errors` for use in this module.
from mastermind_api.errors import APIError

# Imports selected names from `mastermind_api.models` for use in this module.
from mastermind_api.models import (
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

# Imports selected names from `mastermind_api.realtime` for use in this module.
from mastermind_api.realtime import InMemoryBroker, finalize_due_rooms_once

# Imports selected names from `mastermind_api.routers.rooms` for use in this module.
from mastermind_api.routers.rooms import (
    # Supplies this item to the surrounding call or collection.
    _claim_connection,
    # Supplies this item to the surrounding call or collection.
    _release_connection,
    # Supplies this item to the surrounding call or collection.
    _server_event,
    # Supplies this item to the surrounding call or collection.
    _submit_duel_attempt_transaction,
    # Closes the multiline call, declaration, or collection started above.
)

# Imports selected names from `mastermind_api.schemas` for use in this module.
from mastermind_api.schemas import (
    # Supplies this item to the surrounding call or collection.
    CreateChallengeRequest,
    # Supplies this item to the surrounding call or collection.
    CreateGameRequest,
    # Supplies this item to the surrounding call or collection.
    GameConfigSchema,
    # Supplies this item to the surrounding call or collection.
    RoomClientMessage,
    # Closes the multiline call, declaration, or collection started above.
)

# Imports selected names from `mastermind_api.services` for use in this module.
from mastermind_api.services import (
    # Supplies this item to the surrounding call or collection.
    create_challenge,
    # Supplies this item to the surrounding call or collection.
    create_game,
    # Supplies this item to the surrounding call or collection.
    create_room,
    # Supplies this item to the surrounding call or collection.
    join_room,
    # Supplies this item to the surrounding call or collection.
    ready_room,
    # Supplies this item to the surrounding call or collection.
    start_challenge,
    # Supplies this item to the surrounding call or collection.
    start_daily,
    # Supplies this item to the surrounding call or collection.
    submit_attempt,
    # Closes the multiline call, declaration, or collection started above.
)

# Imports selected names from `mastermind_core` for use in this module.
from mastermind_core import GameMode, get_preset

# Imports selected names from `redis.asyncio` for use in this module.
from redis.asyncio import Redis

# Imports selected names from `sqlalchemy` for use in this module.
from sqlalchemy import MetaData, Table, create_engine, func, inspect, select, text

# Imports selected names from `sqlalchemy.ext.asyncio` for use in this module.
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

# Imports selected names from `.conftest` for use in this module.
from .conftest import APIContext, principal


# Defines the `test_alembic_migrates_empty_sqlite_database_and_downgrades` callable and its typed
# interface.
def test_alembic_migrates_empty_sqlite_database_and_downgrades(tmp_path: Path) -> None:
    # Computes and stores `database` for subsequent operations.
    database = tmp_path / "migration.sqlite"
    # Computes and stores `environment` for subsequent operations.
    environment = os.environ | {
        # Associates the `MASTERMIND_ENVIRONMENT` key with its value.
        "MASTERMIND_ENVIRONMENT": "test",
        # Associates the `MASTERMIND_DATABASE_URL` key with its value.
        "MASTERMIND_DATABASE_URL": f"sqlite+aiosqlite:///{database}",
        # Closes the multiline call, declaration, or collection started above.
    }
    # Computes and stores `upgrade` for subsequent operations.
    upgrade = subprocess.run(
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
    assert upgrade.returncode == 0, upgrade.stderr
    # Computes and stores `sync_engine` for subsequent operations.
    sync_engine = create_engine(f"sqlite:///{database}")
    # Computes and stores `tables` for subsequent operations.
    tables = set(inspect(sync_engine).get_table_names())
    # Asserts this invariant so an unexpected test state fails immediately.
    assert {
        # Supplies this item to the surrounding call or collection.
        "profiles",
        # Supplies this item to the surrounding call or collection.
        "game_sessions",
        # Supplies this item to the surrounding call or collection.
        "game_attempts",
        # Supplies this item to the surrounding call or collection.
        "daily_challenges",
        # Supplies this item to the surrounding call or collection.
        "friend_challenges",
        # Supplies this item to the surrounding call or collection.
        "multiplayer_rooms",
        # Supplies this item to the surrounding call or collection.
        "support_requests",
        # Supplies this item to the surrounding call or collection.
        "account_deletion_requests",
        # Supplies this item to the surrounding call or collection.
        "product_events",
        # Supplies this item to the surrounding call or collection.
        "alembic_version",
        # Executes this statement as the next step in the surrounding logic.
    }.issubset(tables)
    # Computes and stores `inspector` for subsequent operations.
    inspector = inspect(sync_engine)
    # Computes and stores `game_checks` for subsequent operations.
    game_checks = {item["name"] for item in inspector.get_check_constraints("game_sessions")}
    # Computes and stores `attempt_checks` for subsequent operations.
    attempt_checks = {item["name"] for item in inspector.get_check_constraints("game_attempts")}
    # Computes and stores `member_columns` for subsequent operations.
    member_columns = {item["name"] for item in inspector.get_columns("multiplayer_members")}
    # Computes and stores `game_columns` for subsequent operations.
    game_columns = {item["name"] for item in inspector.get_columns("game_sessions")}
    # Computes and stores `game_indexes` for subsequent operations.
    game_indexes = {item["name"] for item in inspector.get_indexes("game_sessions")}
    # Asserts this invariant so an unexpected test state fails immediately.
    assert {
        # Supplies this item to the surrounding call or collection.
        "ck_game_sessions_mode_allowed",
        # Supplies this item to the surrounding call or collection.
        "ck_game_sessions_status_allowed",
        # Supplies this item to the surrounding call or collection.
        "ck_game_sessions_attempts_within_limit",
        # Supplies this item to the surrounding call or collection.
        "ck_game_sessions_expiry_after_start",
        # Executes this statement as the next step in the surrounding logic.
    }.issubset(game_checks)
    # Asserts this invariant so an unexpected test state fails immediately.
    assert "ck_game_attempts_feedback_within_code_length" in attempt_checks
    # Asserts this invariant so an unexpected test state fails immediately.
    assert {"ready", "ready_at"}.issubset(member_columns)
    # Asserts this invariant so an unexpected test state fails immediately.
    assert "expires_at" in game_columns
    # Asserts this invariant so an unexpected test state fails immediately.
    assert "ix_game_sessions_status_expires" in game_indexes
    # Acquires this managed resource and guarantees cleanup afterward.
    with sync_engine.connect() as connection:
        # Computes and stores `comeback_count` for subsequent operations.
        comeback_count = connection.scalar(
            # Calls `text` with the supplied values.
            text("SELECT count(*) FROM achievements WHERE key = 'comeback'")
            # Closes the multiline call, declaration, or collection started above.
        )
    # Asserts this invariant so an unexpected test state fails immediately.
    assert comeback_count == 1
    # Calls `sync_engine.dispose` with the supplied values.
    sync_engine.dispose()
    # Computes and stores `downgrade` for subsequent operations.
    downgrade = subprocess.run(
        # Supplies this item to the surrounding call or collection.
        ["alembic", "-c", "apps/api/alembic.ini", "downgrade", "base"],
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
    assert downgrade.returncode == 0, downgrade.stderr


# Defines the `test_retention_migration_backfills_existing_game_deadline` callable and its typed
# interface.
def test_retention_migration_backfills_existing_game_deadline(tmp_path: Path) -> None:
    # Computes and stores `database` for subsequent operations.
    database = tmp_path / "retention-backfill.sqlite"
    # Computes and stores `environment` for subsequent operations.
    environment = os.environ | {
        # Associates the `MASTERMIND_ENVIRONMENT` key with its value.
        "MASTERMIND_ENVIRONMENT": "test",
        # Associates the `MASTERMIND_DATABASE_URL` key with its value.
        "MASTERMIND_DATABASE_URL": f"sqlite+aiosqlite:///{database}",
        # Closes the multiline call, declaration, or collection started above.
    }
    # Computes and stores `repository` for subsequent operations.
    repository = Path(__file__).parents[2]
    # Computes and stores `before_retention` for subsequent operations.
    before_retention = subprocess.run(
        # Supplies this item to the surrounding call or collection.
        ["alembic", "-c", "apps/api/alembic.ini", "upgrade", "20260716_0002"],
        # Provides the `cwd` parameter or keyword argument.
        cwd=repository,
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
    assert before_retention.returncode == 0, before_retention.stderr
    # Computes and stores `engine` for subsequent operations.
    engine = create_engine(f"sqlite:///{database}")
    # Computes and stores `metadata` for subsequent operations.
    metadata = MetaData()
    # Computes and stores `profiles` for subsequent operations.
    profiles = Table("profiles", metadata, autoload_with=engine)
    # Computes and stores `games` for subsequent operations.
    games = Table("game_sessions", metadata, autoload_with=engine)
    # Computes and stores `owner_id` for subsequent operations.
    owner_id = uuid.uuid4()
    # Computes and stores `game_id` for subsequent operations.
    game_id = uuid.uuid4()
    # Computes and stores `started_at` for subsequent operations.
    started_at = datetime(2026, 7, 1, 12, tzinfo=UTC)
    # Computes and stores `config` for subsequent operations.
    config = get_preset("normal")
    # Acquires this managed resource and guarantees cleanup afterward.
    with engine.begin() as connection:
        # Calls `connection.execute` with the supplied values.
        connection.execute(profiles.insert().values(id=owner_id.hex, is_anonymous=False))
        # Calls `connection.execute` with the supplied values.
        connection.execute(
            # Calls `games.insert` with the supplied values.
            games.insert().values(
                # Provides the `id` parameter or keyword argument.
                id=game_id.hex,
                # Provides the `public_id` parameter or keyword argument.
                public_id="existing-retention-game",
                # Provides the `owner_id` parameter or keyword argument.
                owner_id=owner_id.hex,
                # Provides the `mode` parameter or keyword argument.
                mode="solo",
                # Provides the `difficulty` parameter or keyword argument.
                difficulty="normal",
                # Provides the `config` parameter or keyword argument.
                config=config.to_dict(),
                # Provides the `status` parameter or keyword argument.
                status="active",
                # Provides the `rule_set_version` parameter or keyword argument.
                rule_set_version="rules_v1",
                # Provides the `scoring_version` parameter or keyword argument.
                scoring_version="score_v1",
                # Provides the `encrypted_secret` parameter or keyword argument.
                encrypted_secret=b"ciphertext",
                # Provides the `secret_nonce` parameter or keyword argument.
                secret_nonce=b"nonce",
                # Provides the `secret_key_version` parameter or keyword argument.
                secret_key_version="v1",
                # Provides the `attempts_used` parameter or keyword argument.
                attempts_used=0,
                # Provides the `maximum_attempts` parameter or keyword argument.
                maximum_attempts=config.max_attempts,
                # Provides the `started_at` parameter or keyword argument.
                started_at=started_at,
                # Provides the `ranked_eligibility` parameter or keyword argument.
                ranked_eligibility="eligible",
                # Closes the multiline call, declaration, or collection started above.
            )
            # Closes the multiline call, declaration, or collection started above.
        )
    # Calls `engine.dispose` with the supplied values.
    engine.dispose()

    # Computes and stores `upgraded` for subsequent operations.
    upgraded = subprocess.run(
        # Supplies this item to the surrounding call or collection.
        ["alembic", "-c", "apps/api/alembic.ini", "upgrade", "head"],
        # Provides the `cwd` parameter or keyword argument.
        cwd=repository,
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
    assert upgraded.returncode == 0, upgraded.stderr
    # Computes and stores `engine` for subsequent operations.
    engine = create_engine(f"sqlite:///{database}")
    # Acquires this managed resource and guarantees cleanup afterward.
    with engine.connect() as connection:
        # Begins the nested block or multiline expression completed below.
        stored_started, stored_expiry = connection.execute(
            # Calls `text` with the supplied values.
            text("SELECT started_at, expires_at FROM game_sessions WHERE id = :game_id"),
            # Supplies this item to the surrounding call or collection.
            {"game_id": game_id.hex},
            # Executes this statement as the next step in the surrounding logic.
        ).one()
    # Calls `engine.dispose` with the supplied values.
    engine.dispose()
    # Asserts this invariant so an unexpected test state fails immediately.
    assert datetime.fromisoformat(stored_expiry) - datetime.fromisoformat(
        # Executes this statement as the next step in the surrounding logic.
        stored_started
        # Executes this statement as the next step in the surrounding logic.
    ) == timedelta(days=7)

    # Computes and stores `repeated` for subsequent operations.
    repeated = subprocess.run(
        # Supplies this item to the surrounding call or collection.
        ["alembic", "-c", "apps/api/alembic.ini", "upgrade", "head"],
        # Provides the `cwd` parameter or keyword argument.
        cwd=repository,
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
    assert repeated.returncode == 0, repeated.stderr


# Defines the `test_in_memory_broker_fans_out_and_unsubscribes` callable and its typed interface.
async def test_in_memory_broker_fans_out_and_unsubscribes() -> None:
    # Computes and stores `broker` for subsequent operations.
    broker = InMemoryBroker()
    # Acquires this asynchronous managed resource for the nested operation.
    async with broker.subscribe("room") as first, broker.subscribe("room") as second:
        # Waits for this asynchronous operation to complete.
        await broker.publish("room", {"sequence": 1, "type": "presence", "payload": {}})
        # Asserts this invariant so an unexpected test state fails immediately.
        assert await anext(first) == {
            # Associates the `sequence` key with its value.
            "sequence": 1,
            # Associates the `type` key with its value.
            "type": "presence",
            # Associates the `payload` key with its value.
            "payload": {},
            # Closes the multiline call, declaration, or collection started above.
        }
        # Asserts this invariant so an unexpected test state fails immediately.
        assert await anext(second) == {
            # Associates the `sequence` key with its value.
            "sequence": 1,
            # Associates the `type` key with its value.
            "type": "presence",
            # Associates the `payload` key with its value.
            "payload": {},
            # Closes the multiline call, declaration, or collection started above.
        }
    # Waits for this asynchronous operation to complete.
    await broker.close()


# Defines the `test_realtime_envelopes_are_versioned_and_reject_unknown_versions` callable and its
# typed interface.
def test_realtime_envelopes_are_versioned_and_reject_unknown_versions() -> None:
    # Asserts this invariant so an unexpected test state fails immediately.
    assert _server_event("heartbeat_ack", {}) == {
        # Associates the `version` key with its value.
        "version": 1,
        # Associates the `sequence` key with its value.
        "sequence": None,
        # Associates the `type` key with its value.
        "type": "heartbeat_ack",
        # Associates the `payload` key with its value.
        "payload": {},
        # Closes the multiline call, declaration, or collection started above.
    }
    # Asserts this invariant so an unexpected test state fails immediately.
    assert RoomClientMessage.model_validate({"version": 1, "type": "heartbeat"}).version == 1
    # Acquires this managed resource and guarantees cleanup afterward.
    with pytest.raises(ValueError):
        # Calls `RoomClientMessage.model_validate` with the supplied values.
        RoomClientMessage.model_validate({"type": "heartbeat"})
    # Acquires this managed resource and guarantees cleanup afterward.
    with pytest.raises(ValueError):
        # Calls `RoomClientMessage.model_validate` with the supplied values.
        RoomClientMessage.model_validate({"version": 2, "type": "heartbeat"})


# Defines the `test_due_tie_window_is_durably_finalized_and_published` callable and its typed
# interface.
async def test_due_tie_window_is_durably_finalized_and_published(api: APIContext) -> None:
    # Computes and stores `created` for subsequent operations.
    created = await api.client.post("/v1/rooms", json={"difficulty": "normal"})
    # Asserts this invariant so an unexpected test state fails immediately.
    assert created.status_code == 201, created.text
    # Computes and stores `room_id` for subsequent operations.
    room_id = uuid.UUID(created.json()["id"])
    # Computes and stores `now` for subsequent operations.
    now = datetime.now(UTC)
    # Acquires this asynchronous managed resource for the nested operation.
    async with api.sessions() as session:
        # Computes and stores `room` for subsequent operations.
        room = await session.get(MultiplayerRoom, room_id)
        # Asserts this invariant so an unexpected test state fails immediately.
        assert room is not None
        # Computes and stores `room.status` for subsequent operations.
        room.status = "active"
        # Computes and stores `room.winner_id` for subsequent operations.
        room.winner_id = api.current["principal"].user_id
        # Computes and stores `room.winner_at` for subsequent operations.
        room.winner_at = now - timedelta(seconds=1)
        # Computes and stores `room.tie_deadline` for subsequent operations.
        room.tie_deadline = now - timedelta(milliseconds=1)
        # Waits for this asynchronous operation to complete.
        await session.commit()

    # Computes and stores `broker` for subsequent operations.
    broker = InMemoryBroker()
    # Acquires this asynchronous managed resource for the nested operation.
    async with broker.subscribe(str(room_id)) as events:
        # Asserts this invariant so an unexpected test state fails immediately.
        assert await finalize_due_rooms_once(api.sessions, broker, now=now) == 1
        # Computes and stores `published` for subsequent operations.
        published = await asyncio.wait_for(anext(events), timeout=1)
    # Asserts this invariant so an unexpected test state fails immediately.
    assert published["version"] == 1
    # Asserts this invariant so an unexpected test state fails immediately.
    assert published["type"] == "room_completed"
    # Asserts this invariant so an unexpected test state fails immediately.
    assert published["payload"]["reason"] == "tie_window_elapsed"
    # Acquires this asynchronous managed resource for the nested operation.
    async with api.sessions() as session:
        # Computes and stores `room` for subsequent operations.
        room = await session.get(MultiplayerRoom, room_id)
        # Computes and stores `persisted` for subsequent operations.
        persisted = await session.scalar(
            # Calls `select` with the supplied values.
            select(MultiplayerEvent).where(
                # Supplies this item to the surrounding call or collection.
                MultiplayerEvent.room_id == room_id,
                # Supplies this item to the surrounding call or collection.
                MultiplayerEvent.event_type == "room_completed",
                # Closes the multiline call, declaration, or collection started above.
            )
            # Closes the multiline call, declaration, or collection started above.
        )
        # Asserts this invariant so an unexpected test state fails immediately.
        assert room is not None and room.status == "completed"
        # Asserts this invariant so an unexpected test state fails immediately.
        assert persisted is not None
    # Asserts this invariant so an unexpected test state fails immediately.
    assert await finalize_due_rooms_once(api.sessions, broker, now=now) == 0
    # Waits for this asynchronous operation to complete.
    await broker.close()


# Applies `@pytest.mark.postgres` to configure the declaration immediately below.
@pytest.mark.postgres
# Applies `@pytest.mark.skipif(` to configure the declaration immediately below.
@pytest.mark.skipif(
    # Supplies this item to the surrounding call or collection.
    not os.getenv("MASTERMIND_TEST_POSTGRES_URL"),
    # Provides the `reason` parameter or keyword argument.
    reason="Set MASTERMIND_TEST_POSTGRES_URL to an isolated empty PostgreSQL database.",
    # Closes the multiline call, declaration, or collection started above.
)
# Defines the `test_real_postgres_migration_and_constraints` callable and its typed interface.
async def test_real_postgres_migration_and_constraints() -> None:
    # Computes and stores `url` for subsequent operations.
    url = os.environ["MASTERMIND_TEST_POSTGRES_URL"]
    # Computes and stores `environment` for subsequent operations.
    environment = os.environ | {
        # Associates the `MASTERMIND_ENVIRONMENT` key with its value.
        "MASTERMIND_ENVIRONMENT": "test",
        # Associates the `MASTERMIND_DATABASE_URL` key with its value.
        "MASTERMIND_DATABASE_URL": url,
        # Closes the multiline call, declaration, or collection started above.
    }
    # Computes and stores `result` for subsequent operations.
    result = await asyncio.to_thread(
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
    assert result.returncode == 0, result.stderr
    # Computes and stores `engine` for subsequent operations.
    engine = create_async_engine(url)
    # Acquires this asynchronous managed resource for the nested operation.
    async with engine.connect() as connection:
        # Computes and stores `privileges` for subsequent operations.
        privileges = (
            # Waits for this asynchronous operation to complete.
            await connection.execute(
                # Calls `text` with the supplied values.
                text(
                    # Executes this statement as the next step in the surrounding logic.
                    "SELECT "
                    # Executes this statement as the next step in the surrounding logic.
                    "has_table_privilege('mastermind_runtime', 'profiles', 'UPDATE'), "
                    # Executes this statement as the next step in the surrounding logic.
                    "has_table_privilege('mastermind_runtime', 'achievements', 'UPDATE'), "
                    # Executes this statement as the next step in the surrounding logic.
                    "has_table_privilege('mastermind_runtime', 'audit_events', 'DELETE'), "
                    # Executes this statement as the next step in the surrounding logic.
                    "has_table_privilege('mastermind_runtime', 'product_events', 'SELECT'), "
                    # Executes this statement as the next step in the surrounding logic.
                    "has_table_privilege('mastermind_retention', 'game_sessions', 'DELETE'), "
                    # Executes this statement as the next step in the surrounding logic.
                    "has_table_privilege('mastermind_retention', 'product_events', 'DELETE'), "
                    # Executes this statement as the next step in the surrounding logic.
                    "has_table_privilege('mastermind_retention', 'audit_events', 'DELETE')"
                    # Closes the multiline call, declaration, or collection started above.
                )
                # Closes the multiline call, declaration, or collection started above.
            )
            # Executes this statement as the next step in the surrounding logic.
        ).one()
    # Waits for this asynchronous operation to complete.
    await engine.dispose()
    # Asserts this invariant so an unexpected test state fails immediately.
    assert privileges == (True, False, False, False, True, True, False)


# Applies `@pytest.mark.postgres` to configure the declaration immediately below.
@pytest.mark.postgres
# Applies `@pytest.mark.skipif(` to configure the declaration immediately below.
@pytest.mark.skipif(
    # Supplies this item to the surrounding call or collection.
    not os.getenv("MASTERMIND_TEST_POSTGRES_URL"),
    # Provides the `reason` parameter or keyword argument.
    reason="Set MASTERMIND_TEST_POSTGRES_URL to an isolated disposable PostgreSQL database.",
    # Closes the multiline call, declaration, or collection started above.
)
# Defines the `test_real_postgres_creates_room_before_foreign_key_member` callable and its typed
# interface.
async def test_real_postgres_creates_room_before_foreign_key_member() -> None:
    # Computes and stores `settings` for subsequent operations.
    settings = Settings(
        # Provides the `environment` parameter or keyword argument.
        environment="test",
        # Provides the `database_url` parameter or keyword argument.
        database_url=os.environ["MASTERMIND_TEST_POSTGRES_URL"],
        # Provides the `secret_encryption_keys` parameter or keyword argument.
        secret_encryption_keys=json.dumps({"v1": base64.b64encode(b"r" * 32).decode()}),
        # Provides the `secret_active_key_version` parameter or keyword argument.
        secret_active_key_version="v1",
        # Provides the `public_identifier_hmac_key` parameter or keyword argument.
        public_identifier_hmac_key="i" * 32,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `engine` for subsequent operations.
    engine = create_async_engine(settings.database_url)
    # Computes and stores `sessions` for subsequent operations.
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    # Acquires this asynchronous managed resource for the nested operation.
    async with engine.begin() as connection:
        # Waits for this asynchronous operation to complete.
        await connection.run_sync(Base.metadata.drop_all)
        # Waits for this asynchronous operation to complete.
        await connection.run_sync(Base.metadata.create_all)
    # Computes and stores `player` for subsequent operations.
    player = principal()
    # Acquires this asynchronous managed resource for the nested operation.
    async with sessions() as session:
        # Begins the nested block or multiline expression completed below.
        room, room_code = await create_room(
            # Supplies this item to the surrounding call or collection.
            session,
            # Supplies this item to the surrounding call or collection.
            player,
            # Supplies this item to the surrounding call or collection.
            "easy",
            # Calls `SecretCipher.from_settings` with the supplied values.
            SecretCipher.from_settings(settings),
            # Supplies this item to the surrounding call or collection.
            settings,
            # Supplies this item to the surrounding call or collection.
            "postgres-room-create-0001",
            # Closes the multiline call, declaration, or collection started above.
        )
        # Computes and stores `member_count` for subsequent operations.
        member_count = await session.scalar(
            # Calls `select` with the supplied values.
            select(func.count(MultiplayerMember.id)).where(MultiplayerMember.room_id == room.id)
            # Closes the multiline call, declaration, or collection started above.
        )
    # Asserts this invariant so an unexpected test state fails immediately.
    assert room_code
    # Asserts this invariant so an unexpected test state fails immediately.
    assert member_count == 1
    # Acquires this asynchronous managed resource for the nested operation.
    async with engine.begin() as connection:
        # Waits for this asynchronous operation to complete.
        await connection.run_sync(Base.metadata.drop_all)
    # Waits for this asynchronous operation to complete.
    await engine.dispose()


# Applies `@pytest.mark.skipif(` to configure the declaration immediately below.
@pytest.mark.skipif(
    # Supplies this item to the surrounding call or collection.
    not os.getenv("MASTERMIND_TEST_REDIS_URL"),
    # Provides the `reason` parameter or keyword argument.
    reason="Set MASTERMIND_TEST_REDIS_URL to an isolated Redis database.",
    # Closes the multiline call, declaration, or collection started above.
)
# Defines the `test_real_redis_ticket_getdel_is_atomic` callable and its typed interface.
async def test_real_redis_ticket_getdel_is_atomic() -> None:
    # Computes and stores `redis` for subsequent operations.
    redis = Redis.from_url(os.environ["MASTERMIND_TEST_REDIS_URL"], decode_responses=True)
    # Computes and stores `key` for subsequent operations.
    key = f"mastermind:test:ticket:{uuid.uuid4()}"
    # Waits for this asynchronous operation to complete.
    await redis.setex(key, 30, "ticket-payload")
    # Executes this statement as the next step in the surrounding logic.
    first, second = await asyncio.gather(redis.getdel(key), redis.getdel(key))
    # Asserts this invariant so an unexpected test state fails immediately.
    assert sorted([first, second], key=lambda item: item is None) == ["ticket-payload", None]
    # Waits for this asynchronous operation to complete.
    await redis.aclose()


# Applies `@pytest.mark.skipif(` to configure the declaration immediately below.
@pytest.mark.skipif(
    # Supplies this item to the surrounding call or collection.
    not os.getenv("MASTERMIND_TEST_REDIS_URL"),
    # Provides the `reason` parameter or keyword argument.
    reason="Set MASTERMIND_TEST_REDIS_URL to an isolated Redis database.",
    # Closes the multiline call, declaration, or collection started above.
)
# Defines the `test_real_redis_connection_cap_counts_tabs_and_releases` callable and its typed
# interface.
async def test_real_redis_connection_cap_counts_tabs_and_releases() -> None:
    # Computes and stores `redis` for subsequent operations.
    redis = Redis.from_url(os.environ["MASTERMIND_TEST_REDIS_URL"], decode_responses=True)
    # Computes and stores `user` for subsequent operations.
    user = principal()
    # Computes and stores `settings` for subsequent operations.
    settings = Settings(
        # Provides the `environment` parameter or keyword argument.
        environment="test",
        # Provides the `websocket_user_connection_limit` parameter or keyword argument.
        websocket_user_connection_limit=2,
        # Provides the `websocket_ip_connection_limit` parameter or keyword argument.
        websocket_ip_connection_limit=3,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `claimed` for subsequent operations.
    claimed: list[tuple[str, str, str]] = []
    # Iterates through the supplied values for the nested operation.
    for token in ("tab-one", "tab-two"):
        # Begins the nested block or multiline expression completed below.
        allowed, count, user_key, ip_key = await _claim_connection(
            # Executes this statement as the next step in the surrounding logic.
            redis,
            # Supplies this item to the surrounding call or collection.
            user,
            # Supplies this string to the surrounding call or collection.
            "192.0.2.5",
            # Supplies this item to the surrounding call or collection.
            token,
            # Supplies this item to the surrounding call or collection.
            settings,
            # Closes the multiline call, declaration, or collection started above.
        )
        # Asserts this invariant so an unexpected test state fails immediately.
        assert allowed is True
        # Calls `claimed.append` with the supplied values.
        claimed.append((user_key, ip_key, token))
    # Asserts this invariant so an unexpected test state fails immediately.
    assert count == 2
    # Executes this statement as the next step in the surrounding logic.
    denied, count, _, _ = await _claim_connection(redis, user, "192.0.2.5", "tab-three", settings)
    # Asserts this invariant so an unexpected test state fails immediately.
    assert denied is False and count == 2
    # Computes and stores `remaining` for subsequent operations.
    remaining = await _release_connection(redis, *claimed[0])
    # Asserts this invariant so an unexpected test state fails immediately.
    assert remaining == 1
    # Computes and stores `remaining` for subsequent operations.
    remaining = await _release_connection(redis, *claimed[1])
    # Asserts this invariant so an unexpected test state fails immediately.
    assert remaining == 0
    # Waits for this asynchronous operation to complete.
    await redis.aclose()


# Applies `@pytest.mark.postgres` to configure the declaration immediately below.
@pytest.mark.postgres
# Applies `@pytest.mark.skipif(` to configure the declaration immediately below.
@pytest.mark.skipif(
    # Supplies this item to the surrounding call or collection.
    not os.getenv("MASTERMIND_TEST_POSTGRES_URL"),
    # Provides the `reason` parameter or keyword argument.
    reason="Set MASTERMIND_TEST_POSTGRES_URL to an isolated disposable PostgreSQL database.",
    # Closes the multiline call, declaration, or collection started above.
)
# Defines the `test_real_postgres_serializes_concurrent_attempts` callable and its typed interface.
async def test_real_postgres_serializes_concurrent_attempts() -> None:
    # Computes and stores `settings` for subsequent operations.
    settings = Settings(
        # Provides the `environment` parameter or keyword argument.
        environment="test",
        # Provides the `database_url` parameter or keyword argument.
        database_url=os.environ["MASTERMIND_TEST_POSTGRES_URL"],
        # Provides the `secret_encryption_keys` parameter or keyword argument.
        secret_encryption_keys=json.dumps({"v1": base64.b64encode(b"p" * 32).decode()}),
        # Provides the `secret_active_key_version` parameter or keyword argument.
        secret_active_key_version="v1",
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `engine` for subsequent operations.
    engine = create_async_engine(settings.database_url)
    # Computes and stores `sessions` for subsequent operations.
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    # Acquires this asynchronous managed resource for the nested operation.
    async with engine.begin() as connection:
        # Waits for this asynchronous operation to complete.
        await connection.run_sync(Base.metadata.drop_all)
        # Waits for this asynchronous operation to complete.
        await connection.run_sync(Base.metadata.create_all)
    # Computes and stores `user` for subsequent operations.
    user = principal()
    # Computes and stores `cipher` for subsequent operations.
    cipher = SecretCipher.from_settings(settings)
    # Acquires this asynchronous managed resource for the nested operation.
    async with sessions() as session:
        # Computes and stores `game` for subsequent operations.
        game = await create_game(
            # Supplies this item to the surrounding call or collection.
            session,
            # Supplies this item to the surrounding call or collection.
            user,
            # Calls `CreateGameRequest` with the supplied values.
            CreateGameRequest(
                # Provides the `mode` parameter or keyword argument.
                mode=GameMode.PASS_AND_PLAY,
                # Computes and stores `config` for subsequent operations.
                config=GameConfigSchema(
                    # Provides the `colours` parameter or keyword argument.
                    colours=list("RBGYW"),
                    # Provides the `code_length` parameter or keyword argument.
                    code_length=4,
                    # Provides the `max_attempts` parameter or keyword argument.
                    max_attempts=4,
                    # Provides the `duplicates_allowed` parameter or keyword argument.
                    duplicates_allowed=True,
                    # Provides the `code_maker` parameter or keyword argument.
                    code_maker="human",
                    # Closes the multiline call, declaration, or collection started above.
                ),
                # Provides the `secret` parameter or keyword argument.
                secret=list("RBGY"),
                # Closes the multiline call, declaration, or collection started above.
            ),
            # Supplies this item to the surrounding call or collection.
            cipher,
            # Closes the multiline call, declaration, or collection started above.
        )
        # Computes and stores `game_id` for subsequent operations.
        game_id = game.public_id

    # Defines the `attempt` callable and its typed interface.
    async def attempt(guess: list[str], key: str) -> int:
        # Acquires this asynchronous managed resource for the nested operation.
        async with sessions() as session:
            # Computes and stores `updated` for subsequent operations.
            updated = await submit_attempt(
                # Executes this statement as the next step in the surrounding logic.
                session,
                # Supplies this item to the surrounding call or collection.
                user,
                # Supplies this item to the surrounding call or collection.
                game_id,
                # Supplies this item to the surrounding call or collection.
                guess,
                # Supplies this item to the surrounding call or collection.
                key,
                # Supplies this item to the surrounding call or collection.
                f"test:{key}",
                # Supplies this item to the surrounding call or collection.
                cipher,
                # Closes the multiline call, declaration, or collection started above.
            )
            # Returns this result to the caller and ends the current function.
            return updated.attempts_used

    # Computes and stores `used` for subsequent operations.
    used = await asyncio.gather(
        # Calls `attempt` with the supplied values.
        attempt(list("WWWW"), "postgres-attempt-0001"),
        # Calls `attempt` with the supplied values.
        attempt(list("WRRR"), "postgres-attempt-0002"),
        # Closes the multiline call, declaration, or collection started above.
    )
    # Asserts this invariant so an unexpected test state fails immediately.
    assert sorted(used) == [1, 2]
    # Acquires this asynchronous managed resource for the nested operation.
    async with sessions() as session:
        # Asserts this invariant so an unexpected test state fails immediately.
        assert await session.scalar(select(func.count(GameAttempt.id))) == 2
        # Computes and stores `numbers` for subsequent operations.
        numbers = list(await session.scalars(select(GameAttempt.attempt_number)))
        # Asserts this invariant so an unexpected test state fails immediately.
        assert sorted(numbers) == [1, 2]
    # Acquires this asynchronous managed resource for the nested operation.
    async with engine.begin() as connection:
        # Waits for this asynchronous operation to complete.
        await connection.run_sync(Base.metadata.drop_all)
    # Waits for this asynchronous operation to complete.
    await engine.dispose()


# Applies `@pytest.mark.postgres` to configure the declaration immediately below.
@pytest.mark.postgres
# Applies `@pytest.mark.skipif(` to configure the declaration immediately below.
@pytest.mark.skipif(
    # Supplies this item to the surrounding call or collection.
    not os.getenv("MASTERMIND_TEST_POSTGRES_URL"),
    # Provides the `reason` parameter or keyword argument.
    reason="Set MASTERMIND_TEST_POSTGRES_URL to an isolated disposable PostgreSQL database.",
    # Closes the multiline call, declaration, or collection started above.
)
# Defines the `test_real_postgres_serializes_simultaneous_duel_solves_as_a_tie` callable and its
# typed interface.
async def test_real_postgres_serializes_simultaneous_duel_solves_as_a_tie() -> None:
    # Computes and stores `settings` for subsequent operations.
    settings = Settings(
        # Provides the `environment` parameter or keyword argument.
        environment="test",
        # Provides the `database_url` parameter or keyword argument.
        database_url=os.environ["MASTERMIND_TEST_POSTGRES_URL"],
        # Provides the `secret_encryption_keys` parameter or keyword argument.
        secret_encryption_keys=json.dumps({"v1": base64.b64encode(b"p" * 32).decode()}),
        # Provides the `secret_active_key_version` parameter or keyword argument.
        secret_active_key_version="v1",
        # Provides the `public_identifier_hmac_key` parameter or keyword argument.
        public_identifier_hmac_key="i" * 32,
        # Provides the `room_tie_window_ms` parameter or keyword argument.
        room_tie_window_ms=2000,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `engine` for subsequent operations.
    engine = create_async_engine(settings.database_url)
    # Computes and stores `sessions` for subsequent operations.
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    # Acquires this asynchronous managed resource for the nested operation.
    async with engine.begin() as connection:
        # Waits for this asynchronous operation to complete.
        await connection.run_sync(Base.metadata.drop_all)
        # Waits for this asynchronous operation to complete.
        await connection.run_sync(Base.metadata.create_all)
    # Computes and stores `host` for subsequent operations.
    host = principal()
    # Computes and stores `guest` for subsequent operations.
    guest = principal()
    # Computes and stores `cipher` for subsequent operations.
    cipher = SecretCipher.from_settings(settings)
    # Acquires this asynchronous managed resource for the nested operation.
    async with sessions() as session:
        # Executes this statement as the next step in the surrounding logic.
        room, room_code = await create_room(session, host, "normal", cipher, settings)
        # Computes and stores `room_id` for subsequent operations.
        room_id = room.id
    # Acquires this asynchronous managed resource for the nested operation.
    async with sessions() as session:
        # Waits for this asynchronous operation to complete.
        await join_room(session, guest, room_code, cipher, settings)
    # Acquires this asynchronous managed resource for the nested operation.
    async with sessions() as session:
        # Waits for this asynchronous operation to complete.
        await ready_room(session, host, room_id, cipher)
    # Acquires this asynchronous managed resource for the nested operation.
    async with sessions() as session:
        # Waits for this asynchronous operation to complete.
        await ready_room(session, guest, room_id, cipher)
        # Computes and stores `stored_room` for subsequent operations.
        stored_room = await session.get(MultiplayerRoom, room_id)
        # Asserts this invariant so an unexpected test state fails immediately.
        assert stored_room is not None
        # Computes and stores `secret` for subsequent operations.
        secret = cipher.decrypt(
            # Supplies this item to the surrounding call or collection.
            stored_room.encrypted_secret,
            # Supplies this item to the surrounding call or collection.
            stored_room.secret_nonce,
            # Supplies this item to the surrounding call or collection.
            stored_room.secret_key_version,
            # Provides the `context` parameter or keyword argument.
            context=f"room:{room_id}:rules_v1",
            # Closes the multiline call, declaration, or collection started above.
        )

    # Defines the `attempt` callable and its typed interface.
    async def attempt(user: AuthPrincipal, key: str) -> tuple[str, bool]:
        # Acquires this asynchronous managed resource for the nested operation.
        async with sessions() as session:
            # Computes and stores `outcome` for subsequent operations.
            outcome = await _submit_duel_attempt_transaction(
                # Supplies this item to the surrounding call or collection.
                session,
                # Supplies this item to the surrounding call or collection.
                room_id,
                # Supplies this item to the surrounding call or collection.
                user,
                # Calls `list` with the supplied values.
                list(secret),
                # Supplies this item to the surrounding call or collection.
                key,
                # Supplies this item to the surrounding call or collection.
                f"test:{key}",
                # Supplies this item to the surrounding call or collection.
                cipher,
                # Supplies this item to the surrounding call or collection.
                settings,
                # Closes the multiline call, declaration, or collection started above.
            )
            # Returns this result to the caller and ends the current function.
            return outcome.game.status, outcome.completion_event is not None

    # Computes and stores `used` for subsequent operations.
    used = await asyncio.wait_for(
        # Calls `asyncio.gather` with the supplied values.
        asyncio.gather(
            # Calls `attempt` with the supplied values.
            attempt(host, "duel-postgres-attempt-0001"),
            # Calls `attempt` with the supplied values.
            attempt(guest, "duel-postgres-attempt-0002"),
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Provides the `timeout` parameter or keyword argument.
        timeout=5,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Asserts this invariant so an unexpected test state fails immediately.
    assert sorted(used, key=lambda item: item[1]) == [("won", False), ("won", True)]
    # Acquires this asynchronous managed resource for the nested operation.
    async with sessions() as session:
        # Computes and stores `attempts` for subsequent operations.
        attempts = await session.scalar(
            # Calls `select` with the supplied values.
            select(func.count(GameAttempt.id))
            # Executes this statement as the next step in the surrounding logic.
            .join(GameSession)
            # Executes this statement as the next step in the surrounding logic.
            .where(GameSession.room_id == room_id)
            # Closes the multiline call, declaration, or collection started above.
        )
        # Asserts this invariant so an unexpected test state fails immediately.
        assert attempts == 2
        # Computes and stores `completed_room` for subsequent operations.
        completed_room = await session.get(MultiplayerRoom, room_id)
        # Computes and stores `game_statuses` for subsequent operations.
        game_statuses = list(
            # Waits for this asynchronous operation to complete.
            await session.scalars(
                # Calls `select` with the supplied values.
                select(GameSession.status)
                # Executes this statement as the next step in the surrounding logic.
                .where(GameSession.room_id == room_id)
                # Executes this statement as the next step in the surrounding logic.
                .order_by(GameSession.id)
                # Closes the multiline call, declaration, or collection started above.
            )
            # Closes the multiline call, declaration, or collection started above.
        )
        # Computes and stores `completion_events` for subsequent operations.
        completion_events = await session.scalar(
            # Calls `select` with the supplied values.
            select(func.count(MultiplayerEvent.id)).where(
                # Supplies this item to the surrounding call or collection.
                MultiplayerEvent.room_id == room_id,
                # Supplies this item to the surrounding call or collection.
                MultiplayerEvent.event_type == "room_completed",
                # Closes the multiline call, declaration, or collection started above.
            )
            # Closes the multiline call, declaration, or collection started above.
        )
        # Asserts this invariant so an unexpected test state fails immediately.
        assert completed_room is not None
        # Asserts this invariant so an unexpected test state fails immediately.
        assert completed_room.status == "completed"
        # Asserts this invariant so an unexpected test state fails immediately.
        assert completed_room.is_tie is True
        # Asserts this invariant so an unexpected test state fails immediately.
        assert completed_room.winner_id is None
        # Asserts this invariant so an unexpected test state fails immediately.
        assert game_statuses == ["won", "won"]
        # Asserts this invariant so an unexpected test state fails immediately.
        assert completion_events == 1
    # Acquires this asynchronous managed resource for the nested operation.
    async with engine.begin() as connection:
        # Waits for this asynchronous operation to complete.
        await connection.run_sync(Base.metadata.drop_all)
    # Waits for this asynchronous operation to complete.
    await engine.dispose()


# Applies `@pytest.mark.postgres` to configure the declaration immediately below.
@pytest.mark.postgres
# Applies `@pytest.mark.skipif(` to configure the declaration immediately below.
@pytest.mark.skipif(
    # Supplies this item to the surrounding call or collection.
    not os.getenv("MASTERMIND_TEST_POSTGRES_URL"),
    # Provides the `reason` parameter or keyword argument.
    reason="Set MASTERMIND_TEST_POSTGRES_URL to an isolated disposable PostgreSQL database.",
    # Closes the multiline call, declaration, or collection started above.
)
# Defines the `test_real_postgres_recovers_concurrent_official_starts` callable and its typed
# interface.
async def test_real_postgres_recovers_concurrent_official_starts() -> None:
    # Computes and stores `settings` for subsequent operations.
    settings = Settings(
        # Provides the `environment` parameter or keyword argument.
        environment="test",
        # Provides the `database_url` parameter or keyword argument.
        database_url=os.environ["MASTERMIND_TEST_POSTGRES_URL"],
        # Provides the `secret_encryption_keys` parameter or keyword argument.
        secret_encryption_keys=json.dumps({"v1": base64.b64encode(b"p" * 32).decode()}),
        # Provides the `secret_active_key_version` parameter or keyword argument.
        secret_active_key_version="v1",
        # Provides the `daily_hmac_key` parameter or keyword argument.
        daily_hmac_key="d" * 32,
        # Provides the `public_identifier_hmac_key` parameter or keyword argument.
        public_identifier_hmac_key="i" * 32,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `engine` for subsequent operations.
    engine = create_async_engine(settings.database_url)
    # Computes and stores `sessions` for subsequent operations.
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    # Acquires this asynchronous managed resource for the nested operation.
    async with engine.begin() as connection:
        # Waits for this asynchronous operation to complete.
        await connection.run_sync(Base.metadata.drop_all)
        # Waits for this asynchronous operation to complete.
        await connection.run_sync(Base.metadata.create_all)
    # Computes and stores `cipher` for subsequent operations.
    cipher = SecretCipher.from_settings(settings)
    # Computes and stores `daily_player` for subsequent operations.
    daily_player = principal()

    # Defines the `daily_start` callable and its typed interface.
    async def daily_start() -> str:
        # Acquires this asynchronous managed resource for the nested operation.
        async with sessions() as session:
            # Returns this result to the caller and ends the current function.
            return (await start_daily(session, daily_player, settings, cipher)).public_id

    # Computes and stores `daily_ids` for subsequent operations.
    daily_ids = await asyncio.gather(daily_start(), daily_start())
    # Asserts this invariant so an unexpected test state fails immediately.
    assert daily_ids[0] == daily_ids[1]

    # Computes and stores `creator` for subsequent operations.
    creator = principal()
    # Acquires this asynchronous managed resource for the nested operation.
    async with sessions() as session:
        # Begins the nested block or multiline expression completed below.
        challenge, _ = await create_challenge(
            # Supplies this item to the surrounding call or collection.
            session,
            # Supplies this item to the surrounding call or collection.
            creator,
            # Calls `CreateChallengeRequest` with the supplied values.
            CreateChallengeRequest(
                # Provides the `difficulty` parameter or keyword argument.
                difficulty="normal",
                # Provides the `secret` parameter or keyword argument.
                secret=list("RBGY"),
                # Provides the `idempotency_key` parameter or keyword argument.
                idempotency_key="postgres-friend-create-0001",
                # Closes the multiline call, declaration, or collection started above.
            ),
            # Supplies this item to the surrounding call or collection.
            cipher,
            # Supplies this item to the surrounding call or collection.
            settings,
            # Closes the multiline call, declaration, or collection started above.
        )
    # Computes and stores `participant` for subsequent operations.
    participant = principal()

    # Defines the `friend_start` callable and its typed interface.
    async def friend_start() -> str:
        # Acquires this asynchronous managed resource for the nested operation.
        async with sessions() as session:
            # Returns this result to the caller and ends the current function.
            return (await start_challenge(session, participant, challenge, cipher)).public_id

    # Computes and stores `friend_ids` for subsequent operations.
    friend_ids = await asyncio.gather(friend_start(), friend_start())
    # Asserts this invariant so an unexpected test state fails immediately.
    assert friend_ids[0] == friend_ids[1]

    # Computes and stores `idempotent_player` for subsequent operations.
    idempotent_player = principal()

    # Defines the `keyed_game` callable and its typed interface.
    async def keyed_game(secret: str) -> str:
        # Acquires this asynchronous managed resource for the nested operation.
        async with sessions() as session:
            # Computes and stores `game` for subsequent operations.
            game = await create_game(
                # Supplies this item to the surrounding call or collection.
                session,
                # Supplies this item to the surrounding call or collection.
                idempotent_player,
                # Calls `CreateGameRequest` with the supplied values.
                CreateGameRequest(
                    # Provides the `mode` parameter or keyword argument.
                    mode=GameMode.PASS_AND_PLAY,
                    # Computes and stores `config` for subsequent operations.
                    config=GameConfigSchema(
                        # Provides the `colours` parameter or keyword argument.
                        colours=list("RBGYW"),
                        # Provides the `code_length` parameter or keyword argument.
                        code_length=4,
                        # Provides the `max_attempts` parameter or keyword argument.
                        max_attempts=4,
                        # Provides the `duplicates_allowed` parameter or keyword argument.
                        duplicates_allowed=True,
                        # Provides the `code_maker` parameter or keyword argument.
                        code_maker="human",
                        # Closes the multiline call, declaration, or collection started above.
                    ),
                    # Provides the `secret` parameter or keyword argument.
                    secret=list(secret),
                    # Provides the `idempotency_key` parameter or keyword argument.
                    idempotency_key="postgres-game-create-0001",
                    # Closes the multiline call, declaration, or collection started above.
                ),
                # Supplies this item to the surrounding call or collection.
                cipher,
                # Provides the `settings` parameter or keyword argument.
                settings=settings,
                # Closes the multiline call, declaration, or collection started above.
            )
            # Returns this result to the caller and ends the current function.
            return game.public_id

    # Computes and stores `keyed_results` for subsequent operations.
    keyed_results = await asyncio.gather(
        # Calls `keyed_game` with the supplied values.
        keyed_game("RBGY"),
        # Calls `keyed_game` with these supplied values.
        keyed_game("WWWW"),
        # Provides the `return_exceptions` value to the surrounding call.
        return_exceptions=True,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Asserts this invariant so an unexpected test state fails immediately.
    assert sum(isinstance(result, str) for result in keyed_results) == 1
    # Computes and stores `conflicts` for subsequent operations.
    conflicts = [result for result in keyed_results if isinstance(result, APIError)]
    # Asserts this invariant so an unexpected test state fails immediately.
    assert len(conflicts) == 1 and conflicts[0].code == "IDEMPOTENCY_KEY_REUSED"
    # Acquires this asynchronous managed resource for the nested operation.
    async with sessions() as session:
        # Computes and stores `official_daily` for subsequent operations.
        official_daily = await session.scalar(
            # Calls `select` with the supplied values.
            select(func.count(GameSession.id)).where(
                # Supplies this item to the surrounding call or collection.
                GameSession.owner_id == daily_player.user_id,
                # Calls `GameSession.daily_challenge_id.is_not` with the supplied values.
                GameSession.daily_challenge_id.is_not(None),
                # Closes the multiline call, declaration, or collection started above.
            )
            # Closes the multiline call, declaration, or collection started above.
        )
        # Computes and stores `official_friend` for subsequent operations.
        official_friend = await session.scalar(
            # Calls `select` with the supplied values.
            select(func.count(GameSession.id)).where(
                # Supplies this item to the surrounding call or collection.
                GameSession.owner_id == participant.user_id,
                # Calls `GameSession.friend_challenge_id.is_not` with the supplied values.
                GameSession.friend_challenge_id.is_not(None),
                # Closes the multiline call, declaration, or collection started above.
            )
            # Closes the multiline call, declaration, or collection started above.
        )
        # Asserts this invariant so an unexpected test state fails immediately.
        assert official_daily == official_friend == 1
        # Computes and stores `keyed_count` for subsequent operations.
        keyed_count = await session.scalar(
            # Calls `select` with the supplied values.
            select(func.count(GameSession.id)).where(
                # Supplies this item to the surrounding call or collection.
                GameSession.owner_id == idempotent_player.user_id,
                # Supplies this item to the surrounding call or collection.
                GameSession.creation_idempotency_key == "postgres-game-create-0001",
                # Closes the multiline call, declaration, or collection started above.
            )
            # Closes the multiline call, declaration, or collection started above.
        )
        # Asserts this invariant so an unexpected test state fails immediately.
        assert keyed_count == 1
    # Acquires this asynchronous managed resource for the nested operation.
    async with engine.begin() as connection:
        # Waits for this asynchronous operation to complete.
        await connection.run_sync(Base.metadata.drop_all)
    # Waits for this asynchronous operation to complete.
    await engine.dispose()
