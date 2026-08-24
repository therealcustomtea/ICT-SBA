# Defers type-annotation evaluation to support modern hints safely.
from __future__ import annotations

# Imports `asyncio` so the module can use that dependency.
import asyncio

# Imports `hashlib` so the module can use that dependency.
import hashlib

# Imports `time` so the module can use that dependency.
import time

# Imports selected names from `collections` for use in this module.
from collections import defaultdict, deque

# Imports selected names from `collections.abc` for use in this module.
from collections.abc import Awaitable

# Imports selected names from `typing` for use in this module.
from typing import Any, cast

# Imports selected names from `fastapi` for use in this module.
from fastapi import Request

# Imports selected names from `redis.asyncio` for use in this module.
from redis.asyncio import Redis

# Imports selected names from `redis.exceptions` for use in this module.
from redis.exceptions import RedisError

# Imports selected names from `.errors` for use in this module.
from .errors import APIError


# Defines the `RateLimiter` class and its related behavior.
class RateLimiter:
    # Defines the `__init__` callable and its typed interface.
    def __init__(
        # Declares the current instance received by this method.
        self,
        # Makes the following parameters keyword-only for clear call sites.
        *,
        # Declares the typed `limit` data field.
        limit: int,
        # Declares the typed `redis` data field.
        redis: Redis | None,
        # Declares the typed `fail_closed` data field.
        fail_closed: bool,
        # Completes the signature and declares the callable return type.
    ) -> None:
        # Computes and stores `self.limit` for subsequent operations.
        self.limit = limit
        # Computes and stores `self.redis` for subsequent operations.
        self.redis = redis
        # Computes and stores `self.fail_closed` for subsequent operations.
        self.fail_closed = fail_closed
        # Computes and stores `self._requests` for subsequent operations.
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        # Computes and stores `self._lock` for subsequent operations.
        self._lock = asyncio.Lock()

    # Defines the `check` callable and its typed interface.
    async def check(self, key: str, *, weight: int = 1) -> None:
        # Computes and stores `retry_after` for subsequent operations.
        retry_after = max(1, 60 - int(time.time() % 60))
        # Checks this condition before executing the nested branch.
        if self.redis:
            # Computes and stores `bucket` for subsequent operations.
            bucket = int(time.time() // 60)
            # Computes and stores `redis_key` for subsequent operations.
            redis_key = f"mastermind:rate:{bucket}:{key}"
            # Computes and stores `script` for subsequent operations.
            script = """
            local count = redis.call('INCRBY', KEYS[1], ARGV[1])
            if count == tonumber(ARGV[1]) then
              redis.call('EXPIRE', KEYS[1], ARGV[2])
            end
            return count
            """
            # Starts a protected operation whose expected failures are handled below.
            try:
                # Acquires this asynchronous managed resource for the nested operation.
                async with asyncio.timeout(2):
                    # Computes and stores `result` for subsequent operations.
                    result = self.redis.eval(script, 1, redis_key, str(weight), "70")
                    # Computes and stores `count` for subsequent operations.
                    count = int(await cast(Awaitable[Any], result))
                # Checks this condition before executing the nested branch.
                if count > self.limit:
                    # Raises this exception to report an invalid or failed operation.
                    raise APIError(
                        # Supplies this item to the surrounding call or collection.
                        429,
                        # Supplies this item to the surrounding call or collection.
                        "RATE_LIMITED",
                        # Supplies this item to the surrounding call or collection.
                        "Too many requests. Please try again shortly.",
                        # Supplies this item to the surrounding call or collection.
                        {"Retry-After": str(retry_after)},
                        # Closes the multiline call, declaration, or collection started above.
                    )
                # Returns this result to the caller and ends the current function.
                return
            # Handles the listed exception so failure remains controlled.
            except APIError:
                # Executes this statement as the next step in the surrounding logic.
                raise
            # Handles the listed exception so failure remains controlled.
            except (RedisError, TimeoutError) as exc:
                # Checks this condition before executing the nested branch.
                if self.fail_closed:
                    # Raises this exception to report an invalid or failed operation.
                    raise APIError(
                        # Supplies this item to the surrounding call or collection.
                        503,
                        # Supplies this item to the surrounding call or collection.
                        "RATE_LIMIT_UNAVAILABLE",
                        # Supplies this item to the surrounding call or collection.
                        "This action is temporarily unavailable.",
                        # Executes this statement as the next step in the surrounding logic.
                    ) from exc
        # Computes and stores `now` for subsequent operations.
        now = time.monotonic()
        # Acquires this asynchronous managed resource for the nested operation.
        async with self._lock:
            # Computes and stores `values` for subsequent operations.
            values = self._requests[key]
            # Repeats the nested block while this condition remains true.
            while values and values[0] < now - 60:
                # Calls `values.popleft` with the supplied values.
                values.popleft()
            # Checks this condition before executing the nested branch.
            if len(values) + weight > self.limit:
                # Raises this exception to report an invalid or failed operation.
                raise APIError(
                    # Supplies this item to the surrounding call or collection.
                    429,
                    # Supplies this item to the surrounding call or collection.
                    "RATE_LIMITED",
                    # Supplies this item to the surrounding call or collection.
                    "Too many requests. Please try again shortly.",
                    # Supplies this item to the surrounding call or collection.
                    {"Retry-After": str(retry_after)},
                    # Closes the multiline call, declaration, or collection started above.
                )
            # Calls `values.extend` with the supplied values.
            values.extend([now] * weight)


# Defines the `action_rate_key` callable and its typed interface.
def action_rate_key(action: str, subject: object, resource: object | None = None) -> str:
    # Documents the purpose or contract of this module, class, or function.
    """Return a bounded, pseudonymous key for an action-specific rate bucket."""

    # Computes and stores `material` for subsequent operations.
    material = f"action:{action}:subject:{subject}"
    # Checks this condition before executing the nested branch.
    if resource is not None:
        # Executes this statement as the next step in the surrounding logic.
        material += f":resource:{resource}"
    # Returns this result to the caller and ends the current function.
    return hashlib.sha256(material.encode()).hexdigest()


# Defines the `enforce_action_limit` callable and its typed interface.
async def enforce_action_limit(
    # Declares the typed `request` data field.
    request: Request,
    # Makes the following parameters keyword-only for clear call sites.
    *,
    # Declares the typed `action` data field.
    action: str,
    # Declares the typed `subject` data field.
    subject: object,
    # Declares the typed `weight` data field.
    weight: int,
    # Provides the `resource` parameter or keyword argument.
    resource: object | None = None,
    # Provides the `integrity_required` parameter or keyword argument.
    integrity_required: bool = False,
    # Completes the signature and declares the callable return type.
) -> None:
    # Documents the purpose or contract of this module, class, or function.
    """Apply an action bucket, optionally failing closed without shared Redis state."""

    # Computes and stores `state_name` for subsequent operations.
    state_name = "integrity_rate_limiter" if integrity_required else "rate_limiter"
    # Computes and stores `limiter` for subsequent operations.
    limiter: RateLimiter = getattr(request.app.state, state_name)
    # Waits for this asynchronous operation to complete.
    await limiter.check(action_rate_key(action, subject, resource), weight=weight)
