# SwarmAI agent bootstrap

Canonical agent rules are on `coordination/swarm-control`.

Read:
- `CLAUDE.md`
- `docs/coordination/SESSION_START.md`
- current status/heartbeat
- active packet only

Use:
`git show origin/coordination/swarm-control:<path>`

Do not rely on legacy A/B lane instructions present in history.
Current topology is one implementation worker/session + one heartbeat unless operator explicitly changes it.
Git/source/evidence is truth; past memory is context only.
