# Security controls

## Identity and session validation

- Supabase Auth provides anonymous, magic-link, and OAuth identities. Anonymous users are still authenticated and carry the signed `is_anonymous` claim.
- FastAPI requires `Authorization: Bearer` on protected routes. It validates signature against the project JWKS, exact issuer and audience, allowed asymmetric algorithm, expiry, issued-at time, and UUID subject. Decoded-but-unverified claims are never used.
- User-editable metadata never grants permissions. Administrative roles are read from server-controlled application data. Admin routes require a permanent identity, a signed access token carrying a nonempty Supabase `session_id`, `aal2`, and authentication within the configured recent-auth window. Because the application database is separate from Supabase Auth, the API does not claim provider-side `auth.sessions` revocation checks; production keeps admin JWT lifetime within the documented residual-risk window and revokes provider sessions during response.
- Guest-to-account linking preserves the Supabase subject. Linking to an existing unrelated account is not automatic because it requires an explicit conflict and ownership process.
- Production enables CAPTCHA/Turnstile for anonymous account creation and custom SMTP for email delivery. Auth redirect URLs are exact HTTPS routes.

## Database and authorization

- The Data API is disabled. Browser roles have no privileges on application tables or functions.
- A migrator role owns schema changes. A separate runtime role is non-owner and receives only required DML and sequence privileges. The API does not run as `postgres` or a Supabase service role.
- Repository queries include the current owner/member predicate. Opaque IDs improve privacy but never replace authorization.
- SQLAlchemy bound parameters are mandatory. User-supplied sort keys, column names, and directions are selected from allowlists.
- PostgreSQL check, foreign-key, unique, and partial unique constraints backstop application validation. Race-sensitive state changes use transactions and row locks.
- Production configures bounded pools, `statement_timeout`, `lock_timeout`, `idle_in_transaction_session_timeout`, and verify-full TLS using the integrity-checked provider CA.

## Secret-code protection

- Production randomness uses the operating system CSPRNG. Seeded generators are test/development-only.
- Standard, human-created, and multiplayer secrets use AES-256-GCM with a unique 96-bit nonce. Ciphertext is bound through associated data to record type, record UUID, and rule-set version.
- The key ring and active version come from a managed secret store. Startup decodes and validates every configured version, and staging/production require 32-byte AES-256 material for every active or retained key. Missing or malformed keys fail startup/readiness or the affected operation safely; the service never creates a replacement key in staging or production.
- Daily secrets derive from a separate versioned HMAC key, UTC date, rules version, and derivation version. Neither seed nor key material reaches the client.
- API responses, WebSocket messages, analytics, logs, error reports, and browser persistence exclude active secrets. Results reveal a secret only when mode rules allow.

## Web and transport security

The web application sends a restrictive Content Security Policy, `frame-ancestors 'none'`, MIME-sniffing protection, strict referrer policy, and a minimal Permissions Policy. Production ingress adds HSTS after HTTPS is confirmed on all subdomains. Browser source maps are not publicly served. Private challenge and room pages are `noindex`.

Production CSP must narrow `connect-src` to the exact API and Supabase origins. Inline script/style allowances are removed through nonces or hashes before launch; adding `unsafe-eval` is prohibited. There is no advertising or unreviewed third-party script boundary.

CORS lists exact HTTPS origins and does not use wildcard origins with credentials. The public API authenticates mutations with an explicit bearer token, not an ambient API cookie. Auth callbacks use provider state/PKCE and validate their expected origin. Cookies are Secure, SameSite, scoped narrowly, and HttpOnly where the client does not need to read them.

## Abuse and availability controls

Redis applies atomic limits to account and trusted client IP dimensions. The ingress strips client-supplied forwarding headers and writes its own. Endpoint-specific budgets protect account creation, game/room/challenge creation, attempts, invalid invite lookups, admin mutations, and WebSocket connections/messages.

If Redis is unavailable, ranked attempts, invite operations, administrative mutations, and new multiplayer connections fail closed. Explicitly unranked solo play may use a conservative process-local fallback. Requests have body, page, execution, and connection limits; WebSockets have frame, rate, concurrency, heartbeat, and queue limits.

## Logging and observability

Operational events are structured and allowlisted. Request bodies are not logged. Recursive redaction removes authorization/cookie headers, tokens, secret/guess fields, invite material, ciphertext, and email. Error-report integrations apply the same filter before network transmission. General metrics use bounded labels and pseudonymous identifiers.

The application emits bounded metrics and structured events for HTTP failures, authentication failures, rate limits, dependency readiness, active games/rooms, guess latency, leaderboard latency, sockets, and reconnects. Production log/metrics rules must additionally monitor authorization denials, decryption failures, admin mutations, broker errors, database saturation, retention failures, and pending deletion age. Alert routing and thresholds are external launch configuration and point to the incident runbook and deployment version.

## Administrative controls

Admin access is denied by default, server-authorized, permanent-account-only, MFA protected, and rate-limited. Sensitive views do not expose ciphertext or raw PII. Each mutation validates a bounded reason and writes an audit event in the same transaction. Operators use named accounts; shared admin accounts are prohibited.

Database/secret-manager/hosting access uses least privilege, MFA, short-lived credentials where supported, and periodic access review. Production deployment uses protected environments and immutable image references.

The protected administrative discovery surface is explicit and paginated: `GET /v1/admin/games`, `/profiles`, `/rooms`, `/challenges`, and `/leaderboard-review`, plus `/summary`, `/flags`, and `/audit`. Mutation routes for flag changes, leaderboard invalidation/restoration, profile moderation, challenge revocation, and room termination use the same server-side admin dependency and audit requirements. Discovery routes never return decrypted secrets or raw invite codes.

Authenticated support intake is `POST /v1/support`. It accepts a bounded topic, reply email, and message, applies an account-weighted abuse limit, and returns `202`; support data remains restricted and follows the support retention schedule. The reply email is not copied into product analytics or general request logs.

## Supply chain and CI

Python and Node lockfiles are committed; builds use frozen installs. GitHub Actions are pinned to reviewed commit SHAs, and CI service/base images are pinned to registry digests while retaining version labels for deliberate updates. Container stages discard build tooling, run non-root, drop capabilities, and use read-only filesystems. CI runs lint, type checks, tests, migration-from-empty validation, OpenAPI drift, accessibility/e2e checks, dependency review, CodeQL, filesystem/container vulnerability scans, and secret scanning. Release artifacts receive environment/source traceability tags, are scanned, and are deployed only by their resolved registry digests.

## Launch-blocking control checks

Launch is blocked unless all of these have evidence:

- no service/secret key or real credential in client bundles, repository, images, or logs;
- exact production issuer, audience, CORS, redirect, CSP, and ingress proxy configuration;
- working allowed/denied owner, member, guest, banned, deleted, and admin tests;
- active secrets absent from every response/event/log/analytics/browser-storage test fixture;
- PostgreSQL runtime role cannot migrate/drop and browser roles cannot access application data;
- Redis failure exercises demonstrate fail-closed ranked/admin/multiplayer behavior;
- current and previous encryption keys decrypt expected fixtures and missing-key behavior alerts safely;
- backup restore and rollback exercises meet the documented objectives;
- CAPTCHA, SMTP, MFA, dependency scanning, protected environments, and alert routing are enabled.
