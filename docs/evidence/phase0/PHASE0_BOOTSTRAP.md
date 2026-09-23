# Phase 0 bootstrap

Coordination docs landed from `coordination/swarm-control`.
Tip-bound FIX-003 evidence files live under `var/evidence/` (gitignored runtime).
Regenerate after each commit that must pass `swarm release verify`:

```sh
# after commit, rewrite candidate_sha / git_sha to $(git rev-parse HEAD)
# CandidateManifest tracked copy: docs/evidence/v20/candidate_manifest.json
```

Gap-close tip (2026-09-23): offline_ci_pass rebound; live_local left `pending` (no invented live pass).
