# Launch checklist

Every item requires an owner and link to evidence in the private launch record. A checked box without evidence is not approval.

## Product and business configuration

- [ ] Legal entity, jurisdiction, effective policy date, monitored support/security address, and product origin are configured.
- [ ] Privacy, terms, accessibility, support, and deletion pages match the deployed processors/features; legal review is approved.
- [ ] Service is clearly intended for age 13+ and does not collect date of birth or advertising identifiers.
- [ ] English and Traditional Chinese primary flows and localized validation/share text are reviewed.
- [ ] No required button/page/admin card is mocked, static sample data, disabled, or “coming soon”.

## Identity, privacy, and administration

- [ ] Supabase production project uses asymmetric signing keys, exact HTTPS redirects, short access tokens, refresh rotation, custom SMTP, CAPTCHA/Turnstile, and reviewed Auth limits.
- [ ] Browser bundle contains only the publishable key; service/secret/admin credentials are absent from source, image, logs, and artifacts.
- [ ] Guest creation, same-sub identity upgrade, registered login, expiry, sign-out, and revoked-session behavior pass.
- [ ] Owner/member/BOLA tests pass for every game/challenge/room/profile route and WebSocket reconnect.
- [ ] Admin is permanent-account-only, server-role-authorized, recent-auth/MFA protected, denied by default, and audited.
- [ ] Public visibility opt-out removes entries immediately; banned/deleted/under-review users are excluded.
- [ ] Data export is authenticated, complete, UTF-8, and CSV-injection-safe.
- [ ] Account deletion hides first, revokes sessions, tolerates Auth failure, is idempotent, and completes retention scheduling.
- [ ] Processor inventory, DPA/region/retention/deletion support, and user disclosures are approved.

## Game and data integrity

- [ ] Empty-database migration and current upgrade/downgrade/upgrade validation pass on PostgreSQL.
- [ ] Runtime role cannot migrate/drop; migrator is absent from app containers; Data API/browser roles cannot access tables/functions.
- [ ] Runtime and migrator connections both verify the PostgreSQL hostname against the fingerprint-verified provider CA mounted read-only into their containers.
- [ ] Constraints and indexes cover attempt/idempotency uniqueness, one official run, membership, event sequence, leaderboard, and foreign keys.
- [ ] Concurrent attempts, final-attempt win, post-terminal rejection, same/different idempotency replay, daily rollover, and simultaneous duel tests pass.
- [ ] Scores/times/config eligibility are server-authoritative and custom/guest/invalidated records cannot enter public boards.
- [ ] Representative leaderboard queries use intended indexes and bounded deterministic pagination with the immutable row identifier as the final tie-breaker.
- [ ] Achievements and audit events are idempotent/transactional.

## Secret and application security

- [ ] Every current/previous AES key decodes to 32 bytes at startup; wrong AAD/tag, missing-key, rotation, and restore fixtures pass.
- [ ] Daily derivation is identical across instances, versioned, UTC-safe, and stable across midnight/key rotation.
- [ ] Active secrets are absent from all API/WS schemas, logs, traces, analytics, errors, local/session storage, service-worker cache, and share output.
- [ ] Friend/room tokens are high entropy, stored only as digests, generic on invalid lookup, rate-limited, revocable, and expiring.
- [ ] JWT wrong issuer/audience/algorithm/key, malformed/expired token, and anonymous claim cases pass.
- [ ] Exact CORS, CSP/connect origins, HSTS at ingress, frame denial, nosniff, referrer/permissions policies, secure cookies, and no public source maps are verified.
- [ ] Input normalization, Unicode control/bidi rejection, output escaping, request/body/page/time limits, and SQL parameterization are tested.
- [ ] Redis loss proves ranked/invite/admin/socket fail-closed behavior; trusted proxy/IP handling and endpoint limits are tested.
- [ ] WebSocket single-use ticket, replay, wrong room, expiry, frame/rate/concurrency, heartbeat, slow consumer, reconnect, and broker interruption tests pass.
- [ ] Threat model has current security/privacy/operations approval.

## Accessibility and client resilience

- [ ] WCAG 2.2 AA automated checks and documented keyboard/screen-reader/manual checks pass.
- [ ] Pegs/feedback never rely on colour; focus, announcements, target sizes, contrast, reduced motion, and timer behavior pass.
- [ ] Mobile/responsive, light/dark, offline explanation, stale service worker, reconnect, and unsent-row restoration pass.
- [ ] PWA manifest/icons/installability and no offline-ranked claim are verified.

## Reliability, performance, and observability

- [ ] Production load profile meets documented p95 targets without N+1 queries, pool starvation, lock spikes, or unbounded labels.
- [ ] Liveness/readiness accurately cover process, PostgreSQL, and Redis degraded rules; graceful shutdown/draining is exercised.
- [ ] Dashboards/alerts cover release, errors, latency, DB/Redis, auth failure, limits, decrypt failure, sockets, replay, deletion backlog, and jobs.
- [ ] Logs are structured, access-restricted, retained 30 days, and pass token/secret/PII/guess canary scans.
- [ ] Backup/PITR is enabled; quarterly isolated restore and encryption-key recovery meet RPO/RTO.
- [ ] Incident contacts, private channel, status communication, provider escalation, and runbooks are exercised.

## Supply chain and release

- [ ] `uv.lock` and `pnpm-lock.yaml` are current; frozen clean installs pass.
- [ ] Python/TypeScript lint, type checks, unit/integration/property/e2e/accessibility/load tests and production builds pass.
- [ ] OpenAPI client drift, migration, Docker build, CodeQL, dependency review, secret scan, and filesystem/image vulnerability scans pass or have approved exceptions with expiry.
- [ ] Images run non-root/read-only, drop capabilities, contain no secrets/dev dependencies, expose health checks, and use immutable digests.
- [ ] Staging uses isolated Auth/database/Redis/keys and passes the complete smoke suite.
- [ ] Protected production environment requires review; unreviewed pull requests cannot deploy.
- [ ] Release images, migration revision, backup point, previous compatible images, observation window, and rollback decision owner are recorded.

## Final go/no-go

- [ ] Product owner approves required behavior and copy.
- [ ] Engineering owner approves test/build/performance evidence.
- [ ] Security/privacy owners approve controls, threat model, processors, and incident readiness.
- [ ] Operations owner approves capacity, alerts, backup/restore, deployment, and rollback.
- [ ] Legal owner approves policy/terms configuration.
- [ ] No unresolved launch-blocking item or expired exception remains.
