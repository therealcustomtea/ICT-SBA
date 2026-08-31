# Security controls

## Authentication and sessions

- Protected routes require a first-party bearer access token with an allowlisted algorithm and exact issuer, audience, expiry, issued-at time, subject, and session identifiers.
- The API verifies that the referenced MongoDB session is live and not revoked.
- Refresh tokens are random opaque values, stored only as keyed hashes, rotated on every use, and sent only in an HttpOnly, Secure production cookie scoped to `/v1/auth`.
- Refresh-token reuse revokes the session family. Logout and account deletion revoke sessions server-side.
- Magic links are random, one-use, short-lived, rate-limited tokens delivered through SMTP. TOTP secrets are encrypted at rest.

## Data and authorization

- FastAPI owns all MongoDB access. The browser has no database credentials.
- Resource queries enforce owner, member, user, and administrator boundaries. Knowing an object ID, room code, or invite code is not authorization.
- MongoDB transactions protect multi-document account, room, leaderboard, and audit mutations. Unique/partial indexes enforce idempotency and local uniqueness.
- Game and TOTP secrets use AES-256-GCM with versioned keys. Invite, room, and refresh tokens are stored only as keyed hashes.

## Operations

- Production requires TLS MongoDB/Redis, exact HTTPS origins, Secure cookies, non-placeholder keys, immutable releases, and a managed secret store.
- Containers run non-root, read-only, without Linux capabilities, and with `no-new-privileges`.
- Logs, metrics, analytics, exports, and errors omit tokens, secret codes, email bodies, encryption material, and raw capability links.
- Administrative mutations require a database-backed grant, recent authentication where applicable, a reason, and a durable audit event.
