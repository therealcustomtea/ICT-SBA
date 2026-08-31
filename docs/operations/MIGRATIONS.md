# MongoDB collection and index changes

MongoDB collection/index definitions live in `apps/api/mastermind_api/database.py`. Dataclass document shapes live in `apps/api/mastermind_api/models.py`.

The idempotent initializer is the only schema-management entry point:

```bash
uv run mastermind-initialize
```

The production release profile runs the same entry point before the API rollout. It creates missing collections, indexes, and required seed documents. It does not drop collections or delete documents.

For a document-shape change:

1. Add tolerant reads so old and new documents remain usable during rollout.
2. Add the new field/index definition and a focused test.
3. Backfill in bounded, resumable batches when existing documents require transformation.
4. Deploy compatible application code before enforcing a new unique or required invariant.
5. Verify index build status, error rate, and representative old/new documents.

Avoid unbounded scans, collection-wide in-memory loads, and destructive rename/drop operations. Take a verified backup before medium- or high-risk changes. Rollback normally means rolling back application images while retaining forward-compatible document shapes.
