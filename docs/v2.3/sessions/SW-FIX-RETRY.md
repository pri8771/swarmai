# SW-FIX-RETRY handoff
- Branch: `cursor/sw-fix-retry-after-460c`   Base SHA: `ed388b7bf61066d49082a81b675a57ef945b6272`   Head SHA (code): `1adf4b12cad2ba10bffb81cf5adf337d728d54da`
- PR: to `cursor/sw-v23-integration-460c` (PR body `pr_bodies/SW-FIX-RETRY.md` in the coordinator audit dir).
## Problem
`RetryOwner.decide` clamped an upstream `Retry-After` above `max_retry_after_seconds` (30 s) to the cap and returned `should_retry=True`, so SwarmAI would retry before the upstream Retry-After elapsed. SplitSignal's consumer contract says "never retry before Retry-After has elapsed" (flagged by SW-X1-S1 and SW-W4-S1 "Needs other owner").
## Done
- `src/swarm/broker/retry.py`: `Retry-After > cap` or non-finite (`inf`, `nan`) → `RetryDecision(should_retry=False, wait_seconds=0.0, reason="retry_after_exceeds_cap", allow_route_change=False)`; constant `RETRY_AFTER_EXCEEDS_CAP`. Values within `[0, cap]` are honored unchanged (negative → 0). Terminal classes (auth, policy, quota, ambiguous send) and `max_attempts` keep precedence.
- `tests/broker/test_retry_after_cap.py`: replaced the clamp expectations with give-up regressions (10 over-cap cases × rate_limit/transient, exact-cap boundary, repeat stays terminal, configurable cap, backoff without Retry-After).
- `CHANGELOG.md` F-06 line updated.
## Callers
- No production code calls `decide` with an upstream Retry-After yet: `router_client.py` and the unmerged SplitSignal adapter (`cursor/sw-x1-s1-460c`) only put `retry_after_s` on the receipt. Trial merge of the adapter branch with this fix: clean; `tests/providers tests/pursuit tests/broker` → `162 passed`.
## Verification
- Reproduced first: the new tests against the old `retry.py` → `12 failed, 7 passed`.
- `/agent/wt/check.sh` on `1adf4b12` (private DB `swarm_fix460c`): ruff pass; mypy `Success: no issues found in 256 source files`; one head `a23opsplatform0001`; session `87 passed`; offline CI `687 passed, 1 skipped`; integration (Postgres) `88 passed`.
## Status
implemented / offline-tested (NOT accepted; needs independent Codex review)
