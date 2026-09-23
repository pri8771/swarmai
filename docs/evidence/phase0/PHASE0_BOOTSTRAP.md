# Phase 0 bootstrap

Coordination docs landed from `coordination/swarm-control`.
Tip-bound FIX-003 evidence files live under `var/evidence/` (gitignored runtime).
Regenerate after each commit that must pass `swarm release verify`:

```sh
# after commit, rewrite candidate_sha to $(git rev-parse HEAD)
```
