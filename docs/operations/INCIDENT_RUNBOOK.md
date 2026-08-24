# Incident runbook

First contain the affected surface, preserve correlation IDs and audit evidence, and avoid logging tokens, email links, credentials, game secrets, or personal data.

- **Auth token or signing-key compromise:** rotate the signing key, revoke all affected `auth_sessions`, require reauthentication, rotate any exposed refresh-token hashing material, and verify refresh reuse detection.
- **MongoDB credential compromise:** disable the Atlas user or network path, create a replacement least-privilege user, rotate the secret-managed URI, inspect Atlas audit/network evidence, and sample unauthorized document changes.
- **MongoDB outage/corruption:** fail integrity-sensitive writes closed, restore/fail over through the provider, verify indexes and transactions, reconcile backups/PITR, then re-admit traffic gradually.
- **Redis outage:** new rate-sensitive, ticket, and room coordination paths fail closed or degrade as documented. MongoDB remains authoritative. Restore Redis, clear stale ephemeral presence/tickets, and test pub/sub before normal traffic.
- **SMTP compromise/outage:** disable magic-link issuance if delivery cannot be trusted, rotate provider credentials, invalidate outstanding `auth_email_tokens`, verify sender/DNS controls, and keep existing sessions available when safe.
- **Encryption-key compromise:** disable creation/decryption paths that use the key, rotate to a new version, preserve evidence, assess affected ciphertext, and re-encrypt only through a bounded audited job.

After containment, document scope, timeline, root cause, data/session impact, rotations, restoration evidence, and follow-up owners. Notify users/regulators according to the applicable legal and privacy process.
