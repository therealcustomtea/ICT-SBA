from __future__ import annotations

from redis.asyncio import Redis
from redis.exceptions import RedisError

LEADERBOARD_CACHE_VERSION_KEY = "mastermind:leaderboard:cache-version"


async def leaderboard_cache_version(redis: Redis) -> int:
    try:
        return int(await redis.get(LEADERBOARD_CACHE_VERSION_KEY) or 0)
    except (RedisError, TypeError, ValueError):
        return 0


async def invalidate_leaderboard_cache(redis: Redis | None) -> None:
    if redis is None:
        return
    try:
        await redis.incr(LEADERBOARD_CACHE_VERSION_KEY)
    except RedisError:
        # PostgreSQL remains authoritative and cache entries have a short TTL;
        # cache failure must not roll back an accepted attempt.
        return
