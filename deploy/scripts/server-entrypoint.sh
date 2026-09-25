#!/bin/sh
# Server container entrypoint: fix volume perms, migrate, then serve as non-root.
# Never prints secret values.
set -eu

PORT="${SWARM_PORT:-8765}"
HOST="${SWARM_BIND_HOST:-0.0.0.0}"

if [ "$(id -u)" = "0" ]; then
  mkdir -p /app/var/artifacts /app/var/missions /app/var/install /app/var/projects
  chown -R swarm:swarm /app/var
  # Re-exec as swarm for migrate + serve (no privileged runtime).
  exec runuser -u swarm -- "$0" "$@"
fi

if [ -n "${SWARM_DATABASE_URL:-}" ]; then
  echo "swarm-entrypoint: running alembic upgrade head"
  alembic upgrade head
else
  echo "swarm-entrypoint: SWARM_DATABASE_URL unset — skip migrate (mock-only)"
fi

echo "swarm-entrypoint: starting api on ${HOST}:${PORT}"
exec uvicorn swarm.api.app:app --host "${HOST}" --port "${PORT}" --proxy-headers
