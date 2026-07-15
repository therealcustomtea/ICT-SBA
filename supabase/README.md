# Supabase local authentication

Supabase is used for authentication only. The product API remains the sole data API and uses SQLAlchemy/Alembic for application schema changes. Do not add application migrations under this directory; `apps/api/alembic` is the single migration history.

The local configuration enables anonymous identities, manual identity linking, email testing through Inbucket, short access tokens, and conservative Auth rate limits. PostgREST, Storage, Realtime, and local analytics are disabled because the product has its own FastAPI, Redis real-time layer, and first-party telemetry boundary.

Start the local Auth stack with a currently supported Supabase CLI:

```bash
supabase start
supabase status
```

Copy the reported API URL and publishable key into `.env`. Never copy the reported secret key or service-role credential into a `NEXT_PUBLIC_` variable. Run the web and API processes on the host when using the default `127.0.0.1` local Supabase URL; the all-container Compose path expects a Supabase URL reachable from containers.

Production Auth settings are managed in the Supabase project dashboard or its management API. Before launch, enable CAPTCHA/Turnstile for anonymous creation, configure custom SMTP, restrict redirect URLs to exact HTTPS locations, configure asymmetric signing keys, and verify session/JWT expiry policy. Local relaxed email confirmation is not a production setting.
