**Goal.** Implement V20-E08, the sandbox cancel kill-bound.
- `IsolatedCodeRunner.run_python` uses `subprocess.run(timeout=…)`, which kills only the direct child. Grandchildren (for example a test that starts a server) survive the timeout, and there is no way to cancel a run.

**After this session:**
- The script runs in its **own session/process group** (`start_new_session=True`).
- On timeout, or when the optional `cancel: threading.Event` is set, the **whole group** gets `SIGKILL`, and the runner waits at most `KILL_BOUND_SECONDS = 10.0` for the pipes to close.

**Compatibility.**
- `SandboxResult` keeps every existing field, gains `cancelled` and `killed_group` (both default `False`), and existing callers are unchanged.
- The positional signature `run_python(relative_script, args=None)` is unchanged; `cancel` is keyword-only.

The code below was compiled and run against `dev @ 8e1c0fde`. `tests/tools tests/foundation tests/selfdev tests/evals` gives 76 passed, and ruff and mypy are clean. Paste it **exactly**.

### Step 1 — `src/swarm/tools/sandbox_runner.py` (replace the whole file, exactly)
```python
{{FILE:src/swarm/tools/sandbox_runner.py}}
```

### Step 2 — `tests/tools/test_v20_cancel_killbound.py` (create, exactly)
```python
{{FILE:tests/tools/test_v20_cancel_killbound.py}}
```

### Step 3 — run
```bash
uv run pytest tests/tools/test_v20_cancel_killbound.py -q     # 4 passed (about 5 s)
uv run pytest tests/tools tests/foundation tests/selfdev tests/evals -q
```
If the kill-bound tests fail only on macOS, record it in the handoff; CI is Linux. Do not add skips beyond the existing `win32` skip.

### Section-5 acceptance
- [ ] On timeout, a grandchild process is dead within `KILL_BOUND_SECONDS`, and the result has `timed_out=True, killed_group=True, ok=False`.
- [ ] Setting `cancel` kills the group before the timeout, and the result has `cancelled=True`.
- [ ] Normal runs return the same fields and values as before.
- [ ] `swarm sandbox self-test --network off`, if it exists in the CLI, still reports `ok`.
