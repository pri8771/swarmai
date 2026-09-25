# Deployment and recovery runbooks

**Primary install:** [`docs/install/`](../install/README.md) (portable; no personal paths).

**Reference only (named hosts / ingress):** [`docs/reference/`](../reference/README.md) — R730, Mac connector, Cloudflare Tunnel.

## Profiles

| Profile | Use |
|---|---|
| mock | Local fixtures; no external providers |
| standalone | Single-node compose; DB internal-only |
| hybrid | Local control + private model endpoint |
| recovery | Restore drill with side-effect freeze |
| server | Always-on server role (API + Postgres; optional tunnel profile) |
| mac_connector | Outbound worker connector (no local Postgres; historical name) |

Portable product target is **configurable server/worker/combined roles** with placeholder hostnames. Named hardware and DNS are deployment qualification — see reference guides.

**No production/public deploy from this kit without auth.** No paid cloud auto-path. Optional tunnel profile stays off until origin cert + Access are verified.

## Doctor

```sh
uv run swarm deploy doctor --profile mock
uv run swarm deploy doctor --profile standalone --require-start
uv run swarm deploy doctor --profile server --require-start
uv run swarm deploy doctor --profile mac_connector --require-start
uv run swarm recovery verify --profile recovery
```

`ok` = security posture. `ready_to_start` = required env refs present. `--require-start` exits non-zero when start refs are missing (values never printed).

## Portable startup (loopback)

```sh
cp deploy/env/portable.env.example deploy/env/portable.env
# Set SWARM_SEED_LOOPBACK_TOKEN and SWARM_PG_PASSWORD to local random values only.

docker compose -f deploy/compose/server.yml --env-file deploy/env/portable.env build
docker compose -f deploy/compose/server.yml --env-file deploy/env/portable.env up -d
curl -fsS "http://127.0.0.1:${SWARM_HOST_PORT:-8765}/health/live"
curl -fsS "http://127.0.0.1:${SWARM_HOST_PORT:-8765}/health/ready"
```

Fresh-install walkthrough: [`docs/install/FRESH_INSTALL.md`](../install/FRESH_INSTALL.md).

## Restore (local)

1. Stop old primary; set fence generation.
2. Create empty local volume.
3. Restore dump referenced in backup manifest; verify sha256.
4. Start recovery profile with `SWARM_SIDE_EFFECT_FREEZE=true`.
5. Confirm unresolved reservations/action receipts from manifest.
6. Promote only after checks pass — do not claim seamless failover.

Details: [`docs/install/STORAGE_BACKUP_RESTORE.md`](../install/STORAGE_BACKUP_RESTORE.md).

## Rollback

Revert compose image tag to previous known digest; restore prior dump; keep side effects frozen until ledger reconciliation completes.

## Reference topologies

| Topic | Doc |
|---|---|
| Always-on named server host | [`docs/reference/R730-SERVER.md`](../reference/R730-SERVER.md) |
| macOS connector evidence | [`docs/reference/MAC-CONNECTOR.md`](../reference/MAC-CONNECTOR.md) |
| Authenticated tunnel ingress | [`docs/reference/CLOUDFLARE-TUNNEL.md`](../reference/CLOUDFLARE-TUNNEL.md) |

Do not write host-specific IP/DNS into source. Do not publish without Access.
