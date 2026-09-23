# Phase 0 bootstrap

Coordination docs landed from `coordination/swarm-control`.
Tip-bound FIX-003 evidence files live under `var/evidence/` (gitignored runtime).
Regenerate after each commit that must pass `swarm release verify`:

```sh
# after commit, rewrite candidate_sha / git_sha to $(git rev-parse HEAD)
# CandidateManifest tracked copy: docs/evidence/v20/candidate_manifest.json
```

Gap-close tip (2026-09-23): offline_ci_pass rebound.
live_local (2026-09-23): pytest suite restored on `cursor/restore-live-local-tests-712f`;
local run **10 passed / 1 skipped** (loopback-only host skip) + Ollama canary canaried at cost 0.
Evidence: `docs/evidence/live_local/20260923T-restore/`; runtime bind `var/evidence/live_local_pass.json`.
