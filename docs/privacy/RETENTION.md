# Retention and deletion

## Implemented schedule

Retention periods are counted from the event stated below. The maintenance command implements only the rows marked automatic. The current schema has no record-level legal-hold field. A deployment that requires legal holds must add and review that capability before enabling destructive scheduled cleanup; pausing a whole job is not represented here as a record-level hold.

| Record | Default retention | Deletion/anonymization action |
|---|---:|---|
| Active solo game | 7 days from creation | Automatically transition to `expired` at its fixed deadline |
| Active daily game | 24 hours from creation | Automatically transition to `expired`; crossing UTC midnight does not change its daily definition |
| Active practice or pass-and-play game | 24 hours from creation | Automatically transition to `expired` |
| Active friend challenge game | Earlier of 30 days from start or the parent challenge expiry | Automatically transition to `expired` |
| Active duel game | Earlier of 2 hours from start or the parent room expiry | Automatically transition to `expired` |
| Eligible ranked win/loss and attempts | 730 days after completion | Automatically delete the session; attempts and leaderboard row are deleted first |
| Abandoned, expired, or unranked session and attempts | 365 days after completion | Automatically delete attempts and the session |
| Public leaderboard entry | While user opts in, maximum 24 months for rolling boards | Remove immediately on opt-out/deletion/ban; all-time may retain anonymous score only after policy approval |
| Daily challenge definition | Indefinite | Keep date/config/versions; never store HMAC key/seed in the row |
| Friend challenge unused | At its 30-day expiry | Automatically delete title, token digest, and encrypted secret |
| Friend challenge completed | 90 days after last official win/loss, and only after challenge expiry | Automatically delete challenge data; participant sessions remain with the relationship cleared |
| Multiplayer room and safe events | 30 days after completion, termination, or natural expiry | Automatically delete events and members before the room; member game records remain with the relationship cleared |
| Redis ticket/presence | 60 seconds / 5 minutes maximum | Automatic TTL |
| Redis rate-limit keys | Enforcement window plus 10 minutes maximum | Automatic TTL |
| Product analytics events | 396 days from collection | Automatically delete event-level rows; no aggregate table is currently created by this job |
| Application logs | 30 days | Automatic log-store expiry |
| Security logs and admin audit events | Operator policy | Not deleted by the automated job because incident/hold disposition is not represented in schema |
| Moderation actions/restrictions | Operator policy | Not deleted by the automated job because restriction and review disposition are not represented in schema |
| Pending account deletion | Target completion within 24 hours | Alert if pending exceeds one hour; retry until reconciled |
| Anonymous Auth identity with no activity | Not automated | The schema does not yet have a trustworthy account-level last-activity or legal-hold marker |
| Backup | 35 days rolling; monthly restore-test artifact 90 days | Provider lifecycle deletion; encryption keys retained for backup window |
| Support correspondence | 12 months after ticket closure | Delete or anonymize according to support-provider controls |

The `mastermind-retention` command touches only application MongoDB rows: game sessions/attempts and dependent leaderboard links, friend challenges, rooms/members/events, and product events. first-party authentication identities, Redis TTLs, centralized application/security logs, database backups, support-provider records, audit events, and moderation actions require the external provider or reviewed operator policies shown above; this command does not claim to enforce those lifecycles.

## Account deletion sequence

1. Reauthenticate the requester and verify the live session.
2. In a database transaction, set `deletion_pending`, disable public visibility, revoke owned active challenges/rooms, and create an audit event without copying PII.
3. Deny new activity for the profile immediately.
4. Globally revoke refresh sessions using the presented live first-party authentication access token, then delete the Auth user using a server-only admin credential. Already-issued access JWTs remain cryptographically valid until expiry, so the application tombstone denies account activity immediately.
5. In an idempotent application transaction, remove display name/preferences, detach or delete public entries, delete achievements and private history due for immediate removal, and pseudonymize retained integrity records.
6. Mark deletion complete and schedule remaining records/backups for normal expiry.

If Auth is unavailable, the account remains hidden and blocked with a durable `provider_failed` deletion row. A bounded application worker claims rows with database locks and retries the idempotent Auth deletion without requiring the user to sign in again. Repeating the request returns the same safe status and does not recreate data.

## Anonymous cleanup

first-party authentication does not automatically remove anonymous users, but automatic anonymous-account deletion is intentionally disabled in this release. `profiles.updated_at` is not a reliable last-activity timestamp, and there is no legal-hold state. Guessing from profile age could delete an active or recently used identity. Add a reviewed account-activity marker and hold model before scheduling anonymous cleanup, then route candidates through the existing application tombstone and `account_deletion_requests` provider-retry state machine. Direct bulk deletion from `auth.users` without application reconciliation is prohibited.

## Backups and deletion

Deleted records may remain in encrypted backups until the 35-day backup lifecycle expires. Backups are not restored to answer ordinary user requests. If a disaster restore reintroduces deletion tombstones or pending deletions, the reconciliation job reapplies them before public traffic is enabled.

## Verification

Automated tests cover deterministic mode deadlines, request-time expiry, bounded/resumable cleanup, dependency ordering, MongoDB `SKIP LOCKED`, visibility removal, repeat account deletion, external Auth failure, challenge/room revocation, and leaderboard exclusion. Operations monitor overdue account deletion jobs, retention command failures, unexpectedly old Redis keys, and backup lifecycle policy. A quarterly sample reconciles database age distributions against this schedule without viewing private game content.
