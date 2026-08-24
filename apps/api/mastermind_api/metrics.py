# Defers type-annotation evaluation to support modern hints safely.
from __future__ import annotations

# Imports selected names from `prometheus_client` for use in this module.
from prometheus_client import Counter, Gauge, Histogram

# Computes and stores `HTTP_REQUESTS` for subsequent operations.
HTTP_REQUESTS = Counter(
    # Supplies this item to the surrounding call or collection.
    "mastermind_http_requests_total",
    # Supplies this item to the surrounding call or collection.
    "HTTP requests received",
    # Supplies this item to the surrounding call or collection.
    ("method", "route", "status"),
    # Closes the multiline call, declaration, or collection started above.
)
# Computes and stores `HTTP_LATENCY` for subsequent operations.
HTTP_LATENCY = Histogram(
    # Supplies this item to the surrounding call or collection.
    "mastermind_http_request_duration_seconds",
    # Supplies this item to the surrounding call or collection.
    "HTTP request latency",
    # Supplies this item to the surrounding call or collection.
    ("method", "route"),
    # Closes the multiline call, declaration, or collection started above.
)
# Computes and stores `HTTP_ERRORS` for subsequent operations.
HTTP_ERRORS = Counter(
    # Supplies this item to the surrounding call or collection.
    "mastermind_http_errors_total",
    # Supplies this item to the surrounding call or collection.
    "HTTP error responses",
    # Supplies this item to the surrounding call or collection.
    ("route", "status"),
    # Closes the multiline call, declaration, or collection started above.
)
# Computes and stores `AUTH_FAILURES` for subsequent operations.
AUTH_FAILURES = Counter("mastermind_auth_failures_total", "Authentication failures")
# Computes and stores `RATE_LIMITS` for subsequent operations.
RATE_LIMITS = Counter("mastermind_rate_limits_total", "Rate limit rejections")
# Computes and stores `GUESS_LATENCY` for subsequent operations.
GUESS_LATENCY = Histogram(
    # Supplies this item to the surrounding call or collection.
    "mastermind_guess_submission_duration_seconds",
    # Supplies this item to the surrounding call or collection.
    "Authoritative guess-submission request latency",
    # Closes the multiline call, declaration, or collection started above.
)
# Computes and stores `ACTIVE_GAMES` for subsequent operations.
ACTIVE_GAMES = Gauge("mastermind_active_games", "Durable active game sessions")
# Computes and stores `ACTIVE_ROOMS` for subsequent operations.
ACTIVE_ROOMS = Gauge("mastermind_active_rooms", "Durable waiting or active multiplayer rooms")
# Computes and stores `DEPENDENCY_READY` for subsequent operations.
DEPENDENCY_READY = Gauge(
    # Supplies this item to the surrounding call or collection.
    "mastermind_dependency_ready",
    # Supplies this item to the surrounding call or collection.
    "Dependency readiness (1 ready, 0 unavailable)",
    # Supplies this item to the surrounding call or collection.
    ("dependency",),
    # Closes the multiline call, declaration, or collection started above.
)
# Computes and stores `WEBSOCKET_CONNECTIONS` for subsequent operations.
WEBSOCKET_CONNECTIONS = Gauge(
    # Supplies this item to the surrounding call or collection.
    "mastermind_websocket_connections",
    # Supplies this item to the surrounding call or collection.
    "WebSocket connections held by this API process",
    # Closes the multiline call, declaration, or collection started above.
)
# Computes and stores `WEBSOCKET_RECONNECTS` for subsequent operations.
WEBSOCKET_RECONNECTS = Counter(
    # Supplies this item to the surrounding call or collection.
    "mastermind_websocket_reconnects_total",
    # Supplies this item to the surrounding call or collection.
    "Authorized WebSocket connections requesting durable replay",
    # Closes the multiline call, declaration, or collection started above.
)
# Computes and stores `LEADERBOARD_LATENCY` for subsequent operations.
LEADERBOARD_LATENCY = Histogram(
    # Supplies this item to the surrounding call or collection.
    "mastermind_leaderboard_query_duration_seconds",
    # Supplies this item to the surrounding call or collection.
    "Leaderboard request latency including cache lookup",
    # Supplies this item to the surrounding call or collection.
    ("board",),
    # Closes the multiline call, declaration, or collection started above.
)
