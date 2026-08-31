# Verification

Run the pinned dependency and static checks:

```bash
uv sync --all-extras --frozen
pnpm install --frozen-lockfile
uv run ruff format --check .
uv run ruff check .
uv run mypy .
pnpm format:check
pnpm lint
pnpm typecheck
```

With a MongoDB replica set and Redis available:

```bash
uv run mastermind-initialize
uv run pytest
pnpm test
pnpm build
```

Verify the real auth path with guest creation, refresh rotation, an authenticated profile request, logout, refresh rejection, email-link upgrade through Mailpit, and account deletion. Verify MongoDB index initialization and transaction rollback with `tests/api/test_migration_realtime.py`.

For containers, run `docker compose config --quiet`, build both images, and confirm non-root/read-only execution, liveness/readiness, graceful shutdown, and secret scanning. For a release, also verify one daily game, one leaderboard result, one friend challenge, and one two-client duel.
