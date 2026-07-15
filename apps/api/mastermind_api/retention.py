from __future__ import annotations

import argparse
import asyncio
import json
import os
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from urllib.parse import urlsplit, urlunsplit

from mastermind_core import (
    GameConfig,
    GameMode,
    GameStatus,
    LeaderboardEligibility,
    calculate_score,
)
from sqlalchemy import and_, delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from .config import validate_deployed_postgres_url
from .database import prepare_asyncpg_connection
from .models import (
    FriendChallenge,
    GameAttempt,
    GameSession,
    LeaderboardEntry,
    MultiplayerEvent,
    MultiplayerMember,
    MultiplayerRoom,
    ProductEvent,
    UserAchievement,
)

SOLO_ACTIVE_LIFETIME = timedelta(days=7)
DAILY_ACTIVE_LIFETIME = timedelta(days=1)
LOCAL_ACTIVE_LIFETIME = timedelta(days=1)
FRIEND_ACTIVE_LIFETIME = timedelta(days=30)
DUEL_ACTIVE_LIFETIME = timedelta(hours=2)

PRODUCT_EVENT_RETENTION = timedelta(days=396)
UNRANKED_GAME_RETENTION = timedelta(days=365)
RANKED_GAME_RETENTION = timedelta(days=730)
FRIEND_COMPLETION_RETENTION = timedelta(days=90)
ROOM_RETENTION = timedelta(days=30)

MAX_BATCH_SIZE = 5_000
MAX_BATCHES = 100


def _aware(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def game_expiry_for_mode(
    mode: GameMode | str,
    started_at: datetime,
    *,
    linked_expires_at: datetime | None = None,
) -> datetime:
    """Return the fixed server deadline for a newly-created game session."""

    normalized_mode = GameMode(mode)
    started = _aware(started_at)
    lifetime = {
        GameMode.SOLO: SOLO_ACTIVE_LIFETIME,
        GameMode.DAILY: DAILY_ACTIVE_LIFETIME,
        GameMode.PRACTICE: LOCAL_ACTIVE_LIFETIME,
        GameMode.PASS_AND_PLAY: LOCAL_ACTIVE_LIFETIME,
        GameMode.FRIEND_CHALLENGE: FRIEND_ACTIVE_LIFETIME,
        GameMode.DUEL: DUEL_ACTIVE_LIFETIME,
    }[normalized_mode]
    default_expiry = started + lifetime
    if linked_expires_at is None:
        return default_expiry
    linked_expiry = _aware(linked_expires_at)
    if linked_expiry <= started:
        raise ValueError("A linked challenge or room must remain active after game creation.")
    return min(default_expiry, linked_expiry)


def expire_game_record(game: GameSession, *, now: datetime) -> bool:
    """Apply the deterministic active-to-expired transition when its deadline is due."""

    if game.status != GameStatus.ACTIVE.value or _aware(game.expires_at) > _aware(now):
        return False
    completed_at = _aware(game.expires_at)
    elapsed_seconds = max(0, int((completed_at - _aware(game.started_at)).total_seconds()))
    breakdown = calculate_score(
        GameConfig.from_dict(game.config),
        status=GameStatus.EXPIRED,
        attempts_used=game.attempts_used,
        elapsed_seconds=elapsed_seconds,
    )
    game.status = GameStatus.EXPIRED.value
    game.completed_at = completed_at
    game.elapsed_seconds = elapsed_seconds
    game.final_score = 0
    game.score_breakdown = breakdown.to_dict()
    game.ranked_eligibility = LeaderboardEligibility.UNRANKED.value
    return True


@dataclass(slots=True)
class RetentionSummary:
    game_sessions_expired: int = 0
    rooms_expired: int = 0
    product_events_deleted: int = 0
    friend_challenges_deleted: int = 0
    rooms_deleted: int = 0
    game_sessions_deleted: int = 0
    batches: int = 0

    @property
    def records_changed(self) -> int:
        return (
            self.game_sessions_expired
            + self.rooms_expired
            + self.product_events_deleted
            + self.friend_challenges_deleted
            + self.rooms_deleted
            + self.game_sessions_deleted
        )

    def add(self, other: RetentionSummary) -> None:
        self.game_sessions_expired += other.game_sessions_expired
        self.rooms_expired += other.rooms_expired
        self.product_events_deleted += other.product_events_deleted
        self.friend_challenges_deleted += other.friend_challenges_deleted
        self.rooms_deleted += other.rooms_deleted
        self.game_sessions_deleted += other.game_sessions_deleted
        self.batches += other.batches


async def run_retention_batch(
    session: AsyncSession,
    *,
    now: datetime | None = None,
    batch_size: int = 500,
) -> RetentionSummary:
    """Process one bounded, restart-safe lifecycle and retention batch."""

    if not 1 <= batch_size <= MAX_BATCH_SIZE:
        raise ValueError(f"batch_size must be between 1 and {MAX_BATCH_SIZE}")
    effective_now = _aware(now or datetime.now(UTC))
    summary = RetentionSummary(batches=1)

    due_games_query = (
        select(GameSession)
        .where(
            GameSession.status == GameStatus.ACTIVE.value,
            GameSession.expires_at <= effective_now,
        )
        .order_by(GameSession.expires_at, GameSession.id)
        .limit(batch_size)
        .with_for_update(skip_locked=True)
    )
    due_games = list(await session.scalars(due_games_query))
    for game in due_games:
        summary.game_sessions_expired += int(expire_game_record(game, now=effective_now))
    await session.flush()

    due_rooms_query = (
        select(MultiplayerRoom)
        .where(
            MultiplayerRoom.status.in_(["waiting", "active"]),
            MultiplayerRoom.expires_at <= effective_now,
        )
        .order_by(MultiplayerRoom.expires_at, MultiplayerRoom.id)
        .limit(batch_size)
        .with_for_update(skip_locked=True)
    )
    due_rooms = list(await session.scalars(due_rooms_query))
    for room in due_rooms:
        room.status = "expired"
        room.updated_at = _aware(room.expires_at)
    summary.rooms_expired = len(due_rooms)
    await session.flush()

    event_ids_query = (
        select(ProductEvent.id)
        .where(ProductEvent.expires_at <= effective_now)
        .order_by(ProductEvent.expires_at, ProductEvent.id)
        .limit(batch_size)
        .with_for_update(skip_locked=True)
    )
    event_ids = list(await session.scalars(event_ids_query))
    if event_ids:
        await session.execute(delete(ProductEvent).where(ProductEvent.id.in_(event_ids)))
    summary.product_events_deleted = len(event_ids)

    latest_official_completion = (
        select(func.max(GameSession.completed_at))
        .where(
            GameSession.friend_challenge_id == FriendChallenge.id,
            GameSession.mode == GameMode.FRIEND_CHALLENGE.value,
            GameSession.status.in_([GameStatus.WON.value, GameStatus.LOST.value]),
        )
        .correlate(FriendChallenge)
        .scalar_subquery()
    )
    challenge_ids_query = (
        select(FriendChallenge.id)
        .where(
            FriendChallenge.expires_at <= effective_now,
            or_(
                latest_official_completion.is_(None),
                latest_official_completion <= effective_now - FRIEND_COMPLETION_RETENTION,
            ),
        )
        .order_by(FriendChallenge.expires_at, FriendChallenge.id)
        .limit(batch_size)
        .with_for_update(skip_locked=True)
    )
    challenge_ids = list(await session.scalars(challenge_ids_query))
    if challenge_ids:
        await session.execute(
            update(GameSession)
            .where(GameSession.friend_challenge_id.in_(challenge_ids))
            .values(friend_challenge_id=None)
        )
        await session.execute(delete(FriendChallenge).where(FriendChallenge.id.in_(challenge_ids)))
    summary.friend_challenges_deleted = len(challenge_ids)

    room_ids_query = (
        select(MultiplayerRoom.id)
        .where(
            MultiplayerRoom.status.in_(["completed", "expired", "terminated"]),
            MultiplayerRoom.updated_at <= effective_now - ROOM_RETENTION,
        )
        .order_by(MultiplayerRoom.updated_at, MultiplayerRoom.id)
        .limit(batch_size)
        .with_for_update(skip_locked=True)
    )
    room_ids = list(await session.scalars(room_ids_query))
    if room_ids:
        await session.execute(
            update(GameSession).where(GameSession.room_id.in_(room_ids)).values(room_id=None)
        )
        await session.execute(
            delete(MultiplayerEvent).where(MultiplayerEvent.room_id.in_(room_ids))
        )
        await session.execute(
            delete(MultiplayerMember).where(MultiplayerMember.room_id.in_(room_ids))
        )
        await session.execute(delete(MultiplayerRoom).where(MultiplayerRoom.id.in_(room_ids)))
    summary.rooms_deleted = len(room_ids)

    short_retention = or_(
        GameSession.status.in_([GameStatus.ABANDONED.value, GameStatus.EXPIRED.value]),
        GameSession.ranked_eligibility != LeaderboardEligibility.ELIGIBLE.value,
    )
    old_game_ids_query = (
        select(GameSession.id)
        .where(
            GameSession.completed_at.is_not(None),
            or_(
                and_(
                    short_retention,
                    GameSession.completed_at <= effective_now - UNRANKED_GAME_RETENTION,
                ),
                and_(
                    GameSession.status.in_([GameStatus.WON.value, GameStatus.LOST.value]),
                    GameSession.ranked_eligibility == LeaderboardEligibility.ELIGIBLE.value,
                    GameSession.completed_at <= effective_now - RANKED_GAME_RETENTION,
                ),
            ),
        )
        .order_by(GameSession.completed_at, GameSession.id)
        .limit(batch_size)
        .with_for_update(skip_locked=True)
    )
    old_game_ids = list(await session.scalars(old_game_ids_query))
    if old_game_ids:
        await session.execute(
            update(UserAchievement)
            .where(UserAchievement.game_id.in_(old_game_ids))
            .values(game_id=None)
        )
        await session.execute(
            delete(LeaderboardEntry).where(LeaderboardEntry.game_id.in_(old_game_ids))
        )
        await session.execute(delete(GameAttempt).where(GameAttempt.game_id.in_(old_game_ids)))
        await session.execute(delete(GameSession).where(GameSession.id.in_(old_game_ids)))
    summary.game_sessions_deleted = len(old_game_ids)

    await session.commit()
    return summary


async def run_retention(
    sessions: async_sessionmaker[AsyncSession],
    *,
    batch_size: int = 500,
    max_batches: int = 20,
    now: datetime | None = None,
) -> RetentionSummary:
    if not 1 <= max_batches <= MAX_BATCHES:
        raise ValueError(f"max_batches must be between 1 and {MAX_BATCHES}")
    total = RetentionSummary()
    for _ in range(max_batches):
        async with sessions() as session:
            batch = await run_retention_batch(session, now=now, batch_size=batch_size)
        total.add(batch)
        if batch.records_changed == 0:
            break
    return total


def _normalize_database_url(value: str) -> str:
    parsed = urlsplit(value)
    if parsed.scheme in {"postgres", "postgresql"}:
        return urlunsplit(parsed._replace(scheme="postgresql+asyncpg"))
    return value


async def _run_from_environment(batch_size: int, max_batches: int) -> RetentionSummary:
    raw_url = os.getenv("DATABASE_RETENTION_URL", "").strip()
    if not raw_url:
        raise RuntimeError("DATABASE_RETENTION_URL is required for the retention job.")
    database_url = _normalize_database_url(raw_url)
    environment = os.getenv("MASTERMIND_ENVIRONMENT", "development").lower()
    if environment in {"staging", "production"}:
        validate_deployed_postgres_url(database_url)
    connection_url, connect_args = prepare_asyncpg_connection(database_url)
    engine = create_async_engine(
        connection_url,
        connect_args=connect_args,
        poolclass=NullPool,
    )
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    try:
        return await run_retention(
            sessions,
            batch_size=batch_size,
            max_batches=max_batches,
        )
    finally:
        await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run bounded Cipherboard retention cleanup.")
    parser.add_argument("--batch-size", type=int, default=500)
    parser.add_argument("--max-batches", type=int, default=20)
    args = parser.parse_args()
    summary = asyncio.run(_run_from_environment(args.batch_size, args.max_batches))
    print(
        json.dumps(asdict(summary) | {"records_changed": summary.records_changed}, sort_keys=True)
    )


if __name__ == "__main__":
    main()
