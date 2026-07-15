# Key rotation

## Key separation

Cipherboard uses independent secrets for:

- AES-256-GCM game-secret encryption;
- deterministic daily HMAC derivation;
- Supabase JWT signing (managed by Supabase);
- Supabase server administration, if required for deletion/session revocation;
- PostgreSQL runtime and migrator roles;
- Redis;
- CI registry/deployment access;
- observability integrations.

Never reuse material across purposes or environments. Keys live in the managed secret store, are accessed by workload identity where possible, and never appear in images, browser variables, database rows, logs, tickets, or documentation.

## Game-secret encryption rotation

`MASTERMIND_SECRET_ENCRYPTION_KEYS` is a JSON key ring and `MASTERMIND_SECRET_ACTIVE_KEY_VERSION` selects new writes. Version labels are monotonic operational identifiers such as `v2`; key values are base64-encoded 32-byte random values.

Rotation is staged:

1. Inventory ciphertext counts by key version and confirm current backups/key escrow.
2. Generate a 32-byte key directly into the secret manager and add it as a standby version while leaving the active version unchanged.
3. Deploy and verify that every API instance can decrypt controlled fixtures for old and standby versions. Secret values are never printed.
4. Change the active version. New games now use it; monitor encrypt/decrypt failures and readiness.
5. Re-encrypt retained rows in bounded, idempotent batches. Each batch locks the row, decrypts with recorded old version and correct associated data, encrypts with a fresh nonce/new version, verifies a decrypt, updates atomically, and reports counts only.
6. Reconcile until no live or retained row uses the old version. Include sessions, daily cached secrets, friend challenges, and rooms.
7. Keep the old version available through the maximum backup retention and active-session window. Perform a restore drill with the historical key ring.
8. Disable, then destroy the old key only after security/data owners approve recorded evidence.

An unknown version, invalid authentication tag, or unavailable key returns a safe unavailable response and a high-severity alert. The service must not substitute the active key or generate a replacement.

## Daily HMAC rotation

A daily HMAC change alters puzzle derivation and therefore requires a new derivation/key version, not an in-place secret replacement. Schedule the cutover on a future UTC date:

1. add the new key version to the server key ring and release code/config able to select by challenge row;
2. retain the old key for every existing daily official run and backup window;
3. create the first new-version challenge at the planned UTC date;
4. compare the derived puzzle across at least two independent API instances without logging it;
5. ensure active sessions crossing midnight continue using their recorded date/key/derivation versions;
6. retire the old key only after no retained session or backup requires it.

Production uses `MASTERMIND_DAILY_HMAC_KEYS` and `MASTERMIND_DAILY_HMAC_ACTIVE_KEY_VERSION`. The single `MASTERMIND_DAILY_HMAC_KEY` input is local-development compatibility only and is not eligible for a production rotation.

## Supabase JWT signing rotation

Use asymmetric signing keys. Create a standby key, wait at least the provider cache interval plus safety margin, promote it, and keep the previous public key available through access-token lifetime and JWKS cache expiry. The API caches JWKS for no longer than the provider guidance and refreshes once on an unknown `kid`. Test old/current tokens, exact issuer/audience, and failure of an unrelated key. Emergency compromise rotation also revokes sessions and follows the incident runbook.

## Database, Redis, and service credentials

Create a new credential with identical least privileges, inject it alongside the old one, rotate connection pools through a rolling restart, verify health/traffic, and then revoke the old credential. Rotate runtime and migrator separately. The migrator is absent from normal API containers. Redis rotation must preserve fail-closed rate limiting; deploy during a controlled window and verify ticket/rate/pubsub paths.

## Frequency and evidence

Rotate on suspected exposure, staff/vendor access change, provider requirement, or cryptographic policy change. Routine credential rotation follows the secret-manager policy; encryption and HMAC keys need not rotate merely on a short calendar if rotation creates more data risk, but the procedure is rehearsed quarterly. Evidence contains version identifiers, counts, times, approvers, tests, and deletion confirmation—never secret values.
