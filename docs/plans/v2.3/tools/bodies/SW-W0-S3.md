**Goal.** Fix two security findings with the smallest possible change.
- **F-01 (P1, cross-tenant):** `GET /v1/ops/events` without `project_id` returns every project's events. Only admins may see everything; other principals see only their own projects.
- **F-06 (P3, retries):** `RetryOwner.decide` uses upstream `Retry-After` unbounded (`wait = float(retry_after)`). Clamp it to `[0, max_retry_after_seconds]` (default 30 s) and treat NaN/inf as the cap.

Both fixes and tests were compiled and run against `dev @ 8e1c0fde` (all green).

### Step 1 — reproduce F-01 first (it must FAIL before the fix)
Create `tests/api/test_v23_ops_events_scope.py` exactly:
```python
{{FILE:tests/api/test_v23_ops_events_scope.py}}
```
Run `uv run pytest tests/api/test_v23_ops_events_scope.py -q`. Expected **before** the fix: `test_unscoped_list_only_returns_own_projects` fails (it sees `proj_other` and `None`). Write the failing output line in the handoff.

### Step 2 — fix `list_ops_events` in `src/swarm/api/routes_v1.py`
Find the function that starts with `@router.get("/ops/events")` (around line 2173). Replace the **whole function** (decorator through its `return`) with exactly this. Do not touch any other function.
```python
{{FILE:w0s3_list_ops_events.py}}
```
Re-run Step 1's test: 3 passed.

### Step 3 — reproduce F-06, then fix `src/swarm/broker/retry.py`
Create `tests/broker/test_retry_after_cap.py` exactly:
```python
{{FILE:tests/broker/test_retry_after_cap.py}}
```
Run it: it fails before the fix (`RetryConfig` has no `max_retry_after_seconds`; waits are unbounded).

Edit `src/swarm/broker/retry.py`:
1. Add `import math` above `import random`.
2. In `class RetryConfig`, add a last field: `max_retry_after_seconds: float = 30.0`.
3. In `decide`, replace
```python
        if retry_after is not None:
            wait = float(retry_after)
```
with
```python
        if retry_after is not None:
            wait = float(retry_after)
            if not math.isfinite(wait):
                wait = self.config.max_retry_after_seconds
            wait = min(max(wait, 0.0), self.config.max_retry_after_seconds)
```
Nothing else changes (attempt counting stays as is).

### Section-5 acceptance
- [ ] Before-fix failure of both new test files recorded in the handoff.
- [ ] `tests/api/test_v23_ops_events_scope.py` 3 passed; `tests/broker/test_retry_after_cap.py` 7 passed.
- [ ] `git diff src/swarm/api/routes_v1.py` touches only `list_ops_events`.
- [ ] Existing `tests/api` and `tests/broker` pass unchanged.

> Later change (EXECUTED): SW-FIX-RETRY (`b3162712`) replaced the F-06 clamp with a give-up (`retry_after_exceeds_cap`) when `Retry-After` exceeds the cap; `tests/broker/test_retry_after_cap.py` was rewritten accordingly. On a tree containing that fix, this session's F-06 test expectations no longer apply.
