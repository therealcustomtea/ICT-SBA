#!/usr/bin/env bash
# Uses Bash from the current environment to execute this script.
# Enables strict shell behavior so failures and unset variables stop execution.
set -euo pipefail

# Changes into the repository root before running project commands.
cd "$(dirname "${BASH_SOURCE[0]}")/../.."

# Computes and stores this shell variable for subsequent commands.
environment="${MASTERMIND_ENVIRONMENT:-}"
# Computes and stores this shell variable for subsequent commands.
database_url="${DATABASE_MIGRATOR_URL:-}"

# Checks this condition before running the guarded branch.
if [[ -z "${environment}" || -z "${database_url}" ]]; then
  # Prints this status or error message for the operator.
  echo 'MASTERMIND_ENVIRONMENT and DATABASE_MIGRATOR_URL are required.' >&2
  # Stops the script with this explicit process status.
  exit 1
# Closes the conditional, loop, or function block started above.
fi

# Checks this condition before running the guarded branch.
if [[ "${database_url}" == sqlite* ]]; then
  # Prints this status or error message for the operator.
  echo 'Release migrations require PostgreSQL.' >&2
  # Stops the script with this explicit process status.
  exit 1
# Closes the conditional, loop, or function block started above.
fi

# Exports this value so child processes inherit it.
export MASTERMIND_DATABASE_URL="${database_url}"
# Runs this Python project command through the locked environment.
uv run alembic -c apps/api/alembic.ini upgrade head
