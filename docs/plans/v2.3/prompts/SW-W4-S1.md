# SW-W4-S1 — Campaign runner, V2.3 evidence, exit checklist, status/agents/CHANGELOG/README, candidate rebind

Copy this whole file into a fresh Cursor session opened on the **swarmai** repository. Follow it top to bottom. It is self-contained: do not read other plans to decide what to do.

| Field | Value |
|---|---|
| Session ID | `SW-W4-S1` |
| Repository | `pri8771/swarmai` (GitHub remote `origin`; **public** repo) |
| Base branch | `cursor/sw-v23-integration-460c` — always the **current** `origin/cursor/sw-v23-integration-460c` (plan baseline `dev` @ `8e1c0fde`) |
| Your branch | `cursor/v23-w4-s1-evidence-status` |
| Branch-suffix rule | If your environment forces a suffix (for example `-460c`), append it **once** to *your* branch and write the exact final name in the handoff. Never add a suffix to `cursor/sw-v23-integration-460c`: it already ends in `-460c`. |
| PR target | `cursor/sw-v23-integration-460c` — **draft** PR. Never `dev`, never `main`. |
| Wave | 4 |
| Depends on | SW-W0-S3, SW-W1-S12, SW-W2-S2, SW-W3-S1, SW-W3-S2, SW-W3-S3, SW-W3-S4 |
| Handoff file | `docs/v2.3/sessions/SW-W4-S1.md` |
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
git checkout -b cursor/v23-w4-s1-evidence-status origin/cursor/sw-v23-integration-460c
git log -1 --format='%H %s'       # record this SHA in the handoff as 'base'
command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh   # then: export PATH=$HOME/.local/bin:$PATH
uv sync
git clean -fdX -- var/
```

## 2. Dependency and environment check
Depends on: SW-W0-S3, SW-W1-S12, SW-W2-S2, SW-W3-S1, SW-W3-S2, SW-W3-S3, SW-W3-S4. Their PRs must already be merged into `cursor/sw-v23-integration-460c` (by the wave MERGE prompt).
Run every command below. Each must print `OK`. If any prints `MISSING`, STOP (condition S2 in section 10).

```bash
git fetch origin cursor/sw-v23-integration-460c
git cat-file -e origin/cursor/sw-v23-integration-460c:src/swarm/api/routes_v23.py && echo "OK src/swarm/api/routes_v23.py" || echo "MISSING src/swarm/api/routes_v23.py"
git cat-file -e origin/cursor/sw-v23-integration-460c:src/swarm/cli_v23.py && echo "OK src/swarm/cli_v23.py" || echo "MISSING src/swarm/cli_v23.py"
git cat-file -e origin/cursor/sw-v23-integration-460c:src/swarm/acceptance/v23_probes.py && echo "OK src/swarm/acceptance/v23_probes.py" || echo "MISSING src/swarm/acceptance/v23_probes.py"
git cat-file -e origin/cursor/sw-v23-integration-460c:src/swarm/pursuit/native_loop.py && echo "OK src/swarm/pursuit/native_loop.py" || echo "MISSING src/swarm/pursuit/native_loop.py"
git cat-file -e origin/cursor/sw-v23-integration-460c:apps/console/src/components/OpsPanel.tsx && echo "OK apps/console/src/components/OpsPanel.tsx" || echo "MISSING apps/console/src/components/OpsPanel.tsx"
```

This session needs **no** secrets or environment variables.

## 3. Files you own (the ONLY files you may create or modify)
- `scripts/v23_acceptance_campaign.py` — create
- `docs/evidence/v23/**` — create (campaign outputs)
- `docs/v2.3/EXIT_CHECKLIST.md` — create
- `docs/v2.3/STATUS.md` — modify
- `docs/v2.0/STATUS.md` — modify
- `docs/agents/CURRENT.md, docs/agents/context.json, docs/agents/RESUME.md, docs/agents/V20_TODO.md` — modify
- `CHANGELOG.md` — modify
- `README.md` — modify
- `src/swarm/release/candidate.py` — modify (add CURRENT_SCHEMA_REVISION)
- `src/swarm/cli.py and src/swarm/api/routes_v1.py` — modify (replace literal "a18tov30schema0001" with the constant; admin-gate candidate-freeze; nothing else)
- `tests/release/test_schema_revision.py` — create
- `docs/v2.3/sessions/SW-W4-S1.md` — create (your handoff)

## 4. Do NOT touch
- Any file not listed in section 3 (in particular: `src/swarm/api/app.py`, `src/swarm/api/store.py`, `src/swarm/cli.py`, `src/swarm/db/models.py`, `migrations/`, `docs/agents/*`, `docs/plans/v2.3/*`, `CHANGELOG.md`, `README.md`, `.github/`, unless listed above).
- The `inference_server` repository: read-only, and only through the commands in section 5.
- The branches `main`, `dev`, `cursor/sw-v23-integration-460c`, `cursor/v23-plan-460c`, and any other session's branch.
- Generated files that tests rewrite: `schemas/v1/*`, `docs/evidence/fix-004/*`, `var/*` — always restore them before committing (section 6).

## 5. Steps
**Goal.** This is the Wave-4 **serialization point**. Run it only after `SW-MERGE-W3` reports every required session merged into `cursor/sw-v23-integration-460c`. It does four things:
1. Fixes **F-14**: a single `CURRENT_SCHEMA_REVISION` constant replaces the three stale `"a18tov30schema0001"` literals, and a test pins it to the Alembic head.
2. Fixes **F-16**: `POST /v1/release/candidate-freeze` becomes admin-only. Today any authenticated principal can run `git` and write a candidate manifest.
3. Adds `scripts/v23_acceptance_campaign.py`, runs it, and commits the sanitized evidence.
4. Rewrites the status and agent docs to state **exactly** what is true: implementation-complete candidate, **not accepted**, with the external gates listed as pending or blocked.

The code below was compiled and run on the fully integrated scratch tree (`dev @ 8e1c0fde` plus all 23 other sessions):
- The full `uv run pytest` gives 763 passed, 1 skipped on the scratch tree. On the executed integration branch (after SW-FIX-ALEMBIC, `604f7ace`) it gives `778 passed, 1 skipped` with a private database; before that fix it had 4 Alembic failures (see Step 6).
- The campaign gives `deterministic: pass` (10/10). On a VM without router, Docker or LiveGrant it reports `live_router_free_route: blocked:router_not_configured` and `compose_smoke_v20_e10: blocked_env_no_docker`.
- ruff and mypy: clean.

### Step 1 — `src/swarm/release/candidate.py` (one insertion)
Directly below the line `from swarm.contracts.common import new_id, utc_now` (and its blank line), insert:
```python
# Must equal the Alembic head; tests/release/test_schema_revision.py enforces it.
CURRENT_SCHEMA_REVISION = "a23opsplatform0001"
```
Then check the head. If this prints anything other than `a23opsplatform0001 (head)`, use the printed revision id as the constant value instead:
```bash
uv run alembic heads
```
There must be **exactly one** head. Two heads means a second migration slipped in; STOP (S4, section 10).

### Step 2 — `src/swarm/cli.py` (three exact edits, nothing else)
**2a.** Find this block (the recovery backup command):
```python
        from swarm.recovery import BackupService
```
and replace it with:
```python
        from swarm.recovery import BackupService
        from swarm.release.candidate import CURRENT_SCHEMA_REVISION
```
**2b.** In the same command, replace `            schema_revision="a18tov30schema0001",` with `            schema_revision=CURRENT_SCHEMA_REVISION,`.

**2c.** In the `release candidate-freeze` branch:
- replace `        from swarm.release.candidate import CandidateFreezer` with `        from swarm.release.candidate import CURRENT_SCHEMA_REVISION, CandidateFreezer`;
- replace `            source_sha=sha, schema_revision="a18tov30schema0001"` with `            source_sha=sha, schema_revision=CURRENT_SCHEMA_REVISION`.

### Step 3 — `src/swarm/api/routes_v1.py` (function `freeze_candidate` only)
Replace:
```python
    principal: Principal = Depends(get_principal),
) -> dict[str, Any]:
    _ = principal
    import subprocess
    from pathlib import Path

    from swarm.release.candidate import CandidateFreezer
```
with:
```python
    principal: Principal = Depends(get_principal),
) -> dict[str, Any]:
    if "admin" not in principal.roles:
        raise ApiError("forbidden_admin", "admin role required", status_code=403)
    import subprocess
    from pathlib import Path

    from swarm.release.candidate import CURRENT_SCHEMA_REVISION, CandidateFreezer
```
and replace `.freeze(source_sha=sha, schema_revision="a18tov30schema0001")` with `.freeze(source_sha=sha, schema_revision=CURRENT_SCHEMA_REVISION)`.

Then run:
```bash
grep -rn "a18tov30schema0001" src/swarm/cli.py src/swarm/api/routes_v1.py   # must print nothing
```

### Step 4 — `tests/release/test_schema_revision.py` (create, exactly)
```python
"""SW-W4-S1 / F-14, F-16: candidate schema revision tracks the Alembic head; freeze is admin-only."""

from __future__ import annotations

from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory
from fastapi.testclient import TestClient

from swarm.api.app import create_app
from swarm.release.candidate import CURRENT_SCHEMA_REVISION

ROOT = Path(__file__).resolve().parents[2]


def test_constant_matches_single_alembic_head() -> None:
    script = ScriptDirectory.from_config(Config(str(ROOT / "alembic.ini")))
    assert script.get_heads() == [CURRENT_SCHEMA_REVISION]


def test_no_hardcoded_schema_literals_remain() -> None:
    for rel in ("src/swarm/cli.py", "src/swarm/api/routes_v1.py"):
        assert "a18tov30schema0001" not in (ROOT / rel).read_text(encoding="utf-8"), rel


def test_candidate_freeze_requires_admin() -> None:
    app = create_app(require_auth=True, db_reachable=False, seed_fixtures=True)
    with TestClient(app) as client:
        res = client.post(
            "/v1/release/candidate-freeze", headers={"Authorization": "Bearer atk_policy_demo"}
        )
    assert res.status_code == 403
    assert res.json()["code"] == "forbidden_admin"
```

### Step 5 — `scripts/v23_acceptance_campaign.py` (create, exactly)
```python
#!/usr/bin/env python3
"""V2.3 acceptance campaign: frozen deterministic probes plus honest external-gate status.

Never marks a version accepted, never invents a LiveGrant, never spends.
Writes ``docs/evidence/v23/acceptance_campaign.json``. Exit 0 only when every
deterministic probe passes; external gates are reported, not required.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from swarm.acceptance.v23_probes import run_v23_probes  # noqa: E402
from swarm.pursuit.native_loop import native_loop_from_env  # noqa: E402
from swarm.release.candidate import CURRENT_SCHEMA_REVISION  # noqa: E402

EVIDENCE = ROOT / "docs" / "evidence" / "v23" / "acceptance_campaign.json"
COMPOSE_SMOKE = ROOT / "docs" / "evidence" / "v20" / "compose-smoke" / "latest.json"


def _git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _compose_status() -> str:
    if not COMPOSE_SMOKE.is_file():
        return "not_run"
    try:
        return str(json.loads(COMPOSE_SMOKE.read_text(encoding="utf-8")).get("status", "unknown"))
    except (OSError, json.JSONDecodeError):
        return "unreadable"


def _live_router_status() -> str:
    loop, reason = native_loop_from_env({}, grant=None)
    return "configured_but_not_run" if loop is not None else f"blocked:{reason}"


def main() -> int:
    os.chdir(ROOT)
    started = datetime.now(UTC).isoformat()
    with tempfile.TemporaryDirectory(prefix="v23_campaign_") as tmp:
        report = run_v23_probes(Path(tmp))
    deterministic_ok = report["deterministic_passed"] == report["deterministic_total"]
    summary = {
        "packet": "V23-ACCEPTANCE-CAMPAIGN",
        "started_at": started,
        "finished_at": datetime.now(UTC).isoformat(),
        "source_sha": _git_sha(),
        "schema_revision": CURRENT_SCHEMA_REVISION,
        "freeze_id": report["freeze_id"],
        "policy_version": report["policy_version"],
        "gates": {
            "deterministic": "pass" if deterministic_ok else "fail",
            "multi_process_private": "pending_owner_approval",
            "live_router_free_route": _live_router_status(),
            "compose_smoke_v20_e10": _compose_status(),
            "durable_postgres_flag": os.environ.get("SWARM_V23_DURABLE", "") == "1",
        },
        "deterministic_passed": report["deterministic_passed"],
        "deterministic_total": report["deterministic_total"],
        "results": [
            {k: r[k] for k in ("id", "probe", "gate", "ok", "status")} for r in report["results"]
        ],
        "pending": report["pending"],
        "version_claim": report["version_claim"],
        "any_version_accepted": False,
        "spend_usd": 0.0,
        "spend_basis": "no provider calls; probes are in-process fakes",
    }
    EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("gates", "deterministic_passed", "version_claim")}))
    return 0 if deterministic_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
```

### Step 6 — run checks, then the campaign
```bash
git clean -fdX -- var/
uv run ruff check . && uv run mypy src/swarm
export SWARM_DATABASE_URL=postgresql+psycopg://swarm:swarm@127.0.0.1:5432/swarm_sw_w4_s1   # private DB (section 6 creates it)
uv run pytest -q                                     # whole suite; record passed/skipped counts
(cd apps/console && npx vitest run && npx oxlint src) # console
uv run python scripts/v23_acceptance_campaign.py; echo "exit=$?"
git checkout -- schemas/v1 docs/evidence/fix-004 var 2>/dev/null || true   # undo test rewrites (F-11)
git status --short                                   # only your owned files may appear
```
- Do **not** set `SWARM_ROUTER_BASE_URL`, `SWARM_ROUTER_MODEL`, `SPLITSIGNAL_BASE_URL` or `SPLITSIGNAL_MODEL`, and do not create a LiveGrant, to "make the gate green". If the environment already injects `SPLITSIGNAL_*` secrets, leave them; the gate then honestly reads `blocked:<LiveGrant reason>`. The campaign must report the environment as it really is.
- The whole-repo `uv run pytest -q` must pass on a tree that contains SW-FIX-ALEMBIC. If the Alembic schema tests (`test_single_alembic_head_after_upgrade`, `test_alembic_upgrade_empty_db`, `test_alembic_upgrade_preserves_populated_legacy_rows`, `test_upgrade_downgrade_upgrade`) fail with empty table sets, something in the run removed `SWARM_DATABASE_URL` from the process environment (historically the V20-S11 probe) and Alembic migrated the default `swarm` database. Record the failing tests; the authoritative checks remain the section 6 offline list and `pytest tests/integration -m integration` run separately. Do not STOP for this alone.
- If the campaign exits 1, a probe failed. Do not edit probes. Record the failing `results[].status` and STOP (S3, section 10).

### Step 7 — `docs/v2.3/EXIT_CHECKLIST.md` (create)
Start from the template below. Fill in every `<…>` placeholder from `docs/evidence/v23/acceptance_campaign.json` and `git rev-parse HEAD`. If an item's evidence test is missing or failing on your tree, change its status to `not done` and say why. **Never** mark item 16 done. If the V20-E10 gate is `fail`, write `not done — gate fail` with the failing step and the follow-up owner; if it is `pass`, say where it ran (dev VM or operator host). For `<splitsignal adapter status>`: run `git cat-file -e origin/cursor/sw-v23-integration-460c:src/swarm/providers/splitsignal_client.py && echo MERGED || echo NOT_MERGED`; write `done (fake SplitSignal); live pending SW-X2-S1 (SP4)` if MERGED, else `pending: SW-X1-S1 not merged (gate SP1)`.
```markdown
# V2.3 implementation-complete — exit checklist

Source checklist: `docs/coordination/FUTURE_VERSION_EXIT_CHECKLISTS_20260921.md` §"V2.3 implementation-complete".
Contracts: `src/swarm/contracts/v23.py` (artifact `docs/artifacts/future/ART-V23-MULTIMISSION_SCHEDULER.md`), policy `config/v23/scheduler_policy.v1.json` (`v23-wdrr-1`).

| Field | Value |
|---|---|
| Tree | `origin/cursor/sw-v23-integration-460c` @ `<SHA_OF_THE_COMMIT_YOU_RAN_ON>` |
| Schema head | `a23opsplatform0001` (`CURRENT_SCHEMA_REVISION`) |
| Campaign | `docs/evidence/v23/acceptance_campaign.json` (`freeze_id` `v23-acceptance-deterministic-20260926`) |
| Deterministic probes | `<N>/10` pass |
| Version claim | **implementation-complete candidate only. NOT accepted.** Acceptance needs Codex review (D2), owner sign-off, the owner's merge into `dev`, and the multi-process/private gate. |

Legend: **done**, meaning implemented with a deterministic test and, where it says "PG", a PostgreSQL integration test. **pending** means an external gate, honestly not run.

| # | Checklist item | Status | Evidence (test or artifact) |
|---|---|---|---|
| 1 | scheduler state durable | done (PG) | `tests/integration/db/test_v23_store_sql.py`, `test_v23_service_restart_sql.py`, `test_v23_routes_durable_sql.py` |
| 2 | project-level fairness defined | done | `tests/controller/test_v23_wdrr.py`; probe V23-A01 |
| 3 | aging/priority deterministic | done | `tests/controller/test_v23_wdrr.py`; `test_v23_pathological.py::test_03` |
| 4 | reservation intent transactional / fail-closed | done | `tests/controller/test_v23_dispatch_intent.py`; `test_v23_pathological.py::test_05,test_06` |
| 5 | provider/worker/tool capacity integrated | done | `SchedulerService(reserve=, release=)`; `test_v23_pathological.py::test_09`; probe V23-A09 |
| 6 | backpressure bounded | done | WDRR caps + `test_v23_pathological.py::test_01,test_10` |
| 7 | cancellation/drain fenced | done | `test_v23_pathological.py::test_07`; `tests/workers/test_v23_fleet_policy.py`; probe V23-A05 |
| 8 | scheduler bound to SiteEpoch | done | `tests/controller/test_v23_epoch.py`; `test_v23_pathological.py::test_07,test_11` |
| 9 | decision receipts emitted | done (PG) | `SqlSchedulingStore.append_receipt`; `GET /v1/scheduler/receipts` (`tests/api/test_v23_routes.py`) |
| 10 | capability packs lifecycle complete | done (PG) | `tests/extensions/test_v23_pack_lifecycle.py`; `test_v23_pack_installs_sql.py`; probe V23-A06 |
| 11 | portability export/import complete | done | `tests/portability/test_v23_bundle.py`; probe V23-A07 |
| 12 | observability read surface complete | done | `tests/api/test_v23_ops_events_scope.py`; `tests/controller/test_v23_ops_trace.py`; `GET /v1/ops/trace/{id}`; console Ops tab (`apps/console/src/ops.test.tsx`) |
| 13 | dashboard mutation uses action boundary | done | console `WorkerControls` → `POST /v1/workers/{id}/drain|revoke` (audited `operator.action`) |
| 14 | fleet placement/trust/locality complete | done | `tests/workers/test_v23_fleet_policy.py`; probe V23-A03 |
| 15 | pathological deterministic suite passes | done | `tests/controller/test_v23_pathological.py` (11 cases); `tests/acceptance/test_v23_acceptance.py` |
| 16 | multi-process/private evidence complete or honestly pending | **pending_owner_approval** | scenario V23-A11; blocker B-04 |

## V2.0 depth prerequisites

| Item | Status | Evidence |
|---|---|---|
| V20-E03 pursuit PostgreSQL write-through | done (PG), behind `SWARM_V23_DURABLE=1` | `tests/integration/db/test_v20_pursuit_writethrough_sql.py`, `test_v20_durable_wiring_sql.py` |
| V20-E04 durable holds/lessons (+ F-13 unknown ≠ zero) | done (PG) | `tests/pursuit/test_v20_durable_holds.py`, `test_v20_unknown_usage_budget.py`, `test_v20_holds_sql.py` |
| V20-E05 inference_server router client | done (fake router) | `tests/providers/test_router_client.py` |
| SplitSignal consumer adapter (contract `swarmai-consumer 1.x`, sync point SP1/SP2) | `<splitsignal adapter status>` | `tests/providers/test_splitsignal_client.py` |
| V20-E06 singleton pursuit ticker | done | `tests/product/test_v20_durable_wiring.py::test_only_one_ticker_runs_per_site` |
| V20-E07 native model/tool loop | implemented; **live run blocked** (`<live_router_free_route gate value>`) | `tests/pursuit/test_v20_native_loop.py` |
| V20-E08 sandbox cancel kill-bound | done | `tests/tools/test_v20_cancel_killbound.py` |
| V20-E09 console ops surface | done | `apps/console/src/ops.test.tsx` |
| V20-E10 compose full-path smoke | `<compose_smoke_v20_e10 gate value>` | `docs/evidence/v20/compose-smoke/latest.json` |
| V20-E11 | deferred (out of scope) | — |

## Not claimed

- V2.3 (or any version) **accepted**.
- Multi-process / private-infrastructure evidence (V23-A11).
- A live model call through inference_server, unless the owner granted a LiveGrant **and** it is recorded in the campaign.
- Any spend. `spend_usd` is 0.0 because no provider was called, not because costs were measured as zero.
```

### Step 8 — status and agent docs (edit in place; keep each file's existing structure)
- **`docs/v2.3/STATUS.md`** — replace the whole body with:
  - title: `# SwarmAI V2.3 Status — implementation-complete candidate (NOT accepted)`;
  - tip SHA and schema head;
  - one line per gate, copied from `acceptance_campaign.json` `gates`;
  - a link to `EXIT_CHECKLIST.md`;
  - a "Not claimed" list copied from the checklist.
  - Remove the old unsupported "implementation-complete (local)" claim (F-09).
- **`docs/v2.0/STATUS.md`** — update `Tip`, `Schema head` (the new constant) and the last "Not claimed" bullet: E03–E06 and E08–E10 are now implemented with evidence; E07's live run and E11 stay open.
- **`docs/agents/CURRENT.md`**:
  - front-matter `verified_at` becomes now (UTC);
  - `pause:` and `v20_work:` take whatever SW-W0-S1 recorded the owner decided (do not invent);
  - the `refs` table gets a new `origin/cursor/sw-v23-integration-460c` row with the SHA/subject of your base (keep the `origin/dev` row unchanged) and `alembic_head` = the constant;
  - in `version_flags`, add rows `v23_impl_complete_candidate | true` and `v23_accepted | false`;
  - keep every `versions_accepted.*` as `false`.
- **`docs/agents/context.json`** — mirror the same values under `refs`, `version_flags` and `remaining_eng`. It must stay valid JSON: `python3 -m json.tool docs/agents/context.json >/dev/null`.
- **`docs/agents/RESUME.md`** — the next step becomes "Codex review of the V2.3 candidate range on `cursor/sw-v23-integration-460c`; SW-X2-S1 (SplitSignal live smoke, SP4–SP6); owner merges `cursor/sw-v23-integration-460c` into `dev`; owner decision on the V23-A11 multi-process gate (SW-PREAPPROVAL-A5)".
- **`docs/agents/V20_TODO.md`** — tick E03–E06 and E08–E10 with PR links. E07 is "implemented; live run via SplitSignal is SW-X2-S1 (<live_router_free_route gate value>)"; E11 is deferred.
- **`CHANGELOG.md`** — add a new top section, `## [Unreleased] — V2.3 implementation-complete candidate (<date>)`, with Added / Fixed (F-01, F-13, F-14, F-16) / Evidence / Notes. Notes: "Not accepted. Multi-process gate pending owner approval. Zero spend." Do not edit older sections.
- **`README.md`** — replace the stale "V0.9 hardening" label (F-12) with "V2.3 implementation-complete candidate (not accepted)". Add a two-line "V2.3 operator commands" pointer to `swarm v23 --help` and `scripts/v23_acceptance_campaign.py`.

Wording rules for every doc:
- Use exactly one of these words per claim: *proposed, implemented, tested, independently reviewed, live verified*.
- "Accepted" appears only in the negative.
- Unknown cost is written "unknown", never "$0". The campaign's `spend_usd: 0.0` is justified by "no provider calls".

### Step 9 — final verification
```bash
uv run pytest tests/release tests/acceptance -q
python3 -m json.tool docs/agents/context.json >/dev/null && echo JSON_OK
grep -rniE "v2\.3[^|]*accepted" docs/v2.3 docs/agents CHANGELOG.md README.md | grep -viE "not accepted|accepted: *false|v23_accepted \| false|never|no version" || echo NO_FALSE_ACCEPT_CLAIMS
```

## 6. Verify (run exactly; all must pass)
```bash
git clean -fdX -- var/            # F-15: stale runtime state breaks re-runs
# Private database for this session: concurrent sessions on one host must never share one.
sudo -u postgres psql -c "CREATE DATABASE swarm_sw_w4_s1 OWNER swarm;" || true
export SWARM_DATABASE_URL=postgresql+psycopg://swarm:swarm@127.0.0.1:5432/swarm_sw_w4_s1
uv run ruff check .
uv run mypy src/swarm
uv run alembic heads               # must print exactly ONE line ending in (head)
uv run pytest tests/release tests/acceptance -q
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
git add scripts/v23_acceptance_campaign.py docs/evidence/v23/ docs/v2.3/EXIT_CHECKLIST.md docs/v2.3/STATUS.md docs/v2.0/STATUS.md docs/agents/CURRENT.md docs/agents/context.json docs/agents/RESUME.md docs/agents/V20_TODO.md CHANGELOG.md README.md src/swarm/release/candidate.py src/swarm/cli.py src/swarm/api/routes_v1.py tests/release/test_schema_revision.py docs/v2.3/sessions/SW-W4-S1.md
git status --porcelain            # nothing unexpected staged or left over
git commit -m "docs(v2.3): acceptance campaign evidence, exit checklist and honest status; bind candidate schema revision" -m "Session: SW-W4-S1. Plan: docs/plans/v2.3/PLAN.md."
git push -u origin cursor/v23-w4-s1-evidence-status
gh pr create --draft --base cursor/sw-v23-integration-460c --head cursor/v23-w4-s1-evidence-status --title "[SW-W4-S1] Campaign runner, V2.3 evidence, exit checklist, status/agents/CHANGELOG/README, candidate rebind" --body-file docs/v2.3/sessions/SW-W4-S1.md
git ls-remote origin refs/heads/cursor/v23-w4-s1-evidence-status   # must print the same SHA as: git rev-parse HEAD
```
If `gh pr create` is refused (read-only `gh`), the environment opens the PR: check that its base is `cursor/sw-v23-integration-460c` and that it is a draft, and put the PR URL (or the compare URL from section 10, step 4) into the handoff.
If push fails for network reasons, retry up to 4 times waiting 4 s, 8 s, 16 s, 32 s; then STOP (S8).
Docs to update: only your handoff file, plus any doc listed in section 3.

## 9. Handoff file (create before committing)
Create `docs/v2.3/sessions/SW-W4-S1.md` with exactly these headings:
```markdown
# SW-W4-S1 handoff
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
1. Commit whatever is complete inside your own files: `git add <your files> docs/v2.3/sessions/SW-W4-S1.md` then `git commit -m "WIP(SW-W4-S1): <one-line reason>"`.
2. Write the handoff (section 9) with `## Status` = `BLOCKED: <condition id> <one-line reason>`, and under `## Needs other owner` the exact file, function and change you need. Commit it.
3. Push: `git push -u origin cursor/v23-w4-s1-evidence-status` (plus your suffix).
4. Open the draft PR against `cursor/sw-v23-integration-460c` with the title prefix `[BLOCKED]`, or record the compare URL `https://github.com/pri8771/swarmai/compare/cursor/sw-v23-integration-460c...cursor/v23-w4-s1-evidence-status?expand=1` in the handoff.
5. End the session with a final message: the condition id, the reason, the branch and the head SHA.
Never work around a STOP by editing other files, weakening tests, or adding `skip`/`xfail`.

If `tests/tools/test_v20_cancel_killbound.py` fails once in the full run and you did not touch `sandbox_runner.py` or that test, re-run the full list once. If it passes, record both result lines in the handoff under Verification and continue; if it fails twice, STOP (S3). (The known race was fixed by SW-FIX-FLAKE; a new failure is worth reporting.)

## 11. Codex review packet (put this in the PR description and in the handoff)
```markdown
### Codex review packet — SW-W4-S1
- PR: <PR URL — fill in after the PR exists>
- Branch: <exact branch name>  Base: origin/cursor/sw-v23-integration-460c @ <base SHA from Setup>
- Head SHA: <output of `git rev-parse HEAD`; must equal `git ls-remote origin refs/heads/<branch>`>
- Diff for review: `git diff <base SHA>...<head SHA>`
- Files to review: `scripts/v23_acceptance_campaign.py`, `docs/evidence/v23/`, `docs/v2.3/EXIT_CHECKLIST.md`, `docs/v2.3/STATUS.md`, `docs/v2.0/STATUS.md`, `docs/agents/CURRENT.md`, `docs/agents/context.json`, `docs/agents/RESUME.md`, `docs/agents/V20_TODO.md`, `CHANGELOG.md`, `README.md`, `src/swarm/release/candidate.py`, `src/swarm/cli.py`, `src/swarm/api/routes_v1.py`, `tests/release/test_schema_revision.py`, `docs/v2.3/sessions/SW-W4-S1.md`
- Review focus (AGENTS.md Code Review Rules): cross-tenant/project access; secret disclosure; financial accounting (unknown usage or cost is never zero); unbounded retries; silently changed model behaviour; recovery gaps after a crash/restart; unsupported release claims ("accepted", "complete"). Session-specific: candidate-freeze admin gate (F-16); evidence and status make no acceptance claim.
- Checks run: <paste the final result line of every command in section 6>
- Verdict requested: `RECOMMEND_ACCEPT <head SHA>` or `REQUEST_CHANGES` with file:line findings.
```
