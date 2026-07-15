# Database migrations

## Ownership and credentials

Alembic under `apps/api/alembic` is the sole application schema history. The API never calls `create_all`, migrates, seeds, downgrades, or creates roles at startup. Supabase Auth configuration is independent; do not duplicate application DDL under `supabase/migrations`.

Use a non-login privilege group plus separate login identities:

- `mastermind_migrator`: owns application tables/sequences and is available only to protected release jobs;
- `mastermind_runtime`: non-login, non-owner group with the minimum table DML privileges and RLS policies needed by the API;
- an environment-specific workload login (or managed workload identity) that is granted `mastermind_runtime`, owns no objects, and is used by `MASTERMIND_DATABASE_URL`.

The production Compose path reads separate secret-manager files. The API receives only `MASTERMIND_DATABASE_URL`; the release-profile migration container receives only `DATABASE_MIGRATOR_URL` plus migration-scope configuration. Both URLs use `ssl=verify-full` and the read-only provider CA mounted at `/run/secrets/cipherboard/postgres-ca.pem` through `sslrootcert`. Never render both credentials into one environment file.

Revoke application objects from `PUBLIC`, `anon`, and `authenticated`. If the application database is hosted in the Supabase project, keep the Data API disabled and verify its exposed-schema settings after every platform change.

The initial migration creates the non-login `mastermind_runtime` group where the provider permits role management, revokes table access from public/browser roles, enables RLS, and grants the group only table DML. Provision the workload login through the provider control plane and grant group membership; do not put a login password in a migration. A provider that forbids `CREATE ROLE` requires the database administrator to create the group before the first migration.

## Creating a migration

1. Update SQLAlchemy models and domain behavior together.
2. Generate a descriptive revision using the repository's Alembic command; do not hand-invent revision identifiers.
3. Review generated SQL. Alembic cannot infer data backfills, partial indexes, safe constraint validation, grants, or destructive risk.
4. Add explicit upgrade and a practical downgrade or documented forward-fix strategy.
5. Verify empty-database upgrade, current-revision upgrade, and upgrade/downgrade/upgrade in isolated PostgreSQL.
6. Inspect locks and table rewrites for representative production scale.

```bash
uv run alembic -c apps/api/alembic.ini revision --autogenerate -m 'descriptive change'
uv run alembic -c apps/api/alembic.ini upgrade head
uv run alembic -c apps/api/alembic.ini current
uv run alembic -c apps/api/alembic.ini history
```

Autogeneration output is a draft, not approval evidence.

## Deployment pattern

Prefer expand/migrate/contract:

1. **Expand:** add nullable columns/tables/indexes without breaking old code. Large PostgreSQL indexes use `CREATE INDEX CONCURRENTLY` in a migration designed outside Alembic's transaction wrapper.
2. **Migrate:** deploy code that reads both shapes and writes the new one; backfill in bounded, resumable batches with progress metrics.
3. **Verify:** compare counts, nulls, constraints, representative queries, and rollback behavior.
4. **Contract:** only after the observation window and rollback release no longer need the old shape, remove it in a separate release.

For large tables, add checks as `NOT VALID`, backfill/clean, then `VALIDATE CONSTRAINT` before making a column required. Set bounded lock and statement timeouts for release jobs. Do not combine irreversible data deletion with a routine code release.

## Release execution

The release environment sets `DATABASE_MIGRATOR_URL` and runs the migration inside the Compose release profile. If an approved operator runs the script directly instead, `sslrootcert` must name the absolute provider-CA path visible to that host process rather than the container mount path.

```bash
MASTERMIND_ENVIRONMENT=staging infra/scripts/migrate.sh
MASTERMIND_ENVIRONMENT=production infra/scripts/migrate.sh
```

The script rejects SQLite and exports the migrator URL only to Alembic. Take a pre-change backup for medium/high-risk migrations. Run one migration job, monitor database locks/replication lag, and record the before/after revision.

## Validation from empty

CI starts a clean PostgreSQL service, runs `upgrade head`, checks the expected revision and constraints, exercises integration tests, then performs the supported downgrade/upgrade cycle. Seed data is local/test-only and is never part of a production migration.

## Failure handling

Stop the rollout and preserve logs/revision if a migration fails. Determine whether PostgreSQL rolled the transaction back. Do not blindly rerun non-transactional or concurrent-index steps. If old application code remains compatible, keep it serving while applying a reviewed forward fix. Restore is the last resort for destructive corruption and follows `BACKUP_AND_RESTORE.md`.

Application rollback and database rollback are separate decisions. Never run an Alembic downgrade in production unless the migration explicitly supports it, a current backup exists, data-loss impact is accepted, and the incident commander/database owner approve.
