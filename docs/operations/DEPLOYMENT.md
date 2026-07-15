# Deployment

## Production topology

Cipherboard ships as separate OCI images for the Next.js web application and FastAPI. A production environment requires:

- HTTPS ingress/load balancer with health checks and trusted proxy-header rewriting;
- at least two API instances for availability and WebSocket draining;
- at least two web instances;
- managed PostgreSQL with certificate and hostname verification (`ssl=verify-full` plus the provider CA), automated backups, point-in-time recovery, and separate runtime/migrator roles;
- managed Redis with TLS/authentication and no public endpoint;
- managed Supabase Auth with asymmetric signing keys, anonymous sign-in protection, exact redirects, and custom SMTP;
- managed secret injection, registry vulnerability scanning, centralized logs/metrics/alerts, and protected deployment environments.

The images contain no secrets. Browser variables are compiled into the web image and therefore require a distinct web image for each environment unless the values are identical. Runtime API secrets are injected when the container starts.

## Build

Lockfiles are release inputs. A release fails if `uv.lock` or `pnpm-lock.yaml` is missing or does not match its manifest.

```bash
docker build -f infra/docker/api.Dockerfile -t registry.example/cipherboard-api:$GIT_SHA .
docker build -f infra/docker/web.Dockerfile \
  --build-arg NEXT_PUBLIC_API_ORIGIN=https://api.example.com \
  --build-arg NEXT_PUBLIC_PRODUCT_ORIGIN=https://play.example.com \
  --build-arg NEXT_PUBLIC_SUPABASE_URL=https://project.supabase.co \
  --build-arg NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY="$SUPABASE_PUBLISHABLE_KEY" \
  --build-arg NEXT_PUBLIC_PRODUCT_NAME=Cipherboard \
  --build-arg NEXT_PUBLIC_SUPPORT_EMAIL=support@example.com \
  --build-arg NEXT_PUBLIC_LEGAL_ENTITY='Configured legal entity' \
  --build-arg NEXT_PUBLIC_JURISDICTION='Configured jurisdiction' \
  --build-arg NEXT_PUBLIC_POLICY_DATE=2026-07-15 \
  -t registry.example/cipherboard-web:$GIT_SHA .
```

Use the actual registry and launch configuration. A commit/environment tag is a traceability label, not the deployment identity: record and deploy the resolved registry digest because the web artifact also depends on environment-specific public values. Do not use `latest` or promote by a mutable tag.

## Supported concrete path: OCI host with Docker Compose

`infra/docker/compose.production.yml` supports a provider-neutral Linux host behind a managed TLS load balancer. The host needs Docker Engine with Compose, outbound access to the registry/PostgreSQL/Redis/Supabase, and no public access to ports 3000 or 8000. The load balancer connects through a private network or local reverse proxy.

On the host, a secret-manager agent renders two `0600` environment files outside the repository, owned by the restricted deployment identity so Docker Compose can read them: a runtime file containing only the non-owner application credential and API secrets, and a release-only migrator file containing `MASTERMIND_ENVIRONMENT=production` plus `DATABASE_MIGRATOR_URL`. Both database URLs set `ssl=verify-full&sslrootcert=%2Frun%2Fsecrets%2Fcipherboard%2Fpostgres-ca.pem`. Install the managed provider's CA bundle separately, verify its published fingerprint through an authenticated provider channel, and keep it root-owned or deployment-identity-owned and non-writable by containers. For Supabase-hosted PostgreSQL, download the Server root certificate from the project's database connection settings and verify it against the provider-published value. Compose injects the runtime file only into the API service, reads the migrator file only for the one-shot release-profile migration, and mounts the CA bundle read-only into both; neither application container receives the other credential. Set:

```bash
export API_IMAGE=ghcr.io/organization/repository-api@sha256:resolved-digest
export WEB_IMAGE=ghcr.io/organization/repository-web@sha256:resolved-digest
export MASTERMIND_RELEASE=reviewed-source-commit-sha
export RUNTIME_ENV_FILE=/run/secrets/cipherboard/runtime.env
export MIGRATOR_ENV_FILE=/run/secrets/cipherboard/migrator.env
export POSTGRES_CA_FILE=/run/secrets/cipherboard/provider-postgres-ca.pem
```

Then:

```bash
docker compose -f infra/docker/compose.production.yml pull api web
docker compose -f infra/docker/compose.production.yml --profile release run --rm migrate
docker compose -f infra/docker/compose.production.yml up -d --no-build api web
docker compose -f infra/docker/compose.production.yml ps
curl --fail --silent http://127.0.0.1:8000/health/ready
curl --fail --silent http://127.0.0.1:3000/ >/dev/null
```

For zero-downtime production, use an orchestrator or blue/green pair of Compose hosts: deploy the new revision out of rotation, run readiness and smoke checks, add it to ingress, drain the old revision, and retain it for the rollback window. WebSocket ingress must support upgrade headers, idle timeouts longer than heartbeat intervals, connection draining, and sticky routing only if broker-backed fan-out is unavailable. The intended design does not require sticky sessions.

## Release order

1. Confirm CI, scans, review, change record, backup policy, and rollback image.
2. Deploy backward-compatible application code first when a phased schema change requires it.
3. Take a pre-change backup for migrations classified medium/high risk.
4. Run Alembic once with the migrator credential.
5. Deploy API, wait for readiness, and run authenticated smoke tests.
6. Deploy the environment-specific web image and verify security headers/static assets.
7. Verify guest game, ranked game integrity, admin denial/allow, and one two-client room.
8. Watch errors, latency, DB locks, Redis, auth failures, and WebSocket reconnects through the observation window.
9. Record image digests, migration revision, operator, times, and evidence.

## Scheduled retention

Alembic creates the non-login `mastermind_retention` role and its narrow table grants/RLS policies. Provision a distinct managed-database login, grant it membership in that role, and store its verify-full URL as `DATABASE_RETENTION_URL` in a scheduler-only `0600` environment file. Do not reuse the API runtime or schema-owner/migrator credential.

Run the API image's bounded command every 15 minutes from the platform scheduler. For the documented OCI host, an equivalent invocation is:

```bash
docker run --rm \
  --read-only \
  --cap-drop ALL \
  --security-opt no-new-privileges \
  --env-file /run/secrets/cipherboard/retention.env \
  --mount type=bind,source=/run/secrets/cipherboard/provider-postgres-ca.pem,target=/run/secrets/cipherboard/postgres-ca.pem,readonly \
  "$API_IMAGE" mastermind-retention --batch-size 500 --max-batches 20
```

The retention URL uses `ssl=verify-full&sslrootcert=%2Frun%2Fsecrets%2Fcipherboard%2Fpostgres-ca.pem`. Each invocation is finite and prints only aggregate JSON counts. PostgreSQL workers claim rows with `FOR UPDATE SKIP LOCKED`, so an accidental overlap remains resumable, but the scheduler should still use a no-overlap policy. Alert on a non-zero exit, missed executions, repeated exhaustion of `max-batches`, or age-distribution drift. The external scheduler, maintenance login, secret injection, and alert are deployment configuration and are not created by this repository.

The protected `Deploy` workflow resolves the commit actually checked out from its `ref` input. Staging and production reject any commit outside `origin/main` history. It builds environment-qualified traceability tags, converts them to registry digest references, scans both images, sets `MASTERMIND_RELEASE` to the checked-out source SHA, validates and atomically installs that revision's production Compose definition, and deploys only the digest-pinned references. `DEPLOY_PATH/infra/docker` must already exist and be writable only by the restricted deployment identity. The host also needs read-only registry authentication capable of pulling the private GHCR packages.

## Protected GitHub environment configuration

Create separate `preview`, `staging`, and `production` GitHub environments. Staging and production require reviewers and restrict deployment to `main`. Each environment defines the nine documented `NEXT_PUBLIC_*` build variables plus `DEPLOY_PATH`, `RUNTIME_ENV_FILE`, `MIGRATOR_ENV_FILE`, and `POSTGRES_CA_FILE`. Store `DEPLOY_HOST`, `DEPLOY_USER`, `DEPLOY_SSH_PRIVATE_KEY`, and `DEPLOY_SSH_KNOWN_HOST` as environment secrets. The SSH key is deployment-only and unshared; the known-host entry is verified through an out-of-band provider channel rather than accepted on first connection. Never store runtime, migrator, Redis, Supabase service, or encryption credentials in GitHub build variables.

Provision the target directory, two environment files, and verified PostgreSQL CA file before the first dispatch. Confirm both database roles connect with hostname verification before opening traffic. Authenticate the host to GHCR with a read-only machine credential, keep ports 3000/8000 private, and configure the managed ingress health checks and WebSocket drain policy. Dispatch the workflow with the reviewed full ref and target environment; retain its source SHA, image digests, migration revision, CA fingerprint, scan output, approver, and smoke evidence in the release record.

## Network and process controls

Only ingress is internet-facing. PostgreSQL and Redis allow connections from API workload identities only. Supabase administrative endpoints are never called by the browser. Egress can be restricted to Supabase JWKS/Auth, managed database/Redis, error reporting if enabled, and approved telemetry endpoints.

Containers run non-root, drop Linux capabilities, use read-only root filesystems and bounded `/tmp`, expose health checks, and receive SIGTERM with a drain period. The ingress or orchestrator must remove a revision from service and drain WebSockets before sending SIGTERM. Uvicorn then stops accepting new work and allows in-flight requests and database transactions to finish within the configured container grace period.

## Environment promotion

Preview uses non-production data and keys. Staging mirrors production topology and settings but uses distinct Auth/database/Redis/secret projects. Production promotion reuses the reviewed source commit and rebuilds only where environment-specific public variables require a separate web artifact. No environment shares database credentials, encryption keys, daily HMAC keys, Supabase secret keys, Redis credentials, or error-report DSNs.
