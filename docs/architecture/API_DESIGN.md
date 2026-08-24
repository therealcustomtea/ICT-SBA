# API design

## Contract

FastAPI publishes OpenAPI for all JSON routes. `packages/api_client` is generated from that document. Timestamps are UTC ISO 8601 values, enum values are stable lowercase identifiers, and public response models are explicit allowlists rather than ORM serialization.

Errors use one stable shape:

```json
{
  "code": "INVALID_GUESS_LENGTH",
  "message": "Your guess must contain exactly four pegs.",
  "requestId": "01J..."
}
```

The message is safe for people; the code drives localized web copy. Internal exceptions and ciphertext never enter the response.

## Routes

| Area | Routes |
| --- | --- |
| Games | `POST /v1/games`, `GET /v1/games/{id}`, `POST /v1/games/{id}/attempts`, `POST /v1/games/{id}/abandon` |
| Daily | `GET /v1/daily`, `POST /v1/daily/start`, `GET /v1/daily/leaderboard` |
| Friend challenges | `POST /v1/challenges`, `GET /v1/challenges/mine`, `GET /v1/challenges/{shareCode}`, `POST /v1/challenges/{shareCode}/start`, `GET /v1/challenges/{id}/results`, `DELETE /v1/challenges/{id}` |
| Rooms | `POST /v1/rooms`, `POST /v1/rooms/{code}/join`, `GET /v1/rooms/{id}`, `POST /v1/rooms/{id}/ready`, `POST /v1/rooms/{id}/ws-ticket`, `WS /v1/rooms/{id}/events` |
| Player | `GET/PATCH /v1/me/profile`, `GET /v1/me/stats`, `GET /v1/me/games`, `GET /v1/me/export`, `DELETE /v1/me` |
| Analytics | `POST /v1/analytics/events` (authenticated, explicit consent, closed event schema, feature flagged) |
| Public | `GET /v1/leaderboards` |
| Admin | `GET /v1/admin/summary`, moderation, invalidation, room, flag, and audit routes under `/v1/admin` |
| Operations | `GET /health/live`, `GET /health/ready`, `GET /metrics` |

## Authentication and authorization

All game creation uses a real first-party authentication subject, including guests. Public challenge descriptions and leaderboards disclose only safe public fields. The API checks ownership or membership in the database query; a client knowing a UUID or share code is not authorization. Admin access is denied by default and depends on a server-side grant, not route obscurity or editable user metadata.

## Idempotency and retry

Game creation and attempt submission accept bounded idempotency keys. Reusing a key for the same operation returns the stored result. Reusing it with a different payload is rejected. Database unique constraints are the final guard against concurrent duplicates. Clients retry only idempotent requests and must resynchronize after reconnecting.

Creation requests persist an HMAC fingerprint of the canonical operation and payload. The HMAC prevents low-entropy human secrets from becoming offline-verifiable hashes. Game, challenge, and room retries compare the fingerprint before returning an existing record; official daily and friend starts additionally recover the one unique authoritative run after a concurrent insert.

Registered profiles may own at most 25 unexpired, unrevoked friend challenges; guest profiles may own at most 3. Creation locks the profile before counting so concurrent requests cannot exceed the allowance; idempotent retries are resolved before the allowance check.

`GET /v1/challenges/mine` is owner-scoped, paginated, and returns management identifiers and aggregate completion state without returning the one-time share capability. Expired or revoked public capability lookups use the same generic not-found response as unknown tokens.

`GET /v1/challenges/{id}/results` is creator-only and paginated. It returns aggregate statistics plus ranked, pseudonymous result rows; it never returns a user ID, display name, email address, guess history, or secret. Rows use the documented score, attempt, validated-time, completion-time, and stable-ID tie-break order. `GET /v1/me/stats` bounds daily completion history to the latest 90 UTC challenge dates and exposes only the server-calculated `logic_week` progress pair, capped at its target of seven distinct completed daily challenges.

`GET /v1/me/export` is registered-account-only and returns `cipherboard-data.zip`. The archive contains a manifest, profile JSON, and separate game, attempt, achievement, challenge, and room CSV files. It excludes Auth data, secret codes, invite tokens, idempotency keys, and encryption material. `DELETE /v1/me` is also registered-account-only, requires the exact JSON body `{ "confirmation": "DELETE" }` and a bearer session authenticated within the configured recent-authentication window. It hides and anonymizes application data first, globally revokes the presented first-party authentication session, and then deletes the Auth identity. Provider failure leaves a durable retry row consumed by the bounded application worker.

Analytics collection is disabled unless both the environment and database feature flags permit it. The endpoint requires `consent: true` and the supported consent version, accepts only documented event-specific enum and bounded numeric fields, derives the anonymous flag from the verified principal, and stores no user identifier, IP address, title, guess, secret, token, or arbitrary property object. Client event UUIDs make safe retries idempotent.

## Pagination and sorting

List routes have a bounded `pageSize` (maximum 100). Public leaderboard order is:

1. score descending;
2. attempts ascending;
3. validated elapsed time ascending;
4. completion timestamp ascending;
5. immutable row identifier for stable pagination.

Creator-only friend-challenge result boards use the same deterministic order against their game-session fields. Their response rank is global across pages rather than restarting at one on every page.

## Secret omission

`GameResponse.secret` is `null` while a session is active. Terminal results may reveal the secret only for modes whose rules allow it. Challenge descriptions, daily definitions, room state, leaderboard data, WebSocket events, analytics, logs, and CSV exports have no secret field.

## Request safety

The production deployment sets exact CORS origins, maximum body size, request timeouts, per-IP and per-subject rate limits, correlation IDs, and safe security headers. The configured baseline applies to each authenticated subject and to action-specific buckets; a separate aggregate IP guardrail is derived at ten times that baseline so users behind shared NAT are not forced into one account-sized budget. CORS preflight requests do not consume either budget. JWTs are accepted in `Authorization: Bearer` only; the game API does not use ambient cookies, reducing CSRF exposure.
