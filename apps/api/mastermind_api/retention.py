# Defers type-annotation evaluation to support modern hints safely.
from __future__ import annotations

# Imports `argparse` so the module can use that dependency.
import argparse

# Imports `asyncio` so the module can use that dependency.
import asyncio

# Imports `json` so the module can use that dependency.
import json

# Imports `os` so the module can use that dependency.
import os

# Imports selected names from `dataclasses` for use in this module.
from dataclasses import asdict, dataclass

# Imports selected names from `datetime` for use in this module.
from datetime import UTC, datetime, timedelta

# Imports selected names from `urllib.parse` for use in this module.
from urllib.parse import urlsplit, urlunsplit

# Imports selected names from `mastermind_core` for use in this module.
from mastermind_core import (
    # Supplies this item to the surrounding call or collection.
    GameConfig,
    # Supplies this item to the surrounding call or collection.
    GameMode,
    # Supplies this item to the surrounding call or collection.
    GameStatus,
    # Supplies this item to the surrounding call or collection.
    LeaderboardEligibility,
    # Supplies this item to the surrounding call or collection.
    calculate_score,
    # Closes the multiline call, declaration, or collection started above.
)

# Imports selected names from `sqlalchemy` for use in this module.
from sqlalchemy import and_, delete, func, or_, select, update

# Imports selected names from `sqlalchemy.ext.asyncio` for use in this module.
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Imports selected names from `sqlalchemy.pool` for use in this module.
from sqlalchemy.pool import NullPool

# Imports selected names from `.config` for use in this module.
from .config import validate_deployed_postgres_url

# Imports selected names from `.database` for use in this module.
from .database import prepare_asyncpg_connection

# Imports selected names from `.models` for use in this module.
from .models import (
    # Supplies this item to the surrounding call or collection.
    FriendChallenge,
    # Supplies this item to the surrounding call or collection.
    GameAttempt,
    # Supplies this item to the surrounding call or collection.
    GameSession,
    # Supplies this item to the surrounding call or collection.
    LeaderboardEntry,
    # Supplies this item to the surrounding call or collection.
    MultiplayerEvent,
    # Supplies this item to the surrounding call or collection.
    MultiplayerMember,
    # Supplies this item to the surrounding call or collection.
    MultiplayerRoom,
    # Supplies this item to the surrounding call or collection.
    ProductEvent,
    # Supplies this item to the surrounding call or collection.
    UserAchievement,
    # Closes the multiline call, declaration, or collection started above.
)

# Computes and stores `SOLO_ACTIVE_LIFETIME` for subsequent operations.
SOLO_ACTIVE_LIFETIME = timedelta(days=7)
# Computes and stores `DAILY_ACTIVE_LIFETIME` for subsequent operations.
DAILY_ACTIVE_LIFETIME = timedelta(days=1)
# Computes and stores `LOCAL_ACTIVE_LIFETIME` for subsequent operations.
LOCAL_ACTIVE_LIFETIME = timedelta(days=1)
# Computes and stores `FRIEND_ACTIVE_LIFETIME` for subsequent operations.
FRIEND_ACTIVE_LIFETIME = timedelta(days=30)
# Computes and stores `DUEL_ACTIVE_LIFETIME` for subsequent operations.
DUEL_ACTIVE_LIFETIME = timedelta(hours=2)

# Computes and stores `PRODUCT_EVENT_RETENTION` for subsequent operations.
PRODUCT_EVENT_RETENTION = timedelta(days=396)
# Computes and stores `UNRANKED_GAME_RETENTION` for subsequent operations.
UNRANKED_GAME_RETENTION = timedelta(days=365)
# Computes and stores `RANKED_GAME_RETENTION` for subsequent operations.
RANKED_GAME_RETENTION = timedelta(days=730)
# Computes and stores `FRIEND_COMPLETION_RETENTION` for subsequent operations.
FRIEND_COMPLETION_RETENTION = timedelta(days=90)
# Computes and stores `ROOM_RETENTION` for subsequent operations.
ROOM_RETENTION = timedelta(days=30)

# Computes and stores `MAX_BATCH_SIZE` for subsequent operations.
MAX_BATCH_SIZE = 5_000
# Computes and stores `MAX_BATCHES` for subsequent operations.
MAX_BATCHES = 100


# Defines the `_aware` callable and its typed interface.
def _aware(value: datetime) -> datetime:
    # Returns this result to the caller and ends the current function.
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


# Defines the `game_expiry_for_mode` callable and its typed interface.
def game_expiry_for_mode(
    # Declares the typed `mode` data field.
    mode: GameMode | str,
    # Declares the typed `started_at` data field.
    started_at: datetime,
    # Makes the following parameters keyword-only for clear call sites.
    *,
    # Provides the `linked_expires_at` parameter or keyword argument.
    linked_expires_at: datetime | None = None,
    # Completes the signature and declares the callable return type.
) -> datetime:
    # Documents the purpose or contract of this module, class, or function.
    """Return the fixed server deadline for a newly-created game session."""

    # Computes and stores `normalized_mode` for subsequent operations.
    normalized_mode = GameMode(mode)
    # Computes and stores `started` for subsequent operations.
    started = _aware(started_at)
    # Computes and stores `lifetime` for subsequent operations.
    lifetime = {
        # Supplies this item to the surrounding call or collection.
        GameMode.SOLO: SOLO_ACTIVE_LIFETIME,
        # Supplies this item to the surrounding call or collection.
        GameMode.DAILY: DAILY_ACTIVE_LIFETIME,
        # Supplies this item to the surrounding call or collection.
        GameMode.PRACTICE: LOCAL_ACTIVE_LIFETIME,
        # Supplies this item to the surrounding call or collection.
        GameMode.PASS_AND_PLAY: LOCAL_ACTIVE_LIFETIME,
        # Supplies this item to the surrounding call or collection.
        GameMode.FRIEND_CHALLENGE: FRIEND_ACTIVE_LIFETIME,
        # Supplies this item to the surrounding call or collection.
        GameMode.DUEL: DUEL_ACTIVE_LIFETIME,
        # Executes this statement as the next step in the surrounding logic.
    }[normalized_mode]
    # Computes and stores `default_expiry` for subsequent operations.
    default_expiry = started + lifetime
    # Checks this condition before executing the nested branch.
    if linked_expires_at is None:
        # Returns this result to the caller and ends the current function.
        return default_expiry
    # Computes and stores `linked_expiry` for subsequent operations.
    linked_expiry = _aware(linked_expires_at)
    # Checks this condition before executing the nested branch.
    if linked_expiry <= started:
        # Raises this exception to report an invalid or failed operation.
        raise ValueError("A linked challenge or room must remain active after game creation.")
    # Returns this result to the caller and ends the current function.
    return min(default_expiry, linked_expiry)


# Defines the `expire_game_record` callable and its typed interface.
def expire_game_record(game: GameSession, *, now: datetime) -> bool:
    # Documents the purpose or contract of this module, class, or function.
    """Apply the deterministic active-to-expired transition when its deadline is due."""

    # Checks this condition before executing the nested branch.
    if game.status != GameStatus.ACTIVE.value or _aware(game.expires_at) > _aware(now):
        # Returns this result to the caller and ends the current function.
        return False
    # Computes and stores `completed_at` for subsequent operations.
    completed_at = _aware(game.expires_at)
    # Computes and stores `elapsed_seconds` for subsequent operations.
    elapsed_seconds = max(0, int((completed_at - _aware(game.started_at)).total_seconds()))
    # Computes and stores `breakdown` for subsequent operations.
    breakdown = calculate_score(
        # Calls `GameConfig.from_dict` with the supplied values.
        GameConfig.from_dict(game.config),
        # Provides the `status` parameter or keyword argument.
        status=GameStatus.EXPIRED,
        # Provides the `attempts_used` parameter or keyword argument.
        attempts_used=game.attempts_used,
        # Provides the `elapsed_seconds` parameter or keyword argument.
        elapsed_seconds=elapsed_seconds,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `game.status` for subsequent operations.
    game.status = GameStatus.EXPIRED.value
    # Computes and stores `game.completed_at` for subsequent operations.
    game.completed_at = completed_at
    # Computes and stores `game.elapsed_seconds` for subsequent operations.
    game.elapsed_seconds = elapsed_seconds
    # Computes and stores `game.final_score` for subsequent operations.
    game.final_score = 0
    # Computes and stores `game.score_breakdown` for subsequent operations.
    game.score_breakdown = breakdown.to_dict()
    # Computes and stores `game.ranked_eligibility` for subsequent operations.
    game.ranked_eligibility = LeaderboardEligibility.UNRANKED.value
    # Returns this result to the caller and ends the current function.
    return True


# Applies `@dataclass(slots=True)` to configure the declaration immediately below.
@dataclass(slots=True)
# Defines the `RetentionSummary` class and its related behavior.
class RetentionSummary:
    # Computes and stores `game_sessions_expired` for subsequent operations.
    game_sessions_expired: int = 0
    # Computes and stores `rooms_expired` for subsequent operations.
    rooms_expired: int = 0
    # Computes and stores `product_events_deleted` for subsequent operations.
    product_events_deleted: int = 0
    # Computes and stores `friend_challenges_deleted` for subsequent operations.
    friend_challenges_deleted: int = 0
    # Computes and stores `rooms_deleted` for subsequent operations.
    rooms_deleted: int = 0
    # Computes and stores `game_sessions_deleted` for subsequent operations.
    game_sessions_deleted: int = 0
    # Computes and stores `batches` for subsequent operations.
    batches: int = 0

    # Applies `@property` to configure the declaration immediately below.
    @property
    # Defines the `records_changed` callable and its typed interface.
    def records_changed(self) -> int:
        # Returns this result to the caller and ends the current function.
        return (
            # Executes this statement as the next step in the surrounding logic.
            self.game_sessions_expired
            # Executes this statement as the next step in the surrounding logic.
            + self.rooms_expired
            # Executes this statement as the next step in the surrounding logic.
            + self.product_events_deleted
            # Executes this statement as the next step in the surrounding logic.
            + self.friend_challenges_deleted
            # Executes this statement as the next step in the surrounding logic.
            + self.rooms_deleted
            # Executes this statement as the next step in the surrounding logic.
            + self.game_sessions_deleted
            # Closes the multiline call, declaration, or collection started above.
        )

    # Defines the `add` callable and its typed interface.
    def add(self, other: RetentionSummary) -> None:
        # Executes this statement as the next step in the surrounding logic.
        self.game_sessions_expired += other.game_sessions_expired
        # Executes this statement as the next step in the surrounding logic.
        self.rooms_expired += other.rooms_expired
        # Executes this statement as the next step in the surrounding logic.
        self.product_events_deleted += other.product_events_deleted
        # Executes this statement as the next step in the surrounding logic.
        self.friend_challenges_deleted += other.friend_challenges_deleted
        # Executes this statement as the next step in the surrounding logic.
        self.rooms_deleted += other.rooms_deleted
        # Executes this statement as the next step in the surrounding logic.
        self.game_sessions_deleted += other.game_sessions_deleted
        # Executes this statement as the next step in the surrounding logic.
        self.batches += other.batches


# Defines the `run_retention_batch` callable and its typed interface.
async def run_retention_batch(
    # Declares the typed `session` data field.
    session: AsyncSession,
    # Makes the following parameters keyword-only for clear call sites.
    *,
    # Provides the `now` parameter or keyword argument.
    now: datetime | None = None,
    # Provides the `batch_size` parameter or keyword argument.
    batch_size: int = 500,
    # Completes the signature and declares the callable return type.
) -> RetentionSummary:
    # Documents the purpose or contract of this module, class, or function.
    """Process one bounded, restart-safe lifecycle and retention batch."""

    # Checks this condition before executing the nested branch.
    if not 1 <= batch_size <= MAX_BATCH_SIZE:
        # Raises this exception to report an invalid or failed operation.
        raise ValueError(f"batch_size must be between 1 and {MAX_BATCH_SIZE}")
    # Computes and stores `effective_now` for subsequent operations.
    effective_now = _aware(now or datetime.now(UTC))
    # Computes and stores `summary` for subsequent operations.
    summary = RetentionSummary(batches=1)

    # Computes and stores `due_games_query` for subsequent operations.
    due_games_query = (
        # Calls `select` with the supplied values.
        select(GameSession)
        # Begins the nested block or multiline expression completed below.
        .where(
            # Supplies this item to the surrounding call or collection.
            GameSession.status == GameStatus.ACTIVE.value,
            # Supplies this item to the surrounding call or collection.
            GameSession.expires_at <= effective_now,
            # Closes the multiline call, declaration, or collection started above.
        )
        # Executes this statement as the next step in the surrounding logic.
        .order_by(GameSession.expires_at, GameSession.id)
        # Executes this statement as the next step in the surrounding logic.
        .limit(batch_size)
        # Executes this statement as the next step in the surrounding logic.
        .with_for_update(skip_locked=True)
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `due_games` for subsequent operations.
    due_games = list(await session.scalars(due_games_query))
    # Iterates through the supplied values for the nested operation.
    for game in due_games:
        # Executes this statement as the next step in the surrounding logic.
        summary.game_sessions_expired += int(expire_game_record(game, now=effective_now))
    # Waits for this asynchronous operation to complete.
    await session.flush()

    # Computes and stores `due_rooms_query` for subsequent operations.
    due_rooms_query = (
        # Calls `select` with the supplied values.
        select(MultiplayerRoom)
        # Begins the nested block or multiline expression completed below.
        .where(
            # Calls `MultiplayerRoom.status.in_` with the supplied values.
            MultiplayerRoom.status.in_(["waiting", "active"]),
            # Supplies this item to the surrounding call or collection.
            MultiplayerRoom.expires_at <= effective_now,
            # Closes the multiline call, declaration, or collection started above.
        )
        # Executes this statement as the next step in the surrounding logic.
        .order_by(MultiplayerRoom.expires_at, MultiplayerRoom.id)
        # Executes this statement as the next step in the surrounding logic.
        .limit(batch_size)
        # Executes this statement as the next step in the surrounding logic.
        .with_for_update(skip_locked=True)
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `due_rooms` for subsequent operations.
    due_rooms = list(await session.scalars(due_rooms_query))
    # Iterates through the supplied values for the nested operation.
    for room in due_rooms:
        # Computes and stores `room.status` for subsequent operations.
        room.status = "expired"
        # Computes and stores `room.updated_at` for subsequent operations.
        room.updated_at = _aware(room.expires_at)
    # Computes and stores `summary.rooms_expired` for subsequent operations.
    summary.rooms_expired = len(due_rooms)
    # Waits for this asynchronous operation to complete.
    await session.flush()

    # Computes and stores `event_ids_query` for subsequent operations.
    event_ids_query = (
        # Calls `select` with the supplied values.
        select(ProductEvent.id)
        # Executes this statement as the next step in the surrounding logic.
        .where(ProductEvent.expires_at <= effective_now)
        # Executes this statement as the next step in the surrounding logic.
        .order_by(ProductEvent.expires_at, ProductEvent.id)
        # Executes this statement as the next step in the surrounding logic.
        .limit(batch_size)
        # Executes this statement as the next step in the surrounding logic.
        .with_for_update(skip_locked=True)
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `event_ids` for subsequent operations.
    event_ids = list(await session.scalars(event_ids_query))
    # Checks this condition before executing the nested branch.
    if event_ids:
        # Waits for this asynchronous operation to complete.
        await session.execute(delete(ProductEvent).where(ProductEvent.id.in_(event_ids)))
    # Computes and stores `summary.product_events_deleted` for subsequent operations.
    summary.product_events_deleted = len(event_ids)

    # Computes and stores `latest_official_completion` for subsequent operations.
    latest_official_completion = (
        # Calls `select` with the supplied values.
        select(func.max(GameSession.completed_at))
        # Begins the nested block or multiline expression completed below.
        .where(
            # Supplies this item to the surrounding call or collection.
            GameSession.friend_challenge_id == FriendChallenge.id,
            # Supplies this item to the surrounding call or collection.
            GameSession.mode == GameMode.FRIEND_CHALLENGE.value,
            # Calls `GameSession.status.in_` with the supplied values.
            GameSession.status.in_([GameStatus.WON.value, GameStatus.LOST.value]),
            # Closes the multiline call, declaration, or collection started above.
        )
        # Executes this statement as the next step in the surrounding logic.
        .correlate(FriendChallenge)
        # Executes this statement as the next step in the surrounding logic.
        .scalar_subquery()
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `challenge_ids_query` for subsequent operations.
    challenge_ids_query = (
        # Calls `select` with the supplied values.
        select(FriendChallenge.id)
        # Begins the nested block or multiline expression completed below.
        .where(
            # Supplies this item to the surrounding call or collection.
            FriendChallenge.expires_at <= effective_now,
            # Calls `or_` with the supplied values.
            or_(
                # Calls `latest_official_completion.is_` with the supplied values.
                latest_official_completion.is_(None),
                # Supplies this item to the surrounding call or collection.
                latest_official_completion <= effective_now - FRIEND_COMPLETION_RETENTION,
                # Closes the multiline call, declaration, or collection started above.
            ),
            # Closes the multiline call, declaration, or collection started above.
        )
        # Executes this statement as the next step in the surrounding logic.
        .order_by(FriendChallenge.expires_at, FriendChallenge.id)
        # Executes this statement as the next step in the surrounding logic.
        .limit(batch_size)
        # Executes this statement as the next step in the surrounding logic.
        .with_for_update(skip_locked=True)
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `challenge_ids` for subsequent operations.
    challenge_ids = list(await session.scalars(challenge_ids_query))
    # Checks this condition before executing the nested branch.
    if challenge_ids:
        # Waits for this asynchronous operation to complete.
        await session.execute(
            # Calls `update` with the supplied values.
            update(GameSession)
            # Executes this statement as the next step in the surrounding logic.
            .where(GameSession.friend_challenge_id.in_(challenge_ids))
            # Executes this statement as the next step in the surrounding logic.
            .values(friend_challenge_id=None)
            # Closes the multiline call, declaration, or collection started above.
        )
        # Waits for this asynchronous operation to complete.
        await session.execute(delete(FriendChallenge).where(FriendChallenge.id.in_(challenge_ids)))
    # Computes and stores `summary.friend_challenges_deleted` for subsequent operations.
    summary.friend_challenges_deleted = len(challenge_ids)

    # Computes and stores `room_ids_query` for subsequent operations.
    room_ids_query = (
        # Calls `select` with the supplied values.
        select(MultiplayerRoom.id)
        # Begins the nested block or multiline expression completed below.
        .where(
            # Calls `MultiplayerRoom.status.in_` with the supplied values.
            MultiplayerRoom.status.in_(["completed", "expired", "terminated"]),
            # Supplies this item to the surrounding call or collection.
            MultiplayerRoom.updated_at <= effective_now - ROOM_RETENTION,
            # Closes the multiline call, declaration, or collection started above.
        )
        # Executes this statement as the next step in the surrounding logic.
        .order_by(MultiplayerRoom.updated_at, MultiplayerRoom.id)
        # Executes this statement as the next step in the surrounding logic.
        .limit(batch_size)
        # Executes this statement as the next step in the surrounding logic.
        .with_for_update(skip_locked=True)
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `room_ids` for subsequent operations.
    room_ids = list(await session.scalars(room_ids_query))
    # Checks this condition before executing the nested branch.
    if room_ids:
        # Waits for this asynchronous operation to complete.
        await session.execute(
            # Calls `update` with the supplied values.
            update(GameSession).where(GameSession.room_id.in_(room_ids)).values(room_id=None)
            # Closes the multiline call, declaration, or collection started above.
        )
        # Waits for this asynchronous operation to complete.
        await session.execute(
            # Calls `delete` with the supplied values.
            delete(MultiplayerEvent).where(MultiplayerEvent.room_id.in_(room_ids))
            # Closes the multiline call, declaration, or collection started above.
        )
        # Waits for this asynchronous operation to complete.
        await session.execute(
            # Calls `delete` with the supplied values.
            delete(MultiplayerMember).where(MultiplayerMember.room_id.in_(room_ids))
            # Closes the multiline call, declaration, or collection started above.
        )
        # Waits for this asynchronous operation to complete.
        await session.execute(delete(MultiplayerRoom).where(MultiplayerRoom.id.in_(room_ids)))
    # Computes and stores `summary.rooms_deleted` for subsequent operations.
    summary.rooms_deleted = len(room_ids)

    # Computes and stores `short_retention` for subsequent operations.
    short_retention = or_(
        # Calls `GameSession.status.in_` with the supplied values.
        GameSession.status.in_([GameStatus.ABANDONED.value, GameStatus.EXPIRED.value]),
        # Supplies this item to the surrounding call or collection.
        GameSession.ranked_eligibility != LeaderboardEligibility.ELIGIBLE.value,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `old_game_ids_query` for subsequent operations.
    old_game_ids_query = (
        # Calls `select` with the supplied values.
        select(GameSession.id)
        # Begins the nested block or multiline expression completed below.
        .where(
            # Calls `GameSession.completed_at.is_not` with the supplied values.
            GameSession.completed_at.is_not(None),
            # Calls `or_` with the supplied values.
            or_(
                # Calls `and_` with the supplied values.
                and_(
                    # Supplies this item to the surrounding call or collection.
                    short_retention,
                    # Supplies this item to the surrounding call or collection.
                    GameSession.completed_at <= effective_now - UNRANKED_GAME_RETENTION,
                    # Closes the multiline call, declaration, or collection started above.
                ),
                # Calls `and_` with the supplied values.
                and_(
                    # Calls `GameSession.status.in_` with the supplied values.
                    GameSession.status.in_([GameStatus.WON.value, GameStatus.LOST.value]),
                    # Supplies this item to the surrounding call or collection.
                    GameSession.ranked_eligibility == LeaderboardEligibility.ELIGIBLE.value,
                    # Supplies this item to the surrounding call or collection.
                    GameSession.completed_at <= effective_now - RANKED_GAME_RETENTION,
                    # Closes the multiline call, declaration, or collection started above.
                ),
                # Closes the multiline call, declaration, or collection started above.
            ),
            # Closes the multiline call, declaration, or collection started above.
        )
        # Executes this statement as the next step in the surrounding logic.
        .order_by(GameSession.completed_at, GameSession.id)
        # Executes this statement as the next step in the surrounding logic.
        .limit(batch_size)
        # Executes this statement as the next step in the surrounding logic.
        .with_for_update(skip_locked=True)
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `old_game_ids` for subsequent operations.
    old_game_ids = list(await session.scalars(old_game_ids_query))
    # Checks this condition before executing the nested branch.
    if old_game_ids:
        # Waits for this asynchronous operation to complete.
        await session.execute(
            # Calls `update` with the supplied values.
            update(UserAchievement)
            # Executes this statement as the next step in the surrounding logic.
            .where(UserAchievement.game_id.in_(old_game_ids))
            # Executes this statement as the next step in the surrounding logic.
            .values(game_id=None)
            # Closes the multiline call, declaration, or collection started above.
        )
        # Waits for this asynchronous operation to complete.
        await session.execute(
            # Calls `delete` with the supplied values.
            delete(LeaderboardEntry).where(LeaderboardEntry.game_id.in_(old_game_ids))
            # Closes the multiline call, declaration, or collection started above.
        )
        # Waits for this asynchronous operation to complete.
        await session.execute(delete(GameAttempt).where(GameAttempt.game_id.in_(old_game_ids)))
        # Waits for this asynchronous operation to complete.
        await session.execute(delete(GameSession).where(GameSession.id.in_(old_game_ids)))
    # Computes and stores `summary.game_sessions_deleted` for subsequent operations.
    summary.game_sessions_deleted = len(old_game_ids)

    # Waits for this asynchronous operation to complete.
    await session.commit()
    # Returns this result to the caller and ends the current function.
    return summary


# Defines the `run_retention` callable and its typed interface.
async def run_retention(
    # Declares the typed `sessions` data field.
    sessions: async_sessionmaker[AsyncSession],
    # Makes the following parameters keyword-only for clear call sites.
    *,
    # Provides the `batch_size` parameter or keyword argument.
    batch_size: int = 500,
    # Provides the `max_batches` parameter or keyword argument.
    max_batches: int = 20,
    # Provides the `now` parameter or keyword argument.
    now: datetime | None = None,
    # Completes the signature and declares the callable return type.
) -> RetentionSummary:
    # Checks this condition before executing the nested branch.
    if not 1 <= max_batches <= MAX_BATCHES:
        # Raises this exception to report an invalid or failed operation.
        raise ValueError(f"max_batches must be between 1 and {MAX_BATCHES}")
    # Computes and stores `total` for subsequent operations.
    total = RetentionSummary()
    # Iterates through the supplied values for the nested operation.
    for _ in range(max_batches):
        # Acquires this asynchronous managed resource for the nested operation.
        async with sessions() as session:
            # Computes and stores `batch` for subsequent operations.
            batch = await run_retention_batch(session, now=now, batch_size=batch_size)
        # Calls `total.add` with the supplied values.
        total.add(batch)
        # Checks this condition before executing the nested branch.
        if batch.records_changed == 0:
            # Stops the nearest loop after reaching its terminating case.
            break
    # Returns this result to the caller and ends the current function.
    return total


# Defines the `_normalize_database_url` callable and its typed interface.
def _normalize_database_url(value: str) -> str:
    # Computes and stores `parsed` for subsequent operations.
    parsed = urlsplit(value)
    # Checks this condition before executing the nested branch.
    if parsed.scheme in {"postgres", "postgresql"}:
        # Returns this result to the caller and ends the current function.
        return urlunsplit(parsed._replace(scheme="postgresql+asyncpg"))
    # Returns this result to the caller and ends the current function.
    return value


# Defines the `_run_from_environment` callable and its typed interface.
async def _run_from_environment(batch_size: int, max_batches: int) -> RetentionSummary:
    # Computes and stores `raw_url` for subsequent operations.
    raw_url = os.getenv("DATABASE_RETENTION_URL", "").strip()
    # Checks this condition before executing the nested branch.
    if not raw_url:
        # Raises this exception to report an invalid or failed operation.
        raise RuntimeError("DATABASE_RETENTION_URL is required for the retention job.")
    # Computes and stores `database_url` for subsequent operations.
    database_url = _normalize_database_url(raw_url)
    # Computes and stores `environment` for subsequent operations.
    environment = os.getenv("MASTERMIND_ENVIRONMENT", "development").lower()
    # Checks this condition before executing the nested branch.
    if environment in {"staging", "production"}:
        # Calls `validate_deployed_postgres_url` with the supplied values.
        validate_deployed_postgres_url(database_url)
    # Executes this statement as the next step in the surrounding logic.
    connection_url, connect_args = prepare_asyncpg_connection(database_url)
    # Computes and stores `engine` for subsequent operations.
    engine = create_async_engine(
        # Supplies this item to the surrounding call or collection.
        connection_url,
        # Provides the `connect_args` parameter or keyword argument.
        connect_args=connect_args,
        # Provides the `poolclass` parameter or keyword argument.
        poolclass=NullPool,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `sessions` for subsequent operations.
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    # Starts a protected operation whose expected failures are handled below.
    try:
        # Returns this result to the caller and ends the current function.
        return await run_retention(
            # Supplies this item to the surrounding call or collection.
            sessions,
            # Provides the `batch_size` parameter or keyword argument.
            batch_size=batch_size,
            # Provides the `max_batches` parameter or keyword argument.
            max_batches=max_batches,
            # Closes the multiline call, declaration, or collection started above.
        )
    # Runs this cleanup block regardless of the protected result.
    finally:
        # Waits for this asynchronous operation to complete.
        await engine.dispose()


# Defines the `main` callable and its typed interface.
def main() -> None:
    # Computes and stores `parser` for subsequent operations.
    parser = argparse.ArgumentParser(description="Run bounded Cipherboard retention cleanup.")
    # Calls `parser.add_argument` with the supplied values.
    parser.add_argument("--batch-size", type=int, default=500)
    # Calls `parser.add_argument` with the supplied values.
    parser.add_argument("--max-batches", type=int, default=20)
    # Computes and stores `args` for subsequent operations.
    args = parser.parse_args()
    # Computes and stores `summary` for subsequent operations.
    summary = asyncio.run(_run_from_environment(args.batch_size, args.max_batches))
    # Calls `print` with the supplied values.
    print(
        # Calls `json.dumps` with the supplied values.
        json.dumps(asdict(summary) | {"records_changed": summary.records_changed}, sort_keys=True)
        # Closes the multiline call, declaration, or collection started above.
    )


# Checks this condition before executing the nested branch.
if __name__ == "__main__":
    # Calls `main` with the supplied values.
    main()
