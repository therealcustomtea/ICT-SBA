# Environment variables

`NEXT_PUBLIC_*` values are embedded into browser JavaScript and must never contain credentials. `MASTERMIND_*` values configure the API and belong in a managed secret store in staging and production.

## API runtime

| Variable | Production | Purpose |
| --- | --- | --- |
| `MASTERMIND_ENVIRONMENT` | Required | `staging` or `production` enables strict validation |
| `MASTERMIND_MONGODB_URL` | Secret, required | TLS MongoDB connection string for the application database |
| `MASTERMIND_MONGODB_DATABASE` | Required | Database name; `Atom` is used by the configured Atlas workflow |
| `MASTERMIND_REDIS_URL` | Secret, required | TLS `rediss://` URL |
| `MASTERMIND_ALLOWED_ORIGINS` | Required | JSON array of exact HTTPS browser origins |
| `MASTERMIND_PRODUCT_ORIGIN` | Required | Exact browser origin used by email-link redirects |
| `MASTERMIND_RELEASE` | Required | Immutable source SHA or release identifier |

## First-party authentication

| Variable | Production | Purpose |
| --- | --- | --- |
| `MASTERMIND_AUTH_ISSUER` | Required | Exact public HTTPS API origin |
| `MASTERMIND_AUTH_AUDIENCE` | Required | Access-token audience; defaults to `cipherboard-web` |
| `MASTERMIND_AUTH_SIGNING_KEY` | Secret, required | At least 32 random bytes used for HS256 signing and token hashing |
| `MASTERMIND_AUTH_ACCESS_TOKEN_SECONDS` | Optional | Short-lived access token lifetime, 300–3600 seconds |
| `MASTERMIND_AUTH_REFRESH_TOKEN_DAYS` | Optional | Opaque refresh-token lifetime, 1–90 days |
| `MASTERMIND_AUTH_EMAIL_TOKEN_SECONDS` | Optional | One-time email-link lifetime |
| `MASTERMIND_AUTH_COOKIE_SECURE` | Must be `true` | Sends refresh cookies only over HTTPS |
| `MASTERMIND_AUTH_COOKIE_SAMESITE` | Required | `lax`, `strict`, or `none`; `none` requires Secure cookies |
| `MASTERMIND_AUTH_EMAIL_SENDER` | Required | Verified sender identity |
| `MASTERMIND_SMTP_HOST` | Required | SMTP hostname |
| `MASTERMIND_SMTP_PORT` | Required | SMTP port |
| `MASTERMIND_SMTP_USERNAME` | Secret when used | SMTP username |
| `MASTERMIND_SMTP_PASSWORD` | Secret when used | SMTP password |
| `MASTERMIND_SMTP_STARTTLS` | Required | Enable when the provider requires STARTTLS |

## Cryptography

| Variable | Production | Purpose |
| --- | --- | --- |
| `MASTERMIND_SECRET_ENCRYPTION_KEYS` | Secret, required | JSON map of key version to base64-encoded 32-byte AES key |
| `MASTERMIND_SECRET_ACTIVE_KEY_VERSION` | Required | Key version used for new ciphertext |
| `MASTERMIND_DAILY_HMAC_KEYS` | Secret, required | Versioned daily-puzzle HMAC keyring |
| `MASTERMIND_DAILY_HMAC_ACTIVE_KEY_VERSION` | Required | Active daily key version |
| `MASTERMIND_PUBLIC_IDENTIFIER_HMAC_KEY` | Secret, required | At least 32 bytes for capability-code hashing |

## Browser build

`NEXT_PUBLIC_API_ORIGIN`, `NEXT_PUBLIC_PRODUCT_ORIGIN`, `NEXT_PUBLIC_PRODUCT_NAME`, `NEXT_PUBLIC_SUPPORT_EMAIL`, `NEXT_PUBLIC_LEGAL_ENTITY`, `NEXT_PUBLIC_JURISDICTION`, and `NEXT_PUBLIC_POLICY_DATE` are public configuration. No database, Redis, SMTP, auth-signing, refresh-token, or encryption value may use the `NEXT_PUBLIC_` prefix.

## Production validation

Startup rejects local MongoDB/Redis hosts, non-TLS runtime URLs, inexact HTTPS origins, insecure cookies, placeholder keys, malformed AES keyrings, and mutable release identifiers. Atlas `mongodb+srv://` URLs enable TLS by default. Store the complete URI as one secret and percent-encode reserved characters in credentials.
