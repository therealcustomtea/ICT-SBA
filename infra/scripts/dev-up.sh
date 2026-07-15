#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/../.."

for command_name in docker supabase uv pnpm; do
  if ! command -v "${command_name}" >/dev/null 2>&1; then
    echo "${command_name} is required." >&2
    exit 1
  fi
done

if [[ ! -f .env ]]; then
  echo 'Run infra/scripts/bootstrap-local-env.sh first.' >&2
  exit 1
fi

unset _MASTERMIND_DOTENV_LOAD_COMPLETE
while IFS= read -r -d '' assignment; do
  # The assignment contains the validated variable name and value.
  # shellcheck disable=SC2163
  export "$assignment"
done < <(
  uv run python - <<'PY'
import re
import sys

from dotenv import dotenv_values

for name, value in dotenv_values('.env').items():
    if value is None:
        continue
    if re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', name) is None:
        raise SystemExit(f'Invalid environment variable name: {name!r}')
    if name == '_MASTERMIND_DOTENV_LOAD_COMPLETE':
        raise SystemExit('The local environment file contains a reserved variable name.')
    sys.stdout.buffer.write(f'{name}={value}'.encode() + b'\0')
sys.stdout.buffer.write(b'_MASTERMIND_DOTENV_LOAD_COMPLETE=1\0')
PY
)
if [[ "${_MASTERMIND_DOTENV_LOAD_COMPLETE:-}" != '1' ]]; then
  echo 'Unable to parse .env safely.' >&2
  exit 1
fi
unset _MASTERMIND_DOTENV_LOAD_COMPLETE

for variable_name in MASTERMIND_SUPABASE_URL NEXT_PUBLIC_SUPABASE_URL NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY; do
  if [[ -z "${!variable_name:-}" ]]; then
    echo "${variable_name} must be set in .env after running supabase status." >&2
    exit 1
  fi
done

supabase start
docker compose up -d --wait postgres redis
uv run alembic -c apps/api/alembic.ini upgrade head

cleanup() {
  jobs -p | xargs -r kill 2>/dev/null || true
}
trap cleanup EXIT INT TERM

uv run uvicorn mastermind_api.main:app --host 127.0.0.1 --port 8000 --reload &
pnpm --filter @mastermind/web dev &
wait
