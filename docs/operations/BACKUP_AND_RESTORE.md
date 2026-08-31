# Backup and restore

## Objectives

- MongoDB production target RPO: 5 minutes or better through managed point-in-time recovery.
- MongoDB target RTO: 60 minutes for a regional service with a rehearsed restore path.
- Redis is coordination/cache state and is not the game ledger; restoration is not required for correctness.
- Secret-manager versions and infrastructure configuration must be recoverable independently of database backups.

The selected provider's measured capabilities replace these targets only through an approved architecture decision and launch checklist update.

## Backup policy

Enable encrypted automated MongoDB backups and continuous WAL/PITR. Retain rolling backups for 35 days and protect deletion/settings changes with MFA and least privilege. Take an on-demand snapshot before any medium/high-risk migration. Store backups in a different failure domain; cross-region copies are recommended where jurisdiction and processor agreements permit.

Back up first-party authentication according to the selected Auth/database plan. If Auth and application data are separate, both restoration points and their UTC times must be recorded. Export neither refresh tokens nor application encryption keys into the database backup location.

Redis persistence may shorten degraded recovery but is not counted toward the RPO. After Redis loss, tickets/presence/rate counters are rebuilt; ranked and invite operations remain fail-closed until rate limiting and coordination are healthy.

## Preflight evidence

Record provider backup identifier, source environment/region, UTC restore point, schema revision, application image digest, encryption key versions required at that point, operator, incident/change identifier, and checksum where the provider exposes one. Verify all required key versions remain enabled before beginning.

## Restore drill

Restore into a new isolated network and database identity, never over the source:

1. Provision an empty target with no public ingress and a fresh runtime credential.
2. Restore the chosen snapshot/PITR point.
3. Configure the application with the historical key ring required for retained ciphertext.
4. Run MongoDB initializer `current`; apply only migrations approved for the target application image.
5. Run integrity checks: document counts by core collection, cross-collection reference sampling, unique-index status, active/terminal state consistency, decryption of a controlled fixture for each retained key version, leaderboard eligibility sampling, and deletion reconciliation.
6. Start API/web on an internal endpoint and run authenticated allowed/denied tests, a game attempt, daily lookup, and room reconnect simulation.
7. Confirm no email, analytics, webhooks, or public indexing can leave the isolated environment.
8. Measure RPO/RTO, capture non-sensitive evidence, then securely destroy the drill environment.

If production recovery is required, additionally rotate database credentials, rebind private networking, run deletion reconciliation before traffic, warm only safe caches, switch ingress gradually, and monitor closely.

## Logical backup for local/controlled migration checks

Use a libpq service entry and protected password file so credentials do not appear in shell history:

```bash
PGSERVICE=mastermind-backup pg_dump --format=custom --no-owner --no-acl --file=mastermind.dump
createdb mastermind_restore_test
PGSERVICE=mastermind-restore pg_restore --exit-on-error --single-transaction --no-owner --no-acl --dbname=mastermind_restore_test mastermind.dump
```

Logical dumps are supplemental; they do not replace managed PITR. Store dumps encrypted, restrict file permissions, checksum them, apply the 35-day lifecycle, and never upload them to issue trackers or CI artifacts.

## Quarterly drill acceptance

The restored service reaches the recorded revision; controlled ciphertext decrypts with all required versions; secrets never appear in output; auth/resource denial checks pass; deletion tombstones are reapplied; measured RPO/RTO meet targets; and the backup is destroyed on schedule. Failures create an owned launch/operational action and shorten the next drill interval.
