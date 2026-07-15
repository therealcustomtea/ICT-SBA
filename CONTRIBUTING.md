# Contributing to Cipherboard

Cipherboard is a security-sensitive game service. Keep changes narrow, preserve server authority, and include evidence for every changed behavior.

## Development setup

Use the pinned Python, Node.js, uv, and pnpm versions from `.python-version`, `.node-version`, `pyproject.toml`, and `package.json`.

```bash
cp .env.example .env
infra/scripts/bootstrap-local-env.sh
uv sync --all-extras --frozen
pnpm install --frozen-lockfile
docker compose up -d postgres redis
uv run alembic -c apps/api/alembic.ini upgrade head
```

Run the API, web application, or CLI with the commands in `README.md`. Never commit `.env`, credentials, generated local data, dependency directories, or build output.

## Change workflow

1. Branch from the current integration branch with a descriptive `feat/`, `fix/`, `docs/`, or `chore/` name.
2. Inspect adjacent implementation, tests, migrations, contracts, and documentation before editing.
3. Keep authoritative rules in `mastermind_core`; clients never calculate accepted feedback, ranked scores, or terminal state.
4. Add a reversible Alembic migration for schema changes. Do not create production schema at application startup.
5. Regenerate the OpenAPI client when the public API changes and review the generated diff.
6. Add focused tests for success, denial, malformed input, retries, and concurrency where relevant.
7. Run the applicable checks from `docs/operations/TESTING.md`.
8. Use Conventional Commits and keep schema, implementation, and relevant tests together.

## Engineering standards

- Python is formatted and linted by Ruff and type-checked by strict mypy.
- TypeScript uses strict mode, ESM, single quotes, accessible semantic markup, and generated API types.
- Validate at boundaries and preserve user, room, challenge, and administrator authorization.
- Never log or expose active secrets, access tokens, complete private guess histories, emails, or credentials.
- New user-facing copy must be added to both English and Traditional Chinese catalogs.
- Gameplay cannot rely on colour alone; keyboard and screen-reader behavior is release-critical.

## Pull requests

Describe architecture, migrations, security impact, actual test results, deployment steps, and external configuration. Do not mark a check as passing unless its command completed successfully. Suspected vulnerabilities follow `SECURITY.md`, not a public issue.
