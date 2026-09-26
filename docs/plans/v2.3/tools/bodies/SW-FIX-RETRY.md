> **EXECUTED** 2026-09-26 by the integrator: branch `cursor/sw-fix-retry-after-460c` head `a42a94bd468f532cdc8ebf5ec2a7761e41d358e2` (code `1adf4b12`), merged into `cursor/sw-v23-integration-460c` at `b31627121d9d56836374f5dbfad32e579821937c`. Kept as a record and for re-runs on a fresh tree; do not run it again on a tree that already contains `retry_after_exceeds_cap`.

**Goal.** SplitSignal's consumer contract says "never retry before Retry-After has elapsed". `RetryOwner.decide` clamped a `Retry-After` above `max_retry_after_seconds` (30 s) to the cap and retried, which retries early. Make that case a terminal give-up.

### Step 0 — reproduce
`grep -n "min(max(wait, 0.0), self.config.max_retry_after_seconds)" src/swarm/broker/retry.py` must print one line. If it prints nothing and `grep -n retry_after_exceeds_cap src/swarm/broker/retry.py` prints a line, the fix is already in: record `already fixed` and STOP (S4).

### Step 1 — `src/swarm/broker/retry.py`
- Add a module constant `RETRY_AFTER_EXCEEDS_CAP = "retry_after_exceeds_cap"` below `Clock = …`.
- In `decide`, replace the Retry-After branch so that a non-finite value or a value `> self.config.max_retry_after_seconds` returns `RetryDecision(False, 0.0, RETRY_AFTER_EXCEEDS_CAP)`; otherwise `wait = max(wait, 0.0)`. Keep the terminal-class checks and `max_attempts` before it.

### Step 2 — `tests/broker/test_retry_after_cap.py` (rewrite)
Cases: within cap honored (`5.0`, `30.0`, `0.0`, `-10.0 → 0.0`); above cap gives up for `30.001, 31.0, 86400.0, inf, nan` × `RATE_LIMIT, TRANSIENT` with `should_retry False`, `wait_seconds 0.0`, `allow_route_change False`; repeat stays terminal; configurable cap (`2.5` at cap retries, `100.0` gives up); attempt bound; auth keeps `auth_failure_no_retry`; bounded backoff without Retry-After. Run the new tests against the old `retry.py` first (observed: `12 failed, 7 passed`).

### Step 3 — callers
`router_client.py` and the SplitSignal adapter (`cursor/sw-x1-s1-460c`, unmerged) only record `retry_after_s` on the receipt; neither calls `decide`. Check with `git merge-tree --write-tree origin/cursor/sw-x1-s1-460c HEAD` (must succeed) and record the result. Observed: clean; `tests/providers tests/pursuit tests/broker` on the trial merge → `162 passed`.

### Acceptance (this session)
- [ ] Over-cap and non-finite Retry-After give up with `retry_after_exceeds_cap`.
- [ ] Within-cap values are unchanged.
- [ ] The adapter branch still merges cleanly.
