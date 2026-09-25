# Fresh install example (no personal credentials or paths)

**Goal:** start SwarmAI on a new machine from an empty environment without copying developer secrets, personal home paths, or a named production hostname.

This follows the clean-install intent in `docs/artifacts/future/ART-V20-INSTALL_UPGRADE_PROTOCOL.md` for local engineering installs. It is **not** production launch evidence.

## Preconditions

- Empty checkout (or fresh clone) with no prior `var/`, no local Postgres volume from a previous install, and no filled `.env`
- Python 3.12 + [uv](https://docs.astral.sh/uv/)
- Optional: Docker for standalone/server profiles
- No provider API keys required for mock path

## Forbidden in this example

Do **not** use:

- Personal absolute home checkouts (any operator-specific home directory as a required install root)
- Personal hostnames or emails
- Copied production tokens, Cloudflare credentials, or provider keys
- Hardcoded public DNS (use placeholders such as `coordinator.example.test`)

Use checkout-relative paths and env placeholders only.

## Steps (mock — no Docker)

```sh
# 1) Dependencies
uv sync

# 2) Blank env — values stay empty for mock
cp .env.example .env
# Optional portable overlay (still blank secrets):
cp examples/fresh-install/portable.env.example examples/fresh-install/portable.env

# 3) Doctor (security + start readiness)
uv run swarm deploy doctor --profile mock
# Expect ready_to_start=true for mock

# 4) Offline packaging smoke
uv run swarm release install-check
uv run swarm release verify

# 5) Start API (loopback)
uv run swarm serve --host 127.0.0.1 --port 8765

# 6) Health
curl -fsS http://127.0.0.1:8765/health/live
curl -fsS http://127.0.0.1:8765/health/ready

# 7) Optional console (no public bind)
npm --prefix apps/console install
npm --prefix apps/console run dev -- --host 127.0.0.1 --port 5173
```

## Steps (product — Docker: console + API + worker)

Preferred real-product packaging (PC-10 / L6):

```sh
cp deploy/env/product.env.example deploy/env/product.env
# Set SWARM_PG_PASSWORD and SWARM_SEED_LOOPBACK_TOKEN to local random values only.

docker compose -f deploy/compose/product.yml --env-file deploy/env/product.env up --build -d

# API / SDK / CLI (loopback)
curl -fsS "http://127.0.0.1:${SWARM_HOST_PORT:-8765}/health/live"
curl -fsS "http://127.0.0.1:${SWARM_HOST_PORT:-8765}/health/ready"

# Console (same-origin /v1 proxy; pass token query or rely on injected seed)
# http://127.0.0.1:${SWARM_CONSOLE_HOST_PORT:-43127}/?mode=live
# http://127.0.0.1:43127/?mode=live&token=$SWARM_SEED_LOOPBACK_TOKEN
```

Services: `api` (coordinator/server), `console` (static UI + nginx proxy), `worker` (outbound connector), `db` (private Postgres). Volumes persist `var/`, worker workspaces, and Postgres. No public ingress; `SWARM_ALLOW_PAID=false`.

Server-only or worker-only stacks remain available (`server.yml`, `worker.yml`).

## Steps (standalone — Docker, empty DB volume)

```sh
cp deploy/env/portable.env.example deploy/env/portable.env
# Edit ONLY placeholders: set SWARM_PG_PASSWORD to a random local value
# and SWARM_SEED_LOOPBACK_TOKEN to a long random string. Do not paste
# tokens from another machine.

export SWARM_DATABASE_URL="postgresql+psycopg://swarm:REPLACE_LOCAL_PG_PASSWORD@127.0.0.1:5432/swarm"
# Note: standalone compose keeps Postgres on the internal network only —
# set SWARM_DATABASE_URL for doctor/host-side migrate tools when you
# intentionally publish or exec into the DB network.

uv run swarm deploy doctor --profile standalone
# ready_to_start is false until SWARM_DATABASE_URL is set for host-side tools;
# compose itself injects the DB URL inside the API container.

docker compose -f deploy/compose/standalone.yml build
docker compose -f deploy/compose/standalone.yml up -d

# Migrations: standalone image may require an entrypoint or:
# docker compose -f deploy/compose/standalone.yml exec api alembic upgrade head
# Prefer deploy/compose/server.yml for migrate-on-start.
```

For migrate-on-start + persisted `var/`, use the portable **server** profile with `deploy/env/portable.env` (see [SERVER_WORKER_STARTUP.md](SERVER_WORKER_STARTUP.md)).

## Verify empty/honest state

After start with no provider keys:

- `/health/ready` reports `allow_paid: false` and does not invent live provider readiness
- `uv run swarm providers onboarding-report` lists missing secret **names**, never values
- No mission fixtures appear unless you explicitly seed fixtures or run a demo command

## Restart persistence check

```sh
# After creating a local project/mission via API or CLI in mock/file mode:
uv run swarm projects list
# Stop and restart serve; durable identities under var/ must reopen unchanged.
```

## Support bundle (secret-safe)

```sh
uv run swarm install support-bundle
# Bundle lists env *names* only — never paste real .env contents into tickets.
```

## Exit criteria for this example

| Check | Pass when |
|---|---|
| No personal paths in commands | Only checkout-relative or `$HOME` as optional token *storage* you create |
| No personal hostnames | Public URL placeholders only |
| No copied secrets | Tokens generated on this host |
| Health | live=ok; ready reflects real DB/runtime state |
| Install without code edits | Env + compose only |
