#!/usr/bin/env bash
# Uses Bash from the current environment to execute this script.
# Enables strict shell behavior so failures and unset variables stop execution.
set -euo pipefail

# Changes into the repository root before running project commands.
cd "$(dirname "${BASH_SOURCE[0]}")/../.."

# Checks this condition before running the guarded branch.
if [[ "${MASTERMIND_ENVIRONMENT:-development}" != 'development' && "${MASTERMIND_ENVIRONMENT:-}" != 'test' ]]; then
  # Prints this status or error message for the operator.
  echo 'Database reset is restricted to development and test.' >&2
  # Stops the script with this explicit process status.
  exit 1
# Closes the conditional, loop, or function block started above.
fi

# Checks this condition before running the guarded branch.
if [[ "${CONFIRM_LOCAL_RESET:-}" != 'mastermind-local-only' ]]; then
  # Prints this status or error message for the operator.
  echo 'Set CONFIRM_LOCAL_RESET=mastermind-local-only to destroy the local Compose database.' >&2
  # Stops the script with this explicit process status.
  exit 1
# Closes the conditional, loop, or function block started above.
fi

# Runs this container operation for the local development stack.
docker compose down --volumes --remove-orphans
# Runs this container operation for the local development stack.
docker compose up -d --wait mongo redis mailpit
