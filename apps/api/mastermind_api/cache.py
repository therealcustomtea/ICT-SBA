# Defers type-annotation evaluation to support modern hints safely.
from __future__ import annotations

# Imports selected names from `redis.asyncio` for use in this module.
from redis.asyncio import Redis

# Imports selected names from `redis.exceptions` for use in this module.
from redis.exceptions import RedisError

# Computes and stores `LEADERBOARD_CACHE_VERSION_KEY` for subsequent operations.
LEADERBOARD_CACHE_VERSION_KEY = "mastermind:leaderboard:cache-version"


# Defines the `leaderboard_cache_version` callable and its typed interface.
async def leaderboard_cache_version(redis: Redis) -> int:
    # Starts a protected operation whose expected failures are handled below.
    try:
        # Returns this result to the caller and ends the current function.
        return int(await redis.get(LEADERBOARD_CACHE_VERSION_KEY) or 0)
    # Handles the listed exception so failure remains controlled.
    except (RedisError, TypeError, ValueError):
        # Returns this result to the caller and ends the current function.
        return 0


# Defines the `invalidate_leaderboard_cache` callable and its typed interface.
async def invalidate_leaderboard_cache(redis: Redis | None) -> None:
    # Checks this condition before executing the nested branch.
    if redis is None:
        # Returns this result to the caller and ends the current function.
        return
    # Starts a protected operation whose expected failures are handled below.
    try:
        # Waits for this asynchronous operation to complete.
        await redis.incr(LEADERBOARD_CACHE_VERSION_KEY)
    # Handles the listed exception so failure remains controlled.
    except RedisError:
        # MongoDB remains authoritative and cache entries have a short TTL;
        # cache failure must not roll back an accepted attempt.
        # Returns this result to the caller and ends the current function.
        return
