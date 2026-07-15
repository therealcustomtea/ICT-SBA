from __future__ import annotations

from datetime import UTC, datetime

from mastermind_api.client_ip import trusted_client_ip
from mastermind_api.errors import APIError
from mastermind_api.models import GameSession
from mastermind_api.rate_limit import RateLimiter
from mastermind_api.routers.leaderboards import weekly_period_start
from redis.exceptions import RedisError
from sqlalchemy import select

from .conftest import APIContext


async def test_private_responses_have_correlation_and_no_store_headers(api: APIContext) -> None:
    response = await api.client.get(
        "/v1/me/profile",
        headers={"X-Request-ID": "request-123", "X-Correlation-ID": "journey-456"},
    )

    assert response.status_code == 200
    assert response.headers["x-request-id"] == "request-123"
    assert response.headers["x-correlation-id"] == "journey-456"
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["vary"] == "Authorization"


async def test_rate_limit_returns_retry_metadata_without_blocking_liveness(
    api: APIContext,
) -> None:
    api.app.state.ip_rate_limiter.limit = 1

    assert (await api.client.get("/v1/me/profile")).status_code == 200
    limited = await api.client.get("/v1/me/profile")
    live = await api.client.get("/health/live")

    assert limited.status_code == 429
    assert limited.json()["code"] == "RATE_LIMITED"
    assert 1 <= int(limited.headers["retry-after"]) <= 60
    assert live.status_code == 200


async def test_preflights_do_not_consume_the_aggregate_ip_budget(api: APIContext) -> None:
    api.app.state.ip_rate_limiter.limit = 1
    preflight_headers = {
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "GET",
    }

    preflight = await api.client.options("/v1/me/profile", headers=preflight_headers)
    allowed = await api.client.get("/v1/me/profile")
    limited = await api.client.get("/v1/me/profile")

    assert preflight.status_code == 200
    assert allowed.status_code == 200
    assert limited.status_code == 429
    assert api.app.state.rate_limiter.limit == api.settings.rate_limit_per_minute


def test_aggregate_ip_budget_is_derived_above_the_subject_budget(api: APIContext) -> None:
    assert api.app.state.ip_rate_limiter.limit == api.settings.rate_limit_per_minute * 10


def test_forwarded_client_ip_is_used_only_for_an_explicitly_trusted_peer() -> None:
    trusted = ("10.0.0.8",)

    assert trusted_client_ip("10.0.0.8", "203.0.113.9, 10.0.0.7", trusted) == "203.0.113.9"
    assert trusted_client_ip("10.0.0.9", "203.0.113.9", trusted) == "10.0.0.9"
    assert trusted_client_ip("10.0.0.8", "not-an-ip", trusted) == "10.0.0.8"


async def test_secret_recovery_failure_is_a_retryable_service_error(api: APIContext) -> None:
    created = await api.client.post(
        "/v1/games",
        json={
            "mode": "pass_and_play",
            "config": {
                "colours": ["R", "B", "G", "Y", "W"],
                "codeLength": 4,
                "maxAttempts": 3,
                "duplicatesAllowed": True,
                "codeMaker": "human",
                "visibility": "private",
                "ranked": False,
            },
            "secret": ["R", "B", "G", "Y"],
        },
    )
    assert created.status_code == 201
    async with api.sessions() as session:
        game = await session.scalar(
            select(GameSession).where(GameSession.public_id == created.json()["id"])
        )
        assert game is not None
        game.secret_key_version = "retired"
        await session.commit()

    response = await api.client.post(
        f"/v1/games/{created.json()['id']}/attempts",
        json={"guess": ["R", "B", "G", "Y"], "idempotencyKey": "mismatch-000"},
    )

    assert response.status_code == 503
    assert response.json()["code"] == "SECRET_KEY_UNAVAILABLE"
    assert set(response.json()) == {"code", "message", "requestId"}


class UnavailableRedis:
    async def eval(self, *_args: object) -> int:
        raise RedisError("unavailable")


class RecordingRedis:
    def __init__(self) -> None:
        self.calls: list[tuple[object, ...]] = []

    async def eval(self, *args: object) -> int:
        self.calls.append(args)
        return 1


async def test_shared_rate_limit_increment_and_expiry_are_atomic() -> None:
    redis = RecordingRedis()
    limiter = RateLimiter(limit=10, redis=redis, fail_closed=True)  # type: ignore[arg-type]

    await limiter.check("atomic-bucket", weight=2)

    assert len(redis.calls) == 1
    script, key_count, redis_key, weight, ttl = redis.calls[0]
    assert "INCRBY" in str(script) and "EXPIRE" in str(script)
    assert key_count == 1
    assert str(redis_key).endswith(":atomic-bucket")
    assert weight == "2"
    assert ttl == "70"


async def test_shared_integrity_limits_fail_closed_but_general_limits_degrade() -> None:
    strict = RateLimiter(limit=10, redis=UnavailableRedis(), fail_closed=True)  # type: ignore[arg-type]
    degraded = RateLimiter(limit=10, redis=UnavailableRedis(), fail_closed=False)  # type: ignore[arg-type]

    try:
        await strict.check("ranked-action")
    except APIError as error:
        assert error.status_code == 503
        assert error.code == "RATE_LIMIT_UNAVAILABLE"
    else:
        raise AssertionError("Ranked integrity must fail closed without shared rate limits.")

    await degraded.check("ordinary-read")


def test_weekly_leaderboard_starts_at_monday_midnight_utc() -> None:
    assert weekly_period_start(datetime(2026, 7, 16, 18, 45, tzinfo=UTC)) == datetime(
        2026, 7, 13, tzinfo=UTC
    )
