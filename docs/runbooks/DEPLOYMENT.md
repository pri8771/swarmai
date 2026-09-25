# Deployment and recovery runbooks

## Profiles

| Profile | Use |
|---|---|
| mock | Local fixtures; no external providers |
| standalone | Single-node compose; DB internal-only |
| hybrid | Local control + private model endpoint |
| recovery | Restore drill with side-effect freeze |
| server | Two-host always-on server (R730 target; Mac loopback verify) |
| mac_connector | Mac worker connector (outbound only; no local Postgres) |

**Adopted topology (2026-09-25):** R730 server + Mac connector + authenticated `swarm.splitsignal.ai`. Local-only single-host is superseded as the target; existing profiles remain for engineering drills.

**No production/public deploy from this kit without auth.** No paid cloud auto-path. Cloudflare Tunnel profile stays off until origin cert + Access are verified.

## Doctor

```sh
uv run swarm deploy doctor --profile server
uv run swarm deploy doctor --profile mac_connector
uv run swarm deploy doctor --profile standalone
uv run swarm recovery verify --profile recovery
```

Server/standalone/hybrid/recovery refuse *live start* without `SWARM_DATABASE_URL` (doctor reports the gap; values never printed). `mac_connector` requires `SWARM_SERVER_URL` instead.

## Startup (TH-01 Mac verify / R730 when access exists)

```sh
cp deploy/env/server.env.example deploy/env/server.env   # set SWARM_SEED_LOOPBACK_TOKEN
docker compose -f deploy/compose/server.yml build
docker compose -f deploy/compose/server.yml up -d
curl -fsS http://127.0.0.1:18766/health/live
curl -fsS http://127.0.0.1:18766/health/ready
```

Tunnel (optional, blocked without credentials):

```sh
# After origin cert + tunnel.json exist — never enable unauthenticated
docker compose -f deploy/compose/server.yml --profile tunnel up -d
```

Mac connector (TH-03; after server is up):

```sh
# Preferred Mac-host one-shot (authoritative evidence path)
cp deploy/env/mac-connector.env.example deploy/env/mac-connector.env
# copy SWARM_SEED_LOOPBACK_TOKEN from server.env into mac-connector.env for loopback verify
uv run python scripts/th03_mac_connector.py

# Optional compose one-shot (uses host.docker.internal → published server port)
docker compose -f deploy/compose/mac-connector.yml up --abort-on-container-exit
# Server must still answer:
curl -fsS http://127.0.0.1:18766/health/ready
```

## Restore (local)

1. Stop old primary; set fence generation.
2. Create empty local volume.
3. Restore dump referenced in backup manifest; verify sha256.
4. Start recovery profile with `SWARM_SIDE_EFFECT_FREEZE=true`.
5. Confirm unresolved reservations/action receipts from manifest.
6. Promote only after checks pass — do not claim seamless failover.

## Rollback

Revert compose image tag to previous known digest; restore prior dump; keep side effects frozen until ledger reconciliation completes.

## Host gates

- Do not write R730-specific IP/DNS into source.
- Do not overwrite Cloudflare DNS or publish without Access.
- Record blockers in `docs/swarm-mvp/STATE.md` and `docs/evidence/two-host/`.
