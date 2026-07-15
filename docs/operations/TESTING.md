# Testing and release validation

Use the pinned runtimes and frozen lockfiles. Start PostgreSQL and Redis for service-backed checks; CI also starts an isolated Supabase Auth stack for browser authentication.

## Static, unit, and coverage checks

```bash
uv sync --all-extras --frozen
uv run ruff format --check .
uv run ruff check .
uv run mypy .
uv run pytest
uv run pytest tests/core --cov=mastermind_core --cov-branch --cov-fail-under=95

pnpm install --frozen-lockfile
pnpm lint
pnpm typecheck
pnpm test
pnpm build
```

The core branch gate is 95%. Web coverage is produced by Vitest. A passing SQLite-focused API test does not replace the PostgreSQL marker suite for locks, constraints, grants, or concurrency.

## PostgreSQL, migrations, and contracts

```bash
docker compose up -d postgres redis
uv run alembic -c apps/api/alembic.ini upgrade head
uv run alembic -c apps/api/alembic.ini check
uv run pytest tests/api -m postgres
pnpm generate:api
git diff --exit-code -- packages/api_client/src/schema.ts
```

Set `MASTERMIND_TEST_POSTGRES_URL` and `MASTERMIND_TEST_REDIS_URL` to isolated test services. Validate an empty upgrade, one supported downgrade/upgrade cycle, runtime grants, and the current revision.

## Browser and accessibility

```bash
pnpm --filter @mastermind/web exec playwright install chromium webkit
pnpm test:e2e
pnpm test:a11y
```

Browser evidence covers both locales, keyboard gameplay, semantic announcements, guest authentication, refresh/reconnect/offline behavior, responsive layouts, reduced motion, private-page indexing, account controls, admin denial, and two-client rooms. Complete the manual checklist in `docs/product/ACCESSIBILITY.md` before launch.

In CI, Playwright owns the Next.js development server for the browser run so its HTTP and HMR lifecycles start and stop with the test process. The API and backing services are readied separately before Playwright starts.

## Containers, security, and load

```bash
docker compose config --quiet
docker compose build api web
docker compose up -d
curl --fail http://127.0.0.1:8000/health/ready
curl --fail http://127.0.0.1:3000/
k6 run tests/load/gameplay.js
k6 run tests/load/realtime.js
```

GitHub Actions additionally runs CodeQL, dependency review, Gitleaks, Trivy, migration drift, OpenAPI drift, container builds, and uploads coverage/browser artifacts. Record load environment, concurrency, duration, and measured percentiles; targets are not measurements.
