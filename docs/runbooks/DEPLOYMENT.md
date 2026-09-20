# Deployment and recovery runbooks

## Profiles

| Profile | Use |
|---|---|
| mock | Local fixtures; no external providers |
| standalone | Single-node compose; DB internal-only |
| hybrid | Local control + private model endpoint |
| recovery | Restore drill with side-effect freeze |

**No production deploy from this kit.** No paid cloud auto-path. Oracle Always Free is optional and requires owner verification first.

## Doctor

```sh
uv run swarm deploy doctor --profile standalone
uv run swarm recovery verify --profile recovery
```

Standalone/hybrid/recovery refuse *live start* without `SWARM_DATABASE_URL` (doctor reports the gap; values never printed).

## Restore (local)

1. Stop old primary; set fence generation.
2. Create empty local volume.
3. Restore dump referenced in backup manifest; verify sha256.
4. Start recovery profile with `SWARM_SIDE_EFFECT_FREEZE=true`.
5. Confirm unresolved reservations/action receipts from manifest.
6. Promote only after checks pass — do not claim seamless failover.

## Rollback

Revert compose image tag to previous known digest; restore prior dump; keep side effects frozen until ledger reconciliation completes.
