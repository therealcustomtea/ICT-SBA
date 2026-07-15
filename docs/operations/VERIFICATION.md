# Verification and evidence

## Policy

Targets and measured results are different. Documentation may state a target before it is met, but may say a check passed only when the exact command completed successfully in the cited environment. Partial suites, mocked persistence, or SQLite do not stand in for required PostgreSQL integration evidence. External-service blockers record the missing service, substitute evidence, and exact remaining check.

Launch coverage gates are:

- canonical Python core: at least 95% branch coverage;
- tested web surface: at least 80% statement coverage and 75% branch coverage;
- API/CLI/integration code: tracked and increased through risk-based tests, with no numeric production claim until a reviewed threshold is configured and achieved.

A broader-backend development measurement of 68% is diagnostic only. It is neither a launch target nor evidence that security, concurrency, account deletion, admin, or real-time paths are adequately tested. Coverage never replaces required behavior/integration checks.

## Frozen dependency and static checks

```bash
uv sync --all-extras --frozen
uv run ruff format --check .
uv run ruff check .
uv run mypy .
pnpm install --frozen-lockfile
pnpm lint
pnpm typecheck
pnpm test
```

## Core and backend

```bash
uv run pytest \
  --cov=packages/mastermind_core/mastermind_core \
  --cov-branch \
  --cov-report=term-missing \
  --cov-fail-under=95
```

With isolated PostgreSQL 17 and Redis configured:

```bash
uv run alembic -c apps/api/alembic.ini upgrade head
uv run alembic -c apps/api/alembic.ini check
uv run pytest tests/api -m postgres
```

Database evidence includes upgrade from empty, constraint/grant inspection, current revision, one supported downgrade/upgrade cycle, and tests for authentication, owner/member/admin denial, secret omission, idempotency, concurrent final attempts, daily uniqueness/rollover, challenge revocation/expiry, leaderboard exclusion, account-deletion retry, and audit atomicity.

Retention evidence additionally checks mode-specific deadlines, request-time expiry, dependency-ordered SQLite cleanup, and PostgreSQL resumability while an expired row is locked:

```bash
uv run pytest tests/api/test_retention.py
uv run pytest tests/api/test_retention.py -m postgres
```

## Web, end-to-end, and accessibility

```bash
pnpm --filter @mastermind/web test -- --coverage
pnpm build
pnpm exec playwright install chromium webkit
pnpm test:e2e
pnpm test:a11y
```

The coverage artifact must demonstrate at least 80% statements and 75% branches over the declared tested web surface. Playwright evidence uses semantic selectors and covers guest/registered flows, keyboard and screen-reader announcements, both locales, responsive/light/dark/reduced-motion states, refresh/reconnect/offline behavior, account deletion, admin allow/deny, and two independent duel clients.

## Contracts and infrastructure

```bash
pnpm generate:api
git diff --exit-code -- packages/api_client/src/schema.ts
docker compose config --quiet
docker build -f infra/docker/api.Dockerfile -t mastermind-api:verify .
docker build -f infra/docker/web.Dockerfile \
  --build-arg NEXT_PUBLIC_API_ORIGIN=https://api.example.invalid \
  --build-arg NEXT_PUBLIC_PRODUCT_ORIGIN=https://play.example.invalid \
  --build-arg NEXT_PUBLIC_SUPABASE_URL=https://test.supabase.co \
  --build-arg NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=sb_publishable_ci_validation_only \
  --build-arg NEXT_PUBLIC_PRODUCT_NAME=Cipherboard \
  --build-arg NEXT_PUBLIC_SUPPORT_EMAIL=support@example.com \
  --build-arg NEXT_PUBLIC_LEGAL_ENTITY='CI Test Entity' \
  --build-arg NEXT_PUBLIC_JURISDICTION=CI \
  --build-arg NEXT_PUBLIC_POLICY_DATE=2026-07-15 \
  -t mastermind-web:verify .
```

Run both images as non-root/read-only with the production Compose security settings, verify liveness/readiness and graceful SIGTERM, and scan the filesystem/image for critical vulnerabilities and secrets. Verify the web bundle contains the Supabase publishable key only.

## Endpoint discovery checks

An admin token with recent authentication can page `GET /v1/admin/games`, `/profiles`, `/rooms`, `/challenges`, and `/leaderboard-review`; a normal registered and anonymous token receives 403. `GET /v1/admin/summary`, `/flags`, and `/audit` follow the same rule. Discovery payloads are scanned for `secret`, ciphertext, invite token, email, and private guess material.

`POST /v1/support` requires authentication, validates the documented bounded payload, returns 202 on acceptance, and rate-limits repeated use. Its database row is visible only to authorized operational paths.

The real-time handshake calls `POST /v1/rooms/{room_id}/ws-ticket`, receives `ticket` and `expiresAt`, then connects to `/v1/rooms/{room_id}/events?after=…` while offering `cipherboard-v1` and `ticket.{ticket}` in `Sec-WebSocket-Protocol`. The server negotiates only `cipherboard-v1`. Tests cover URL credential omission, single use, 60-second expiry, wrong room/user, unauthorized membership, replay after sequence, heartbeat timeout, safe shared payloads, and Redis failure.

## Load and resilience

```bash
k6 run tests/load/gameplay.js
k6 run tests/load/realtime.js
```

Supply the documented short-lived test identity and isolated load target. Record settings and measured p50/p95/p99 rather than converting targets into claims. Exercise PostgreSQL, Redis, Auth/JWKS, analytics, broker, and deployment-drain failures separately and record the expected fail-closed or degraded response.
