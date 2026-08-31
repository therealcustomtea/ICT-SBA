#!/usr/bin/env bash
# Uses Bash from the current environment to execute this script.
# Enables strict shell behavior so failures and unset variables stop execution.
set -euo pipefail

# Changes into the repository root before running project commands.
cd "$(dirname "${BASH_SOURCE[0]}")/../.."

# Iterates through these names for the repeated validation.
for command_name in docker uv pnpm; do
  # Checks this condition before running the guarded branch.
  if ! command -v "${command_name}" >/dev/null 2>&1; then
    # Prints this status or error message for the operator.
    echo "${command_name} is required." >&2
    # Stops the script with this explicit process status.
    exit 1
  # Closes the conditional, loop, or function block started above.
  fi
# Closes the conditional, loop, or function block started above.
done

# Checks this condition before running the guarded branch.
if [[ ! -f .env ]]; then
  # Prints this status or error message for the operator.
  echo 'Run infra/scripts/bootstrap-local-env.sh first.' >&2
  # Stops the script with this explicit process status.
  exit 1
# Closes the conditional, loop, or function block started above.
fi

# Removes this variable to avoid leaking stale state into later commands.
unset _MASTERMIND_DOTENV_LOAD_COMPLETE
# Reads and processes values until the input stream is exhausted.
while IFS= read -r -d '' assignment; do
  # The assignment contains the validated variable name and value.
  # shellcheck disable=SC2163
  # Exports this value so child processes inherit it.
  export "$assignment"
# Executes this command as the next step in the script workflow.
done < <(
  # Runs this Python project command through the locked environment.
  uv run python - <<'PY'
# Executes this command as the next step in the script workflow.
import re
# Executes this command as the next step in the script workflow.
import sys

# Executes this command as the next step in the script workflow.
from dotenv import dotenv_values

# Iterates through these names for the repeated validation.
for name, value in dotenv_values('.env').items():
    # Checks this condition before running the guarded branch.
    if value is None:
        # Executes this command as the next step in the script workflow.
        continue
    # Checks this condition before running the guarded branch.
    if re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', name) is None:
        # Executes this command as the next step in the script workflow.
        raise SystemExit(f'Invalid environment variable name: {name!r}')
    # Checks this condition before running the guarded branch.
    if name == '_MASTERMIND_DOTENV_LOAD_COMPLETE':
        # Executes this command as the next step in the script workflow.
        raise SystemExit('The local environment file contains a reserved variable name.')
    # Executes this command as the next step in the script workflow.
    sys.stdout.buffer.write(f'{name}={value}'.encode() + b'\0')
# Executes this command as the next step in the script workflow.
sys.stdout.buffer.write(b'_MASTERMIND_DOTENV_LOAD_COMPLETE=1\0')
# Ends the embedded Python heredoc started above.
PY
# Executes this command as the next step in the script workflow.
)
# Checks this condition before running the guarded branch.
if [[ "${_MASTERMIND_DOTENV_LOAD_COMPLETE:-}" != '1' ]]; then
  # Prints this status or error message for the operator.
  echo 'Unable to parse .env safely.' >&2
  # Stops the script with this explicit process status.
  exit 1
# Closes the conditional, loop, or function block started above.
fi
# Removes this variable to avoid leaking stale state into later commands.
unset _MASTERMIND_DOTENV_LOAD_COMPLETE

# Iterates through these names for the repeated validation.
for variable_name in MASTERMIND_MONGODB_URL MASTERMIND_AUTH_SIGNING_KEY; do
  # Checks this condition before running the guarded branch.
  if [[ -z "${!variable_name:-}" ]]; then
    # Prints this status or error message for the operator.
    echo "${variable_name} must be set in .env." >&2
    # Stops the script with this explicit process status.
    exit 1
  # Closes the conditional, loop, or function block started above.
  fi
# Closes the conditional, loop, or function block started above.
done

# Runs this container operation for the local development stack.
docker compose up -d --wait mongo redis mailpit

# Executes this command as the next step in the script workflow.
cleanup() {
  # Executes this command as the next step in the script workflow.
  jobs -p | xargs -r kill 2>/dev/null || true
# Closes the conditional, loop, or function block started above.
}
# Registers cleanup for normal exit and interruption signals.
trap cleanup EXIT INT TERM

# Runs this Python project command through the locked environment.
uv run uvicorn mastermind_api.main:app --host 127.0.0.1 --port 8000 --reload &
# Runs the selected web workspace command through pnpm.
pnpm --filter @mastermind/web dev &
# Waits for the background development services to exit.
wait
