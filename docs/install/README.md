# Portable installation (primary)

This is the **product** install path. It uses placeholder hostnames, blank secret refs, and checkout-relative paths only.

Host-specific topologies belong under [`docs/reference/`](../reference/README.md):

| Reference guide | Label |
|---|---|
| [R730 server](../reference/R730-SERVER.md) | **REFERENCE ONLY** — one operator’s always-on host |
| [Mac connector](../reference/MAC-CONNECTOR.md) | **REFERENCE ONLY** — macOS worker adapter evidence |
| [Cloudflare Tunnel](../reference/CLOUDFLARE-TUNNEL.md) | **REFERENCE ONLY** — optional authenticated ingress |

## Docs in this folder

| Doc | Covers |
|---|---|
| [FRESH_INSTALL.md](FRESH_INSTALL.md) | Clean install with no personal credentials/paths |
| [SERVER_WORKER_STARTUP.md](SERVER_WORKER_STARTUP.md) | Server, worker, and combined-role startup |
| [CONFIG_AND_SECRETS.md](CONFIG_AND_SECRETS.md) | Validated config + secret refs |
| [ENROLLMENT_AND_REVOCATION.md](ENROLLMENT_AND_REVOCATION.md) | Worker enroll, drain, revoke |
| [STORAGE_BACKUP_RESTORE.md](STORAGE_BACKUP_RESTORE.md) | Postgres, migrations, backup/restore |
| [HEALTH_AND_READINESS.md](HEALTH_AND_READINESS.md) | `/health/*` and config errors |
| [URLS_AND_INGRESS.md](URLS_AND_INGRESS.md) | Configurable API/public URLs |

## Quick start

```sh
# From a clean clone (any path — do not hardcode personal directories)
uv sync
cp .env.example .env
cp examples/fresh-install/portable.env.example examples/fresh-install/portable.env
uv run swarm deploy doctor --profile mock
uv run swarm serve --host 127.0.0.1 --port 8765
curl -fsS http://127.0.0.1:8765/health/live
curl -fsS http://127.0.0.1:8765/health/ready
```

Standalone (API + Postgres, loopback only):

```sh
# Set a strong SWARM_PG_PASSWORD in deploy/env/portable.env before first start
cp deploy/env/portable.env.example deploy/env/portable.env
uv run swarm deploy doctor --profile standalone --require-start
# Then: docker compose -f deploy/compose/standalone.yml up -d
```

Install must not require editing application source. Configure via env files and compose overrides only.
