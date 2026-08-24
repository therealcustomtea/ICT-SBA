# Defers type-annotation evaluation to support modern hints safely.
from __future__ import annotations

# Imports `asyncio` so the module can use that dependency.
import asyncio

# Imports `hashlib` so the module can use that dependency.
import hashlib

# Imports `time` so the module can use that dependency.
import time

# Imports `uuid` so the module can use that dependency.
import uuid

# Imports selected names from `collections.abc` for use in this module.
from collections.abc import AsyncIterator, Awaitable, Callable

# Imports selected names from `contextlib` for use in this module.
from contextlib import asynccontextmanager, suppress

# Imports `jwt` so the module can use that dependency.
import jwt

# Imports `structlog` so the module can use that dependency.
import structlog

# Imports selected names from `fastapi` for use in this module.
from fastapi import FastAPI, Request

# Imports selected names from `fastapi.exceptions` for use in this module.
from fastapi.exceptions import RequestValidationError

# Imports selected names from `fastapi.middleware.cors` for use in this module.
from fastapi.middleware.cors import CORSMiddleware

# Imports selected names from `fastapi.responses` for use in this module.
from fastapi.responses import JSONResponse, Response

# Imports selected names from `mastermind_core` for use in this module.
from mastermind_core import DomainError

# Imports selected names from `prometheus_client` for use in this module.
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

# Imports the required names from `pymongo.errors` for this module.
from pymongo.errors import DuplicateKeyError, PyMongoError

# Imports selected names from `redis.asyncio` for use in this module.
from redis.asyncio import Redis

# Imports selected names from `redis.exceptions` for use in this module.
from redis.exceptions import RedisError

# Imports selected names from `starlette.types` for use in this module.
from starlette.types import ASGIApp, Message, Receive, Scope, Send

# Imports selected names from `.account` for use in this module.
# Imports selected names from `.client_ip` for use in this module.
from .client_ip import trusted_client_ip

# Imports selected names from `.config` for use in this module.
from .config import Settings, get_settings

# Imports selected names from `.database` for use in this module.
from .database import (
    # Supplies this required nested value.
    SessionFactory,
    # Supplies this required nested value.
    close_database,
    # Supplies this required nested value.
    configure_database,
    # Supplies this required nested value.
    database_ready,
    # Supplies this required nested value.
    initialize_database,
    # Closes the multiline declaration, call, or collection opened above.
)

# Imports selected names from `.error_reporting` for use in this module.
from .error_reporting import ErrorReporter

# Imports selected names from `.errors` for use in this module.
from .errors import APIError

# Imports selected names from `.logging` for use in this module.
from .logging import configure_logging

# Imports selected names from `.metrics` for use in this module.
from .metrics import (
    # Supplies this item to the surrounding call or collection.
    ACTIVE_GAMES,
    # Supplies this item to the surrounding call or collection.
    ACTIVE_ROOMS,
    # Supplies this item to the surrounding call or collection.
    AUTH_FAILURES,
    # Supplies this item to the surrounding call or collection.
    DEPENDENCY_READY,
    # Supplies this item to the surrounding call or collection.
    GUESS_LATENCY,
    # Supplies this item to the surrounding call or collection.
    HTTP_ERRORS,
    # Supplies this item to the surrounding call or collection.
    HTTP_LATENCY,
    # Supplies this item to the surrounding call or collection.
    HTTP_REQUESTS,
    # Supplies this item to the surrounding call or collection.
    RATE_LIMITS,
    # Closes the multiline call, declaration, or collection started above.
)

# Imports selected names from `.rate_limit` for use in this module.
from .rate_limit import RateLimiter

# Imports selected names from `.realtime` for use in this module.
from .realtime import (
    # Supplies this item to the surrounding call or collection.
    InMemoryBroker,
    # Supplies this item to the surrounding call or collection.
    RedisBroker,
    # Supplies this item to the surrounding call or collection.
    UnavailableBroker,
    # Supplies this item to the surrounding call or collection.
    room_finalization_worker,
    # Closes the multiline call, declaration, or collection started above.
)

# Imports selected names from `.routers` for use in this module.
from .routers import (
    # Supplies this item to the surrounding call or collection.
    admin,
    # Supplies this item to the surrounding call or collection.
    analytics,
    # Supplies this required nested value.
    auth,
    # Supplies this item to the surrounding call or collection.
    challenges,
    # Supplies this item to the surrounding call or collection.
    daily,
    # Supplies this item to the surrounding call or collection.
    games,
    # Supplies this item to the surrounding call or collection.
    leaderboards,
    # Supplies this item to the surrounding call or collection.
    profile,
    # Supplies this item to the surrounding call or collection.
    rooms,
    # Supplies this item to the surrounding call or collection.
    support,
    # Closes the multiline call, declaration, or collection started above.
)


# Defines the `BodyLimitMiddleware` class and its related behavior.
class BodyLimitMiddleware:
    # Defines the `__init__` callable and its typed interface.
    def __init__(self, app: ASGIApp, max_bytes: int) -> None:
        # Computes and stores `self.app` for subsequent operations.
        self.app = app
        # Computes and stores `self.max_bytes` for subsequent operations.
        self.max_bytes = max_bytes

    # Defines the `__call__` callable and its typed interface.
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        # Checks this condition before executing the nested branch.
        if scope["type"] != "http":
            # Waits for this asynchronous operation to complete.
            await self.app(scope, receive, send)
            # Returns this result to the caller and ends the current function.
            return
        # Computes and stores `headers` for subsequent operations.
        headers = dict(scope.get("headers", []))
        # Computes and stores `content_length` for subsequent operations.
        content_length = headers.get(b"content-length")
        # Starts a protected operation whose expected failures are handled below.
        try:
            # Computes and stores `declared_length` for subsequent operations.
            declared_length = int(content_length) if content_length else 0
        # Handles the listed exception so failure remains controlled.
        except ValueError:
            # Computes and stores `declared_length` for subsequent operations.
            declared_length = -1
        # Checks this condition before executing the nested branch.
        if declared_length < 0:
            # Computes and stores `response` for subsequent operations.
            response = JSONResponse(
                # Begins the nested block or multiline expression completed below.
                {
                    # Associates the `code` key with its value.
                    "code": "INVALID_CONTENT_LENGTH",
                    # Associates the `message` key with its value.
                    "message": "The Content-Length header is invalid.",
                    # Associates the `requestId` key with its value.
                    "requestId": "",
                    # Closes the multiline call, declaration, or collection started above.
                },
                # Provides the `status_code` parameter or keyword argument.
                status_code=400,
                # Closes the multiline call, declaration, or collection started above.
            )
            # Waits for this asynchronous operation to complete.
            await response(scope, receive, send)
            # Returns this result to the caller and ends the current function.
            return
        # Checks this condition before executing the nested branch.
        if declared_length > self.max_bytes:
            # Computes and stores `response` for subsequent operations.
            response = JSONResponse(
                # Begins the nested block or multiline expression completed below.
                {
                    # Associates the `code` key with its value.
                    "code": "REQUEST_TOO_LARGE",
                    # Associates the `message` key with its value.
                    "message": "The request body is too large.",
                    # Associates the `requestId` key with its value.
                    "requestId": "",
                    # Closes the multiline call, declaration, or collection started above.
                },
                # Provides the `status_code` parameter or keyword argument.
                status_code=413,
                # Closes the multiline call, declaration, or collection started above.
            )
            # Waits for this asynchronous operation to complete.
            await response(scope, receive, send)
            # Returns this result to the caller and ends the current function.
            return
        # Computes and stores `consumed` for subsequent operations.
        consumed = 0

        # Defines the `limited_receive` callable and its typed interface.
        async def limited_receive() -> Message:
            # Executes this statement as the next step in the surrounding logic.
            nonlocal consumed
            # Computes and stores `message` for subsequent operations.
            message = await receive()
            # Checks this condition before executing the nested branch.
            if message["type"] == "http.request":
                # Executes this statement as the next step in the surrounding logic.
                consumed += len(message.get("body", b""))
                # Checks this condition before executing the nested branch.
                if consumed > self.max_bytes:
                    # Raises this exception to report an invalid or failed operation.
                    raise APIError(413, "REQUEST_TOO_LARGE", "The request body is too large.")
            # Returns this result to the caller and ends the current function.
            return message

        # Waits for this asynchronous operation to complete.
        await self.app(scope, limited_receive, send)


# Defines the `_rate_limit_subject` callable and its typed interface.
def _rate_limit_subject(request: Request) -> str | None:
    # Computes and stores `authorization` for subsequent operations.
    authorization = request.headers.get("authorization", "")
    # Checks this condition before executing the nested branch.
    if not authorization.startswith("Bearer "):
        # Returns this result to the caller and ends the current function.
        return None
    # Starts a protected operation whose expected failures are handled below.
    try:
        # Computes and stores `claims` for subsequent operations.
        claims = jwt.decode(
            # Calls `authorization.removeprefix` with the supplied values.
            authorization.removeprefix("Bearer ").strip(),
            # Provides the `options` parameter or keyword argument.
            options={"verify_signature": False, "verify_exp": False, "verify_aud": False},
            # Closes the multiline call, declaration, or collection started above.
        )
        # Computes and stores `subject` for subsequent operations.
        subject = claims.get("sub")
        # Returns this result to the caller and ends the current function.
        return str(subject) if subject else None
    # Handles the listed exception so failure remains controlled.
    except jwt.InvalidTokenError:
        # Returns this result to the caller and ends the current function.
        return None


# Defines the `create_app` callable and its typed interface.
def create_app(settings: Settings | None = None) -> FastAPI:
    # Computes and stores `config` for subsequent operations.
    config = settings or get_settings()
    # Supplies this required nested value.
    configure_database(config)
    # Calls `configure_logging` with the supplied values.
    configure_logging(config.log_level)

    # Applies `@asynccontextmanager` to configure the declaration immediately below.
    @asynccontextmanager
    # Defines the `lifespan` callable and its typed interface.
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        # Performs this required operation before the surrounding flow continues.
        await initialize_database()
        # Computes and stores `redis` for subsequent operations.
        redis: Redis | None = (
            # Calls `Redis.from_url` with the supplied values.
            Redis.from_url(
                # Supplies this item to the surrounding call or collection.
                config.redis_url,
                # Provides the `decode_responses` parameter or keyword argument.
                decode_responses=True,
                # Provides the `socket_connect_timeout` parameter or keyword argument.
                socket_connect_timeout=2,
                # Provides the `socket_timeout` parameter or keyword argument.
                socket_timeout=2,
                # Closes the multiline call, declaration, or collection started above.
            )
            # Checks this condition before executing the nested branch.
            if config.redis_url
            # Executes this statement as the next step in the surrounding logic.
            else None
            # Closes the multiline call, declaration, or collection started above.
        )
        # Computes and stores `redis_ready` for subsequent operations.
        redis_ready = False
        # Checks this condition before executing the nested branch.
        if redis:
            # Starts a protected operation whose expected failures are handled below.
            try:
                # Waits for this asynchronous operation to complete.
                await redis.ping()
                # Computes and stores `redis_ready` for subsequent operations.
                redis_ready = True
            # Handles the listed exception so failure remains controlled.
            except RedisError:
                # Computes and stores `redis_ready` for subsequent operations.
                redis_ready = False
        # Computes and stores `app.state.redis` for subsequent operations.
        app.state.redis = redis
        # Computes and stores `app.state.redis_ready` for subsequent operations.
        app.state.redis_ready = redis_ready
        # Checks this condition before executing the nested branch.
        if redis:
            # Computes and stores `app.state.broker` for subsequent operations.
            app.state.broker = RedisBroker(redis)
        # Checks this alternative when previous conditions were false.
        elif config.environment in {"production", "staging"}:
            # Computes and stores `app.state.broker` for subsequent operations.
            app.state.broker = UnavailableBroker()
        # Handles the remaining case not matched by earlier branches.
        else:
            # Computes and stores `app.state.broker` for subsequent operations.
            app.state.broker = InMemoryBroker()
        # Computes and stores `app.state.rate_limiter` for subsequent operations.
        app.state.rate_limiter = RateLimiter(
            # Provides the `limit` parameter or keyword argument.
            limit=config.rate_limit_per_minute,
            # Provides the `redis` parameter or keyword argument.
            redis=redis,
            # Provides the `fail_closed` parameter or keyword argument.
            fail_closed=False,
            # Closes the multiline call, declaration, or collection started above.
        )
        # Computes and stores `app.state.ip_rate_limiter` for subsequent operations.
        app.state.ip_rate_limiter = RateLimiter(
            # Provides the `limit` parameter or keyword argument.
            limit=config.rate_limit_per_minute * 10,
            # Provides the `redis` parameter or keyword argument.
            redis=redis,
            # Provides the `fail_closed` parameter or keyword argument.
            fail_closed=False,
            # Closes the multiline call, declaration, or collection started above.
        )
        # Computes and stores `app.state.integrity_rate_limiter` for subsequent operations.
        app.state.integrity_rate_limiter = RateLimiter(
            # Provides the `limit` parameter or keyword argument.
            limit=config.rate_limit_per_minute,
            # Provides the `redis` parameter or keyword argument.
            redis=redis,
            # Provides the `fail_closed` parameter or keyword argument.
            fail_closed=config.environment in {"production", "staging"},
            # Closes the multiline call, declaration, or collection started above.
        )
        # Computes and stores `app.state.error_reporter` for subsequent operations.
        app.state.error_reporter = ErrorReporter(config)
        # Computes and stores `app.state.error_reporting_tasks` for subsequent operations.
        app.state.error_reporting_tasks = set()
        # Computes and stores `finalization_worker` for subsequent operations.
        finalization_worker = None
        # Computes and stores `app.state.room_finalization_tasks` for subsequent operations.
        app.state.room_finalization_tasks = set()
        # Checks this condition before executing the nested branch.
        if config.environment in {"production", "staging"}:
            # Computes and stores `finalization_worker` for subsequent operations.
            finalization_worker = asyncio.create_task(
                # Calls `room_finalization_worker` with the supplied values.
                room_finalization_worker(SessionFactory, app.state.broker)
                # Closes the multiline call, declaration, or collection started above.
            )
        # Executes this statement as the next step in the surrounding logic.
        yield
        # Checks this condition before executing the nested branch.
        if finalization_worker is not None:
            # Calls `finalization_worker.cancel` with the supplied values.
            finalization_worker.cancel()
            # Acquires this managed resource and guarantees cleanup afterward.
            with suppress(asyncio.CancelledError):
                # Waits for this asynchronous operation to complete.
                await finalization_worker
        # Computes and stores `finalization_tasks` for subsequent operations.
        finalization_tasks: set[asyncio.Task[None]] = app.state.room_finalization_tasks
        # Iterates through the supplied values for the nested operation.
        for task in finalization_tasks:
            # Calls `task.cancel` with the supplied values.
            task.cancel()
        # Checks this condition before executing the nested branch.
        if finalization_tasks:
            # Waits for this asynchronous operation to complete.
            await asyncio.gather(*finalization_tasks, return_exceptions=True)
            # Calls `finalization_tasks.clear` with the supplied values.
            finalization_tasks.clear()
        # Computes and stores `reporting_tasks` for subsequent operations.
        reporting_tasks: set[asyncio.Task[None]] = app.state.error_reporting_tasks
        # Checks this condition before executing the nested branch.
        if reporting_tasks:
            # Waits for this asynchronous operation to complete.
            await asyncio.gather(*reporting_tasks, return_exceptions=True)
            # Calls `reporting_tasks.clear` with the supplied values.
            reporting_tasks.clear()
        # Waits for this asynchronous operation to complete.
        await app.state.broker.close()
        # Checks this condition before executing the nested branch.
        if redis and not isinstance(app.state.broker, RedisBroker):
            # Waits for this asynchronous operation to complete.
            await redis.aclose()
        # Performs this required operation before the surrounding flow continues.
        await close_database()

    # Computes and stores `app` for subsequent operations.
    app = FastAPI(
        # Provides the `title` parameter or keyword argument.
        title=f"{config.product_name} API",
        # Provides the `description` parameter or keyword argument.
        description="Server-authoritative code-breaking gameplay API.",
        # Provides the `version` parameter or keyword argument.
        version="1.0.0",
        # Provides the `lifespan` parameter or keyword argument.
        lifespan=lifespan,
        # Provides the `docs_url` parameter or keyword argument.
        docs_url="/docs" if config.environment != "production" else None,
        # Provides the `redoc_url` parameter or keyword argument.
        redoc_url=None,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Checks this condition before executing the nested branch.
    if settings:
        # Executes this statement as the next step in the surrounding logic.
        app.dependency_overrides[get_settings] = lambda: config
    # Calls `app.add_middleware` with the supplied values.
    app.add_middleware(BodyLimitMiddleware, max_bytes=config.request_body_limit_bytes)
    # Calls `app.add_middleware` with the supplied values.
    app.add_middleware(
        # Supplies this item to the surrounding call or collection.
        CORSMiddleware,
        # Provides the `allow_origins` parameter or keyword argument.
        allow_origins=list(config.allowed_origins),
        # Provides the `allow_credentials` parameter or keyword argument.
        allow_credentials=True,
        # Provides the `allow_methods` parameter or keyword argument.
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        # Computes and stores `allow_headers` for subsequent operations.
        allow_headers=[
            # Supplies this item to the surrounding call or collection.
            "Authorization",
            # Supplies this item to the surrounding call or collection.
            "Content-Type",
            # Supplies this item to the surrounding call or collection.
            "Idempotency-Key",
            # Supplies this item to the surrounding call or collection.
            "X-Correlation-ID",
            # Supplies this item to the surrounding call or collection.
            "X-Request-ID",
            # Closes the multiline call, declaration, or collection started above.
        ],
        # Provides the `expose_headers` parameter or keyword argument.
        expose_headers=["Retry-After", "X-Correlation-ID", "X-Request-ID"],
        # Provides the `max_age` parameter or keyword argument.
        max_age=600,
        # Closes the multiline call, declaration, or collection started above.
    )

    # Applies `@app.middleware("http")` to configure the declaration immediately below.
    @app.middleware("http")
    # Defines the `request_context` callable and its typed interface.
    async def request_context(
        # Declares the typed `request` data field.
        request: Request,
        # Supplies this item to the surrounding call or collection.
        call_next: Callable[[Request], Awaitable[Response]],
        # Completes the signature and declares the callable return type.
    ) -> Response:
        # Computes and stores `supplied_id` for subsequent operations.
        supplied_id = request.headers.get("x-request-id", "")
        # Computes and stores `request_id` for subsequent operations.
        request_id = (
            # Executes this statement as the next step in the surrounding logic.
            supplied_id
            # Checks this condition before executing the nested branch.
            if 1 <= len(supplied_id) <= 64 and supplied_id.isascii()
            # Executes this statement as the next step in the surrounding logic.
            else str(uuid.uuid4())
            # Closes the multiline call, declaration, or collection started above.
        )
        # Computes and stores `request.state.request_id` for subsequent operations.
        request.state.request_id = request_id
        # Computes and stores `supplied_correlation_id` for subsequent operations.
        supplied_correlation_id = request.headers.get("x-correlation-id", "")
        # Computes and stores `correlation_id` for subsequent operations.
        correlation_id = (
            # Executes this statement as the next step in the surrounding logic.
            supplied_correlation_id
            # Checks this condition before executing the nested branch.
            if 1 <= len(supplied_correlation_id) <= 64 and supplied_correlation_id.isascii()
            # Executes this statement as the next step in the surrounding logic.
            else request_id
            # Closes the multiline call, declaration, or collection started above.
        )
        # Computes and stores `request.state.correlation_id` for subsequent operations.
        request.state.correlation_id = correlation_id
        # Computes and stores `started` for subsequent operations.
        started = time.perf_counter()
        # Computes and stores `logger` for subsequent operations.
        logger = structlog.get_logger()
        # Computes and stores `client_ip` for subsequent operations.
        client_ip = trusted_client_ip(
            # Uses the current HTTP request or response in this operation.
            request.client.host if request.client else None,
            # Uses the current HTTP request or response in this operation.
            request.headers.get("x-forwarded-for"),
            # Supplies this item to the surrounding call or collection.
            config.trusted_proxy_ips,
            # Closes the multiline call, declaration, or collection started above.
        )
        # Computes and stores `ip_key` for subsequent operations.
        ip_key = hashlib.sha256(f"ip:{client_ip}".encode()).hexdigest()
        # Computes and stores `subject` for subsequent operations.
        subject = _rate_limit_subject(request)
        # Starts a protected operation whose expected failures are handled below.
        try:
            # Checks this condition before executing the nested branch.
            if request.method != "OPTIONS" and request.url.path not in {
                # Supplies this item to the surrounding call or collection.
                "/health/live",
                # Supplies this item to the surrounding call or collection.
                "/health/ready",
                # Supplies this item to the surrounding call or collection.
                "/metrics",
                # Begins the nested block or multiline expression completed below.
            }:
                # Computes and stores `ip_limiter` for subsequent operations.
                ip_limiter: RateLimiter = request.app.state.ip_rate_limiter
                # Waits for this asynchronous operation to complete.
                await ip_limiter.check(ip_key)
                # Checks this condition before executing the nested branch.
                if subject:
                    # Computes and stores `limiter` for subsequent operations.
                    limiter: RateLimiter = request.app.state.rate_limiter
                    # Computes and stores `subject_key` for subsequent operations.
                    subject_key = hashlib.sha256(f"sub:{subject}".encode()).hexdigest()
                    # Waits for this asynchronous operation to complete.
                    await limiter.check(subject_key)
            # Starts a protected operation whose expected failures are handled below.
            try:
                # Acquires this asynchronous managed resource for the nested operation.
                async with asyncio.timeout(config.request_timeout_seconds):
                    # Computes and stores `response` for subsequent operations.
                    response = await call_next(request)
            # Handles the listed exception so failure remains controlled.
            except TimeoutError:
                # Computes and stores `response` for subsequent operations.
                response = JSONResponse(
                    # Begins the nested block or multiline expression completed below.
                    {
                        # Associates the `code` key with its value.
                        "code": "REQUEST_TIMEOUT",
                        # Associates the `message` key with its value.
                        "message": "The service took too long to complete this request.",
                        # Associates the `requestId` key with its value.
                        "requestId": request_id,
                        # Closes the multiline call, declaration, or collection started above.
                    },
                    # Provides the `status_code` parameter or keyword argument.
                    status_code=504,
                    # Closes the multiline call, declaration, or collection started above.
                )
        # Handles the listed exception so failure remains controlled.
        except APIError as exc:
            # Checks this condition before executing the nested branch.
            if exc.status_code == 429:
                # Calls `RATE_LIMITS.inc` with the supplied values.
                RATE_LIMITS.inc()
            # Computes and stores `response` for subsequent operations.
            response = JSONResponse(
                # Supplies this item to the surrounding call or collection.
                {"code": exc.code, "message": exc.message, "requestId": request_id},
                # Provides the `status_code` parameter or keyword argument.
                status_code=exc.status_code,
                # Provides the `headers` parameter or keyword argument.
                headers=exc.headers,
                # Closes the multiline call, declaration, or collection started above.
            )
        # Uses the current HTTP request or response in this operation.
        response.headers["X-Request-ID"] = request_id
        # Uses the current HTTP request or response in this operation.
        response.headers["X-Correlation-ID"] = correlation_id
        # Uses the current HTTP request or response in this operation.
        response.headers["X-Content-Type-Options"] = "nosniff"
        # Uses the current HTTP request or response in this operation.
        response.headers["Referrer-Policy"] = "no-referrer"
        # Uses the current HTTP request or response in this operation.
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        # Uses the current HTTP request or response in this operation.
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
        # Checks this condition before executing the nested branch.
        if request.url.path.startswith("/v1/"):
            # Uses the current HTTP request or response in this operation.
            response.headers["Cache-Control"] = "no-store"
            # Uses the current HTTP request or response in this operation.
            response.headers["Vary"] = "Authorization"
        # Checks this condition before executing the nested branch.
        if config.environment in {"production", "staging"}:
            # Uses the current HTTP request or response in this operation.
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        # Computes and stores `route` for subsequent operations.
        route = request.scope.get("route")
        # Computes and stores `route_name` for subsequent operations.
        route_name = getattr(route, "path", request.url.path)
        # Computes and stores `elapsed` for subsequent operations.
        elapsed = time.perf_counter() - started
        # Calls `HTTP_REQUESTS.labels` with the supplied values.
        HTTP_REQUESTS.labels(request.method, route_name, str(response.status_code)).inc()
        # Calls `HTTP_LATENCY.labels` with the supplied values.
        HTTP_LATENCY.labels(request.method, route_name).observe(elapsed)
        # Checks this condition before executing the nested branch.
        if route_name.endswith("/attempts"):
            # Calls `GUESS_LATENCY.observe` with the supplied values.
            GUESS_LATENCY.observe(elapsed)
        # Checks this condition before executing the nested branch.
        if response.status_code >= 400:
            # Calls `HTTP_ERRORS.labels` with the supplied values.
            HTTP_ERRORS.labels(route_name, str(response.status_code)).inc()
        # Records this diagnostic event for operational visibility.
        logger.info(
            # Supplies this item to the surrounding call or collection.
            "http_request",
            # Provides the `request_id` parameter or keyword argument.
            request_id=request_id,
            # Provides the `correlation_id` parameter or keyword argument.
            correlation_id=correlation_id,
            # Provides the `method` parameter or keyword argument.
            method=request.method,
            # Provides the `route` parameter or keyword argument.
            route=route_name,
            # Provides the `status` parameter or keyword argument.
            status=response.status_code,
            # Provides the `duration_ms` parameter or keyword argument.
            duration_ms=round(elapsed * 1000, 2),
            # Provides the `environment` parameter or keyword argument.
            environment=config.environment,
            # Provides the `release` parameter or keyword argument.
            release=config.release,
            # Closes the multiline call, declaration, or collection started above.
        )
        # Returns this result to the caller and ends the current function.
        return response

    # Applies `@app.exception_handler(APIError)` to configure the declaration immediately below.
    @app.exception_handler(APIError)
    # Defines the `api_error_handler` callable and its typed interface.
    async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
        # Checks this condition before executing the nested branch.
        if exc.status_code == 401:
            # Calls `AUTH_FAILURES.inc` with the supplied values.
            AUTH_FAILURES.inc()
        # Returns this result to the caller and ends the current function.
        return JSONResponse(
            # Supplies this item to the surrounding call or collection.
            {"code": exc.code, "message": exc.message, "requestId": request.state.request_id},
            # Provides the `status_code` parameter or keyword argument.
            status_code=exc.status_code,
            # Provides the `headers` parameter or keyword argument.
            headers=exc.headers,
            # Closes the multiline call, declaration, or collection started above.
        )

    # Applies `@app.exception_handler(DomainError)` to configure the declaration immediately below.
    @app.exception_handler(DomainError)
    # Defines the `domain_error_handler` callable and its typed interface.
    async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
        # Checks this condition before executing the nested branch.
        if exc.code in {"SECRET_KEY_UNAVAILABLE", "SECRET_DECRYPTION_FAILED"}:
            # Computes and stores `status_code` for subsequent operations.
            status_code = 503
        # Checks this alternative when previous conditions were false.
        elif exc.code in {"GAME_NOT_ACTIVE", "ILLEGAL_GAME_TRANSITION"}:
            # Computes and stores `status_code` for subsequent operations.
            status_code = 409
        # Handles the remaining case not matched by earlier branches.
        else:
            # Computes and stores `status_code` for subsequent operations.
            status_code = 422
        # Returns this result to the caller and ends the current function.
        return JSONResponse(
            # Supplies this item to the surrounding call or collection.
            {"code": exc.code, "message": exc.message, "requestId": request.state.request_id},
            # Provides the `status_code` parameter or keyword argument.
            status_code=status_code,
            # Closes the multiline call, declaration, or collection started above.
        )

    # Applies `@app.exception_handler(RequestValidationError)` to configure the declaration
    # immediately below.
    @app.exception_handler(RequestValidationError)
    # Defines the `validation_error_handler` callable and its typed interface.
    async def validation_error_handler(
        # Declares the typed `request` data field.
        request: Request,
        # Supplies this item to the surrounding call or collection.
        exc: RequestValidationError,
        # Completes the signature and declares the callable return type.
    ) -> JSONResponse:
        # Computes and stores `first` for subsequent operations.
        first = exc.errors()[0] if exc.errors() else {}
        # Computes and stores `message` for subsequent operations.
        message = str(first.get("msg", "The request is invalid.")).removeprefix("Value error, ")
        # Returns this result to the caller and ends the current function.
        return JSONResponse(
            # Supplies this item to the surrounding call or collection.
            {"code": "VALIDATION_ERROR", "message": message, "requestId": request.state.request_id},
            # Provides the `status_code` parameter or keyword argument.
            status_code=422,
            # Closes the multiline call, declaration, or collection started above.
        )

    # Applies `@app.exception_handler(IntegrityError)` to configure the declaration immediately
    # below.
    @app.exception_handler(DuplicateKeyError)
    # Defines the `integrity_error_handler` callable and its typed interface.
    async def integrity_error_handler(request: Request, exc: DuplicateKeyError) -> JSONResponse:
        # Calls `structlog.get_logger` with the supplied values.
        structlog.get_logger().warning("database_conflict", request_id=request.state.request_id)
        # Returns this result to the caller and ends the current function.
        return JSONResponse(
            # Begins the nested block or multiline expression completed below.
            {
                # Associates the `code` key with its value.
                "code": "RESOURCE_CONFLICT",
                # Associates the `message` key with its value.
                "message": "That change conflicts with an existing record.",
                # Associates the `requestId` key with its value.
                "requestId": request.state.request_id,
                # Closes the multiline call, declaration, or collection started above.
            },
            # Provides the `status_code` parameter or keyword argument.
            status_code=409,
            # Closes the multiline call, declaration, or collection started above.
        )

    # Applies `@app.exception_handler(Exception)` to configure the declaration immediately below.
    @app.exception_handler(Exception)
    # Defines the `unexpected_error_handler` callable and its typed interface.
    async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
        # Calls `structlog.get_logger` with the supplied values.
        structlog.get_logger().exception("unhandled_error", request_id=request.state.request_id)
        # Computes and stores `reporter` for subsequent operations.
        reporter: ErrorReporter = request.app.state.error_reporter
        # Checks this condition before executing the nested branch.
        if reporter.enabled:
            # Computes and stores `route` for subsequent operations.
            route = request.scope.get("route")
            # Computes and stores `route_name` for subsequent operations.
            route_name = getattr(route, "path", request.url.path)
            # Computes and stores `task` for subsequent operations.
            task = asyncio.create_task(
                # Calls `reporter.capture` with the supplied values.
                reporter.capture(
                    # Provides the `code` parameter or keyword argument.
                    code="INTERNAL_ERROR",
                    # Provides the `request_id` parameter or keyword argument.
                    request_id=request.state.request_id,
                    # Provides the `correlation_id` parameter or keyword argument.
                    correlation_id=request.state.correlation_id,
                    # Provides the `route` parameter or keyword argument.
                    route=route_name,
                    # Closes the multiline call, declaration, or collection started above.
                )
                # Closes the multiline call, declaration, or collection started above.
            )
            # Computes and stores `reporting_tasks` for subsequent operations.
            reporting_tasks: set[asyncio.Task[None]] = request.app.state.error_reporting_tasks
            # Calls `reporting_tasks.add` with the supplied values.
            reporting_tasks.add(task)
            # Calls `task.add_done_callback` with the supplied values.
            task.add_done_callback(reporting_tasks.discard)
        # Returns this result to the caller and ends the current function.
        return JSONResponse(
            # Begins the nested block or multiline expression completed below.
            {
                # Associates the `code` key with its value.
                "code": "INTERNAL_ERROR",
                # Associates the `message` key with its value.
                "message": "The service could not complete your request.",
                # Associates the `requestId` key with its value.
                "requestId": request.state.request_id,
                # Closes the multiline call, declaration, or collection started above.
            },
            # Provides the `status_code` parameter or keyword argument.
            status_code=500,
            # Closes the multiline call, declaration, or collection started above.
        )

    # Applies `@app.get("/health/live", include_in_schema=False)` to configure the declaration
    # immediately below.
    @app.get("/health/live", include_in_schema=False)
    # Defines the `live` callable and its typed interface.
    async def live() -> dict[str, str]:
        # Returns this result to the caller and ends the current function.
        return {"status": "ok", "release": config.release}

    # Applies `@app.get("/health/ready", include_in_schema=False)` to configure the declaration
    # immediately below.
    @app.get("/health/ready", include_in_schema=False)
    # Defines the `ready` callable and its typed interface.
    async def ready(request: Request) -> JSONResponse:
        # Stores `mongo_ready` because later steps depend on this value.
        mongo_ready = await database_ready()
        # Computes and stores `redis_required` for subsequent operations.
        redis_required = config.environment in {"production", "staging"}
        # Computes and stores `redis` for subsequent operations.
        redis = request.app.state.redis
        # Computes and stores `redis_ready` for subsequent operations.
        redis_ready = redis is None and not redis_required
        # Checks this condition before executing the nested branch.
        if redis is not None:
            # Starts a protected operation whose expected failures are handled below.
            try:
                # Waits for this asynchronous operation to complete.
                await redis.ping()
                # Computes and stores `redis_ready` for subsequent operations.
                redis_ready = True
            # Handles the listed exception so failure remains controlled.
            except RedisError:
                # Computes and stores `redis_ready` for subsequent operations.
                redis_ready = False
        # Computes and stores `request.app.state.redis_ready` for subsequent operations.
        request.app.state.redis_ready = redis_ready
        # Calls `DEPENDENCY_READY.labels` with the supplied values.
        DEPENDENCY_READY.labels("mongodb").set(1 if mongo_ready else 0)
        # Calls `DEPENDENCY_READY.labels` with the supplied values.
        DEPENDENCY_READY.labels("redis").set(1 if redis_ready else 0)
        # Computes and stores `healthy` for subsequent operations.
        healthy = mongo_ready and (redis_ready or not redis_required)
        # Returns this result to the caller and ends the current function.
        return JSONResponse(
            # Begins the nested block or multiline expression completed below.
            {
                # Associates the `status` key with its value.
                "status": "ok" if healthy else "degraded",
                # Associates the `database` key with its value.
                "database": "ok" if mongo_ready else "unavailable",
                # Associates the `redis` key with its value.
                "redis": "ok" if redis_ready else "unavailable",
                # Associates the `release` key with its value.
                "release": config.release,
                # Closes the multiline call, declaration, or collection started above.
            },
            # Provides the `status_code` parameter or keyword argument.
            status_code=200 if healthy else 503,
            # Closes the multiline call, declaration, or collection started above.
        )

    # Applies `@app.get("/metrics", include_in_schema=False)` to configure the declaration
    # immediately below.
    @app.get("/metrics", include_in_schema=False)
    # Defines the `metrics` callable and its typed interface.
    async def metrics() -> Response:
        # Checks this condition before executing the nested branch.
        if not config.metrics_enabled:
            # Raises this exception to report an invalid or failed operation.
            raise APIError(404, "NOT_FOUND", "Not found.")
        # Starts a protected operation whose expected failures are handled below.
        try:
            # Scopes this resource so acquisition and cleanup remain paired.
            async with SessionFactory() as session:
                # Imports the required names from `.models` for this module.
                from .models import GameSession, MultiplayerRoom

                # Stores `active_games` because later steps depend on this value.
                active_games = await session.count(GameSession, {"status": "active"})
                # Stores `active_rooms` because later steps depend on this value.
                active_rooms = await session.count(
                    # Supplies this required nested value.
                    MultiplayerRoom,
                    {"status": {"$in": ["waiting", "active"]}},
                    # Closes the multiline declaration, call, or collection opened above.
                )
                # Calls `ACTIVE_GAMES.set` with the supplied values.
                ACTIVE_GAMES.set(int(active_games or 0))
                # Calls `ACTIVE_ROOMS.set` with the supplied values.
                ACTIVE_ROOMS.set(int(active_rooms or 0))
        # Handles the listed exception so failure remains controlled.
        except PyMongoError:
            # Readiness exposes database failure. Metrics remain scrapeable so
            # the failure itself does not blind operators.
            # Calls `ACTIVE_GAMES.set` with the supplied values.
            ACTIVE_GAMES.set(float("nan"))
            # Calls `ACTIVE_ROOMS.set` with the supplied values.
            ACTIVE_ROOMS.set(float("nan"))
        # Returns this result to the caller and ends the current function.
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    # Calls `app.include_router` with the supplied values.
    app.include_router(auth.router)
    # Supplies this required nested value.
    app.include_router(games.router)
    # Calls `app.include_router` with the supplied values.
    app.include_router(daily.router)
    # Calls `app.include_router` with the supplied values.
    app.include_router(challenges.router)
    # Calls `app.include_router` with the supplied values.
    app.include_router(rooms.router)
    # Calls `app.include_router` with the supplied values.
    app.include_router(leaderboards.router)
    # Calls `app.include_router` with the supplied values.
    app.include_router(profile.router)
    # Calls `app.include_router` with the supplied values.
    app.include_router(support.router)
    # Calls `app.include_router` with the supplied values.
    app.include_router(analytics.router)
    # Calls `app.include_router` with the supplied values.
    app.include_router(admin.router)
    # Returns this result to the caller and ends the current function.
    return app


# Computes and stores `app` for subsequent operations.
app = create_app()
