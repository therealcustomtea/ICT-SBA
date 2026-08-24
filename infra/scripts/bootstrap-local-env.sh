#!/usr/bin/env bash
# Uses Bash from the current environment to execute this script.
# Enables strict shell behavior so failures and unset variables stop execution.
set -euo pipefail

# Changes into the repository root before running project commands.
cd "$(dirname "${BASH_SOURCE[0]}")/../.."

# Checks this condition before running the guarded branch.
if [[ -e .env ]]; then
  # Prints this status or error message for the operator.
  echo '.env already exists; refusing to overwrite it.' >&2
  # Stops the script with this explicit process status.
  exit 1
# Closes the conditional, loop, or function block started above.
fi

# Checks this condition before running the guarded branch.
if ! command -v openssl >/dev/null 2>&1; then
  # Prints this status or error message for the operator.
  echo 'openssl is required to generate local-only keys.' >&2
  # Stops the script with this explicit process status.
  exit 1
# Closes the conditional, loop, or function block started above.
fi

# Computes and stores this shell variable for subsequent commands.
db_password="$(openssl rand -hex 18)"
# Computes and stores this shell variable for subsequent commands.
game_key="$(openssl rand -base64 32 | tr -d '\n')"
# Computes and stores this shell variable for subsequent commands.
daily_key="$(openssl rand -hex 32)"
# Computes and stores this shell variable for subsequent commands.
identifier_key="$(openssl rand -hex 32)"

# Executes this command as the next step in the script workflow.
  # Passes this generated value into the AWK environment transformation.
  # Passes this generated value into the AWK environment transformation.
  # Passes this generated value into the AWK environment transformation.
  # Passes this generated value into the AWK environment transformation.
awk \
  -v db_password="${db_password}" \
  -v game_key="${game_key}" \
  -v daily_key="${daily_key}" \
  -v identifier_key="${identifier_key}" '
    # Transforms this matching environment entry in the AWK program.
    /^POSTGRES_PASSWORD=/ { print "POSTGRES_PASSWORD=" db_password; next }
    # Transforms this matching environment entry in the AWK program.
    /^MASTERMIND_DATABASE_URL=/ { print "MASTERMIND_DATABASE_URL=postgresql+asyncpg://mastermind:" db_password "@localhost:5432/mastermind"; next }
    # Transforms this matching environment entry in the AWK program.
    /^DATABASE_MIGRATOR_URL=/ { print "DATABASE_MIGRATOR_URL=postgresql+asyncpg://mastermind:" db_password "@localhost:5432/mastermind"; next }
    # Transforms this matching environment entry in the AWK program.
    /^MASTERMIND_SECRET_ENCRYPTION_KEYS=/ { print "MASTERMIND_SECRET_ENCRYPTION_KEYS={\"v1\":\"" game_key "\"}"; next }
    # Transforms this matching environment entry in the AWK program.
    /^MASTERMIND_DAILY_HMAC_KEY=/ { print "MASTERMIND_DAILY_HMAC_KEY=" daily_key; next }
    # Transforms this matching environment entry in the AWK program.
    /^MASTERMIND_PUBLIC_IDENTIFIER_HMAC_KEY=/ { print "MASTERMIND_PUBLIC_IDENTIFIER_HMAC_KEY=" identifier_key; next }
    # Transforms this matching environment entry in the AWK program.
    { print }
  # Executes this command as the next step in the script workflow.
  ' .env.example > .env

# Restricts the generated file permissions to its owner.
chmod 600 .env

# Prints this status or error message for the operator.
echo 'Created .env with local-only database and cryptographic keys.'
# Command names are intentionally rendered literally.
# shellcheck disable=SC2016
# Prints this status or error message for the operator.
echo 'Run `supabase start` and `supabase status`, then fill the four empty Supabase values.'
