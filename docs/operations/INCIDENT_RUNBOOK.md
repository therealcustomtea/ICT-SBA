# Incident runbook

## Severity

- **SEV-1:** confirmed credential/secret-code breach, active auth/admin bypass, destructive data corruption, broad privacy exposure, or complete production outage.
- **SEV-2:** ranked integrity compromise, major feature outage, sustained elevated errors/latency, Redis/WebSocket outage, or suspected limited unauthorized access.
- **SEV-3:** isolated defect with a safe workaround, non-sensitive monitoring gap, or minor degradation.

The on-call incident commander assigns operations, security/privacy, communications, and scribe roles. Use an approved private incident channel. Do not paste tokens, keys, emails, guesses, invite links, ciphertext, raw database rows, or environment dumps into chat/tickets.

## First 15 minutes

1. Confirm impact with health, metrics, and safe logs; note UTC detection time and release.
2. Declare severity and incident commander.
3. Preserve non-sensitive evidence and audit records; pause automated cleanup that could destroy evidence.
4. Contain with the narrowest safe control: force off affected feature, remove a release from ingress, revoke a credential, restrict admin, or fail ranked writes closed.
5. Protect active secrets and user data before availability. Do not bypass authorization/rate limits to recover service.
6. Establish update cadence and identify legal/privacy notification owner where relevant.

## Investigation checklist

- recent image digest, migration revision, feature-flag/admin audit changes;
- auth failures, issuer/audience/JWKS health, session revocation state;
- PostgreSQL connectivity, locks, replication lag, constraint/errors, disk/connection saturation;
- Redis connectivity, latency, memory/eviction, rate-limit and pub/sub failures;
- API/web error rate and latency by bounded route label;
- WebSocket active/reconnect/reject/slow-consumer counts;
- evidence of secret/token/PII strings in logs, traces, analytics, browser bundle, or event payloads;
- unexpected public access to database/Data API, object registry, backups, or admin routes.

Correlate by request/release/audit identifiers, not email or raw player content.

## Playbooks

### Suspected active secret or encryption-key disclosure

Force off creation/ranked/multiplayer modes that depend on affected material. Stop log/trace export if it is the disclosure channel while preserving restricted evidence. Identify versions and records without decrypting broadly. Rotate according to `KEY_ROTATION.md`; do not destroy old keys until affected sessions/backups are assessed. Invalidate compromised games and leaderboard rows through audited admin actions. Scan every response/event/log sink before re-enabling.

### Supabase secret, JWT signing, or session compromise

Remove server secret credentials from workloads, rotate them in Supabase, revoke affected sessions, and rotate asymmetric signing keys through the provider process. Confirm browser bundles never contained a secret/service key. Keep API fail closed if JWKS/session verification is uncertain. Require reauthentication and communicate scope without exposing identifiers.

### Authorization/admin bypass

Disable the affected route or admin feature, revoke suspicious sessions/roles, preserve audit/database evidence, and test adjacent resources for the same missing owner/member predicate. Treat hidden-route or client-role enforcement as no control. Restore only after explicit allowed/denied integration tests and independent review.

### Leaderboard or replay abuse

Force public boards off while leaving clearly unranked solo play available if safe. Mark affected entries under review instead of deleting evidence, inspect official-config/version/idempotency/concurrency controls, and repair transactionally. Re-enable after backfill/recalculation and anomaly monitoring.

### PostgreSQL outage/corruption

Readiness fails and all mutations stop. Do not route writes to an unverified replica. Engage the database provider, record the last known healthy UTC time, and choose failover or PITR using `BACKUP_AND_RESTORE.md`. Before traffic, reconcile migrations, constraints, deletion tombstones, key versions, and idempotency outcomes.

### Redis or real-time outage

Force ranked mutations, invite operations, admin mutations, and new WebSocket tickets closed. Existing connections are not trusted to decide winners without the authoritative database transaction. Restore Redis or fail over, clear stale presence/tickets, verify atomic limits and pub/sub, then admit rooms gradually. Durable PostgreSQL events repair missed fan-out.

### Bad deployment or migration

Stop rollout, remove new instances from ingress, and follow `ROLLBACK.md`. Do not downgrade the database merely to match old code. Prefer forward repair or a backward-compatible old image. Preserve failed migration output and check transaction state before retry.

### Privacy/data exposure

Restrict the affected store/route immediately, preserve access evidence, determine categories/subjects/time range/processors, and notify the privacy/legal owner. Follow jurisdictional assessment and notification deadlines configured for the business. Do not make unsupported promises to users. Complete processor deletion and access-key rotation where applicable.

## Recovery and closure

Run targeted security, gameplay, auth, health, and two-client real-time smokes before traffic. Observe one full peak or agreed window. Record root cause, timeline, scope, containment, evidence locations, user/processor communications, and follow-up owners/dates. Rotate temporary credentials and remove emergency access/overrides. Review whether threat model, controls, tests, retention, alerts, and launch checklist need updates. Conduct a blameless review for SEV-1/2.
