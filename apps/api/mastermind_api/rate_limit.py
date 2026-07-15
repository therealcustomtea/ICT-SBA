from __future__ import annotations

import asyncio
import hashlib
import time
from collections import defaultdict, deque
from collections.abc import Awaitable
from typing import Any, cast

from fastapi import Request
from redis.asyncio import Redis
from redis.exceptions import RedisError

from .errors import APIError


class RateLimiter:
    def __init__(
        self,
        *,
        limit: int,
        redis: Redis | None,
        fail_closed: bool,
    ) -> None:
        self.limit = limit
        self.redis = redis
        self.fail_closed = fail_closed
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def check(self, key: str, *, weight: int = 1) -> None:
        retry_after = max(1, 60 - int(time.time() % 60))
        if self.redis:
            bucket = int(time.time() // 60)
            redis_key = f"mastermind:rate:{bucket}:{key}"
            script = """
            local count = redis.call('INCRBY', KEYS[1], ARGV[1])
            if count == tonumber(ARGV[1]) then
              redis.call('EXPIRE', KEYS[1], ARGV[2])
            end
            return count
            """
            try:
                async with asyncio.timeout(2):
                    result = self.redis.eval(script, 1, redis_key, str(weight), "70")
                    count = int(await cast(Awaitable[Any], result))
                if count > self.limit:
                    raise APIError(
                        429,
                        "RATE_LIMITED",
                        "Too many requests. Please try again shortly.",
                        {"Retry-After": str(retry_after)},
                    )
                return
            except APIError:
                raise
            except (RedisError, TimeoutError) as exc:
                if self.fail_closed:
                    raise APIError(
                        503,
                        "RATE_LIMIT_UNAVAILABLE",
                        "This action is temporarily unavailable.",
                    ) from exc
        now = time.monotonic()
        async with self._lock:
            values = self._requests[key]
            while values and values[0] < now - 60:
                values.popleft()
            if len(values) + weight > self.limit:
                raise APIError(
                    429,
                    "RATE_LIMITED",
                    "Too many requests. Please try again shortly.",
                    {"Retry-After": str(retry_after)},
                )
            values.extend([now] * weight)


def action_rate_key(action: str, subject: object, resource: object | None = None) -> str:
    """Return a bounded, pseudonymous key for an action-specific rate bucket."""

    material = f"action:{action}:subject:{subject}"
    if resource is not None:
        material += f":resource:{resource}"
    return hashlib.sha256(material.encode()).hexdigest()


async def enforce_action_limit(
    request: Request,
    *,
    action: str,
    subject: object,
    weight: int,
    resource: object | None = None,
    integrity_required: bool = False,
) -> None:
    """Apply an action bucket, optionally failing closed without shared Redis state."""

    state_name = "integrity_rate_limiter" if integrity_required else "rate_limiter"
    limiter: RateLimiter = getattr(request.app.state, state_name)
    await limiter.check(action_rate_key(action, subject, resource), weight=weight)
