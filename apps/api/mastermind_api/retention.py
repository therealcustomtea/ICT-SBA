# Defers annotation evaluation so modern type hints remain safe at runtime.
from __future__ import annotations

# Imports `argparse` because this module uses that dependency.
import argparse

# Imports `asyncio` because this module uses that dependency.
import asyncio

# Imports `json` because this module uses that dependency.
import json

# Imports the required names from `dataclasses` for this module.
from dataclasses import asdict, dataclass

# Imports the required names from `datetime` for this module.
from datetime import UTC, datetime, timedelta

# Imports the required names from `mastermind_core` for this module.
from mastermind_core import (
    # Supplies this required nested value.
    GameConfig,
    # Supplies this required nested value.
    GameMode,
    # Supplies this required nested value.
    GameStatus,
    # Supplies this required nested value.
    LeaderboardEligibility,
    # Supplies this required nested value.
    calculate_score,
    # Closes the multiline declaration, call, or collection opened above.
)

# Imports the required names from `.database` for this module.
from .database import MongoSession, MongoSessionFactory, SessionFactory, close_database

# Imports the required names from `.models` for this module.
from .models import (
    # Supplies this required nested value.
    FriendChallenge,
    # Supplies this required nested value.
    GameSession,
    # Supplies this required nested value.
    LeaderboardEntry,
    # Supplies this required nested value.
    MultiplayerEvent,
    # Supplies this required nested value.
    MultiplayerMember,
    # Supplies this required nested value.
    MultiplayerRoom,
    # Supplies this required nested value.
    ProductEvent,
    # Supplies this required nested value.
    UserAchievement,
    # Closes the multiline declaration, call, or collection opened above.
)

# Stores `SOLO_ACTIVE_LIFETIME` because later steps depend on this value.
SOLO_ACTIVE_LIFETIME = timedelta(days=7)
# Stores `DAILY_ACTIVE_LIFETIME` because later steps depend on this value.
DAILY_ACTIVE_LIFETIME = timedelta(days=1)
# Stores `LOCAL_ACTIVE_LIFETIME` because later steps depend on this value.
LOCAL_ACTIVE_LIFETIME = timedelta(days=1)
# Stores `FRIEND_ACTIVE_LIFETIME` because later steps depend on this value.
FRIEND_ACTIVE_LIFETIME = timedelta(days=30)
# Stores `DUEL_ACTIVE_LIFETIME` because later steps depend on this value.
DUEL_ACTIVE_LIFETIME = timedelta(hours=2)

# Stores `PRODUCT_EVENT_RETENTION` because later steps depend on this value.
PRODUCT_EVENT_RETENTION = timedelta(days=396)
# Stores `UNRANKED_GAME_RETENTION` because later steps depend on this value.
UNRANKED_GAME_RETENTION = timedelta(days=365)
# Stores `RANKED_GAME_RETENTION` because later steps depend on this value.
RANKED_GAME_RETENTION = timedelta(days=730)
# Stores `FRIEND_COMPLETION_RETENTION` because later steps depend on this value.
FRIEND_COMPLETION_RETENTION = timedelta(days=90)
# Stores `ROOM_RETENTION` because later steps depend on this value.
ROOM_RETENTION = timedelta(days=30)

# Stores `MAX_BATCH_SIZE` because later steps depend on this value.
MAX_BATCH_SIZE = 5_000
# Stores `MAX_BATCHES` because later steps depend on this value.
MAX_BATCHES = 100


# Defines this callable to implement the operation described by its name.
def _aware(value: datetime) -> datetime:
    # Returns the computed result and ends the current callable.
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


# Defines this callable to implement the operation described by its name.
def game_expiry_for_mode(
    # Declares this typed field so the surrounding contract is explicit.
    mode: GameMode | str,
    # Declares this typed field so the surrounding contract is explicit.
    started_at: datetime,
    # Supplies this required nested value.
    *,
    # Stores `linked_expires_at` because later steps depend on this value.
    linked_expires_at: datetime | None = None,
# Closes the multiline declaration, call, or collection opened above.
) -> datetime:
    # Stores `normalized_mode` because later steps depend on this value.
    normalized_mode = GameMode(mode)
    # Stores `started` because later steps depend on this value.
    started = _aware(started_at)
    # Stores `lifetime` because later steps depend on this value.
    lifetime = {
        # Supplies this required nested value.
        GameMode.SOLO: SOLO_ACTIVE_LIFETIME,
        # Supplies this required nested value.
        GameMode.DAILY: DAILY_ACTIVE_LIFETIME,
        # Supplies this required nested value.
        GameMode.PRACTICE: LOCAL_ACTIVE_LIFETIME,
        # Supplies this required nested value.
        GameMode.PASS_AND_PLAY: LOCAL_ACTIVE_LIFETIME,
        # Supplies this required nested value.
        GameMode.FRIEND_CHALLENGE: FRIEND_ACTIVE_LIFETIME,
        # Supplies this required nested value.
        GameMode.DUEL: DUEL_ACTIVE_LIFETIME,
    # Closes the multiline declaration, call, or collection opened above.
    }[normalized_mode]
    # Stores `default_expiry` because later steps depend on this value.
    default_expiry = started + lifetime
    # Guards the nested operation so it runs only when this condition is satisfied.
    if linked_expires_at is None:
        # Returns the computed result and ends the current callable.
        return default_expiry
    # Stores `linked_expiry` because later steps depend on this value.
    linked_expiry = _aware(linked_expires_at)
    # Guards the nested operation so it runs only when this condition is satisfied.
    if linked_expiry <= started:
        # Raises this error so invalid state cannot continue silently.
        raise ValueError('A linked challenge or room must remain active after game creation.')
    # Returns the computed result and ends the current callable.
    return min(default_expiry, linked_expiry)


# Defines this callable to implement the operation described by its name.
def expire_game_record(game: GameSession, *, now: datetime) -> bool:
    # Guards the nested operation so it runs only when this condition is satisfied.
    if game.status != GameStatus.ACTIVE.value or _aware(game.expires_at) > _aware(now):
        # Returns the computed result and ends the current callable.
        return False
    # Stores `completed_at` because later steps depend on this value.
    completed_at = _aware(game.expires_at)
    # Stores `elapsed_seconds` because later steps depend on this value.
    elapsed_seconds = max(0, int((completed_at - _aware(game.started_at)).total_seconds()))
    # Controls the surrounding branch or loop at this point.
    breakdown = calculate_score(
        # Supplies this required nested value.
        GameConfig.from_dict(game.config),
        # Stores `status` because later steps depend on this value.
        status=GameStatus.EXPIRED,
        # Stores `attempts_used` because later steps depend on this value.
        attempts_used=game.attempts_used,
        # Stores `elapsed_seconds` because later steps depend on this value.
        elapsed_seconds=elapsed_seconds,
    # Closes the multiline declaration, call, or collection opened above.
    )
    # Stores `game.status` because later steps depend on this value.
    game.status = GameStatus.EXPIRED.value
    # Stores `game.completed_at` because later steps depend on this value.
    game.completed_at = completed_at
    # Stores `game.elapsed_seconds` because later steps depend on this value.
    game.elapsed_seconds = elapsed_seconds
    # Stores `game.final_score` because later steps depend on this value.
    game.final_score = 0
    # Stores `game.score_breakdown` because later steps depend on this value.
    game.score_breakdown = breakdown.to_dict()
    # Stores `game.ranked_eligibility` because later steps depend on this value.
    game.ranked_eligibility = LeaderboardEligibility.UNRANKED.value
    # Returns the computed result and ends the current callable.
    return True


# Applies this decorator to configure the declaration immediately below.
@dataclass(slots=True)
# Groups the state and behavior owned by `RetentionSummary`.
class RetentionSummary:
    # Stores `game_sessions_expired` because later steps depend on this value.
    game_sessions_expired: int = 0
    # Stores `rooms_expired` because later steps depend on this value.
    rooms_expired: int = 0
    # Stores `product_events_deleted` because later steps depend on this value.
    product_events_deleted: int = 0
    # Stores `friend_challenges_deleted` because later steps depend on this value.
    friend_challenges_deleted: int = 0
    # Stores `rooms_deleted` because later steps depend on this value.
    rooms_deleted: int = 0
    # Stores `game_sessions_deleted` because later steps depend on this value.
    game_sessions_deleted: int = 0
    # Stores `batches` because later steps depend on this value.
    batches: int = 0

    # Applies this decorator to configure the declaration immediately below.
    @property
    # Defines this callable to implement the operation described by its name.
    def records_changed(self) -> int:
        # Returns the computed result and ends the current callable.
        return (
            # Supplies this required nested value.
            self.game_sessions_expired
            # Supplies this required nested value.
            + self.rooms_expired
            # Supplies this required nested value.
            + self.product_events_deleted
            # Supplies this required nested value.
            + self.friend_challenges_deleted
            # Supplies this required nested value.
            + self.rooms_deleted
            # Supplies this required nested value.
            + self.game_sessions_deleted
        # Closes the multiline declaration, call, or collection opened above.
        )

    # Defines this callable to implement the operation described by its name.
    def add(self, other: RetentionSummary) -> None:
        # Iterates over these values so each item receives the same processing.
        for field in asdict(self):
            # Supplies this required nested value.
            setattr(self, field, getattr(self, field) + getattr(other, field))


# Defines this callable to implement the operation described by its name.
async def _delete_games(session: MongoSession, game_ids: list[object]) -> int:
    # Guards the nested operation so it runs only when this condition is satisfied.
    if not game_ids:
        # Returns the computed result and ends the current callable.
        return 0
    # Stores `match` because later steps depend on this value.
    match = {'$in': game_ids}
    # Performs this required operation before the surrounding flow continues.
    await session.delete_many(LeaderboardEntry, {'game_id': match})
    # Performs this required operation before the surrounding flow continues.
    await session.delete_many(UserAchievement, {'game_id': match})
    # Returns the computed result and ends the current callable.
    return await session.delete_many(GameSession, {'_id': match})


# Defines this callable to implement the operation described by its name.
async def run_retention_batch(
    # Declares this typed field so the surrounding contract is explicit.
    session: MongoSession,
    # Supplies this required nested value.
    *,
    # Stores `now` because later steps depend on this value.
    now: datetime | None = None,
    # Stores `batch_size` because later steps depend on this value.
    batch_size: int = 500,
# Closes the multiline declaration, call, or collection opened above.
) -> RetentionSummary:
    # Guards the nested operation so it runs only when this condition is satisfied.
    if not 1 <= batch_size <= MAX_BATCH_SIZE:
        # Raises this error so invalid state cannot continue silently.
        raise ValueError(f'batch_size must be between 1 and {MAX_BATCH_SIZE}')
    # Stores `cutoff` because later steps depend on this value.
    cutoff = _aware(now or datetime.now(UTC))
    # Stores `summary` because later steps depend on this value.
    summary = RetentionSummary(batches=1)

    # Stores `due_games` because later steps depend on this value.
    due_games = await session.find_many(
        # Supplies this required nested value.
        GameSession,
        # Supplies this required nested value.
        {'status': GameStatus.ACTIVE.value, 'expires_at': {'$lte': cutoff}},
        # Stores `limit` because later steps depend on this value.
        limit=batch_size,
    # Closes the multiline declaration, call, or collection opened above.
    )
    # Stores `summary.game_sessions_expired` because later steps depend on this value.
    summary.game_sessions_expired = sum(expire_game_record(game, now=cutoff) for game in due_games)

    # Stores `due_rooms` because later steps depend on this value.
    due_rooms = await session.find_many(
        # Supplies this required nested value.
        MultiplayerRoom,
        # Supplies this required nested value.
        {'status': {'$in': ['waiting', 'active']}, 'expires_at': {'$lte': cutoff}},
        # Stores `limit` because later steps depend on this value.
        limit=batch_size,
    # Closes the multiline declaration, call, or collection opened above.
    )
    # Iterates over these values so each item receives the same processing.
    for room in due_rooms:
        # Stores `room.status` because later steps depend on this value.
        room.status = 'expired'
    # Stores `summary.rooms_expired` because later steps depend on this value.
    summary.rooms_expired = len(due_rooms)

    # Stores `event_ids` because later steps depend on this value.
    event_ids = [
        # Supplies this required nested value.
        event.id
        # Iterates over these values so each item receives the same processing.
        for event in await session.find_many(
            # Supplies this required nested value.
            ProductEvent, {'expires_at': {'$lte': cutoff}}, limit=batch_size
        # Closes the multiline declaration, call, or collection opened above.
        )
    # Closes the multiline declaration, call, or collection opened above.
    ]
    # Guards the nested operation so it runs only when this condition is satisfied.
    if event_ids:
        # Stores `summary.product_events_deleted` because later steps depend on this value.
        summary.product_events_deleted = await session.delete_many(
            # Supplies this required nested value.
            ProductEvent, {'_id': {'$in': event_ids}}
        # Closes the multiline declaration, call, or collection opened above.
        )

    # Stores `challenge_ids` because later steps depend on this value.
    challenge_ids = [
        # Supplies this required nested value.
        challenge.id
        # Iterates over these values so each item receives the same processing.
        for challenge in await session.find_many(
            # Supplies this required nested value.
            FriendChallenge,
            # Supplies this required nested value.
            {'expires_at': {'$lte': cutoff - FRIEND_COMPLETION_RETENTION}},
            # Stores `limit` because later steps depend on this value.
            limit=batch_size,
        # Closes the multiline declaration, call, or collection opened above.
        )
    # Closes the multiline declaration, call, or collection opened above.
    ]
    # Guards the nested operation so it runs only when this condition is satisfied.
    if challenge_ids:
        # Stores `summary.friend_challenges_deleted` because later steps depend on this value.
        summary.friend_challenges_deleted = await session.delete_many(
            # Supplies this required nested value.
            FriendChallenge, {'_id': {'$in': challenge_ids}}
        # Closes the multiline declaration, call, or collection opened above.
        )

    # Stores `old_rooms` because later steps depend on this value.
    old_rooms = await session.find_many(
        # Supplies this required nested value.
        MultiplayerRoom,
        # Supplies this required nested value.
        {
            # Supplies this literal value to the surrounding declaration or call.
            'status': {'$in': ['completed', 'expired']},
            # Supplies this literal value to the surrounding declaration or call.
            'updated_at': {'$lte': cutoff - ROOM_RETENTION},
        # Closes the multiline declaration, call, or collection opened above.
        },
        # Stores `limit` because later steps depend on this value.
        limit=batch_size,
    # Closes the multiline declaration, call, or collection opened above.
    )
    # Stores `room_ids` because later steps depend on this value.
    room_ids = [room.id for room in old_rooms]
    # Guards the nested operation so it runs only when this condition is satisfied.
    if room_ids:
        # Stores `room_match` because later steps depend on this value.
        room_match = {'$in': room_ids}
        # Performs this required operation before the surrounding flow continues.
        await session.delete_many(MultiplayerMember, {'room_id': room_match})
        # Performs this required operation before the surrounding flow continues.
        await session.delete_many(MultiplayerEvent, {'room_id': room_match})
        # Stores `summary.rooms_deleted` because later steps depend on this value.
        summary.rooms_deleted = await session.delete_many(
            # Supplies this required nested value.
            MultiplayerRoom, {'_id': room_match}
        # Closes the multiline declaration, call, or collection opened above.
        )

    # Stores `old_games` because later steps depend on this value.
    old_games = await session.find_many(
        # Supplies this required nested value.
        GameSession,
        # Supplies this required nested value.
        {
            # Supplies this literal value to the surrounding declaration or call.
            '$or': [
                # Supplies this required nested value.
                {
                    # Supplies this literal value to the surrounding declaration or call.
                    'completed_at': {'$lte': cutoff - RANKED_GAME_RETENTION},
                    # Supplies this literal value to the surrounding declaration or call.
                    'ranked_eligibility': LeaderboardEligibility.ELIGIBLE.value,
                # Closes the multiline declaration, call, or collection opened above.
                },
                # Supplies this required nested value.
                {
                    # Supplies this literal value to the surrounding declaration or call.
                    'completed_at': {'$lte': cutoff - UNRANKED_GAME_RETENTION},
                    # Supplies this literal value to the surrounding declaration or call.
                    'ranked_eligibility': {'$ne': LeaderboardEligibility.ELIGIBLE.value},
                # Closes the multiline declaration, call, or collection opened above.
                },
            # Closes the multiline declaration, call, or collection opened above.
            ]
        # Closes the multiline declaration, call, or collection opened above.
        },
        # Stores `limit` because later steps depend on this value.
        limit=batch_size,
    # Closes the multiline declaration, call, or collection opened above.
    )
    # Stores `summary.game_sessions_deleted` because later steps depend on this value.
    summary.game_sessions_deleted = await _delete_games(
        # Supplies this required nested value.
        session, [game.id for game in old_games]
    # Closes the multiline declaration, call, or collection opened above.
    )
    # Performs this required operation before the surrounding flow continues.
    await session.commit()
    # Returns the computed result and ends the current callable.
    return summary


# Defines this callable to implement the operation described by its name.
async def run_retention(
    # Declares this typed field so the surrounding contract is explicit.
    sessions: MongoSessionFactory,
    # Supplies this required nested value.
    *,
    # Stores `batch_size` because later steps depend on this value.
    batch_size: int = 500,
    # Stores `max_batches` because later steps depend on this value.
    max_batches: int = 20,
    # Stores `now` because later steps depend on this value.
    now: datetime | None = None,
# Closes the multiline declaration, call, or collection opened above.
) -> RetentionSummary:
    # Guards the nested operation so it runs only when this condition is satisfied.
    if not 1 <= max_batches <= MAX_BATCHES:
        # Raises this error so invalid state cannot continue silently.
        raise ValueError(f'max_batches must be between 1 and {MAX_BATCHES}')
    # Stores `total` because later steps depend on this value.
    total = RetentionSummary()
    # Iterates over these values so each item receives the same processing.
    for _ in range(max_batches):
        # Scopes this resource so acquisition and cleanup remain paired.
        async with sessions() as session:
            # Stores `batch` because later steps depend on this value.
            batch = await run_retention_batch(session, now=now, batch_size=batch_size)
        # Supplies this required nested value.
        total.add(batch)
        # Guards the nested operation so it runs only when this condition is satisfied.
        if batch.records_changed == 0:
            # Controls the surrounding branch or loop at this point.
            break
    # Returns the computed result and ends the current callable.
    return total


# Defines this callable to implement the operation described by its name.
async def _run_from_environment(batch_size: int, max_batches: int) -> RetentionSummary:
    # Starts an operation whose expected failures are handled below.
    try:
        # Returns the computed result and ends the current callable.
        return await run_retention(
            # Supplies this required nested value.
            SessionFactory, batch_size=batch_size, max_batches=max_batches
        # Closes the multiline declaration, call, or collection opened above.
        )
    # Ensures this cleanup runs whether the protected operation succeeds or fails.
    finally:
        # Performs this required operation before the surrounding flow continues.
        await close_database()


# Defines this callable to implement the operation described by its name.
def main() -> None:
    # Stores `parser` because later steps depend on this value.
    parser = argparse.ArgumentParser(description='Run bounded Cipherboard retention cleanup.')
    # Supplies this required nested value.
    parser.add_argument('--batch-size', type=int, default=500)
    # Supplies this required nested value.
    parser.add_argument('--max-batches', type=int, default=20)
    # Stores `args` because later steps depend on this value.
    args = parser.parse_args()
    # Stores `summary` because later steps depend on this value.
    summary = asyncio.run(_run_from_environment(args.batch_size, args.max_batches))
    # Stores `result` because later steps depend on this value.
    result = asdict(summary) | {'records_changed': summary.records_changed}
    # Supplies this required nested value.
    print(json.dumps(result, sort_keys=True))


# Guards the nested operation so it runs only when this condition is satisfied.
if __name__ == '__main__':
    # Supplies this required nested value.
    main()
