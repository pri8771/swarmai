# Server and worker startup

Roles are **configuration**, not machine names. Supported profiles: `mock`, `standalone`, `hybrid`, `recovery`, `server`, `mac_connector` (the last is a platform adapter label — see reference guide).

## Roles

| Role | What runs | Profile |
|---|---|---|
| Combined (dev) | API + in-process workers | `mock` or `uv run swarm serve` |
| Server | API + Postgres (+ optional ingress sidecar) | `server` or `standalone` |
| Worker | Outbound connector to `SWARM_SERVER_URL` | connector env / worker client |
| Recovery | Side-effect-frozen restore drill | `recovery` |

Scheduling must use enrolled worker identity and authorized capabilities — never personal host labels as authority.

## Combined / mock (no Docker)

```sh
uv sync
cp .env.example .env
uv run swarm deploy doctor --profile mock
uv run swarm serve --host 127.0.0.1 --port "${SWARM_PORT:-8765}"
```

## Product stack (console + API + worker)

```sh
cp deploy/env/product.env.example deploy/env/product.env
# Fill SWARM_PG_PASSWORD + SWARM_SEED_LOOPBACK_TOKEN only.

docker compose -f deploy/compose/product.yml --env-file deploy/env/product.env up --build -d

curl -fsS "http://127.0.0.1:${SWARM_HOST_PORT:-8765}/health/ready"
# Console: http://127.0.0.1:${SWARM_CONSOLE_HOST_PORT:-43127}/?mode=live
```

Same seed token authenticates SDK/CLI against the published API port and the console (query `token=` or compose-injected runtime config). Worker reaches `http://api:8765` on the compose network with a bounded workspace volume.

## Server (Compose, portable)

```sh
cp deploy/env/portable.env.example deploy/env/portable.env
# Fill placeholders only (password + seed token). Leave public hostname as example.test
# until real DNS/Access exist.

uv run swarm deploy doctor --profile server
docker compose -f deploy/compose/server.yml --env-file deploy/env/portable.env build
docker compose -f deploy/compose/server.yml --env-file deploy/env/portable.env up -d

API_PORT="${SWARM_HOST_PORT:-8765}"
curl -fsS "http://127.0.0.1:${API_PORT}/health/live"
curl -fsS "http://127.0.0.1:${API_PORT}/health/ready"
```

Entrypoint runs `alembic upgrade head` when `SWARM_DATABASE_URL` is set inside the container (`deploy/scripts/server-entrypoint.sh`).

## Worker connector (generic)

```sh
cp deploy/env/worker-connector.env.example deploy/env/worker-connector.env
# Set SWARM_SERVER_URL to the server's reachable API base (loopback or private LAN).
# Copy the same seed/auth token the server uses for loopback verify — do not commit it.

uv run swarm deploy doctor --profile mac_connector
# Profile name is historical; treat as "outbound connector" until renamed (Lane P2).

# Preferred: product worker client / continuous connector against SWARM_SERVER_URL
# Optional compose one-shot (reference Mac path): docs/reference/MAC-CONNECTOR.md
```

## Doctor before live start

```sh
uv run swarm deploy doctor --profile server --require-start
uv run swarm deploy doctor --profile mac_connector --require-start
```

`--require-start` exits non-zero unless `ready_to_start` is true (required env refs present). Security-only `ok` can still be true while start refs are missing — always check `ready_to_start` for go/no-go.

## Stop

```sh
docker compose -f deploy/compose/server.yml down
# Data volumes remain until `down -v` — use deliberately.
```
