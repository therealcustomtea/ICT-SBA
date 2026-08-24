# MongoDB data model

MongoDB is the application system of record. The browser never connects to it directly; FastAPI authenticates, authorizes, validates, and performs database operations.

Document dataclasses and collection names are defined in `apps/api/mastermind_api/models.py`. The initializer in `apps/api/mastermind_api/database.py` creates indexes and seed documents.

Key collections include:

- `auth_users`, `auth_sessions`, and `auth_email_tokens` for first-party identities and session lifecycle;
- `profiles` for public names, preferences, moderation, and deletion state;
- `game_sessions`, with attempts embedded in authoritative order;
- `daily_challenges` and `friend_challenges` for reusable puzzle definitions;
- `multiplayer_rooms`, `multiplayer_members`, and `multiplayer_events` for durable duel state and replay;
- `leaderboard_entries`, `achievements`, and `user_achievements` for competitive/profile projections;
- `feature_flags`, `moderation_actions`, `audit_events`, `support_requests`, and `product_events` for operations.

UUID values are stored with standard MongoDB UUID representation. Date/time values are UTC. Secrets are stored only as AES-GCM ciphertext, nonce, and key version. Refresh, invite, and room tokens are stored only as keyed hashes.

Unique and partial indexes enforce identities, normalized email/name uniqueness, idempotency, room membership, event sequence, and one official daily definition. Cross-collection ownership and lifecycle constraints are enforced in the application transaction and covered by tests. Leaderboards use aggregation pipelines with `$lookup`, `$setWindowFields`, and stable tie ordering.

Document changes must remain compatible with previously stored shapes until a bounded backfill completes. See `docs/operations/MIGRATIONS.md`.
