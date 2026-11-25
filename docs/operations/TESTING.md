# Testing

Use the pinned runtimes and frozen lockfiles. API integration tests require a MongoDB replica set; Redis is required for real-time and shared-rate-limit paths.

```bash
docker compose up -d mongo redis mailpit
uv run mastermind-initialize
uv run ruff format --check .
uv run ruff check .
uv run mypy .
uv run pytest
pnpm format:check
pnpm lint
pnpm typecheck
pnpm test
pnpm build
```

The API fixture creates a randomly named database for each test, initializes indexes, and drops only that exact database during cleanup. Never point tests at a production database or reuse production secrets.

End-to-end tests start the API, web app, MongoDB replica set, Redis, and Mailpit. The account lifecycle test verifies guest creation, in-place email upgrade, export, permanent deletion, and replacement guest creation. CI also checks generated OpenAPI client drift and hardened container builds.

The CLI has offline/controller tests, mocked transport tests, real authenticated API tests, and a two-client WebSocket room test. `tests/cli/test_online_api.py` and `tests/cli/test_online_rooms.py` require the isolated MongoDB replica set and Redis described above. The WebSocket test starts its own local listener and also invokes the module entry point as a subprocess. See [CLI operations](CLI.md) for connection options and separate state directories for multiple players.
