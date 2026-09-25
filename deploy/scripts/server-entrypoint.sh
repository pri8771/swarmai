#!/bin/sh
# Server container entrypoint: migrate then serve.
# Never prints secret values.
set -eu

PORT="${SWARM_PORT:-8765}"
HOST="${SWARM_BIND_HOST:-0.0.0.0}"

if [ -n "${SWARM_DATABASE_URL:-}" ]; then
  echo "swarm-entrypoint: running alembic upgrade head"
  alembic upgrade head
else
  echo "swarm-entrypoint: SWARM_DATABASE_URL unset — skip migrate (mock-only)"
fi

echo "swarm-entrypoint: starting api on ${HOST}:${PORT}"
exec uvicorn swarm.api.app:app --host "${HOST}" --port "${PORT}" --proxy-headers
