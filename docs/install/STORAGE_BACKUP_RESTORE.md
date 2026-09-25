# Storage, migrations, backup, and restore

## Database

- Engine: PostgreSQL 16 (compose images use `postgres:16-alpine`)
- Default compose network: **internal only** — do not publish DB ports on public interfaces
- URL env: `SWARM_DATABASE_URL` (host tools) or compose-injected URL inside API containers
- Password: set `SWARM_PG_PASSWORD` / URL password to a **local random** value — never reuse production passwords in examples

## Migrations

Alembic config: `alembic.ini`. Revisions live under `migrations/versions/`.

```sh
# Host-side (requires reachable DB URL)
export SWARM_DATABASE_URL='postgresql+psycopg://swarm:LOCAL_PASSWORD@127.0.0.1:5432/swarm'
uv run swarm db migrate
uv run swarm db validate
```

Server compose entrypoint runs `alembic upgrade head` automatically when `SWARM_DATABASE_URL` is set (`deploy/scripts/server-entrypoint.sh`).

Fresh install must migrate an **empty** database to head — do not restore a developer dump to mask bootstrap defects.

## Local data directories

| Path | Contents |
|---|---|
| `var/` | Install identity, missions, artifacts (persist across API recreate when volume-mounted) |
| Compose volumes `*_pg_data` | Postgres data |
| Compose volumes `*_pg_backup` | Optional dump target on server profile |

Never commit `var/` secrets or dumps.

## Backup (redacted manifest)

```sh
uv run swarm recovery backup --site-id site_local --epoch 1 --out var/recovery/backups
```

Manifests may list secret **names** and content hashes — never raw credentials. Sample shape: `deploy/backup/sample-backup-manifest.json` (fixture only; placeholder hashes).

## Restore drill (local)

Aligned with `docs/runbooks/DEPLOYMENT.md` recovery section:

1. Stop old primary; record fence / site epoch generation
2. Create an **empty** local volume (do not restore over a dirty volume without intent)
3. Restore dump referenced in the backup manifest; verify sha256
4. Start recovery profile with side-effect freeze:
   ```sh
   docker compose -f deploy/compose/recovery.yml up -d
   # Ensure SWARM_SIDE_EFFECT_FREEZE=true (compose sets recovery defaults)
   uv run swarm recovery verify --profile recovery
   ```
5. Confirm unresolved reservations / action receipts from the manifest
6. Promote only after checks pass — **do not claim seamless failover**

Optional harness:

```sh
uv run swarm recovery drill
```

## Rollback

1. Revert compose image tag to previous known digest
2. Restore prior dump into a clean target when schema is incompatible (Class C)
3. Keep side effects frozen until ledger reconciliation completes
4. Fence candidate-era workers/leases/results

Code-only rollback (Class A) is allowed only when schema compatibility is proven — see ART-V20 install/upgrade protocol.

## Portable vs named-host evidence

Backup/restore product behavior is proven with local volumes and placeholder site ids. Named hardware (R730) restore evidence is **deployment qualification**, not a requirement for this runbook.
