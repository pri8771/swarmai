# SW-W1-S13 — V20-E08 sandbox cancel kill-bound (process group, <=10 s) — optional (**optional** — run it only when the coordinator schedules it)

Copy this whole file into a fresh Cursor session opened on the **swarmai** repository. Follow it top to bottom. It is self-contained: do not read other plans to decide what to do.

| Field | Value |
|---|---|
| Session ID | `SW-W1-S13` |
| Repository | `pri8771/swarmai` (GitHub remote `origin`; **public** repo) |
| Base branch | `cursor/sw-v23-integration-460c` — always the **current** `origin/cursor/sw-v23-integration-460c` (plan baseline `dev` @ `8e1c0fde`) |
| Your branch | `cursor/v20-w1-s13-sandbox-killbound` |
| Branch-suffix rule | If your environment forces a suffix (for example `-460c`), append it **once** to *your* branch and write the exact final name in the handoff. Never add a suffix to `cursor/sw-v23-integration-460c`: it already ends in `-460c`. |
| PR target | `cursor/sw-v23-integration-460c` — **draft** PR. Never `dev`, never `main`. |
| Wave | 1 |
| Depends on | none |
| Handoff file | `docs/v2.3/sessions/SW-W1-S13.md` |
| Independent reviewer | Codex (owner decision D2). You never accept your own work. |
| Plan | `docs/plans/v2.3/PLAN.md`; owner preflight `docs/plans/v2.3/OWNER_PREFLIGHT.md`; decisions `docs/swarm-mvp/DECISIONS.md` |

## 0. Hard rules (read twice)
1. Edit **only** the files listed in “Files you own” plus your handoff file. If another file must change, do not change it: write the exact change under “Needs other owner” in the handoff.
2. Never push to, or merge into, `main`, `dev` or `cursor/sw-v23-integration-460c`. Never merge any PR, never force-push, never rewrite history, never delete branches. Only the wave MERGE prompts (`SW-MERGE-*`) push to `cursor/sw-v23-integration-460c`.
3. Zero spend: no real model/provider calls, no paid APIs, no account creation, no deploys. `SWARM_ALLOW_PAID` stays `false`. Tests use fakes only.
4. Never commit or print secrets, tokens, `.env` files, customer data or raw logs. Test tokens are fake literals such as `atk_policy_demo`. Check environment variables only with `test -n "$NAME"`.
5. Passing tests are *not* acceptance. Never write “accepted”, “complete”, “released” or “V2.3 done”. Use “implemented” and “tested”.
6. `src/swarm/contracts/v23.py`, `src/swarm/db/models.py` and `migrations/` belong to SW-W0-S2. Import from them; never edit them (unless you *are* SW-W0-S2).
7. Do not edit `.github/workflows/`, `pyproject.toml`, `uv.lock`, `package.json` or lockfiles.
8. If a step can be read two ways, choose the reading that changes fewer lines inside your own files, and write the choice under “Decisions” in the handoff.

## 1. Setup
```bash
git status --porcelain            # must print nothing; otherwise STOP (S1)
git fetch origin cursor/sw-v23-integration-460c
git ls-remote --exit-code origin refs/heads/cursor/sw-v23-integration-460c >/dev/null && echo INTEG_OK || echo INTEG_MISSING
```
If it prints `INTEG_MISSING`, STOP (S2): SW-W0-S1 or the executor creates it.
```bash
git checkout -b cursor/v20-w1-s13-sandbox-killbound origin/cursor/sw-v23-integration-460c
git log -1 --format='%H %s'       # record this SHA in the handoff as 'base'
command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh   # then: export PATH=$HOME/.local/bin:$PATH
uv sync
git clean -fdX -- var/
```

## 2. Dependency and environment check
This session has **no dependencies**. Go to Step 1.

This session needs **no** secrets or environment variables.

## 3. Files you own (the ONLY files you may create or modify)
- `src/swarm/tools/sandbox_runner.py` — modify
- `tests/tools/test_v20_cancel_killbound.py` — create
- `docs/v2.3/sessions/SW-W1-S13.md` — create (your handoff)

## 4. Do NOT touch
- Any file not listed in section 3 (in particular: `src/swarm/api/app.py`, `src/swarm/api/store.py`, `src/swarm/cli.py`, `src/swarm/db/models.py`, `migrations/`, `docs/agents/*`, `docs/plans/v2.3/*`, `CHANGELOG.md`, `README.md`, `.github/`, unless listed above).
- The `inference_server` repository: read-only, and only through the commands in section 5.
- The branches `main`, `dev`, `cursor/sw-v23-integration-460c`, `cursor/v23-plan-460c`, and any other session's branch.
- Generated files that tests rewrite: `schemas/v1/*`, `docs/evidence/fix-004/*`, `var/*` — always restore them before committing (section 6).

## 5. Steps
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
"""Isolated code/test runner — operator-controlled trust boundary.

Network is off by default. Paths outside the work directory are denied via an
injected sitecustomize gate (R5). This is still not a hardened multi-tenant
hypervisor; Docker socket and host secrets are never mounted.
"""

from __future__ import annotations

import os
import resource
import signal
import subprocess
import sys
import tempfile
import textwrap
import threading
import time
from dataclasses import dataclass
from pathlib import Path

KILL_BOUND_SECONDS = 10.0
_POLL_SECONDS = 0.05


@dataclass
class SandboxResult:
    ok: bool
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool = False
    cancelled: bool = False
    killed_group: bool = False


class SandboxPolicyError(PermissionError):
    pass


_SITECUSTOMIZE = textwrap.dedent(
    """
    import builtins
    import sys
    from pathlib import Path

    _WORK = Path(__file__).resolve().parent
    _ALLOWED_PREFIXES = (
        str(_WORK),
        sys.base_prefix,
        sys.prefix,
        "/usr",
        "/Library/Frameworks",
        "/System/Library",
    )

    def _allowed(path: Path) -> bool:
        try:
            resolved = path.resolve()
        except OSError:
            return False
        text = str(resolved)
        return any(text.startswith(prefix) for prefix in _ALLOWED_PREFIXES)

    _real_open = builtins.open

    def _open(file, *args, **kwargs):
        try:
            candidate = Path(file)
        except TypeError:
            return _real_open(file, *args, **kwargs)
        if not _allowed(candidate):
            raise PermissionError(f"sandbox_path_denied:{file}")
        return _real_open(file, *args, **kwargs)

    builtins.open = _open

    try:
        import pathlib

        _real_read_text = pathlib.Path.read_text
        _real_read_bytes = pathlib.Path.read_bytes

        def _read_text(self, *args, **kwargs):
            if not _allowed(self):
                raise PermissionError(f"sandbox_path_denied:{self}")
            return _real_read_text(self, *args, **kwargs)

        def _read_bytes(self, *args, **kwargs):
            if not _allowed(self):
                raise PermissionError(f"sandbox_path_denied:{self}")
            return _real_read_bytes(self, *args, **kwargs)

        pathlib.Path.read_text = _read_text  # type: ignore[method-assign]
        pathlib.Path.read_bytes = _read_bytes  # type: ignore[method-assign]
    except Exception:
        pass
    """
)


class IsolatedCodeRunner:
    def __init__(
        self,
        work_dir: Path,
        *,
        network: bool = False,
        timeout_seconds: float = 5.0,
        memory_mb: int = 256,
    ) -> None:
        self.work_dir = work_dir.resolve()
        self.network = network
        self.timeout_seconds = timeout_seconds
        self.memory_mb = memory_mb
        if not self.work_dir.exists():
            raise FileNotFoundError(self.work_dir)
        gate = self.work_dir / "sitecustomize.py"
        if not gate.exists():
            gate.write_text(_SITECUSTOMIZE, encoding="utf-8")

    def _assert_path_allowed(self, path: Path) -> Path:
        resolved = path.resolve()
        try:
            resolved.relative_to(self.work_dir)
        except ValueError as exc:
            raise SandboxPolicyError(f"path escapes allowlisted work_dir: {path}") from exc
        if resolved.is_symlink():
            target = resolved.resolve()
            try:
                target.relative_to(self.work_dir)
            except ValueError as exc:
                raise SandboxPolicyError("symlink escape blocked") from exc
        return resolved

    def run_python(
        self,
        relative_script: str,
        args: list[str] | None = None,
        *,
        cancel: threading.Event | None = None,
    ) -> SandboxResult:
        script = self._assert_path_allowed(self.work_dir / relative_script)
        if self.network:
            raise SandboxPolicyError("network is disabled by default; refuse enabling in self-test")

        def _limit() -> None:
            bytes_limit = self.memory_mb * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (bytes_limit, bytes_limit))

        env = {
            "PATH": os.environ.get("PATH", ""),
            "PYTHONPATH": str(self.work_dir),
            "HOME": str(self.work_dir),
            "PYTHONNOUSERSITE": "1",
        }
        cmd = [sys.executable, str(script), *(args or [])]
        # Own session => own process group, so timeout/cancel kills every descendant.
        proc = subprocess.Popen(
            cmd,
            cwd=str(self.work_dir),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
            preexec_fn=_limit if sys.platform != "darwin" else None,
        )
        deadline = time.monotonic() + self.timeout_seconds
        while True:
            if cancel is not None and cancel.is_set():
                return self._kill_group(proc, timed_out=False, cancelled=True)
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return self._kill_group(proc, timed_out=True, cancelled=False)
            try:
                stdout, stderr = proc.communicate(timeout=min(_POLL_SECONDS, remaining))
            except subprocess.TimeoutExpired:
                continue
            return SandboxResult(
                ok=proc.returncode == 0,
                exit_code=proc.returncode,
                stdout=stdout,
                stderr=stderr,
            )

    def _kill_group(
        self, proc: subprocess.Popen[str], *, timed_out: bool, cancelled: bool
    ) -> SandboxResult:
        killed = False
        try:
            os.killpg(proc.pid, signal.SIGKILL)
            killed = True
        except ProcessLookupError:
            pass
        try:
            stdout, stderr = proc.communicate(timeout=KILL_BOUND_SECONDS)
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, stderr = "", ""
        reason = "timeout" if timed_out else "cancelled"
        return SandboxResult(
            ok=False,
            exit_code=-1,
            stdout=stdout or "",
            stderr=stderr or reason,
            timed_out=timed_out,
            cancelled=cancelled,
            killed_group=killed,
        )


def self_test(*, network: str = "off") -> dict[str, object]:
    if network != "off":
        raise SandboxPolicyError("self-test requires --network off")
    with tempfile.TemporaryDirectory(prefix="swarm-sandbox-") as tmp:
        root = Path(tmp)
        script = root / "ok.py"
        script.write_text("print('sandbox-ok')\n")
        runner = IsolatedCodeRunner(root, network=False, timeout_seconds=3)
        result = runner.run_python("ok.py")
        return {
            "ok": result.ok,
            "stdout": result.stdout.strip(),
            "network": "off",
            "docker_socket_mounted": False,
            "host_secrets_mounted": False,
            "trust_boundary": "operator-controlled-dev-path-gated-not-hostile-multi-tenant",
        }
```

### Step 2 — `tests/tools/test_v20_cancel_killbound.py` (create, exactly)
```python
"""SW-W1-S13 / V20-E08: timeout and cancel kill the whole sandbox process group within bound."""

from __future__ import annotations

import os
import sys
import threading
import time
from pathlib import Path

import pytest

from swarm.tools.sandbox_runner import KILL_BOUND_SECONDS, IsolatedCodeRunner

pytestmark = pytest.mark.skipif(sys.platform == "win32", reason="POSIX process groups")

SPAWNER = """
import subprocess, sys, time
child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)"])
with open("child.pid", "w") as fh:
    fh.write(str(child.pid))
print("spawned", flush=True)
time.sleep(120)
"""


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    try:
        with open(f"/proc/{pid}/stat", encoding="utf-8") as fh:
            state = fh.read().rsplit(")", 1)[1].split()[0]
    except (FileNotFoundError, ProcessLookupError):
        # Reaped between kill(0) and the read: a zombie PID 1 just collected.
        return False
    except OSError:
        return True
    return state not in ("Z", "X")


def _wait_pid(root: Path) -> int:
    for _ in range(200):
        pid_file = root / "child.pid"
        if pid_file.exists() and pid_file.read_text().strip():
            return int(pid_file.read_text())
        time.sleep(0.05)
    raise AssertionError("grandchild never started")


def _assert_dead(pid: int) -> None:
    deadline = time.monotonic() + KILL_BOUND_SECONDS
    alive = _alive(pid)
    while alive and time.monotonic() < deadline:
        time.sleep(0.05)
        alive = _alive(pid)
    assert not alive, "grandchild survived the kill bound"


def test_timeout_kills_grandchildren(tmp_path: Path) -> None:
    (tmp_path / "spawn.py").write_text(SPAWNER, encoding="utf-8")
    # Long enough that the grandchild is always spawned before the timeout fires.
    timeout = 4.0
    runner = IsolatedCodeRunner(tmp_path, timeout_seconds=timeout, memory_mb=512)
    started = time.monotonic()
    result = runner.run_python("spawn.py")
    assert result.timed_out and result.killed_group and not result.ok
    assert time.monotonic() - started < timeout + KILL_BOUND_SECONDS
    _assert_dead(_wait_pid(tmp_path))


def test_cancel_kills_group_before_timeout(tmp_path: Path) -> None:
    (tmp_path / "spawn.py").write_text(SPAWNER, encoding="utf-8")
    runner = IsolatedCodeRunner(tmp_path, timeout_seconds=60, memory_mb=512)
    cancel = threading.Event()
    seen: dict[str, float] = {}

    def _cancel_once_grandchild_exists() -> None:
        seen["pid"] = _wait_pid(tmp_path)
        seen["cancel_at"] = time.monotonic()
        cancel.set()

    trigger = threading.Thread(target=_cancel_once_grandchild_exists, daemon=True)
    trigger.start()
    result = runner.run_python("spawn.py", cancel=cancel)
    returned_at = time.monotonic()
    trigger.join(timeout=1)
    assert "cancel_at" in seen, "cancel was never triggered"
    assert result.cancelled and not result.timed_out and result.killed_group
    assert returned_at - seen["cancel_at"] < KILL_BOUND_SECONDS
    _assert_dead(int(seen["pid"]))


def test_normal_run_unchanged(tmp_path: Path) -> None:
    (tmp_path / "ok.py").write_text("print('ok')\n", encoding="utf-8")
    result = IsolatedCodeRunner(tmp_path).run_python("ok.py")
    assert result.ok and result.stdout.strip() == "ok"
    assert not result.cancelled and not result.killed_group


def test_alive_treats_reaped_zombie_as_dead(monkeypatch: pytest.MonkeyPatch) -> None:
    """kill(0) can succeed on a zombie that PID 1 reaps before /proc is read."""
    import builtins

    monkeypatch.setattr(os, "kill", lambda pid, sig: None)
    real_open = builtins.open

    def _gone(path, *a, **kw):  # type: ignore[no-untyped-def]
        if str(path).startswith("/proc/"):
            raise FileNotFoundError(path)
        return real_open(path, *a, **kw)

    monkeypatch.setattr(builtins, "open", _gone)
    assert _alive(4_000_000) is False
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

## 6. Verify (run exactly; all must pass)
```bash
git clean -fdX -- var/            # F-15: stale runtime state breaks re-runs
# Private database for this session: concurrent sessions on one host must never share one.
sudo -u postgres psql -c "CREATE DATABASE swarm_sw_w1_s13 OWNER swarm;" || true
export SWARM_DATABASE_URL=postgresql+psycopg://swarm:swarm@127.0.0.1:5432/swarm_sw_w1_s13
uv run ruff check .
uv run mypy src/swarm
uv run alembic heads               # must print exactly ONE line ending in (head)
uv run pytest tests/tools tests/foundation -q
uv run pytest tests/contracts tests/spikes tests/api tests/broker tests/controller tests/chaos tests/deployment tests/evals tests/extensions tests/foundation tests/goals tests/pursuit tests/sdk tests/knowledge tests/load tests/memory tests/mission tests/objectives tests/onboarding tests/product tests/providers tests/recovery tests/regressions tests/release tests/runtime tests/selfdev tests/tools tests/ui tests/workers tests/workspace tests/e2e tests/acceptance tests/portability -q --ignore=tests/integration

# PostgreSQL integration (install steps in “PostgreSQL” below)
uv run pytest tests/integration -q -m integration

git checkout -- schemas/v1 docs/evidence/fix-004 var   # tests rewrite these tracked files
git status --porcelain            # every path listed must be one of YOUR files
```

### PostgreSQL (for the integration line)
```bash
pg_isready -h 127.0.0.1 || {
  sudo apt-get update && sudo apt-get install -y postgresql && sudo service postgresql start
  sudo -u postgres psql -c "CREATE USER swarm WITH PASSWORD 'swarm' SUPERUSER;" || true
}
```
Run this block before section 6. Section 6 creates your private database and exports `SWARM_DATABASE_URL` for **both** pytest lines; never unset it and never point it at the shared `swarm` database.
If `pg_isready -h 127.0.0.1` still fails after running this block twice, write `integration: SKIPPED (postgres unavailable: <last error line>)` in the handoff and continue. Never claim integration passed without running it.

## 7. Acceptance checklist (tick every box in the handoff)
- [ ] Every step in section 5 done; every acceptance box in section 5 ticked.
- [ ] `uv run ruff check .` and `uv run mypy src/swarm` pass.
- [ ] `uv run alembic heads` prints exactly one head.
- [ ] Full offline CI list passes (paste the final `N passed` line into the handoff).
- [ ] Integration run passed, or SKIPPED with reason in the handoff.
- [ ] `git status --porcelain` lists only files from section 3 + the handoff.
- [ ] No secrets, no network calls beyond section 5, no `accepted`/`complete` claims.
- [ ] The Codex review packet (section 11) is in the PR description and the handoff.

## 8. Commit, push, draft PR
```bash
git checkout -- schemas/v1 docs/evidence/fix-004 var
git add src/swarm/tools/sandbox_runner.py tests/tools/test_v20_cancel_killbound.py docs/v2.3/sessions/SW-W1-S13.md
git status --porcelain            # nothing unexpected staged or left over
git commit -m "feat(v2.0): E08 sandbox runs in own process group; timeout/cancel kills the whole group within bound" -m "Session: SW-W1-S13. Plan: docs/plans/v2.3/PLAN.md."
git push -u origin cursor/v20-w1-s13-sandbox-killbound
gh pr create --draft --base cursor/sw-v23-integration-460c --head cursor/v20-w1-s13-sandbox-killbound --title "[SW-W1-S13] V20-E08 sandbox cancel kill-bound (process group, <=10 s) — optional" --body-file docs/v2.3/sessions/SW-W1-S13.md
git ls-remote origin refs/heads/cursor/v20-w1-s13-sandbox-killbound   # must print the same SHA as: git rev-parse HEAD
```
If `gh pr create` is refused (read-only `gh`), the environment opens the PR: check that its base is `cursor/sw-v23-integration-460c` and that it is a draft, and put the PR URL (or the compare URL from section 10, step 4) into the handoff.
If push fails for network reasons, retry up to 4 times waiting 4 s, 8 s, 16 s, 32 s; then STOP (S8).
Docs to update: only your handoff file, plus any doc listed in section 3.

## 9. Handoff file (create before committing)
Create `docs/v2.3/sessions/SW-W1-S13.md` with exactly these headings:
```markdown
# SW-W1-S13 handoff
- Branch: <exact branch name>   Base SHA: <from setup>   Head SHA: <git rev-parse HEAD>
- PR: <url, or compare URL>
## Done
<bullet list of what you implemented>
## Verification
<each command from section 6 and its final result line; integration PASSED/SKIPPED(reason)>
## Acceptance
<copy the checkboxes from sections 5 and 7, ticked>
## Decisions
<choices you made under hard rule 8, or 'none'>
## Needs other owner
<files outside your scope that should change, with the exact change; or 'none'>
## Codex review packet
<the block from section 11, filled in>
## Status
implemented + tested (NOT accepted; needs Codex review)
```

## 10. STOP conditions (never wait for a human)
STOP immediately when any of these is true:
- **S1** `git status --porcelain` is not empty before Setup. (Do not commit, stash or discard anything; skip steps 1–4 below and only report.)
- **S2** a dependency check prints `MISSING`.
- **S3** a command in section 6, or a check in section 5, still fails after **2 attempts**. One attempt = one edit to *your own files* followed by re-running the failing command.
- **S4** a “currently reads” / before-block in section 5 does not match the file, or a function named in section 5 does not exist.
- **S5** finishing would require editing a file that is not in section 3.
- **S6** a required environment variable prints `MISSING`.
- **S7** an external gate check (inference_server sync point or approval line) in section 5 fails.
- **S8** `git push` still fails after 4 retries (waits 4 s, 8 s, 16 s, 32 s).

What to do on STOP, in this order:
1. Commit whatever is complete inside your own files: `git add <your files> docs/v2.3/sessions/SW-W1-S13.md` then `git commit -m "WIP(SW-W1-S13): <one-line reason>"`.
2. Write the handoff (section 9) with `## Status` = `BLOCKED: <condition id> <one-line reason>`, and under `## Needs other owner` the exact file, function and change you need. Commit it.
3. Push: `git push -u origin cursor/v20-w1-s13-sandbox-killbound` (plus your suffix).
4. Open the draft PR against `cursor/sw-v23-integration-460c` with the title prefix `[BLOCKED]`, or record the compare URL `https://github.com/pri8771/swarmai/compare/cursor/sw-v23-integration-460c...cursor/v20-w1-s13-sandbox-killbound?expand=1` in the handoff.
5. End the session with a final message: the condition id, the reason, the branch and the head SHA.
Never work around a STOP by editing other files, weakening tests, or adding `skip`/`xfail`.

If `tests/tools/test_v20_cancel_killbound.py` fails once in the full run and you did not touch `sandbox_runner.py` or that test, re-run the full list once. If it passes, record both result lines in the handoff under Verification and continue; if it fails twice, STOP (S3). (The known race was fixed by SW-FIX-FLAKE; a new failure is worth reporting.)

## 11. Codex review packet (put this in the PR description and in the handoff)
```markdown
### Codex review packet — SW-W1-S13
- PR: <PR URL — fill in after the PR exists>
- Branch: <exact branch name>  Base: origin/cursor/sw-v23-integration-460c @ <base SHA from Setup>
- Head SHA: <output of `git rev-parse HEAD`; must equal `git ls-remote origin refs/heads/<branch>`>
- Diff for review: `git diff <base SHA>...<head SHA>`
- Files to review: `src/swarm/tools/sandbox_runner.py`, `tests/tools/test_v20_cancel_killbound.py`, `docs/v2.3/sessions/SW-W1-S13.md`
- Review focus (AGENTS.md Code Review Rules): cross-tenant/project access; secret disclosure; financial accounting (unknown usage or cost is never zero); unbounded retries; silently changed model behaviour; recovery gaps after a crash/restart; unsupported release claims ("accepted", "complete").
- Checks run: <paste the final result line of every command in section 6>
- Verdict requested: `RECOMMEND_ACCEPT <head SHA>` or `REQUEST_CHANGES` with file:line findings.
```
