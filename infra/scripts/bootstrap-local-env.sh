#!/usr/bin/env bash
# Enables strict shell behavior so failures stop the script safely.
set -euo pipefail

# Moves to the expected working directory before project commands run.
cd "$(dirname "${BASH_SOURCE[0]}")/../.."

# Stores `mongodb_uri` for the subsequent shell steps.
mongodb_uri='mongodb://localhost:27017/?replicaSet=rs0'
# Checks this prerequisite before the guarded shell steps run.
if [[ "${1:-}" == '--mongodb-uri-from-stdin' || "${1:-}" == '--mongodb-uri-stdin' ]]; then
  # Stores `IFS` for the subsequent shell steps.
  IFS= read -r mongodb_uri || [[ -n "${mongodb_uri}" ]]
  # Stores `mongodb_uri` for the subsequent shell steps.
  mongodb_uri="${mongodb_uri#MONGODB_URI=}"
  # Stores `mongodb_uri` for the subsequent shell steps.
  mongodb_uri="${mongodb_uri#\'}"
  # Stores `mongodb_uri` for the subsequent shell steps.
  mongodb_uri="${mongodb_uri%\'}"
  # Stores `mongodb_uri` for the subsequent shell steps.
  mongodb_uri="${mongodb_uri#\"}"
  # Stores `mongodb_uri` for the subsequent shell steps.
  mongodb_uri="${mongodb_uri%\"}"
# Closes the conditional, loop, or function block opened above.
fi
# Checks this prerequisite before the guarded shell steps run.
if [[ "${mongodb_uri}" != mongodb://* && "${mongodb_uri}" != mongodb+srv://* ]]; then
  # Reports this status or error message to the operator.
  echo 'Expected a mongodb:// or mongodb+srv:// connection string.' >&2
  # Stops the script with an explicit failure status.
  exit 1
# Closes the conditional, loop, or function block opened above.
fi

# Stores `uri_without_query` for the subsequent shell steps.
uri_without_query="${mongodb_uri%%\?*}"
# Stores `mongodb_database` for the subsequent shell steps.
mongodb_database="${uri_without_query##*/}"
# Checks this prerequisite before the guarded shell steps run.
if [[ -z "${mongodb_database}" || "${mongodb_database}" == *:* ]]; then
  # Stores `mongodb_database` for the subsequent shell steps.
  mongodb_database='mastermind'
# Closes the conditional, loop, or function block opened above.
fi

# Checks this prerequisite before the guarded shell steps run.
if ! command -v openssl >/dev/null 2>&1; then
  # Reports this status or error message to the operator.
  echo 'openssl is required to generate local-only keys.' >&2
  # Stops the script with an explicit failure status.
  exit 1
# Closes the conditional, loop, or function block opened above.
fi

# Stores `source_file` for the subsequent shell steps.
source_file='.env.example'
# Checks this prerequisite before the guarded shell steps run.
if [[ -f .env ]]; then
  # Stores `source_file` for the subsequent shell steps.
  source_file='.env'
# Closes the conditional, loop, or function block opened above.
fi

# Performs this required step in the script or container workflow.
existing_value() {
  # Stores `key` for the subsequent shell steps.
  local key="$1"
  # Performs this required step in the script or container workflow.
  awk -F= -v key="${key}" '$1 == key {sub(/^[^=]*=/, ""); print; exit}' "${source_file}"
# Closes the conditional, loop, or function block opened above.
}

# Stores `auth_key` for the subsequent shell steps.
auth_key="$(existing_value MASTERMIND_AUTH_SIGNING_KEY)"
# Stores `game_keyring` for the subsequent shell steps.
game_keyring="$(existing_value MASTERMIND_SECRET_ENCRYPTION_KEYS)"
# Stores `daily_key` for the subsequent shell steps.
daily_key="$(existing_value MASTERMIND_DAILY_HMAC_KEY)"
# Stores `identifier_key` for the subsequent shell steps.
identifier_key="$(existing_value MASTERMIND_PUBLIC_IDENTIFIER_HMAC_KEY)"

# Performs this required step in the script or container workflow.
[[ -n "${auth_key}" ]] || auth_key="$(openssl rand -base64 48 | tr -d '\n')"
# Performs this required step in the script or container workflow.
[[ -n "${game_keyring}" ]] || game_keyring="{\"v1\":\"$(openssl rand -base64 32 | tr -d '\n')\"}"
# Performs this required step in the script or container workflow.
[[ -n "${daily_key}" ]] || daily_key="$(openssl rand -hex 32)"
# Performs this required step in the script or container workflow.
[[ -n "${identifier_key}" ]] || identifier_key="$(openssl rand -hex 32)"

# Stores `temporary_env` for the subsequent shell steps.
temporary_env="$(mktemp .env.XXXXXX)"
# Registers cleanup so temporary state is not left behind.
trap 'rm -f "${temporary_env}"' EXIT

# Performs this required step in the script or container workflow.
awk \
  -v mongodb_uri="${mongodb_uri}" \
  -v mongodb_database="${mongodb_database}" \
  -v auth_key="${auth_key}" \
  -v game_keyring="${game_keyring}" \
  -v daily_key="${daily_key}" \
  -v identifier_key="${identifier_key}" '
    # Performs this required step in the script or container workflow.
    /^(POSTGRES_|POSTGRES_CA_FILE=|DATABASE_MIGRATOR_URL=|MIGRATOR_ENV_FILE=|MASTERMIND_DATABASE_URL=|MASTERMIND_SUPABASE_|NEXT_PUBLIC_SUPABASE_)/ { next }
    # Performs this required step in the script or container workflow.
    /^MASTERMIND_MONGODB_URL=/ { print "MASTERMIND_MONGODB_URL=" mongodb_uri; seen_mongo=1; next }
    # Performs this required step in the script or container workflow.
    /^MASTERMIND_MONGODB_DATABASE=/ { print "MASTERMIND_MONGODB_DATABASE=" mongodb_database; seen_database=1; next }
    # Performs this required step in the script or container workflow.
    /^MASTERMIND_AUTH_SIGNING_KEY=/ { print "MASTERMIND_AUTH_SIGNING_KEY=" auth_key; seen_auth=1; next }
    # Performs this required step in the script or container workflow.
    /^MASTERMIND_SECRET_ENCRYPTION_KEYS=/ { print "MASTERMIND_SECRET_ENCRYPTION_KEYS=" game_keyring; next }
    # Performs this required step in the script or container workflow.
    /^MASTERMIND_DAILY_HMAC_KEY=/ { print "MASTERMIND_DAILY_HMAC_KEY=" daily_key; next }
    # Performs this required step in the script or container workflow.
    /^MASTERMIND_PUBLIC_IDENTIFIER_HMAC_KEY=/ { print "MASTERMIND_PUBLIC_IDENTIFIER_HMAC_KEY=" identifier_key; next }
    # Performs this required step in the script or container workflow.
    { print }
    # Performs this required step in the script or container workflow.
    END {
      # Checks this prerequisite before the guarded shell steps run.
      if (!seen_mongo) print "MASTERMIND_MONGODB_URL=" mongodb_uri
      # Checks this prerequisite before the guarded shell steps run.
      if (!seen_database) print "MASTERMIND_MONGODB_DATABASE=" mongodb_database
      # Checks this prerequisite before the guarded shell steps run.
      if (!seen_auth) print "MASTERMIND_AUTH_SIGNING_KEY=" auth_key
    # Closes the conditional, loop, or function block opened above.
    }
  # Performs this required step in the script or container workflow.
  ' "${source_file}" > "${temporary_env}"

# Performs this required step in the script or container workflow.
chmod 600 "${temporary_env}"
# Performs this required step in the script or container workflow.
mv "${temporary_env}" .env
# Registers cleanup so temporary state is not left behind.
trap - EXIT

# Reports this status or error message to the operator.
echo "Configured .env for MongoDB database ${mongodb_database} with local auth keys."
