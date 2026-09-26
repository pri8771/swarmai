> **EXECUTED** 2026-09-26 by the integrator: branch `cursor/sw-fix-killbound-flake-460c` head `ee739728aad89b81518b249e062bad665fdb6b4f` (code `221a1f69`), merged into `cursor/sw-v23-integration-460c` at `1b3f48ad2a1d27cb4d485416502cdd3ba2d12796`.

**Goal.** `tests/tools/test_v20_cancel_killbound.py::test_cancel_kills_group_before_timeout` failed about 1 in 25 full runs ("grandchild survived the kill bound"). Make it deterministic without weakening what it proves (V20-E08: cancel/timeout kill the whole process group within `KILL_BOUND_SECONDS`). Test-only; `src/swarm/tools/sandbox_runner.py` is unchanged.

### Step 0 — analysis
Direct reproduction under load (12 busy loops on 4 CPUs, 40 runs) stayed green. The helper has a real race matching the message: `_assert_dead` called `_alive` twice; when the loop saw a zombie and exited, PID 1 could reap it before the final call, whose `/proc/<pid>/stat` read then raised and `except OSError: return True` reported it alive. The cancel test also used a fixed `threading.Timer(1.0, cancel.set)`.

### Step 1 — `tests/tools/test_v20_cancel_killbound.py`
- `_alive`: `FileNotFoundError`/`ProcessLookupError` on the `/proc` read → dead; state after the last `)` in `Z`/`X` → dead; other `OSError` → alive.
- `_assert_dead`: poll until dead or the bound; assert on the last sample.
- Cancel test: a thread waits for `child.pid`, records `cancel_at`, sets `cancel`; assert `returned_at - cancel_at < KILL_BOUND_SECONDS` and the grandchild dies within the bound.
- Timeout test: `timeout_seconds` 4.0 so the grandchild exists before the timeout.
- Add `test_alive_treats_reaped_zombie_as_dead` (fails with the old helper).

### Acceptance (this session)
- [ ] `4 passed`; 50/50 green under CPU load.
- [ ] The kill bound is still asserted for cancel and timeout.
