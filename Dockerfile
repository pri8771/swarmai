# syntax=docker/dockerfile:1.7
# Reproducible SwarmAI API image — non-root, pinned Python via uv.
FROM python:3.12.11-slim-bookworm AS build

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    PIP_DISABLE_PIP_VERSION_CHECK=1

COPY --from=ghcr.io/astral-sh/uv:0.8.22 /uv /usr/local/bin/uv

WORKDIR /app
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock README.md ./
COPY src ./src
COPY migrations ./migrations
COPY alembic.ini ./
COPY config ./config
COPY schemas ./schemas
COPY scripts ./scripts

RUN uv sync --frozen --no-dev --no-editable

FROM python:3.12.11-slim-bookworm AS runtime

RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 1000 swarm \
    && useradd --uid 1000 --gid 1000 --create-home --shell /usr/sbin/nologin swarm

WORKDIR /app
COPY --from=build --chown=swarm:swarm /app /app
COPY --chown=root:root deploy/scripts/server-entrypoint.sh /app/deploy/scripts/server-entrypoint.sh
RUN chmod 755 /app/deploy/scripts/server-entrypoint.sh

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    SWARM_ALLOW_PAID=false \
    SWARM_BIND_HOST=0.0.0.0 \
    SWARM_PORT=8765 \
    SWARM_REPO_ROOT=/app

# Entrypoint starts as root only to chown /app/var, then drops to swarm.
USER root
EXPOSE 8765
HEALTHCHECK --interval=10s --timeout=3s --start-period=20s --retries=5 \
  CMD curl -fsS http://127.0.0.1:8765/health/live || exit 1

ENTRYPOINT ["/app/deploy/scripts/server-entrypoint.sh"]
