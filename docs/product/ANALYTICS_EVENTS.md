# Product analytics events

Analytics is first-party, optional, asynchronous, and disabled unless `MASTERMIND_FEATURE_ANALYTICS=true` and the database `analytics` feature flag is enabled. `POST /v1/analytics/events` requires a verified guest or registered identity, `consent: true`, `consentVersion: privacy-v1`, a UUID client event identifier, and one exact event-specific property set. Delivery failure never blocks gameplay.

## Allowed events

| Event | Safe properties |
| --- | --- |
| `game_started` | mode, official/custom difficulty; anonymous is derived server-side |
| `game_completed` | mode, result, attempts used, ranked boolean, score band |
| `game_abandoned` | mode, attempts used |
| `difficulty_selected` | official difficulty or `custom` |
| `daily_completed` | UTC challenge identifier, result, attempts used |
| `friend_challenge_created` | official/custom boolean, expiry band |
| `room_joined` | room lifecycle state, reconnect boolean |
| `duel_completed` | result, attempts used, tie boolean |
| `validation_error` | stable error category only |
| `reconnect` | surface, recovered boolean |
| `account_upgraded` | previous identity was anonymous |

## Prohibited data

Events never contain secret codes, complete guess sequences, authentication or refresh tokens, email addresses, raw IP addresses, private challenge titles, free-form admin reasons, or encryption material. Operational logs use a pseudonymous identifier only where correlation is required.

## Retention and access

Product-event retention is documented in `docs/privacy/RETENTION.md`. Access is restricted to authorized operators. Analytics records are omitted from user-facing rankings and are not a gameplay source of truth.

The database uses typed nullable columns with allowlist check constraints rather than a general JSON payload. It stores no user/profile foreign key. Event identifiers are at-most-once retry keys: the first accepted payload wins, and later collisions are acknowledged without reading or mutating the insert-only analytics table. Event rows receive an expiry timestamp at collection time.
