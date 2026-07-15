# Rollback

## Principles

Application rollback, feature disablement, data repair, and schema downgrade are different operations. Prefer a feature kill switch or backward-compatible previous image. Never use `git reset`, a force push, destructive database command, or automatic production Alembic downgrade as an incident shortcut.

Every deployment records API/web image digests, source commit, migration before/after revision, public build configuration, operator, and smoke evidence. The previous healthy images remain available through the observation window.

## Application rollback

1. Declare/associate an incident or change record and pause further rollout.
2. Confirm the previous image is compatible with the current schema, production Compose definition, and feature-flag shape.
3. Force off the failing risky feature if that reduces impact.
4. Remove failing instances from ingress while preserving safe logs.
5. Set `API_IMAGE` and/or `WEB_IMAGE` to the prior immutable digest and start the production Compose service or orchestrator rollout.
6. Wait for liveness and readiness, then run guest/authenticated game, secret-omission, admin denial, and relevant feature smokes.
7. Drain old WebSockets; clients reconnect through authoritative state. Do not terminate database transactions mid-flight.
8. Watch errors, latency, auth, database, Redis, and reconnect metrics; record completion.

For the supported Compose host:

```bash
export API_IMAGE=ghcr.io/organization/repository-api@sha256:previous-digest
export WEB_IMAGE=ghcr.io/organization/repository-web@sha256:previous-digest
export MASTERMIND_RELEASE=previous-api-digest
export RUNTIME_ENV_FILE=/run/secrets/cipherboard/runtime.env
export MIGRATOR_ENV_FILE=/run/secrets/cipherboard/migrator.env
export POSTGRES_CA_FILE=/run/secrets/cipherboard/provider-postgres-ca.pem
docker compose -f infra/docker/compose.production.yml pull api web
docker compose -f infra/docker/compose.production.yml up -d --no-build api web
docker compose -f infra/docker/compose.production.yml ps
```

Use the actual recorded digests from this repository and target environment; never substitute `latest`, a staging web artifact in production, or an image from another registry namespace. The protected rollback workflow enforces that provenance. Compose requires the migrator file path while resolving the release-profile definition, but rollback does not enable that profile or mount its credential into either application container.

## Database decisions

If the migration is additive and the previous app is compatible, leave the database at the new revision. If compatibility fails, prefer a reviewed forward migration or deploy an intermediate compatibility image.

A production downgrade requires all of the following: an explicitly tested downgrade, current backup/PITR point, understood data loss, stopped conflicting writes, database and incident-owner approval, and a post-downgrade integrity plan. Destructive restores follow the backup runbook and restore into a new target first. Do not overwrite the source database.

## Public web configuration rollback

Because public origins, Supabase project, and legal/product values are compiled into the web image, roll back to the image built for the same environment. A staging web image is never promoted directly to production. After rollback, verify canonical/robots metadata, CSP/connect origins, publishable-key-only bundle contents, locale routes, PWA update behavior, and service-worker cache transition.

## Abort and recovery criteria

Abort the rollback if it would reintroduce a known auth/authorization/secret leak, cannot read the current schema, or fails readiness. Keep the feature disabled and apply a forward fix. Recovery is complete only when targeted tests pass, metrics stabilize through the observation window, public data is consistent, and emergency credentials/flags are reconciled.
