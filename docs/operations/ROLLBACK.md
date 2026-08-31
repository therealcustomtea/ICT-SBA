# Rollback

Application rollback uses the protected workflow and previously recorded digest-pinned API/web image references. It does not revert MongoDB documents or indexes.

MongoDB shape changes must therefore be forward and backward compatible for at least one release window. If a release writes a new field, the previous release must ignore it safely. If a backfill is required, make it resumable and retain the previous field until rollback is no longer needed.

After rollback, verify API readiness, guest/refresh auth, profile access, gameplay, leaderboard integrity, email delivery, and one room reconnect. Preserve the incident/change identifier and both image digests in the release record.
