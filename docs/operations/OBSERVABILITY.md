# Observability and alert examples

The API emits structured JSON to stdout and Prometheus text at `/metrics` when enabled. Production ingress restricts metrics to the monitoring network. Logs include UTC time, severity, environment, immutable release, request ID, correlation ID, method, route template, status, and duration. Redaction runs after exception formatting and removes credentials, cookies, secrets, ciphertext, guesses, emails, and exception payloads.

Optional error reporting sends only an allowlisted envelope (`code`, route template, request/correlation IDs, environment, release) to the configured HTTPS endpoint. It never sends an exception string, request body, identity, token, secret, guess, or email, and delivery failure does not replace the original response.

## Bounded metrics

- `mastermind_http_requests_total` and `mastermind_http_request_duration_seconds`
- `mastermind_http_errors_total`, `mastermind_auth_failures_total`, and `mastermind_rate_limits_total`
- `mastermind_guess_submission_duration_seconds`
- `mastermind_active_games` and `mastermind_active_rooms`
- `mastermind_websocket_connections` and `mastermind_websocket_reconnects_total`
- `mastermind_leaderboard_query_duration_seconds`
- `mastermind_dependency_ready{dependency="mongodb|redis"}`

Routes are FastAPI templates, not raw URLs, so invite codes and game IDs never become labels. Metrics contain no profile, room, game, IP, email, or challenge identifiers.

## Example PromQL

```promql
# API request p95 over five minutes
histogram_quantile(0.95,
  sum by (le, route) (rate(mastermind_http_request_duration_seconds_bucket[5m])))

# Authoritative attempt p95
histogram_quantile(0.95,
  sum by (le) (rate(mastermind_guess_submission_duration_seconds_bucket[5m])))

# Five-minute server-error ratio
sum(rate(mastermind_http_requests_total{status=~"5.."}[5m]))
/
clamp_min(sum(rate(mastermind_http_requests_total[5m])), 0.001)

# Reconnect rate and current local sockets
rate(mastermind_websocket_reconnects_total[5m])
mastermind_websocket_connections

# Public leaderboard p95
histogram_quantile(0.95,
  sum by (le, board) (rate(mastermind_leaderboard_query_duration_seconds_bucket[5m])))
```

## Initial alert policy

Page on sustained readiness loss, elevated 5xx ratio, or evidence of ranked-integrity failure. Ticket sustained latency, reconnect, auth-failure, or rate-limit anomalies after checking traffic changes and release metadata. Tune thresholds from production baselines; do not invent measured values from local runs. Link alerts to `INCIDENT_RUNBOOK.md`, the active release, dashboard window, and request/correlation IDs.
