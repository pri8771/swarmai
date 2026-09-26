# SW-W3-S3 — CLI `swarm v23 …` commands

Copy this whole file into a fresh Cursor session opened on the **swarmai** repository. Follow it top to bottom. It is self-contained: do not read other plans to decide what to do.

| Field | Value |
|---|---|
| Session ID | `SW-W3-S3` |
| Repository | `pri8771/swarmai` (GitHub remote `origin`; **public** repo) |
| Base branch | `cursor/sw-v23-integration-460c` — always the **current** `origin/cursor/sw-v23-integration-460c` (plan baseline `dev` @ `8e1c0fde`) |
| Your branch | `cursor/v23-w3-s3-cli` |
| Branch-suffix rule | If your environment forces a suffix (for example `-460c`), append it **once** to *your* branch and write the exact final name in the handoff. Never add a suffix to `cursor/sw-v23-integration-460c`: it already ends in `-460c`. |
| PR target | `cursor/sw-v23-integration-460c` — **draft** PR. Never `dev`, never `main`. |
| Wave | 3 |
| Depends on | SW-W2-S1, SW-W1-S5, SW-W1-S6, SW-W1-S7 |
| Handoff file | `docs/v2.3/sessions/SW-W3-S3.md` |
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
git checkout -b cursor/v23-w3-s3-cli origin/cursor/sw-v23-integration-460c
git log -1 --format='%H %s'       # record this SHA in the handoff as 'base'
command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh   # then: export PATH=$HOME/.local/bin:$PATH
uv sync
git clean -fdX -- var/
```

## 2. Dependency and environment check
Depends on: SW-W2-S1, SW-W1-S5, SW-W1-S6, SW-W1-S7. Their PRs must already be merged into `cursor/sw-v23-integration-460c` (by the wave MERGE prompt).
Run every command below. Each must print `OK`. If any prints `MISSING`, STOP (condition S2 in section 10).

```bash
git fetch origin cursor/sw-v23-integration-460c
git cat-file -e origin/cursor/sw-v23-integration-460c:src/swarm/scheduling/service.py && echo "OK src/swarm/scheduling/service.py" || echo "MISSING src/swarm/scheduling/service.py"
git cat-file -e origin/cursor/sw-v23-integration-460c:src/swarm/capabilities/lifecycle.py && echo "OK src/swarm/capabilities/lifecycle.py" || echo "MISSING src/swarm/capabilities/lifecycle.py"
```

This session needs **no** secrets or environment variables.

## 3. Files you own (the ONLY files you may create or modify)
- `src/swarm/cli_v23.py` — create
- `src/swarm/cli.py` — modify (3 small hook edits only)
- `tests/product/test_v23_cli.py` — create
- `docs/v2.3/sessions/SW-W3-S3.md` — create (your handoff)

## 4. Do NOT touch
- Any file not listed in section 3 (in particular: `src/swarm/api/app.py`, `src/swarm/api/store.py`, `src/swarm/cli.py`, `src/swarm/db/models.py`, `migrations/`, `docs/agents/*`, `docs/plans/v2.3/*`, `CHANGELOG.md`, `README.md`, `.github/`, unless listed above).
- The `inference_server` repository: read-only, and only through the commands in section 5.
- The branches `main`, `dev`, `cursor/sw-v23-integration-460c`, `cursor/v23-plan-460c`, and any other session's branch.
- Generated files that tests rewrite: `schemas/v1/*`, `docs/evidence/fix-004/*`, `var/*` — always restore them before committing (section 6).

## 5. Steps
**Goal.** Add offline operator commands under `swarm v23 …` in a **new module**, `src/swarm/cli_v23.py`, and hook it into `src/swarm/cli.py` with three tiny edits. Keeping the commands in their own module keeps `cli.py` (1000+ lines, also touched by SW-W4-S1) conflict-free.

**Commands.** Every command prints one JSON document; any failure prints `{"ok": false, "error": …}` and exits with code 2.

| Command | What it does |
|---|---|
| `swarm v23 scheduler-policy [--policy PATH]` | loads `config/v23/scheduler_policy.v1.json` through `WdrrConfig.from_policy_file` and prints it |
| `swarm v23 scheduler-simulate --projects a:1,b:3 [--decisions N]` | offline `SchedulerService` run with constant demand; prints admitted counts, share and target share. `N` must be in 1..100000. |
| `swarm v23 pack-sign --manifest M --out O` | signs using the key in `SWARM_PACK_KEY_<PUBLISHER>` (through `trusted_keys_from_env`); never prints the key |
| `swarm v23 pack-verify --manifest M` | `verify_manifest` against trusted env keys |
| `swarm v23 export --project-id P [--out-dir D]` | `PortabilityService.export_project` |
| `swarm v23 import --bundle B [--target-project-id T]` | `PortabilityService.import_bundle`; tampering gives `bundle_integrity_mismatch` |

Rules:
- There is no network, provider or HTTP call in any command.
- The simulation broker is local to this module. Do **not** import from `tests/` or from `swarm.acceptance`; SW-W3-S4 has its own copy so the two sessions stay parallel.

The code below was compiled and run against `dev @ 8e1c0fde` plus Wave-1/Wave-2:
- `tests/product/test_v23_cli.py`: 9 passed.
- `swarm v23 scheduler-simulate --projects a:1,b:3 --decisions 400` gives admitted `{"a":100,"b":300}`, an exact 1:3 share.
- ruff and mypy: clean.

### Step 1 — `src/swarm/cli_v23.py` (create, exactly)
```python
"""``swarm v23 …`` offline operator commands (scheduler, packs, portability).

Every command is local and deterministic: no network, no providers, no spending.
Output is one JSON document on stdout; failures print ``{"ok": false, "error": …}``
and exit 2.
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from swarm.capabilities import CapabilityPackManifest
from swarm.capabilities.signing import (
    PackSigningError,
    sign_manifest,
    trusted_keys_from_env,
    verify_manifest,
)
from swarm.contracts.v23 import DispatchIntent, DispatchIntentComponent, SchedulableTask
from swarm.product.portability import PortabilityService
from swarm.scheduling.epoch import InMemorySchedulerEpochService
from swarm.scheduling.memory_store import InMemorySchedulingStore
from swarm.scheduling.service import SchedulerService
from swarm.scheduling.wdrr import WdrrConfig

DEFAULT_POLICY = Path("config/v23/scheduler_policy.v1.json")
MAX_SIM_DECISIONS = 100_000


class CliError(ValueError):
    pass


def register(sub: Any) -> None:
    v23 = sub.add_parser("v23", help="V2.3 scheduler, packs and portability (offline)")
    v23_sub = v23.add_subparsers(dest="v23_command", required=True)

    pol = v23_sub.add_parser("scheduler-policy", help="Validate and print the WDRR policy")
    pol.add_argument("--policy", type=Path, default=DEFAULT_POLICY)

    sim = v23_sub.add_parser("scheduler-simulate", help="Offline WDRR share simulation")
    sim.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    sim.add_argument(
        "--projects", required=True, help="Comma list of project:weight, e.g. a:1,b:3"
    )
    sim.add_argument("--decisions", type=int, default=400)

    sign = v23_sub.add_parser("pack-sign", help="Sign a pack manifest with SWARM_PACK_KEY_*")
    sign.add_argument("--manifest", type=Path, required=True)
    sign.add_argument("--out", type=Path, required=True)

    ver = v23_sub.add_parser("pack-verify", help="Verify a pack manifest against trusted keys")
    ver.add_argument("--manifest", type=Path, required=True)

    exp = v23_sub.add_parser("export", help="Export a project portability bundle")
    exp.add_argument("--project-id", required=True)
    exp.add_argument("--out-dir", type=Path, default=Path("var/portability"))

    imp = v23_sub.add_parser("import", help="Validate and import a portability bundle")
    imp.add_argument("--bundle", type=Path, required=True)
    imp.add_argument("--target-project-id", default=None)


def _parse_projects(spec: str) -> dict[str, float]:
    out: dict[str, float] = {}
    for part in spec.split(","):
        name, _, weight = part.strip().partition(":")
        if not name or not weight:
            raise CliError(f"bad_project_spec:{part}")
        value = float(weight)
        if value <= 0:
            raise CliError(f"weight_must_be_positive:{name}")
        out[name] = value
    if len(out) < 1:
        raise CliError("no_projects")
    return out


def _reserve(intent: DispatchIntent, comp: DispatchIntentComponent) -> str:
    return f"sim_{intent.attempt_id}_{comp.kind}"


def _release(intent: DispatchIntent, comp: DispatchIntentComponent) -> None:
    return None


def simulate(policy: Path, projects: dict[str, float], decisions: int) -> dict[str, Any]:
    if not 1 <= decisions <= MAX_SIM_DECISIONS:
        raise CliError(f"decisions_out_of_range:1..{MAX_SIM_DECISIONS}")
    config = WdrrConfig.from_policy_file(policy)
    svc = SchedulerService(
        InMemorySchedulingStore(),
        epochs=InMemorySchedulerEpochService(),
        holder_id="cli_sim",
        reserve=_reserve,
        release=_release,
        config=config,
    )
    for pid, weight in projects.items():
        svc.register_project(pid, weight=weight)
        svc.register_mission(f"msn_{pid}", pid)
    counts = dict.fromkeys(projects, 0)
    enqueued = datetime(2026, 1, 1, tzinfo=UTC)
    for n in range(decisions):
        tasks = [
            SchedulableTask(
                task_id=f"t_{pid}_{n}",
                mission_id=f"msn_{pid}",
                project_id=pid,
                attempt_id=f"att_{pid}_{n}",
                enqueued_at=enqueued,
            )
            for pid in projects
        ]
        out = svc.schedule_once(tasks)
        if out.intent is not None and out.task is not None and out.decision.value == "admit":
            counts[out.task.project_id] += 1
            svc.mark_dispatched(out.intent.intent_id)
            svc.finish(out.intent.intent_id)
    total_w = sum(projects.values())
    admitted = sum(counts.values()) or 1
    return {
        "ok": True,
        "policy_version": config.policy_version,
        "decisions": decisions,
        "admitted": counts,
        "share": {p: round(c / admitted, 4) for p, c in counts.items()},
        "target_share": {p: round(w / total_w, 4) for p, w in projects.items()},
    }


def _load_manifest(path: Path) -> CapabilityPackManifest:
    return CapabilityPackManifest.model_validate(json.loads(path.read_text(encoding="utf-8")))


def pack_sign(manifest_path: Path, out: Path) -> dict[str, Any]:
    manifest = _load_manifest(manifest_path)
    if not manifest.publisher:
        raise CliError("manifest_publisher_required")
    keys = trusted_keys_from_env()
    key = keys.get(manifest.publisher)
    if key is None:
        raise CliError(f"no_trusted_key_for_publisher:{manifest.publisher}")
    signed = sign_manifest(manifest, key=key)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(signed.model_dump(mode="json"), indent=2) + "\n", encoding="utf-8")
    return {"ok": True, "pack_id": signed.pack_id, "version": signed.version, "out": str(out)}


def pack_verify(manifest_path: Path) -> dict[str, Any]:
    manifest = _load_manifest(manifest_path)
    try:
        verify_manifest(manifest, trusted_keys=trusted_keys_from_env())
    except PackSigningError as exc:
        return {"ok": False, "error": str(exc), "pack_id": manifest.pack_id}
    return {"ok": True, "pack_id": manifest.pack_id, "publisher": manifest.publisher}


def dispatch(args: argparse.Namespace) -> bool:
    """Handle ``swarm v23 …``. Returns False when ``args`` is another command."""
    if getattr(args, "command", None) != "v23":
        return False
    try:
        result = _run(args)
    except (CliError, ValueError, OSError, KeyError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        raise SystemExit(2) from exc
    print(json.dumps(result, indent=2, sort_keys=True))
    if not result.get("ok", False):
        raise SystemExit(2)
    return True


def _run(args: argparse.Namespace) -> dict[str, Any]:
    cmd = args.v23_command
    if cmd == "scheduler-policy":
        config = WdrrConfig.from_policy_file(args.policy)
        return {"ok": True, "policy": asdict(config)}
    if cmd == "scheduler-simulate":
        return simulate(args.policy, _parse_projects(args.projects), args.decisions)
    if cmd == "pack-sign":
        return pack_sign(args.manifest, args.out)
    if cmd == "pack-verify":
        return pack_verify(args.manifest)
    if cmd == "export":
        bundle = PortabilityService().export_project(
            project_id=args.project_id,
            project_config={"project_id": args.project_id},
            out_dir=args.out_dir,
        )
        path = Path(args.out_dir) / f"{bundle.bundle_id}.json"
        return {"ok": True, "bundle_id": bundle.bundle_id, "path": os.fspath(path)}
    if cmd == "import":
        bundle = PortabilityService().import_bundle(
            args.bundle, target_project_id=args.target_project_id
        )
        return {"ok": True, "bundle_id": bundle.bundle_id, "project_id": bundle.project_id}
    raise CliError(f"unknown_v23_command:{cmd}")
```

### Step 2 — hook into `src/swarm/cli.py` (three edits, nothing else)
Save this patch as `/tmp/SW-W3-S3-cli.patch`, then run `git apply --check /tmp/SW-W3-S3-cli.patch && git apply /tmp/SW-W3-S3-cli.patch`.
```diff
diff --git a/src/swarm/cli.py b/src/swarm/cli.py
index 28512def..fab1d617 100644
--- a/src/swarm/cli.py
+++ b/src/swarm/cli.py
@@ -10,6 +10,7 @@ from pathlib import Path
 
 import uvicorn
 
+from swarm import cli_v23
 from swarm.broker.explain import explain_capacity
 from swarm.contracts.fixtures import sample_mission, sample_task
 from swarm.controller.mission import MissionController, spawn_proposal
@@ -115,6 +116,7 @@ def cmd_providers_canary(
 def main() -> None:
     parser = argparse.ArgumentParser(prog="swarm", description="SwarmAI local CLI")
     sub = parser.add_subparsers(dest="command", required=True)
+    cli_v23.register(sub)
 
     serve = sub.add_parser("serve", help="Run the local API")
     serve.add_argument("--host", default="127.0.0.1")
@@ -539,6 +541,8 @@ def main() -> None:
     part.add_argument("mission_id")
 
     args = parser.parse_args()
+    if cli_v23.dispatch(args):
+        return
     if args.command == "serve":
         cmd_serve(args.host, args.port)
     elif args.command == "api" and args.api_command == "export-openapi":
```
If the check fails because line numbers moved, make the three edits by hand:
1. Add `from swarm import cli_v23` as the **first** `from swarm…` import, right after `import uvicorn` and its blank line. Ruff requires it there, with no extra blank line.
2. Directly after `sub = parser.add_subparsers(dest="command", required=True)` inside `main()`, add `    cli_v23.register(sub)`.
3. Directly after `args = parser.parse_args()` inside `main()`, add:
```python
    if cli_v23.dispatch(args):
        return
```

### Step 3 — `tests/product/test_v23_cli.py` (create, exactly)
```python
"""SW-W3-S3: ``swarm v23 …`` commands are offline, deterministic and fail closed."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from swarm.capabilities import CapabilityPackManifest
from swarm.cli import main


def _run(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], *argv: str):
    monkeypatch.setattr(sys, "argv", ["swarm", "v23", *argv])
    code = 0
    try:
        main()
    except SystemExit as exc:
        code = int(exc.code or 0)
    return code, json.loads(capsys.readouterr().out)


def test_policy_loads(monkeypatch, capsys) -> None:
    code, out = _run(monkeypatch, capsys, "scheduler-policy")
    assert code == 0 and out["policy"]["policy_version"] == "v23-wdrr-1"


def test_simulate_matches_weights(monkeypatch, capsys) -> None:
    code, out = _run(
        monkeypatch, capsys, "scheduler-simulate", "--projects", "a:1,b:3", "--decisions", "400"
    )
    assert code == 0
    assert out["admitted"] == {"a": 100, "b": 300}
    assert out["share"] == out["target_share"]


@pytest.mark.parametrize(
    "argv",
    [
        ("--projects", "a:0"),
        ("--projects", "a"),
        ("--projects", "a:1", "--decisions", "0"),
        ("--projects", "a:1", "--decisions", "100001"),
    ],
)
def test_simulate_rejects_bad_input(monkeypatch, capsys, argv) -> None:
    code, out = _run(monkeypatch, capsys, "scheduler-simulate", *argv)
    assert code == 2 and out["ok"] is False


def test_pack_sign_then_verify(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.setenv("SWARM_PACK_TRUSTED_PUBLISHERS", "acme")
    monkeypatch.setenv("SWARM_PACK_KEY_ACME", "test-only-key")
    src = tmp_path / "m.json"
    src.write_text(
        CapabilityPackManifest(
            pack_id="p", version="1", content_digest="sha256:x", publisher="acme"
        ).model_dump_json(),
        encoding="utf-8",
    )
    signed = tmp_path / "signed.json"
    code, out = _run(monkeypatch, capsys, "pack-sign", "--manifest", str(src), "--out", str(signed))
    assert code == 0 and out["ok"]
    code, out = _run(monkeypatch, capsys, "pack-verify", "--manifest", str(signed))
    assert code == 0 and out == {"ok": True, "pack_id": "p", "publisher": "acme"}
    code, out = _run(monkeypatch, capsys, "pack-verify", "--manifest", str(src))
    assert code == 2 and out["error"] == "pack_signature_unkeyed"
    monkeypatch.setenv("SWARM_PACK_KEY_ACME", "rotated-key")
    code, out = _run(monkeypatch, capsys, "pack-verify", "--manifest", str(signed))
    assert code == 2 and out["error"] == "pack_signature_invalid"


def test_pack_sign_without_key_fails(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.delenv("SWARM_PACK_TRUSTED_PUBLISHERS", raising=False)
    src = tmp_path / "m.json"
    src.write_text(
        CapabilityPackManifest(
            pack_id="p", version="1", content_digest="sha256:x", publisher="acme"
        ).model_dump_json(),
        encoding="utf-8",
    )
    code, out = _run(
        monkeypatch, capsys, "pack-sign", "--manifest", str(src), "--out", str(tmp_path / "o")
    )
    assert code == 2 and out["error"] == "no_trusted_key_for_publisher:acme"


def test_export_import_roundtrip_and_tamper(tmp_path: Path, monkeypatch, capsys) -> None:
    code, out = _run(
        monkeypatch, capsys, "export", "--project-id", "proj_x", "--out-dir", str(tmp_path)
    )
    assert code == 0
    path = Path(out["path"])
    code, out = _run(
        monkeypatch, capsys, "import", "--bundle", str(path), "--target-project-id", "proj_y"
    )
    assert code == 0 and out["project_id"] == "proj_y"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["project_config"]["project_id"] = "tampered"
    path.write_text(json.dumps(data), encoding="utf-8")
    code, out = _run(monkeypatch, capsys, "import", "--bundle", str(path))
    assert code == 2 and out["error"] == "bundle_integrity_mismatch"
```

### Step 4 — run
```bash
uv run pytest tests/product/test_v23_cli.py -q          # 9 passed
uv run swarm v23 scheduler-simulate --projects a:1,b:3 --decisions 400   # admitted a=100, b=300
uv run swarm --help | grep v23                          # the subcommand is listed
uv run pytest tests/product -q
```
The tests set `SWARM_PACK_KEY_ACME` to a **test-only** literal through `monkeypatch`. Never put a real key in a test, a doc or a commit.

## 6. Verify (run exactly; all must pass)
```bash
git clean -fdX -- var/            # F-15: stale runtime state breaks re-runs
# Private database for this session: concurrent sessions on one host must never share one.
sudo -u postgres psql -c "CREATE DATABASE swarm_sw_w3_s3 OWNER swarm;" || true
export SWARM_DATABASE_URL=postgresql+psycopg://swarm:swarm@127.0.0.1:5432/swarm_sw_w3_s3
uv run ruff check .
uv run mypy src/swarm
uv run alembic heads               # must print exactly ONE line ending in (head)
uv run pytest tests/product/test_v23_cli.py tests/product -q
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
git add src/swarm/cli_v23.py src/swarm/cli.py tests/product/test_v23_cli.py docs/v2.3/sessions/SW-W3-S3.md
git status --porcelain            # nothing unexpected staged or left over
git commit -m "feat(v2.3): offline swarm v23 CLI (scheduler policy/simulate, pack sign/verify, export/import)" -m "Session: SW-W3-S3. Plan: docs/plans/v2.3/PLAN.md."
git push -u origin cursor/v23-w3-s3-cli
gh pr create --draft --base cursor/sw-v23-integration-460c --head cursor/v23-w3-s3-cli --title "[SW-W3-S3] CLI `swarm v23 …` commands" --body-file docs/v2.3/sessions/SW-W3-S3.md
git ls-remote origin refs/heads/cursor/v23-w3-s3-cli   # must print the same SHA as: git rev-parse HEAD
```
If `gh pr create` is refused (read-only `gh`), the environment opens the PR: check that its base is `cursor/sw-v23-integration-460c` and that it is a draft, and put the PR URL (or the compare URL from section 10, step 4) into the handoff.
If push fails for network reasons, retry up to 4 times waiting 4 s, 8 s, 16 s, 32 s; then STOP (S8).
Docs to update: only your handoff file, plus any doc listed in section 3.

## 9. Handoff file (create before committing)
Create `docs/v2.3/sessions/SW-W3-S3.md` with exactly these headings:
```markdown
# SW-W3-S3 handoff
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
1. Commit whatever is complete inside your own files: `git add <your files> docs/v2.3/sessions/SW-W3-S3.md` then `git commit -m "WIP(SW-W3-S3): <one-line reason>"`.
2. Write the handoff (section 9) with `## Status` = `BLOCKED: <condition id> <one-line reason>`, and under `## Needs other owner` the exact file, function and change you need. Commit it.
3. Push: `git push -u origin cursor/v23-w3-s3-cli` (plus your suffix).
4. Open the draft PR against `cursor/sw-v23-integration-460c` with the title prefix `[BLOCKED]`, or record the compare URL `https://github.com/pri8771/swarmai/compare/cursor/sw-v23-integration-460c...cursor/v23-w3-s3-cli?expand=1` in the handoff.
5. End the session with a final message: the condition id, the reason, the branch and the head SHA.
Never work around a STOP by editing other files, weakening tests, or adding `skip`/`xfail`.

If `tests/tools/test_v20_cancel_killbound.py` fails once in the full run and you did not touch `sandbox_runner.py` or that test, re-run the full list once. If it passes, record both result lines in the handoff under Verification and continue; if it fails twice, STOP (S3). (The known race was fixed by SW-FIX-FLAKE; a new failure is worth reporting.)

## 11. Codex review packet (put this in the PR description and in the handoff)
```markdown
### Codex review packet — SW-W3-S3
- PR: <PR URL — fill in after the PR exists>
- Branch: <exact branch name>  Base: origin/cursor/sw-v23-integration-460c @ <base SHA from Setup>
- Head SHA: <output of `git rev-parse HEAD`; must equal `git ls-remote origin refs/heads/<branch>`>
- Diff for review: `git diff <base SHA>...<head SHA>`
- Files to review: `src/swarm/cli_v23.py`, `src/swarm/cli.py`, `tests/product/test_v23_cli.py`, `docs/v2.3/sessions/SW-W3-S3.md`
- Review focus (AGENTS.md Code Review Rules): cross-tenant/project access; secret disclosure; financial accounting (unknown usage or cost is never zero); unbounded retries; silently changed model behaviour; recovery gaps after a crash/restart; unsupported release claims ("accepted", "complete").
- Checks run: <paste the final result line of every command in section 6>
- Verdict requested: `RECOMMEND_ACCEPT <head SHA>` or `REQUEST_CHANGES` with file:line findings.
```
