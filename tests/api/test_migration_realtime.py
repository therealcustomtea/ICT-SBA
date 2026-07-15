from __future__ import annotations

import asyncio
import base64
import json
import os
import subprocess
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from mastermind_api.auth import AuthPrincipal
from mastermind_api.config import Settings
from mastermind_api.crypto import SecretCipher
from mastermind_api.database import Base
from mastermind_api.errors import APIError
from mastermind_api.models import (
    GameAttempt,
    GameSession,
    MultiplayerEvent,
    MultiplayerMember,
    MultiplayerRoom,
)
from mastermind_api.realtime import InMemoryBroker, finalize_due_rooms_once
from mastermind_api.routers.rooms import (
    _claim_connection,
    _release_connection,
    _server_event,
    _submit_duel_attempt_transaction,
)
from mastermind_api.schemas import (
    CreateChallengeRequest,
    CreateGameRequest,
    GameConfigSchema,
    RoomClientMessage,
)
from mastermind_api.services import (
    create_challenge,
    create_game,
    create_room,
    join_room,
    ready_room,
    start_challenge,
    start_daily,
    submit_attempt,
)
from mastermind_core import GameMode, get_preset
from redis.asyncio import Redis
from sqlalchemy import MetaData, Table, create_engine, func, inspect, select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from .conftest import APIContext, principal


def test_alembic_migrates_empty_sqlite_database_and_downgrades(tmp_path: Path) -> None:
    database = tmp_path / "migration.sqlite"
    environment = os.environ | {
        "MASTERMIND_ENVIRONMENT": "test",
        "MASTERMIND_DATABASE_URL": f"sqlite+aiosqlite:///{database}",
    }
    upgrade = subprocess.run(
        ["alembic", "-c", "apps/api/alembic.ini", "upgrade", "head"],
        cwd=Path(__file__).parents[2],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert upgrade.returncode == 0, upgrade.stderr
    sync_engine = create_engine(f"sqlite:///{database}")
    tables = set(inspect(sync_engine).get_table_names())
    assert {
        "profiles",
        "game_sessions",
        "game_attempts",
        "daily_challenges",
        "friend_challenges",
        "multiplayer_rooms",
        "support_requests",
        "account_deletion_requests",
        "product_events",
        "alembic_version",
    }.issubset(tables)
    inspector = inspect(sync_engine)
    game_checks = {item["name"] for item in inspector.get_check_constraints("game_sessions")}
    attempt_checks = {item["name"] for item in inspector.get_check_constraints("game_attempts")}
    member_columns = {item["name"] for item in inspector.get_columns("multiplayer_members")}
    game_columns = {item["name"] for item in inspector.get_columns("game_sessions")}
    game_indexes = {item["name"] for item in inspector.get_indexes("game_sessions")}
    assert {
        "ck_game_sessions_mode_allowed",
        "ck_game_sessions_status_allowed",
        "ck_game_sessions_attempts_within_limit",
        "ck_game_sessions_expiry_after_start",
    }.issubset(game_checks)
    assert "ck_game_attempts_feedback_within_code_length" in attempt_checks
    assert {"ready", "ready_at"}.issubset(member_columns)
    assert "expires_at" in game_columns
    assert "ix_game_sessions_status_expires" in game_indexes
    with sync_engine.connect() as connection:
        comeback_count = connection.scalar(
            text("SELECT count(*) FROM achievements WHERE key = 'comeback'")
        )
    assert comeback_count == 1
    sync_engine.dispose()
    downgrade = subprocess.run(
        ["alembic", "-c", "apps/api/alembic.ini", "downgrade", "base"],
        cwd=Path(__file__).parents[2],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert downgrade.returncode == 0, downgrade.stderr


def test_retention_migration_backfills_existing_game_deadline(tmp_path: Path) -> None:
    database = tmp_path / "retention-backfill.sqlite"
    environment = os.environ | {
        "MASTERMIND_ENVIRONMENT": "test",
        "MASTERMIND_DATABASE_URL": f"sqlite+aiosqlite:///{database}",
    }
    repository = Path(__file__).parents[2]
    before_retention = subprocess.run(
        ["alembic", "-c", "apps/api/alembic.ini", "upgrade", "20260716_0002"],
        cwd=repository,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert before_retention.returncode == 0, before_retention.stderr
    engine = create_engine(f"sqlite:///{database}")
    metadata = MetaData()
    profiles = Table("profiles", metadata, autoload_with=engine)
    games = Table("game_sessions", metadata, autoload_with=engine)
    owner_id = uuid.uuid4()
    game_id = uuid.uuid4()
    started_at = datetime(2026, 7, 1, 12, tzinfo=UTC)
    config = get_preset("normal")
    with engine.begin() as connection:
        connection.execute(profiles.insert().values(id=owner_id.hex, is_anonymous=False))
        connection.execute(
            games.insert().values(
                id=game_id.hex,
                public_id="existing-retention-game",
                owner_id=owner_id.hex,
                mode="solo",
                difficulty="normal",
                config=config.to_dict(),
                status="active",
                rule_set_version="rules_v1",
                scoring_version="score_v1",
                encrypted_secret=b"ciphertext",
                secret_nonce=b"nonce",
                secret_key_version="v1",
                attempts_used=0,
                maximum_attempts=config.max_attempts,
                started_at=started_at,
                ranked_eligibility="eligible",
            )
        )
    engine.dispose()

    upgraded = subprocess.run(
        ["alembic", "-c", "apps/api/alembic.ini", "upgrade", "head"],
        cwd=repository,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert upgraded.returncode == 0, upgraded.stderr
    engine = create_engine(f"sqlite:///{database}")
    with engine.connect() as connection:
        stored_started, stored_expiry = connection.execute(
            text("SELECT started_at, expires_at FROM game_sessions WHERE id = :game_id"),
            {"game_id": game_id.hex},
        ).one()
    engine.dispose()
    assert datetime.fromisoformat(stored_expiry) - datetime.fromisoformat(
        stored_started
    ) == timedelta(days=7)

    repeated = subprocess.run(
        ["alembic", "-c", "apps/api/alembic.ini", "upgrade", "head"],
        cwd=repository,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert repeated.returncode == 0, repeated.stderr


async def test_in_memory_broker_fans_out_and_unsubscribes() -> None:
    broker = InMemoryBroker()
    async with broker.subscribe("room") as first, broker.subscribe("room") as second:
        await broker.publish("room", {"sequence": 1, "type": "presence", "payload": {}})
        assert await anext(first) == {
            "sequence": 1,
            "type": "presence",
            "payload": {},
        }
        assert await anext(second) == {
            "sequence": 1,
            "type": "presence",
            "payload": {},
        }
    await broker.close()


def test_realtime_envelopes_are_versioned_and_reject_unknown_versions() -> None:
    assert _server_event("heartbeat_ack", {}) == {
        "version": 1,
        "sequence": None,
        "type": "heartbeat_ack",
        "payload": {},
    }
    assert RoomClientMessage.model_validate({"version": 1, "type": "heartbeat"}).version == 1
    with pytest.raises(ValueError):
        RoomClientMessage.model_validate({"type": "heartbeat"})
    with pytest.raises(ValueError):
        RoomClientMessage.model_validate({"version": 2, "type": "heartbeat"})


async def test_due_tie_window_is_durably_finalized_and_published(api: APIContext) -> None:
    created = await api.client.post("/v1/rooms", json={"difficulty": "normal"})
    assert created.status_code == 201, created.text
    room_id = uuid.UUID(created.json()["id"])
    now = datetime.now(UTC)
    async with api.sessions() as session:
        room = await session.get(MultiplayerRoom, room_id)
        assert room is not None
        room.status = "active"
        room.winner_id = api.current["principal"].user_id
        room.winner_at = now - timedelta(seconds=1)
        room.tie_deadline = now - timedelta(milliseconds=1)
        await session.commit()

    broker = InMemoryBroker()
    async with broker.subscribe(str(room_id)) as events:
        assert await finalize_due_rooms_once(api.sessions, broker, now=now) == 1
        published = await asyncio.wait_for(anext(events), timeout=1)
    assert published["version"] == 1
    assert published["type"] == "room_completed"
    assert published["payload"]["reason"] == "tie_window_elapsed"
    async with api.sessions() as session:
        room = await session.get(MultiplayerRoom, room_id)
        persisted = await session.scalar(
            select(MultiplayerEvent).where(
                MultiplayerEvent.room_id == room_id,
                MultiplayerEvent.event_type == "room_completed",
            )
        )
        assert room is not None and room.status == "completed"
        assert persisted is not None
    assert await finalize_due_rooms_once(api.sessions, broker, now=now) == 0
    await broker.close()


@pytest.mark.postgres
@pytest.mark.skipif(
    not os.getenv("MASTERMIND_TEST_POSTGRES_URL"),
    reason="Set MASTERMIND_TEST_POSTGRES_URL to an isolated empty PostgreSQL database.",
)
async def test_real_postgres_migration_and_constraints() -> None:
    url = os.environ["MASTERMIND_TEST_POSTGRES_URL"]
    environment = os.environ | {
        "MASTERMIND_ENVIRONMENT": "test",
        "MASTERMIND_DATABASE_URL": url,
    }
    result = await asyncio.to_thread(
        subprocess.run,
        ["alembic", "-c", "apps/api/alembic.ini", "upgrade", "head"],
        cwd=Path(__file__).parents[2],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    engine = create_async_engine(url)
    async with engine.connect() as connection:
        privileges = (
            await connection.execute(
                text(
                    "SELECT "
                    "has_table_privilege('mastermind_runtime', 'profiles', 'UPDATE'), "
                    "has_table_privilege('mastermind_runtime', 'achievements', 'UPDATE'), "
                    "has_table_privilege('mastermind_runtime', 'audit_events', 'DELETE'), "
                    "has_table_privilege('mastermind_runtime', 'product_events', 'SELECT'), "
                    "has_table_privilege('mastermind_retention', 'game_sessions', 'DELETE'), "
                    "has_table_privilege('mastermind_retention', 'product_events', 'DELETE'), "
                    "has_table_privilege('mastermind_retention', 'audit_events', 'DELETE')"
                )
            )
        ).one()
    await engine.dispose()
    assert privileges == (True, False, False, False, True, True, False)


@pytest.mark.postgres
@pytest.mark.skipif(
    not os.getenv("MASTERMIND_TEST_POSTGRES_URL"),
    reason="Set MASTERMIND_TEST_POSTGRES_URL to an isolated disposable PostgreSQL database.",
)
async def test_real_postgres_creates_room_before_foreign_key_member() -> None:
    settings = Settings(
        environment="test",
        database_url=os.environ["MASTERMIND_TEST_POSTGRES_URL"],
        secret_encryption_keys=json.dumps({"v1": base64.b64encode(b"r" * 32).decode()}),
        secret_active_key_version="v1",
        public_identifier_hmac_key="i" * 32,
    )
    engine = create_async_engine(settings.database_url)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
    player = principal()
    async with sessions() as session:
        room, room_code = await create_room(
            session,
            player,
            "easy",
            SecretCipher.from_settings(settings),
            settings,
            "postgres-room-create-0001",
        )
        member_count = await session.scalar(
            select(func.count(MultiplayerMember.id)).where(MultiplayerMember.room_id == room.id)
        )
    assert room_code
    assert member_count == 1
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.mark.skipif(
    not os.getenv("MASTERMIND_TEST_REDIS_URL"),
    reason="Set MASTERMIND_TEST_REDIS_URL to an isolated Redis database.",
)
async def test_real_redis_ticket_getdel_is_atomic() -> None:
    redis = Redis.from_url(os.environ["MASTERMIND_TEST_REDIS_URL"], decode_responses=True)
    key = f"mastermind:test:ticket:{uuid.uuid4()}"
    await redis.setex(key, 30, "ticket-payload")
    first, second = await asyncio.gather(redis.getdel(key), redis.getdel(key))
    assert sorted([first, second], key=lambda item: item is None) == ["ticket-payload", None]
    await redis.aclose()


@pytest.mark.skipif(
    not os.getenv("MASTERMIND_TEST_REDIS_URL"),
    reason="Set MASTERMIND_TEST_REDIS_URL to an isolated Redis database.",
)
async def test_real_redis_connection_cap_counts_tabs_and_releases() -> None:
    redis = Redis.from_url(os.environ["MASTERMIND_TEST_REDIS_URL"], decode_responses=True)
    user = principal()
    settings = Settings(
        environment="test",
        websocket_user_connection_limit=2,
        websocket_ip_connection_limit=3,
    )
    claimed: list[tuple[str, str, str]] = []
    for token in ("tab-one", "tab-two"):
        allowed, count, user_key, ip_key = await _claim_connection(
            redis, user, "192.0.2.5", token, settings
        )
        assert allowed is True
        claimed.append((user_key, ip_key, token))
    assert count == 2
    denied, count, _, _ = await _claim_connection(redis, user, "192.0.2.5", "tab-three", settings)
    assert denied is False and count == 2
    remaining = await _release_connection(redis, *claimed[0])
    assert remaining == 1
    remaining = await _release_connection(redis, *claimed[1])
    assert remaining == 0
    await redis.aclose()


@pytest.mark.postgres
@pytest.mark.skipif(
    not os.getenv("MASTERMIND_TEST_POSTGRES_URL"),
    reason="Set MASTERMIND_TEST_POSTGRES_URL to an isolated disposable PostgreSQL database.",
)
async def test_real_postgres_serializes_concurrent_attempts() -> None:
    settings = Settings(
        environment="test",
        database_url=os.environ["MASTERMIND_TEST_POSTGRES_URL"],
        secret_encryption_keys=json.dumps({"v1": base64.b64encode(b"p" * 32).decode()}),
        secret_active_key_version="v1",
    )
    engine = create_async_engine(settings.database_url)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
    user = principal()
    cipher = SecretCipher.from_settings(settings)
    async with sessions() as session:
        game = await create_game(
            session,
            user,
            CreateGameRequest(
                mode=GameMode.PASS_AND_PLAY,
                config=GameConfigSchema(
                    colours=list("RBGYW"),
                    code_length=4,
                    max_attempts=4,
                    duplicates_allowed=True,
                    code_maker="human",
                ),
                secret=list("RBGY"),
            ),
            cipher,
        )
        game_id = game.public_id

    async def attempt(guess: list[str], key: str) -> int:
        async with sessions() as session:
            updated = await submit_attempt(
                session, user, game_id, guess, key, f"test:{key}", cipher
            )
            return updated.attempts_used

    used = await asyncio.gather(
        attempt(list("WWWW"), "postgres-attempt-0001"),
        attempt(list("WRRR"), "postgres-attempt-0002"),
    )
    assert sorted(used) == [1, 2]
    async with sessions() as session:
        assert await session.scalar(select(func.count(GameAttempt.id))) == 2
        numbers = list(await session.scalars(select(GameAttempt.attempt_number)))
        assert sorted(numbers) == [1, 2]
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.mark.postgres
@pytest.mark.skipif(
    not os.getenv("MASTERMIND_TEST_POSTGRES_URL"),
    reason="Set MASTERMIND_TEST_POSTGRES_URL to an isolated disposable PostgreSQL database.",
)
async def test_real_postgres_serializes_simultaneous_duel_solves_as_a_tie() -> None:
    settings = Settings(
        environment="test",
        database_url=os.environ["MASTERMIND_TEST_POSTGRES_URL"],
        secret_encryption_keys=json.dumps({"v1": base64.b64encode(b"p" * 32).decode()}),
        secret_active_key_version="v1",
        public_identifier_hmac_key="i" * 32,
        room_tie_window_ms=2000,
    )
    engine = create_async_engine(settings.database_url)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
    host = principal()
    guest = principal()
    cipher = SecretCipher.from_settings(settings)
    async with sessions() as session:
        room, room_code = await create_room(session, host, "normal", cipher, settings)
        room_id = room.id
    async with sessions() as session:
        await join_room(session, guest, room_code, cipher, settings)
    async with sessions() as session:
        await ready_room(session, host, room_id, cipher)
    async with sessions() as session:
        await ready_room(session, guest, room_id, cipher)
        stored_room = await session.get(MultiplayerRoom, room_id)
        assert stored_room is not None
        secret = cipher.decrypt(
            stored_room.encrypted_secret,
            stored_room.secret_nonce,
            stored_room.secret_key_version,
            context=f"room:{room_id}:rules_v1",
        )

    async def attempt(user: AuthPrincipal, key: str) -> tuple[str, bool]:
        async with sessions() as session:
            outcome = await _submit_duel_attempt_transaction(
                session,
                room_id,
                user,
                list(secret),
                key,
                f"test:{key}",
                cipher,
                settings,
            )
            return outcome.game.status, outcome.completion_event is not None

    used = await asyncio.wait_for(
        asyncio.gather(
            attempt(host, "duel-postgres-attempt-0001"),
            attempt(guest, "duel-postgres-attempt-0002"),
        ),
        timeout=5,
    )
    assert sorted(used, key=lambda item: item[1]) == [("won", False), ("won", True)]
    async with sessions() as session:
        attempts = await session.scalar(
            select(func.count(GameAttempt.id))
            .join(GameSession)
            .where(GameSession.room_id == room_id)
        )
        assert attempts == 2
        completed_room = await session.get(MultiplayerRoom, room_id)
        game_statuses = list(
            await session.scalars(
                select(GameSession.status)
                .where(GameSession.room_id == room_id)
                .order_by(GameSession.id)
            )
        )
        completion_events = await session.scalar(
            select(func.count(MultiplayerEvent.id)).where(
                MultiplayerEvent.room_id == room_id,
                MultiplayerEvent.event_type == "room_completed",
            )
        )
        assert completed_room is not None
        assert completed_room.status == "completed"
        assert completed_room.is_tie is True
        assert completed_room.winner_id is None
        assert game_statuses == ["won", "won"]
        assert completion_events == 1
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.mark.postgres
@pytest.mark.skipif(
    not os.getenv("MASTERMIND_TEST_POSTGRES_URL"),
    reason="Set MASTERMIND_TEST_POSTGRES_URL to an isolated disposable PostgreSQL database.",
)
async def test_real_postgres_recovers_concurrent_official_starts() -> None:
    settings = Settings(
        environment="test",
        database_url=os.environ["MASTERMIND_TEST_POSTGRES_URL"],
        secret_encryption_keys=json.dumps({"v1": base64.b64encode(b"p" * 32).decode()}),
        secret_active_key_version="v1",
        daily_hmac_key="d" * 32,
        public_identifier_hmac_key="i" * 32,
    )
    engine = create_async_engine(settings.database_url)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
    cipher = SecretCipher.from_settings(settings)
    daily_player = principal()

    async def daily_start() -> str:
        async with sessions() as session:
            return (await start_daily(session, daily_player, settings, cipher)).public_id

    daily_ids = await asyncio.gather(daily_start(), daily_start())
    assert daily_ids[0] == daily_ids[1]

    creator = principal()
    async with sessions() as session:
        challenge, _ = await create_challenge(
            session,
            creator,
            CreateChallengeRequest(
                difficulty="normal",
                secret=list("RBGY"),
                idempotency_key="postgres-friend-create-0001",
            ),
            cipher,
            settings,
        )
    participant = principal()

    async def friend_start() -> str:
        async with sessions() as session:
            return (await start_challenge(session, participant, challenge, cipher)).public_id

    friend_ids = await asyncio.gather(friend_start(), friend_start())
    assert friend_ids[0] == friend_ids[1]

    idempotent_player = principal()

    async def keyed_game(secret: str) -> str:
        async with sessions() as session:
            game = await create_game(
                session,
                idempotent_player,
                CreateGameRequest(
                    mode=GameMode.PASS_AND_PLAY,
                    config=GameConfigSchema(
                        colours=list("RBGYW"),
                        code_length=4,
                        max_attempts=4,
                        duplicates_allowed=True,
                        code_maker="human",
                    ),
                    secret=list(secret),
                    idempotency_key="postgres-game-create-0001",
                ),
                cipher,
                settings=settings,
            )
            return game.public_id

    keyed_results = await asyncio.gather(
        keyed_game("RBGY"), keyed_game("WWWW"), return_exceptions=True
    )
    assert sum(isinstance(result, str) for result in keyed_results) == 1
    conflicts = [result for result in keyed_results if isinstance(result, APIError)]
    assert len(conflicts) == 1 and conflicts[0].code == "IDEMPOTENCY_KEY_REUSED"
    async with sessions() as session:
        official_daily = await session.scalar(
            select(func.count(GameSession.id)).where(
                GameSession.owner_id == daily_player.user_id,
                GameSession.daily_challenge_id.is_not(None),
            )
        )
        official_friend = await session.scalar(
            select(func.count(GameSession.id)).where(
                GameSession.owner_id == participant.user_id,
                GameSession.friend_challenge_id.is_not(None),
            )
        )
        assert official_daily == official_friend == 1
        keyed_count = await session.scalar(
            select(func.count(GameSession.id)).where(
                GameSession.owner_id == idempotent_player.user_id,
                GameSession.creation_idempotency_key == "postgres-game-create-0001",
            )
        )
        assert keyed_count == 1
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
    await engine.dispose()
