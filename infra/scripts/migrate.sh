#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/../.."

environment="${MASTERMIND_ENVIRONMENT:-}"
database_url="${DATABASE_MIGRATOR_URL:-}"

if [[ -z "${environment}" || -z "${database_url}" ]]; then
  echo 'MASTERMIND_ENVIRONMENT and DATABASE_MIGRATOR_URL are required.' >&2
  exit 1
fi

if [[ "${database_url}" == sqlite* ]]; then
  echo 'Release migrations require PostgreSQL.' >&2
  exit 1
fi

export MASTERMIND_DATABASE_URL="${database_url}"
uv run alembic -c apps/api/alembic.ini upgrade head
