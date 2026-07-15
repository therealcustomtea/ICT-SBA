from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram

HTTP_REQUESTS = Counter(
    "mastermind_http_requests_total",
    "HTTP requests received",
    ("method", "route", "status"),
)
HTTP_LATENCY = Histogram(
    "mastermind_http_request_duration_seconds",
    "HTTP request latency",
    ("method", "route"),
)
HTTP_ERRORS = Counter(
    "mastermind_http_errors_total",
    "HTTP error responses",
    ("route", "status"),
)
AUTH_FAILURES = Counter("mastermind_auth_failures_total", "Authentication failures")
RATE_LIMITS = Counter("mastermind_rate_limits_total", "Rate limit rejections")
GUESS_LATENCY = Histogram(
    "mastermind_guess_submission_duration_seconds",
    "Authoritative guess-submission request latency",
)
ACTIVE_GAMES = Gauge("mastermind_active_games", "Durable active game sessions")
ACTIVE_ROOMS = Gauge("mastermind_active_rooms", "Durable waiting or active multiplayer rooms")
DEPENDENCY_READY = Gauge(
    "mastermind_dependency_ready",
    "Dependency readiness (1 ready, 0 unavailable)",
    ("dependency",),
)
WEBSOCKET_CONNECTIONS = Gauge(
    "mastermind_websocket_connections",
    "WebSocket connections held by this API process",
)
WEBSOCKET_RECONNECTS = Counter(
    "mastermind_websocket_reconnects_total",
    "Authorized WebSocket connections requesting durable replay",
)
LEADERBOARD_LATENCY = Histogram(
    "mastermind_leaderboard_query_duration_seconds",
    "Leaderboard request latency including cache lookup",
    ("board",),
)
