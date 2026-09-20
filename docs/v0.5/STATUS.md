# SwarmAI V0.5 Status — Tools + Permissions

**Date:** 2026-09-20  
**Branch:** `cursor/v0.5-tools-permissions-11e2`

## Proof

`swarm tools permission-proof` exercised:
1. allowed `repo.read` under sandbox allowlist
2. denied path outside allowlist
3. blocked side-effect without approval / write scope
4. human-approved `repo.write` resumed successfully

Cost `$0.00`. Audit persisted under `var/reports/permissions/`.
