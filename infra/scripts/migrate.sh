#!/usr/bin/env bash
# Uses Bash from the current environment to execute this script.
# Enables strict shell behavior so failures and unset variables stop execution.
set -euo pipefail

# Changes into the repository root before running project commands.
cd "$(dirname "${BASH_SOURCE[0]}")/../.."

# Computes and stores this shell variable for subsequent commands.
environment="${MASTERMIND_ENVIRONMENT:-}"
# Computes and stores this shell variable for subsequent commands.
database_url="${MASTERMIND_MONGODB_URL:-}"

# Checks this condition before running the guarded branch.
if [[ -z "${environment}" || -z "${database_url}" ]]; then
  # Prints this status or error message for the operator.
  echo 'MASTERMIND_ENVIRONMENT and MASTERMIND_MONGODB_URL are required.' >&2
  # Stops the script with this explicit process status.
  exit 1
# Closes the conditional, loop, or function block started above.
fi

# Checks this condition before running the guarded branch.
if [[ "${database_url}" != mongodb://* && "${database_url}" != mongodb+srv://* ]]; then
  # Reports this status or error message to the operator.
  echo 'Release index setup requires a MongoDB connection string.' >&2
  # Stops the script with an explicit failure status.
  exit 1
# Closes the conditional, loop, or function block opened above.
fi

# Performs this required step in the script or container workflow.
uv run mastermind-initialize
