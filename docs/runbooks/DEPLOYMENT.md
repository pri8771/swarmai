# Deployment and recovery runbooks

## Profiles

| Profile | Use |
|---|---|
| mock | Local fixtures; no external providers |
| standalone | Single-node compose; DB internal-only |
| hybrid | Local control + private model endpoint |
| recovery | Restore drill with side-effect freeze |

**No production deploy from this kit.** No paid cloud auto-path. Oracle Always Free is optional and requires owner verification first.

## Secrets (V2A-H6A / H6A-R)

Operational default is **empty/unconfigured**. Compose files do **not** embed a fixed DB password.

```sh
python scripts/generate_compose_env.py
# writes deploy/compose/.env (gitignored) owner-only 0600; secret is not printed
# or copy deploy/compose/.env.example and fill SWARM_POSTGRES_PASSWORD + SWARM_DATABASE_URL
```

`SWARM_DATABASE_URL` must be set for live DB access. The forbidden demo DSN containing `swarm:swarm@` is rejected.

Regenerating an existing `.env` requires an explicit fresh-config acknowledgement. This writes a **new** local password/DSN and is **not** safe credential rotation for an already-initialized Postgres volume:

```sh
python scripts/generate_compose_env.py --force --acknowledge-fresh-config
# renames prior .env to .env.pre-force-<UTC> (also 0600); never prints the secret
```

API publish remains loopback: `127.0.0.1:8765`. DB has no host port.

## Doctor

```sh
uv run swarm deploy doctor --profile standalone
uv run swarm recovery verify --profile recovery
```

Standalone/hybrid/recovery refuse *live start* without `SWARM_DATABASE_URL` (doctor reports the gap; values never printed).

## Compose config smoke (local)

```sh
python scripts/generate_compose_env.py --force --acknowledge-fresh-config
docker compose --env-file deploy/compose/.env -f deploy/compose/standalone.yml config
```

This validates secret interpolation and loopback binds. It is **not** a public deployment.

## Restore (local)

1. Stop old primary; set fence generation.
2. Create empty local volume.
3. Restore dump referenced in backup manifest; verify sha256.
4. Start recovery profile with `SWARM_SIDE_EFFECT_FREEZE=true`.
5. Confirm unresolved reservations/action receipts from manifest.
6. Promote only after checks pass — do not claim seamless failover.

## Rollback

Revert compose image tag to previous known digest; restore prior dump; keep side effects frozen until ledger reconciliation completes.
