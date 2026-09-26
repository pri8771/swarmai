# SW-FIX-FLAKE handoff
- Branch: `cursor/sw-fix-killbound-flake-460c`   Base SHA: `604f7acec2c560cffa39bafd87ab9284e4b9a565`   Head SHA (code): `221a1f69b9a38ea3eff3136ae9cd53702739e2e9`
- PR: to `cursor/sw-v23-integration-460c` (PR body `pr_bodies/SW-FIX-FLAKE.md` in the coordinator audit dir).
## Problem
`tests/tools/test_v20_cancel_killbound.py::test_cancel_kills_group_before_timeout` failed about 1 in 25 full runs with "grandchild survived the kill bound" (SW-W1-S13 / V20-E08; PROMPT_FIXES entry).
## Analysis
- Not reproduced directly: 40 runs of the old file and 50 runs of the new file under 12 busy-loop processes on 4 CPUs, all green.
- A real race in the helper matches the message: `_assert_dead` called `_alive` twice. When the loop saw the grandchild as a zombie (`Z`) and exited, PID 1 could reap it before the final `assert not _alive(pid)`. Then `os.kill(pid, 0)` succeeded, `/proc/<pid>/stat` was already gone, and `except OSError: return True` reported the dead process alive. `test_alive_treats_reaped_zombie_as_dead` reproduces this deterministically with the old helper (`1 failed`) and passes with the new one.
- The cancel test also depended on a fixed `threading.Timer(1.0, cancel.set)` instead of on the grandchild existing.
## Done (test-only; `src/swarm/tools/sandbox_runner.py` unchanged)
- `_alive`: `ProcessLookupError`/`FileNotFoundError` on the `/proc` read → dead; `Z`/`X` → dead; other `OSError` stays conservative (alive). The stat state is parsed after the last `)`.
- `_assert_dead`: polls until dead or `KILL_BOUND_SECONDS`, asserts on the last sample.
- Cancel test: a thread waits for `child.pid`, records `cancel_at`, then sets `cancel`. Asserts cancelled + group killed + not timed out, **kill latency `returned_at - cancel_at < KILL_BOUND_SECONDS`**, and the known grandchild is dead within the bound. This is at least as strong as before: the grandchild is guaranteed to exist when the kill happens, and the bound is measured from the cancel.
- Timeout test: `timeout_seconds` 1.5 → 4.0 so the grandchild always exists before the timeout; same `< timeout + KILL_BOUND_SECONDS` and grandchild-dead assertions.
## Verification
- `/agent/wt/check.sh` on `221a1f69` (private DB `swarm_fix460c`): ruff pass; mypy `Success: no issues found in 256 source files`; one head `a23opsplatform0001`; session `4 passed`; offline CI `691 passed, 1 skipped`; integration (Postgres) `88 passed`.
- Load loop: 50/50 green (`4 passed` each) with 12 busy-loop processes on 4 CPUs.
## Status
implemented / offline-tested (NOT accepted; needs independent Codex review)
