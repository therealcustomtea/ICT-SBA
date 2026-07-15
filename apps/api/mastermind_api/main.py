from __future__ import annotations

import asyncio
import hashlib
import time
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager, suppress

import jwt
import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from mastermind_core import DomainError
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from .account import SupabaseAdminClient, account_deletion_retry_worker
from .client_ip import trusted_client_ip
from .config import Settings, get_settings
from .database import SessionFactory, engine
from .error_reporting import ErrorReporter
from .errors import APIError
from .logging import configure_logging
from .metrics import (
    ACTIVE_GAMES,
    ACTIVE_ROOMS,
    AUTH_FAILURES,
    DEPENDENCY_READY,
    GUESS_LATENCY,
    HTTP_ERRORS,
    HTTP_LATENCY,
    HTTP_REQUESTS,
    RATE_LIMITS,
)
from .rate_limit import RateLimiter
from .realtime import (
    InMemoryBroker,
    RedisBroker,
    UnavailableBroker,
    room_finalization_worker,
)
from .routers import (
    admin,
    analytics,
    challenges,
    daily,
    games,
    leaderboards,
    profile,
    rooms,
    support,
)


class BodyLimitMiddleware:
    def __init__(self, app: ASGIApp, max_bytes: int) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        headers = dict(scope.get("headers", []))
        content_length = headers.get(b"content-length")
        try:
            declared_length = int(content_length) if content_length else 0
        except ValueError:
            declared_length = -1
        if declared_length < 0:
            response = JSONResponse(
                {
                    "code": "INVALID_CONTENT_LENGTH",
                    "message": "The Content-Length header is invalid.",
                    "requestId": "",
                },
                status_code=400,
            )
            await response(scope, receive, send)
            return
        if declared_length > self.max_bytes:
            response = JSONResponse(
                {
                    "code": "REQUEST_TOO_LARGE",
                    "message": "The request body is too large.",
                    "requestId": "",
                },
                status_code=413,
            )
            await response(scope, receive, send)
            return
        consumed = 0

        async def limited_receive() -> Message:
            nonlocal consumed
            message = await receive()
            if message["type"] == "http.request":
                consumed += len(message.get("body", b""))
                if consumed > self.max_bytes:
                    raise APIError(413, "REQUEST_TOO_LARGE", "The request body is too large.")
            return message

        await self.app(scope, limited_receive, send)


def _rate_limit_subject(request: Request) -> str | None:
    authorization = request.headers.get("authorization", "")
    if not authorization.startswith("Bearer "):
        return None
    try:
        claims = jwt.decode(
            authorization.removeprefix("Bearer ").strip(),
            options={"verify_signature": False, "verify_exp": False, "verify_aud": False},
        )
        subject = claims.get("sub")
        return str(subject) if subject else None
    except jwt.InvalidTokenError:
        return None


def create_app(settings: Settings | None = None) -> FastAPI:
    config = settings or get_settings()
    configure_logging(config.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        redis: Redis | None = (
            Redis.from_url(
                config.redis_url,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
            )
            if config.redis_url
            else None
        )
        redis_ready = False
        if redis:
            try:
                await redis.ping()
                redis_ready = True
            except RedisError:
                redis_ready = False
        app.state.redis = redis
        app.state.redis_ready = redis_ready
        if redis:
            app.state.broker = RedisBroker(redis)
        elif config.environment in {"production", "staging"}:
            app.state.broker = UnavailableBroker()
        else:
            app.state.broker = InMemoryBroker()
        app.state.rate_limiter = RateLimiter(
            limit=config.rate_limit_per_minute,
            redis=redis,
            fail_closed=False,
        )
        app.state.ip_rate_limiter = RateLimiter(
            limit=config.rate_limit_per_minute * 10,
            redis=redis,
            fail_closed=False,
        )
        app.state.integrity_rate_limiter = RateLimiter(
            limit=config.rate_limit_per_minute,
            redis=redis,
            fail_closed=config.environment in {"production", "staging"},
        )
        app.state.error_reporter = ErrorReporter(config)
        app.state.error_reporting_tasks = set()
        deletion_worker = None
        finalization_worker = None
        app.state.room_finalization_tasks = set()
        if config.environment in {"production", "staging"}:
            deletion_worker = asyncio.create_task(
                account_deletion_retry_worker(
                    SessionFactory,
                    SupabaseAdminClient(
                        config.supabase_url,
                        config.supabase_service_role_key,
                    ),
                )
            )
            finalization_worker = asyncio.create_task(
                room_finalization_worker(SessionFactory, app.state.broker)
            )
        yield
        if finalization_worker is not None:
            finalization_worker.cancel()
            with suppress(asyncio.CancelledError):
                await finalization_worker
        finalization_tasks: set[asyncio.Task[None]] = app.state.room_finalization_tasks
        for task in finalization_tasks:
            task.cancel()
        if finalization_tasks:
            await asyncio.gather(*finalization_tasks, return_exceptions=True)
            finalization_tasks.clear()
        if deletion_worker is not None:
            deletion_worker.cancel()
            with suppress(asyncio.CancelledError):
                await deletion_worker
        reporting_tasks: set[asyncio.Task[None]] = app.state.error_reporting_tasks
        if reporting_tasks:
            await asyncio.gather(*reporting_tasks, return_exceptions=True)
            reporting_tasks.clear()
        await app.state.broker.close()
        if redis and not isinstance(app.state.broker, RedisBroker):
            await redis.aclose()

    app = FastAPI(
        title=f"{config.product_name} API",
        description="Server-authoritative code-breaking gameplay API.",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs" if config.environment != "production" else None,
        redoc_url=None,
    )
    if settings:
        app.dependency_overrides[get_settings] = lambda: config
    app.add_middleware(BodyLimitMiddleware, max_bytes=config.request_body_limit_bytes)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(config.allowed_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "Idempotency-Key",
            "X-Correlation-ID",
            "X-Request-ID",
        ],
        expose_headers=["Retry-After", "X-Correlation-ID", "X-Request-ID"],
        max_age=600,
    )

    @app.middleware("http")
    async def request_context(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        supplied_id = request.headers.get("x-request-id", "")
        request_id = (
            supplied_id
            if 1 <= len(supplied_id) <= 64 and supplied_id.isascii()
            else str(uuid.uuid4())
        )
        request.state.request_id = request_id
        supplied_correlation_id = request.headers.get("x-correlation-id", "")
        correlation_id = (
            supplied_correlation_id
            if 1 <= len(supplied_correlation_id) <= 64 and supplied_correlation_id.isascii()
            else request_id
        )
        request.state.correlation_id = correlation_id
        started = time.perf_counter()
        logger = structlog.get_logger()
        client_ip = trusted_client_ip(
            request.client.host if request.client else None,
            request.headers.get("x-forwarded-for"),
            config.trusted_proxy_ips,
        )
        ip_key = hashlib.sha256(f"ip:{client_ip}".encode()).hexdigest()
        subject = _rate_limit_subject(request)
        try:
            if request.method != "OPTIONS" and request.url.path not in {
                "/health/live",
                "/health/ready",
                "/metrics",
            }:
                ip_limiter: RateLimiter = request.app.state.ip_rate_limiter
                await ip_limiter.check(ip_key)
                if subject:
                    limiter: RateLimiter = request.app.state.rate_limiter
                    subject_key = hashlib.sha256(f"sub:{subject}".encode()).hexdigest()
                    await limiter.check(subject_key)
            try:
                async with asyncio.timeout(config.request_timeout_seconds):
                    response = await call_next(request)
            except TimeoutError:
                response = JSONResponse(
                    {
                        "code": "REQUEST_TIMEOUT",
                        "message": "The service took too long to complete this request.",
                        "requestId": request_id,
                    },
                    status_code=504,
                )
        except APIError as exc:
            if exc.status_code == 429:
                RATE_LIMITS.inc()
            response = JSONResponse(
                {"code": exc.code, "message": exc.message, "requestId": request_id},
                status_code=exc.status_code,
                headers=exc.headers,
            )
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
        if request.url.path.startswith("/v1/"):
            response.headers["Cache-Control"] = "no-store"
            response.headers["Vary"] = "Authorization"
        if config.environment in {"production", "staging"}:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        route = request.scope.get("route")
        route_name = getattr(route, "path", request.url.path)
        elapsed = time.perf_counter() - started
        HTTP_REQUESTS.labels(request.method, route_name, str(response.status_code)).inc()
        HTTP_LATENCY.labels(request.method, route_name).observe(elapsed)
        if route_name.endswith("/attempts"):
            GUESS_LATENCY.observe(elapsed)
        if response.status_code >= 400:
            HTTP_ERRORS.labels(route_name, str(response.status_code)).inc()
        logger.info(
            "http_request",
            request_id=request_id,
            correlation_id=correlation_id,
            method=request.method,
            route=route_name,
            status=response.status_code,
            duration_ms=round(elapsed * 1000, 2),
            environment=config.environment,
            release=config.release,
        )
        return response

    @app.exception_handler(APIError)
    async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
        if exc.status_code == 401:
            AUTH_FAILURES.inc()
        return JSONResponse(
            {"code": exc.code, "message": exc.message, "requestId": request.state.request_id},
            status_code=exc.status_code,
            headers=exc.headers,
        )

    @app.exception_handler(DomainError)
    async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
        if exc.code in {"SECRET_KEY_UNAVAILABLE", "SECRET_DECRYPTION_FAILED"}:
            status_code = 503
        elif exc.code in {"GAME_NOT_ACTIVE", "ILLEGAL_GAME_TRANSITION"}:
            status_code = 409
        else:
            status_code = 422
        return JSONResponse(
            {"code": exc.code, "message": exc.message, "requestId": request.state.request_id},
            status_code=status_code,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        first = exc.errors()[0] if exc.errors() else {}
        message = str(first.get("msg", "The request is invalid.")).removeprefix("Value error, ")
        return JSONResponse(
            {"code": "VALIDATION_ERROR", "message": message, "requestId": request.state.request_id},
            status_code=422,
        )

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
        structlog.get_logger().warning("database_conflict", request_id=request.state.request_id)
        return JSONResponse(
            {
                "code": "RESOURCE_CONFLICT",
                "message": "That change conflicts with an existing record.",
                "requestId": request.state.request_id,
            },
            status_code=409,
        )

    @app.exception_handler(Exception)
    async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
        structlog.get_logger().exception("unhandled_error", request_id=request.state.request_id)
        reporter: ErrorReporter = request.app.state.error_reporter
        if reporter.enabled:
            route = request.scope.get("route")
            route_name = getattr(route, "path", request.url.path)
            task = asyncio.create_task(
                reporter.capture(
                    code="INTERNAL_ERROR",
                    request_id=request.state.request_id,
                    correlation_id=request.state.correlation_id,
                    route=route_name,
                )
            )
            reporting_tasks: set[asyncio.Task[None]] = request.app.state.error_reporting_tasks
            reporting_tasks.add(task)
            task.add_done_callback(reporting_tasks.discard)
        return JSONResponse(
            {
                "code": "INTERNAL_ERROR",
                "message": "The service could not complete your request.",
                "requestId": request.state.request_id,
            },
            status_code=500,
        )

    @app.get("/health/live", include_in_schema=False)
    async def live() -> dict[str, str]:
        return {"status": "ok", "release": config.release}

    @app.get("/health/ready", include_in_schema=False)
    async def ready(request: Request) -> JSONResponse:
        database_ready = True
        try:
            async with engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
        except SQLAlchemyError:
            database_ready = False
        redis_required = config.environment in {"production", "staging"}
        redis = request.app.state.redis
        redis_ready = redis is None and not redis_required
        if redis is not None:
            try:
                await redis.ping()
                redis_ready = True
            except RedisError:
                redis_ready = False
        request.app.state.redis_ready = redis_ready
        DEPENDENCY_READY.labels("postgresql").set(1 if database_ready else 0)
        DEPENDENCY_READY.labels("redis").set(1 if redis_ready else 0)
        healthy = database_ready and (redis_ready or not redis_required)
        return JSONResponse(
            {
                "status": "ok" if healthy else "degraded",
                "database": "ok" if database_ready else "unavailable",
                "redis": "ok" if redis_ready else "unavailable",
                "release": config.release,
            },
            status_code=200 if healthy else 503,
        )

    @app.get("/metrics", include_in_schema=False)
    async def metrics() -> Response:
        if not config.metrics_enabled:
            raise APIError(404, "NOT_FOUND", "Not found.")
        try:
            async with engine.connect() as connection:
                active_games = await connection.scalar(
                    text("SELECT count(*) FROM game_sessions WHERE status = 'active'")
                )
                active_rooms = await connection.scalar(
                    text(
                        "SELECT count(*) FROM multiplayer_rooms "
                        "WHERE status IN ('waiting', 'active')"
                    )
                )
                ACTIVE_GAMES.set(int(active_games or 0))
                ACTIVE_ROOMS.set(int(active_rooms or 0))
        except SQLAlchemyError:
            # Readiness exposes database failure. Metrics remain scrapeable so
            # the failure itself does not blind operators.
            ACTIVE_GAMES.set(float("nan"))
            ACTIVE_ROOMS.set(float("nan"))
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    app.include_router(games.router)
    app.include_router(daily.router)
    app.include_router(challenges.router)
    app.include_router(rooms.router)
    app.include_router(leaderboards.router)
    app.include_router(profile.router)
    app.include_router(support.router)
    app.include_router(analytics.router)
    app.include_router(admin.router)
    return app


app = create_app()
