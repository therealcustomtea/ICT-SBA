# Threat model

This model covers the public PWA, FastAPI, first-party authentication, MongoDB, Redis, SMTP, WebSockets, administrator routes, CI, and deployment tooling. High-value assets are auth sessions, active game codes, ranked-game integrity, private profile data, admin authority, invite capabilities, key material, and audit evidence.

| Threat | Primary controls |
| --- | --- |
| Forged or expired access token | Exact token claims/algorithm, strong server signing key, short lifetime, live session lookup |
| Stolen/replayed refresh token | HttpOnly Secure cookie, keyed hash at rest, rotation, reuse detection, family revocation |
| Magic-link theft or enumeration | Generic responses, short one-use tokens, token hashing, IP/email rate limits, exact redirects |
| Cross-user object access | Owner/member predicates on every resource operation; generic not-found responses |
| Duplicate/racing gameplay mutation | MongoDB transactions, idempotency indexes, server timestamps, deterministic room update order |
| Database credential leakage | Server-only managed secrets, no browser database connection, scoped Atlas user/network rules |
| Stored secret disclosure | AES-GCM ciphertext with versioned keys; plaintext never serialized or logged |
| Invite/room code theft | High-entropy codes, keyed hashes at rest, expiry/revocation, authorization after lookup |
| Redis outage or manipulation | Redis is non-authoritative; integrity-sensitive paths fail closed; durable state remains MongoDB |
| SMTP outage or hostile link scanning | Generic temporary failure, one-use expiry, existing sessions unaffected, monitored delivery |
| Admin abuse | Database-backed grants, recent-auth checks, reason requirement, immutable audit event |
| Dependency/build compromise | Frozen locks, pinned actions, image scanning, digest-pinned deployment, protected environments |

Residual risks include compromise of the runtime secret store, signing key, Atlas administrator, SMTP inbox, or user device. Response includes credential/key rotation, session revocation, evidence preservation, scoped notification, and verified restoration.
