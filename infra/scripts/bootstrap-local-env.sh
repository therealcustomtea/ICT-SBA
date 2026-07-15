#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/../.."

if [[ -e .env ]]; then
  echo '.env already exists; refusing to overwrite it.' >&2
  exit 1
fi

if ! command -v openssl >/dev/null 2>&1; then
  echo 'openssl is required to generate local-only keys.' >&2
  exit 1
fi

db_password="$(openssl rand -hex 18)"
game_key="$(openssl rand -base64 32 | tr -d '\n')"
daily_key="$(openssl rand -hex 32)"
identifier_key="$(openssl rand -hex 32)"

awk \
  -v db_password="${db_password}" \
  -v game_key="${game_key}" \
  -v daily_key="${daily_key}" \
  -v identifier_key="${identifier_key}" '
    /^POSTGRES_PASSWORD=/ { print "POSTGRES_PASSWORD=" db_password; next }
    /^MASTERMIND_DATABASE_URL=/ { print "MASTERMIND_DATABASE_URL=postgresql+asyncpg://mastermind:" db_password "@localhost:5432/mastermind"; next }
    /^DATABASE_MIGRATOR_URL=/ { print "DATABASE_MIGRATOR_URL=postgresql+asyncpg://mastermind:" db_password "@localhost:5432/mastermind"; next }
    /^MASTERMIND_SECRET_ENCRYPTION_KEYS=/ { print "MASTERMIND_SECRET_ENCRYPTION_KEYS={\"v1\":\"" game_key "\"}"; next }
    /^MASTERMIND_DAILY_HMAC_KEY=/ { print "MASTERMIND_DAILY_HMAC_KEY=" daily_key; next }
    /^MASTERMIND_PUBLIC_IDENTIFIER_HMAC_KEY=/ { print "MASTERMIND_PUBLIC_IDENTIFIER_HMAC_KEY=" identifier_key; next }
    { print }
  ' .env.example > .env

chmod 600 .env

echo 'Created .env with local-only database and cryptographic keys.'
# Command names are intentionally rendered literally.
# shellcheck disable=SC2016
echo 'Run `supabase start` and `supabase status`, then fill the four empty Supabase values.'
