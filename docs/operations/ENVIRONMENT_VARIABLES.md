# Environment variables

## Boundaries

Variables prefixed `NEXT_PUBLIC_` are embedded into browser JavaScript and are public. They may contain origins, product/legal copy, and the Supabase publishable key only. `MASTERMIND_` values are API runtime configuration. Database owner/migrator credentials, Supabase secret credentials, cryptographic key material, Redis credentials, and observability credentials belong only in a managed secret store.

Production and staging fail deployment when a required value is absent. Startup messages name missing variable names but never values. `.env` is local-only, ignored by Git, mode `0600`, and generated explicitly by `infra/scripts/bootstrap-local-env.sh`.

## API settings

| Variable | Secret | Required production | Meaning |
|---|---|---|---|
| `MASTERMIND_ENVIRONMENT` | No | Yes | `development`, `test`, `staging`, or `production` |
| `MASTERMIND_PRODUCT_NAME` | No | Yes | API/OpenAPI product name; keep equal to `NEXT_PUBLIC_PRODUCT_NAME` |
| `MASTERMIND_RELEASE` | No | Yes | Immutable commit/image identifier for logs and metrics |
| `MASTERMIND_DATABASE_URL` | Yes | Yes | Async SQLAlchemy PostgreSQL URL for the non-owner runtime role; deployed URLs must set `ssl=verify-full` and an explicit `sslrootcert` CA source |
| `DATABASE_MIGRATOR_URL` | Yes | Release jobs | Separate owner/migrator URL with the same verify-full CA controls; never present in API containers |
| `DATABASE_RETENTION_URL` | Yes | Scheduled maintenance | Separate login inheriting only `mastermind_retention`; required by `mastermind-retention` and never present in API containers |
| `MASTERMIND_REDIS_URL` | Yes | Yes | TLS/authenticated managed Redis URL in deployed environments |
| `MASTERMIND_ALLOWED_ORIGINS` | No | Yes | JSON array of exact HTTPS web origins; wildcard and HTTP are rejected in production |
| `MASTERMIND_SUPABASE_URL` | No | Yes | Exact project URL used to form issuer/JWKS endpoints |
| `MASTERMIND_SUPABASE_SERVICE_ROLE_KEY` | Yes | Yes | Server-only Supabase admin credential used for session revocation/account deletion; never a browser variable |
| `MASTERMIND_SUPABASE_JWT_AUDIENCE` | No | Yes | Expected access-token audience, normally `authenticated` |
| `MASTERMIND_SECRET_ENCRYPTION_KEYS` | Yes | Yes | JSON object mapping versions to base64 32-byte AES keys |
| `MASTERMIND_SECRET_ACTIVE_KEY_VERSION` | No | Yes | Version used for new ciphertext; must exist in key ring |
| `MASTERMIND_DAILY_HMAC_KEYS` | Yes | Yes | JSON key ring of version to at least 32 bytes of independent HMAC material; never reuse an AES key |
| `MASTERMIND_DAILY_HMAC_ACTIVE_KEY_VERSION` | No | Yes | Version used for newly created daily definitions; a persisted daily continues using its recorded version |
| `MASTERMIND_DAILY_HMAC_KEY` | Yes | No | Legacy single-key local-development input mapped to the active version |
| `MASTERMIND_PUBLIC_IDENTIFIER_HMAC_KEY` | Yes | Yes | Independent HMAC key for stored friend/room capability-token digests |
| `MASTERMIND_TRUSTED_PROXY_IPS` | No | Yes | JSON array of immediate proxy IPs allowed to supply forwarding headers |
| `MASTERMIND_ADMIN_RECENT_AUTH_SECONDS` | No | Yes | Maximum admin authentication age, default 900 seconds |
| `MASTERMIND_REQUEST_BODY_LIMIT_BYTES` | No | Yes | Maximum parsed request body; default 65,536 |
| `MASTERMIND_REQUEST_TIMEOUT_SECONDS` | No | Yes | HTTP handler deadline in seconds; default 15, range 1–120 |
| `MASTERMIND_RATE_LIMIT_PER_MINUTE` | No | Yes | Per-subject baseline; endpoint-specific limits remain server policy and the aggregate IP guardrail is derived at 10x |
| `MASTERMIND_ROOM_TIE_WINDOW_MS` | No | Yes | Server-authoritative duel tie window, 50–2,000 ms |
| `MASTERMIND_WEBSOCKET_FRAME_LIMIT_BYTES` | No | Yes | Maximum WebSocket command frame, fixed to 4,096 bytes by default |
| `MASTERMIND_WEBSOCKET_USER_CONNECTION_LIMIT` | No | Yes | Maximum concurrent room sockets for one profile, default 3 |
| `MASTERMIND_WEBSOCKET_IP_CONNECTION_LIMIT` | No | Yes | Maximum concurrent room sockets for one immediate client IP, default 20 |
| `MASTERMIND_WEBSOCKET_CONNECTION_TTL_SECONDS` | No | Yes | Redis lease window used to recover connection counts after instance loss, default 90 seconds |
| `MASTERMIND_LOG_LEVEL` | No | Yes | Structured log threshold; production normally `INFO` |
| `MASTERMIND_METRICS_ENABLED` | No | Yes | Metrics endpoint/collection switch |
| `MASTERMIND_ERROR_REPORTING_URL` | No | No | Optional HTTPS endpoint receiving allowlisted operational error envelopes |
| `MASTERMIND_ERROR_REPORTING_TOKEN` | Yes | No | Bearer credential for the configured error-reporting endpoint; required with its URL |
| `MASTERMIND_FEATURE_DAILY` | No | Yes | Emergency server enforcement for daily challenges |
| `MASTERMIND_FEATURE_LEADERBOARDS` | No | Yes | Emergency server enforcement for public boards |
| `MASTERMIND_FEATURE_FRIEND_CHALLENGES` | No | Yes | Emergency server enforcement for friend challenges |
| `MASTERMIND_FEATURE_MULTIPLAYER` | No | Yes | Emergency server enforcement for rooms/sockets |
| `MASTERMIND_FEATURE_ACHIEVEMENTS` | No | Yes | Emergency server enforcement for achievement awards |
| `MASTERMIND_FEATURE_ACCOUNT_REGISTRATION` | No | Yes | Emergency server enforcement for permanent account upgrades |
| `MASTERMIND_FEATURE_ANALYTICS` | No | Yes | Consent-aware first-party analytics switch; safe default false |

Feature environment controls are operational kill switches. A client flag never grants access, and a database flag cannot override an environment force-off during an incident.

## Browser/build settings

| Variable | Required production | Meaning |
|---|---|---|
| `NEXT_PUBLIC_API_ORIGIN` | Yes | Exact public HTTPS API origin |
| `NEXT_PUBLIC_PRODUCT_ORIGIN` | Yes | Canonical public web origin |
| `NEXT_PUBLIC_SUPABASE_URL` | Yes | Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` | Yes | Publishable browser key; never a secret/service-role key |
| `NEXT_PUBLIC_PRODUCT_NAME` | Yes | Product name |
| `NEXT_PUBLIC_SUPPORT_EMAIL` | Yes | Monitored support/security contact |
| `NEXT_PUBLIC_LEGAL_ENTITY` | Yes | Reviewed operating legal entity |
| `NEXT_PUBLIC_JURISDICTION` | Yes | Reviewed governing jurisdiction copy |
| `NEXT_PUBLIC_POLICY_DATE` | Yes | ISO policy effective date |

Legal settings are deliberately launch-blocking. They are centralized rather than scattered fallback copy.

## Infrastructure-only settings

`POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD` are local Compose inputs. `API_IMAGE` and `WEB_IMAGE` select digest-pinned production images. `MASTERMIND_RELEASE` is supplied separately by the release workflow as the checked-out source SHA (or the recorded API digest during rollback), overriding any stale value in the secret-manager file. `RUNTIME_ENV_FILE` is read only for the API service and contains the non-owner workload URL. `MIGRATOR_ENV_FILE` is read only for the release-profile migration job and contains `DATABASE_MIGRATOR_URL`; its values are never injected into the API. A scheduler-owned `0600` retention environment file contains only `MASTERMIND_ENVIRONMENT=production` and `DATABASE_RETENTION_URL` for a login inheriting `mastermind_retention`. `POSTGRES_CA_FILE` is an absolute host path to the integrity-verified provider CA bundle mounted read-only into database-connected containers. None is a browser build argument. CI/deployment credentials are stored only in protected GitHub environments.

The concrete Compose deployment uses URLs ending in `?ssl=verify-full&sslrootcert=%2Frun%2Fsecrets%2Fcipherboard%2Fpostgres-ca.pem`. Obtain the CA bundle from the managed PostgreSQL provider over an authenticated channel and verify its published fingerprint before installing it. `sslrootcert=system` is supported only when the provider documents that its chain terminates at a CA already present in the image's operating-system trust store; it is not a substitute for a private provider CA.

## Key generation

For an operator-controlled workstation connected to the target secret manager:

```bash
openssl rand -base64 32
openssl rand -hex 32
```

The first output is suitable for one AES-256 key value inside the JSON key ring; the second is suitable independent HMAC material. Copy output directly into the secret manager, clear terminal scrollback according to operator policy, and never paste real keys into tickets, chat, documentation, CI logs, or `.env.example`.

## Production validation

Before starting traffic, confirm exact HTTPS origins, non-local database/Redis hosts, PostgreSQL `ssl=verify-full` plus the intended `sslrootcert` provider CA, TLS Redis, non-development keys, every AES key's decoded 32-byte length, active key version presence, legal configuration, release identifier, and safe feature defaults. Runtime startup and the migration entry point both reject a deployed PostgreSQL URL that does not verify the server certificate and hostname against an explicit CA source. Reserved example endpoints and known placeholder service credentials are rejected. The `ci_validation` configuration scope is limited to the GitHub Actions environment (`CI=true` and `GITHUB_ACTIONS=true`) and a full `ci-<40-character commit SHA>` release; it bypasses only placeholder detection for the isolated import/container smoke and must never be present in deployed environment files. Scan the built web files for names of server-only variables and known credential prefixes. A startup or validation failure blocks rollout; operators do not bypass it with dummy values.
