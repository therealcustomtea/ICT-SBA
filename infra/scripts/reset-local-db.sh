#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/../.."

if [[ "${MASTERMIND_ENVIRONMENT:-development}" != 'development' && "${MASTERMIND_ENVIRONMENT:-}" != 'test' ]]; then
  echo 'Database reset is restricted to development and test.' >&2
  exit 1
fi

if [[ "${CONFIRM_LOCAL_RESET:-}" != 'mastermind-local-only' ]]; then
  echo 'Set CONFIRM_LOCAL_RESET=mastermind-local-only to destroy the local Compose database.' >&2
  exit 1
fi

docker compose down --volumes --remove-orphans
docker compose up -d --wait postgres redis
docker compose run --rm migrate
