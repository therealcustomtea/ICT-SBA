# Defers type-annotation evaluation to support modern hints safely.
from __future__ import annotations

# Imports selected names from `datetime` for use in this module.
from datetime import UTC, datetime

# Imports selected names from `mastermind_api.client_ip` for use in this module.
from mastermind_api.client_ip import trusted_client_ip

# Imports selected names from `mastermind_api.errors` for use in this module.
from mastermind_api.errors import APIError

# Imports selected names from `mastermind_api.models` for use in this module.
from mastermind_api.models import GameSession

# Imports selected names from `mastermind_api.rate_limit` for use in this module.
from mastermind_api.rate_limit import RateLimiter

# Imports selected names from `mastermind_api.routers.leaderboards` for use in this module.
from mastermind_api.routers.leaderboards import weekly_period_start

# Imports selected names from `redis.exceptions` for use in this module.
from redis.exceptions import RedisError

# Imports selected names from `sqlalchemy` for use in this module.
from sqlalchemy import select

# Imports selected names from `.conftest` for use in this module.
from .conftest import APIContext


# Defines the `test_private_responses_have_correlation_and_no_store_headers` callable and its typed
# interface.
async def test_private_responses_have_correlation_and_no_store_headers(api: APIContext) -> None:
    # Computes and stores `response` for subsequent operations.
    response = await api.client.get(
        # Supplies this item to the surrounding call or collection.
        "/v1/me/profile",
        # Provides the `headers` parameter or keyword argument.
        headers={"X-Request-ID": "request-123", "X-Correlation-ID": "journey-456"},
        # Closes the multiline call, declaration, or collection started above.
    )

    # Asserts this invariant so an unexpected test state fails immediately.
    assert response.status_code == 200
    # Asserts this invariant so an unexpected test state fails immediately.
    assert response.headers["x-request-id"] == "request-123"
    # Asserts this invariant so an unexpected test state fails immediately.
    assert response.headers["x-correlation-id"] == "journey-456"
    # Asserts this invariant so an unexpected test state fails immediately.
    assert response.headers["cache-control"] == "no-store"
    # Asserts this invariant so an unexpected test state fails immediately.
    assert response.headers["vary"] == "Authorization"


# Defines the `test_rate_limit_returns_retry_metadata_without_blocking_liveness` callable and its
# typed interface.
async def test_rate_limit_returns_retry_metadata_without_blocking_liveness(
    # Declares the typed `api` data field.
    api: APIContext,
    # Completes the signature and declares the callable return type.
) -> None:
    # Computes and stores `api.app.state.ip_rate_limiter.limit` for subsequent operations.
    api.app.state.ip_rate_limiter.limit = 1

    # Asserts this invariant so an unexpected test state fails immediately.
    assert (await api.client.get("/v1/me/profile")).status_code == 200
    # Computes and stores `limited` for subsequent operations.
    limited = await api.client.get("/v1/me/profile")
    # Computes and stores `live` for subsequent operations.
    live = await api.client.get("/health/live")

    # Asserts this invariant so an unexpected test state fails immediately.
    assert limited.status_code == 429
    # Asserts this invariant so an unexpected test state fails immediately.
    assert limited.json()["code"] == "RATE_LIMITED"
    # Asserts this invariant so an unexpected test state fails immediately.
    assert 1 <= int(limited.headers["retry-after"]) <= 60
    # Asserts this invariant so an unexpected test state fails immediately.
    assert live.status_code == 200


# Defines the `test_preflights_do_not_consume_the_aggregate_ip_budget` callable and its typed
# interface.
async def test_preflights_do_not_consume_the_aggregate_ip_budget(api: APIContext) -> None:
    # Computes and stores `api.app.state.ip_rate_limiter.limit` for subsequent operations.
    api.app.state.ip_rate_limiter.limit = 1
    # Computes and stores `preflight_headers` for subsequent operations.
    preflight_headers = {
        # Associates the `Origin` key with its value.
        "Origin": "http://localhost:3000",
        # Associates the `Access-Control-Request-Method` key with its value.
        "Access-Control-Request-Method": "GET",
        # Closes the multiline call, declaration, or collection started above.
    }

    # Computes and stores `preflight` for subsequent operations.
    preflight = await api.client.options("/v1/me/profile", headers=preflight_headers)
    # Computes and stores `allowed` for subsequent operations.
    allowed = await api.client.get("/v1/me/profile")
    # Computes and stores `limited` for subsequent operations.
    limited = await api.client.get("/v1/me/profile")

    # Asserts this invariant so an unexpected test state fails immediately.
    assert preflight.status_code == 200
    # Asserts this invariant so an unexpected test state fails immediately.
    assert allowed.status_code == 200
    # Asserts this invariant so an unexpected test state fails immediately.
    assert limited.status_code == 429
    # Asserts this invariant so an unexpected test state fails immediately.
    assert api.app.state.rate_limiter.limit == api.settings.rate_limit_per_minute


# Defines the `test_aggregate_ip_budget_is_derived_above_the_subject_budget` callable and its typed
# interface.
def test_aggregate_ip_budget_is_derived_above_the_subject_budget(api: APIContext) -> None:
    # Asserts this invariant so an unexpected test state fails immediately.
    assert api.app.state.ip_rate_limiter.limit == api.settings.rate_limit_per_minute * 10


# Defines the `test_forwarded_client_ip_is_used_only_for_an_explicitly_trusted_peer` callable and
# its typed interface.
def test_forwarded_client_ip_is_used_only_for_an_explicitly_trusted_peer() -> None:
    # Computes and stores `trusted` for subsequent operations.
    trusted = ("10.0.0.8",)

    # Asserts this invariant so an unexpected test state fails immediately.
    assert trusted_client_ip("10.0.0.8", "203.0.113.9, 10.0.0.7", trusted) == "203.0.113.9"
    # Asserts this invariant so an unexpected test state fails immediately.
    assert trusted_client_ip("10.0.0.9", "203.0.113.9", trusted) == "10.0.0.9"
    # Asserts this invariant so an unexpected test state fails immediately.
    assert trusted_client_ip("10.0.0.8", "not-an-ip", trusted) == "10.0.0.8"


# Defines the `test_secret_recovery_failure_is_a_retryable_service_error` callable and its typed
# interface.
async def test_secret_recovery_failure_is_a_retryable_service_error(api: APIContext) -> None:
    # Computes and stores `created` for subsequent operations.
    created = await api.client.post(
        # Supplies this item to the surrounding call or collection.
        "/v1/games",
        # Computes and stores `json` for subsequent operations.
        json={
            # Associates the `mode` key with its value.
            "mode": "pass_and_play",
            # Associates the `config` key with its value.
            "config": {
                # Associates the `colours` key with its value.
                "colours": ["R", "B", "G", "Y", "W"],
                # Associates the `codeLength` key with its value.
                "codeLength": 4,
                # Associates the `maxAttempts` key with its value.
                "maxAttempts": 3,
                # Associates the `duplicatesAllowed` key with its value.
                "duplicatesAllowed": True,
                # Associates the `codeMaker` key with its value.
                "codeMaker": "human",
                # Associates the `visibility` key with its value.
                "visibility": "private",
                # Associates the `ranked` key with its value.
                "ranked": False,
                # Closes the multiline call, declaration, or collection started above.
            },
            # Associates the `secret` key with its value.
            "secret": ["R", "B", "G", "Y"],
            # Closes the multiline call, declaration, or collection started above.
        },
        # Closes the multiline call, declaration, or collection started above.
    )
    # Asserts this invariant so an unexpected test state fails immediately.
    assert created.status_code == 201
    # Acquires this asynchronous managed resource for the nested operation.
    async with api.sessions() as session:
        # Computes and stores `game` for subsequent operations.
        game = await session.scalar(
            # Calls `select` with the supplied values.
            select(GameSession).where(GameSession.public_id == created.json()["id"])
            # Closes the multiline call, declaration, or collection started above.
        )
        # Asserts this invariant so an unexpected test state fails immediately.
        assert game is not None
        # Computes and stores `game.secret_key_version` for subsequent operations.
        game.secret_key_version = "retired"
        # Waits for this asynchronous operation to complete.
        await session.commit()

    # Computes and stores `response` for subsequent operations.
    response = await api.client.post(
        # Supplies this item to the surrounding call or collection.
        f"/v1/games/{created.json()['id']}/attempts",
        # Provides the `json` parameter or keyword argument.
        json={"guess": ["R", "B", "G", "Y"], "idempotencyKey": "mismatch-000"},
        # Closes the multiline call, declaration, or collection started above.
    )

    # Asserts this invariant so an unexpected test state fails immediately.
    assert response.status_code == 503
    # Asserts this invariant so an unexpected test state fails immediately.
    assert response.json()["code"] == "SECRET_KEY_UNAVAILABLE"
    # Asserts this invariant so an unexpected test state fails immediately.
    assert set(response.json()) == {"code", "message", "requestId"}


# Defines the `UnavailableRedis` class and its related behavior.
class UnavailableRedis:
    # Defines the `eval` callable and its typed interface.
    async def eval(self, *_args: object) -> int:
        # Raises this exception to report an invalid or failed operation.
        raise RedisError("unavailable")


# Defines the `RecordingRedis` class and its related behavior.
class RecordingRedis:
    # Defines the `__init__` callable and its typed interface.
    def __init__(self) -> None:
        # Computes and stores `self.calls` for subsequent operations.
        self.calls: list[tuple[object, ...]] = []

    # Defines the `eval` callable and its typed interface.
    async def eval(self, *args: object) -> int:
        # Calls `self.calls.append` with the supplied values.
        self.calls.append(args)
        # Returns this result to the caller and ends the current function.
        return 1


# Defines the `test_shared_rate_limit_increment_and_expiry_are_atomic` callable and its typed
# interface.
async def test_shared_rate_limit_increment_and_expiry_are_atomic() -> None:
    # Computes and stores `redis` for subsequent operations.
    redis = RecordingRedis()
    # Computes and stores `limiter` for subsequent operations.
    limiter = RateLimiter(limit=10, redis=redis, fail_closed=True)  # type: ignore[arg-type]

    # Waits for this asynchronous operation to complete.
    await limiter.check("atomic-bucket", weight=2)

    # Asserts this invariant so an unexpected test state fails immediately.
    assert len(redis.calls) == 1
    # Executes this statement as the next step in the surrounding logic.
    script, key_count, redis_key, weight, ttl = redis.calls[0]
    # Asserts this invariant so an unexpected test state fails immediately.
    assert "INCRBY" in str(script) and "EXPIRE" in str(script)
    # Asserts this invariant so an unexpected test state fails immediately.
    assert key_count == 1
    # Asserts this invariant so an unexpected test state fails immediately.
    assert str(redis_key).endswith(":atomic-bucket")
    # Asserts this invariant so an unexpected test state fails immediately.
    assert weight == "2"
    # Asserts this invariant so an unexpected test state fails immediately.
    assert ttl == "70"


# Defines the `test_shared_integrity_limits_fail_closed_but_general_limits_degrade` callable and its
# typed interface.
async def test_shared_integrity_limits_fail_closed_but_general_limits_degrade() -> None:
    # Computes and stores `strict` for subsequent operations.
    strict = RateLimiter(limit=10, redis=UnavailableRedis(), fail_closed=True)  # type: ignore[arg-type]
    # Computes and stores `degraded` for subsequent operations.
    degraded = RateLimiter(limit=10, redis=UnavailableRedis(), fail_closed=False)  # type: ignore[arg-type]

    # Starts a protected operation whose expected failures are handled below.
    try:
        # Waits for this asynchronous operation to complete.
        await strict.check("ranked-action")
    # Handles the listed exception so failure remains controlled.
    except APIError as error:
        # Asserts this invariant so an unexpected test state fails immediately.
        assert error.status_code == 503
        # Asserts this invariant so an unexpected test state fails immediately.
        assert error.code == "RATE_LIMIT_UNAVAILABLE"
    # Handles the remaining case not matched by earlier branches.
    else:
        # Raises this exception to report an invalid or failed operation.
        raise AssertionError("Ranked integrity must fail closed without shared rate limits.")

    # Waits for this asynchronous operation to complete.
    await degraded.check("ordinary-read")


# Defines the `test_weekly_leaderboard_starts_at_monday_midnight_utc` callable and its typed
# interface.
def test_weekly_leaderboard_starts_at_monday_midnight_utc() -> None:
    # Asserts this invariant so an unexpected test state fails immediately.
    assert weekly_period_start(datetime(2026, 7, 16, 18, 45, tzinfo=UTC)) == datetime(
        # Executes this statement as the next step in the surrounding logic.
        2026,
        # Supplies this item to the surrounding call or collection.
        7,
        # Supplies this item to the surrounding call or collection.
        13,
        # Provides the `tzinfo` value to the surrounding call.
        tzinfo=UTC,
        # Closes the multiline call, declaration, or collection started above.
    )
