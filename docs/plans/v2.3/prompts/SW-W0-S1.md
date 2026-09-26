# SW-W0-S1 — Tracking reset, lift-pause record, honest V2.3 status, frozen scheduler policy + acceptance manifest

Copy this whole file into a fresh Cursor session opened on the **swarmai** repository. Follow it top to bottom. It is self-contained: do not read other plans to decide what to do.

| Field | Value |
|---|---|
| Session ID | `SW-W0-S1` |
| Repository | `pri8771/swarmai` (GitHub remote `origin`; **public** repo) |
| Base branch | `cursor/sw-v23-integration-460c` — always the **current** `origin/cursor/sw-v23-integration-460c` (plan baseline `dev` @ `8e1c0fde`) |
| Your branch | `cursor/v23-w0-s1-tracking-policy` |
| Branch-suffix rule | If your environment forces a suffix (for example `-460c`), append it **once** to *your* branch and write the exact final name in the handoff. Never add a suffix to `cursor/sw-v23-integration-460c`: it already ends in `-460c`. |
| PR target | `cursor/sw-v23-integration-460c` — **draft** PR. Never `dev`, never `main`. |
| Wave | 0 |
| Depends on | none |
| Handoff file | `docs/v2.3/sessions/SW-W0-S1.md` |
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
If it prints `INTEG_MISSING`, create the integration branch (only SW-W0-S1 may do this): `git fetch origin dev && git push origin origin/dev:refs/heads/cursor/sw-v23-integration-460c`, then run the fetch again.
```bash
git checkout -b cursor/v23-w0-s1-tracking-policy origin/cursor/sw-v23-integration-460c
git log -1 --format='%H %s'       # record this SHA in the handoff as 'base'
command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh   # then: export PATH=$HOME/.local/bin:$PATH
uv sync
git clean -fdX -- var/
```

## 2. Dependency and environment check
This session has **no dependencies**. Go to Step 1.

This session needs **no** secrets or environment variables.

## 3. Files you own (the ONLY files you may create or modify)
- `docs/agents/CURRENT.md` — modify
- `docs/agents/context.json` — modify
- `docs/agents/RESUME.md` — modify
- `docs/agents/V20_TODO.md` — modify
- `docs/agents/README.md` — modify
- `docs/v2.3/STATUS.md` — modify
- `docs/v2.3/sessions/README.md` — create
- `docs/v3.0/STATUS.md` — modify
- `CHANGELOG.md` — modify
- `config/v23/scheduler_policy.v1.json` — create
- `benchmarks/v23_acceptance/scenarios.freeze.json` — create
- `docs/v2.3/sessions/SW-W0-S1.md` — create (your handoff)

## 4. Do NOT touch
- Any file not listed in section 3 (in particular: `src/swarm/api/app.py`, `src/swarm/api/store.py`, `src/swarm/cli.py`, `src/swarm/db/models.py`, `migrations/`, `docs/agents/*`, `docs/plans/v2.3/*`, `CHANGELOG.md`, `README.md`, `.github/`, unless listed above).
- The `inference_server` repository: read-only, and only through the commands in section 5.
- The branches `main`, `dev`, `cursor/sw-v23-integration-460c`, `cursor/v23-plan-460c`, and any other session's branch.
- Generated files that tests rewrite: `schemas/v1/*`, `docs/evidence/fix-004/*`, `var/*` — always restore them before committing (section 6).

## 5. Steps
**Goal.** Make the repository tell the truth about where V2.3 stands, record that the owner lifted the V2.0 pause for V2.3 engineering, and freeze the two machine-readable inputs every later session depends on: the scheduler policy and the acceptance scenario manifest. This session changes **docs and JSON only**, no Python.

**Background you need.**
- `docs/v2.3/STATUS.md`, `CHANGELOG.md` and `docs/v3.0/STATUS.md` claim "implementation-complete". The audit found V2.3 is at *scaffold* level: in-memory stubs, fairness ranking ignored, unkeyed pack signatures, key-name-only secret scan, no durable scheduler state, no inference_server client. These claims must be corrected (finding F-09).
- `docs/agents/CURRENT.md` and `context.json` record tip `dd7726eb…`. The real tip is newer (use the SHA from Setup). The owner lifted `pause: true` on 2026-09-26 (blocker B-01; the owner's instruction "get to V2.3 for both projects"); the plan commit on `cursor/v23-plan-460c` records it in `docs/swarm-mvp/DECISIONS.md` and in `CURRENT.md`. The lift covers engineering only; acceptance and merge-to-`main`/`dev` rules do **not** change (finding F-10).
- Session PRs target `cursor/sw-v23-integration-460c`, not `dev` (coordinator decision C1). The owner merges the integration branch into `dev` later.

### Step 0 — bring the plan commit into your branch
```bash
git fetch origin cursor/v23-plan-460c || echo PLAN_BRANCH_MISSING
git merge-base --is-ancestor origin/cursor/v23-plan-460c HEAD && echo PLAN_IN || echo PLAN_OUT
```
- `PLAN_BRANCH_MISSING`: STOP (S2, section 10).
- `PLAN_OUT`: run `git merge --no-ff --no-edit origin/cursor/v23-plan-460c -m "merge: V2.3 plan branch into SW-W0-S1"`. On a conflict run `git merge --abort` and STOP (S4).
- Then `test -f docs/plans/v2.3/PLAN.md && grep -q "B-01" docs/swarm-mvp/DECISIONS.md && echo PLAN_OK || echo PLAN_BAD`. `PLAN_BAD`: STOP (S2).
The plan commit is docs-only and is reviewed on its own PR; your own edits start at Step 1.
- V2.3 definition source: `docs/coordination/FUTURE_VERSION_EXIT_CHECKLISTS_20260921.md` §"V2.3 implementation-complete" (16 items) and `docs/artifacts/future/ART-V23-OPS_PLATFORM.md` §"Acceptance protocol" (10 items).

### Step 1 — `config/v23/scheduler_policy.v1.json` (create, exactly this content)
```json
{
  "schema_version": "1",
  "policy_version": "v23-wdrr-1",
  "status": "frozen_for_v23_implementation",
  "source": "docs/artifacts/future/ART-V23-MULTIMISSION_SCHEDULER.md",
  "wdrr": {
    "base_quantum": 1.0,
    "max_credit_cap_multiplier": 10.0,
    "urgent_borrow_cap": 2.0,
    "aging_floor_ms": 60000,
    "aging_bonus": 0.5,
    "deadline_bonus_cap": 1.0,
    "deadline_slack_ms": 300000,
    "restart_credit_cap_multiplier": 10.0
  },
  "defaults": {
    "project_max_concurrency": 4,
    "mission_max_parallelism": 2,
    "max_queue_depth_per_project": 1000,
    "max_fanout_per_mission": 50
  },
  "intents": {
    "ttl_seconds": 30
  },
  "scheduler_epoch": {
    "ttl_seconds": 15
  },
  "fairness_tolerance": {
    "relative_share_error": 0.15,
    "min_decisions": 200
  },
  "spend": {
    "mode": "zero_spend",
    "allowed_billing": ["free"]
  }
}
```

### Step 2 — `benchmarks/v23_acceptance/scenarios.freeze.json` (create)
Paste this content, then replace the `frozen_at` placeholder with the current UTC time in ISO format (run `date -u +%Y-%m-%dT%H:%M:%S+00:00`).
```json
{
  "schema_version": "2.3.0",
  "freeze_id": "v23-acceptance-deterministic-20260926",
  "frozen_at": "REPLACE_WITH_UTC_TIMESTAMP_AT_COMMIT",
  "source": "docs/artifacts/future/ART-V23-OPS_PLATFORM.md#acceptance-protocol-for-v23-operational-platform",
  "policy_ref": "config/v23/scheduler_policy.v1.json",
  "policy_version": "v23-wdrr-1",
  "version_claim_policy": "never_mark_accepted_from_harness",
  "spend_policy": "zero_no_invented_live_grant",
  "tolerance": {
    "relative_share_error": 0.15,
    "min_decisions": 200
  },
  "gates": {
    "deterministic": {
      "id": "deterministic",
      "description": "Single-process mechanics with fake upstreams and injected clocks; no credentials",
      "requires_live_grant": false,
      "requires_multi_process": false
    },
    "multi_process_private": {
      "id": "multi_process_private",
      "description": "Separate scheduler/control-plane/worker processes on private infrastructure; owner approval required",
      "requires_live_grant": false,
      "requires_multi_process": true
    }
  },
  "scenarios": [
    {
      "id": "V23-A01",
      "title": "Fairness across three weighted projects",
      "art_item": 1,
      "primary_gate": "deterministic",
      "workload": {"projects": {"proj_w1": 1, "proj_w2": 2, "proj_w3": 3}, "decisions": 600},
      "pass_criteria": [
        "each project's admitted share within relative_share_error of weight/sum(weights)",
        "every eligible project admitted at least once"
      ],
      "deterministic_probe": "fairness_three_projects"
    },
    {
      "id": "V23-A02",
      "title": "Anti-amplification under 50+ task expansion",
      "art_item": 2,
      "primary_gate": "deterministic",
      "workload": {"expanding_project_tasks": 60, "baseline_project_tasks": 1, "decisions": 400},
      "pass_criteria": ["expanding project share within tolerance of its weight share (0.5)"],
      "deterministic_probe": "anti_amplification"
    },
    {
      "id": "V23-A03",
      "title": "Two-project isolation negatives",
      "art_item": 3,
      "primary_gate": "deterministic",
      "pass_criteria": [
        "cross-project ops-event read denied (403)",
        "cross-tenant worker placement rejected and audited",
        "pack enabled for project A is not usable by project B",
        "mismatched task/mission project is never admitted (isolation_denied)"
      ],
      "deterministic_probe": "isolation_negatives"
    },
    {
      "id": "V23-A04",
      "title": "Restart preserves pending work, credits, intents and fencing",
      "art_item": 4,
      "primary_gate": "deterministic",
      "also_gates": ["multi_process_private"],
      "pass_criteria": [
        "state reloaded from the durable store equals state before restart",
        "positive credit clamped by restart cap; debt preserved",
        "expired PREPARED/RESERVED intents compensated exactly once",
        "stale scheduler epoch cannot write"
      ],
      "deterministic_probe": "restart_recovery"
    },
    {
      "id": "V23-A05",
      "title": "Drain with active leases",
      "art_item": 5,
      "primary_gate": "deterministic",
      "pass_criteria": [
        "draining worker receives no new placement",
        "draining mission receives no new admission",
        "no duplicate accepted result"
      ],
      "deterministic_probe": "drain_active"
    },
    {
      "id": "V23-A06",
      "title": "Capability pack lifecycle",
      "art_item": 6,
      "primary_gate": "deterministic",
      "pass_criteria": [
        "install -> enable for one project -> deny other project -> drain -> disable -> uninstall",
        "unsigned or wrongly-signed pack refused when signatures required",
        "no implicit capability widening"
      ],
      "deterministic_probe": "pack_lifecycle"
    },
    {
      "id": "V23-A07",
      "title": "Portability export/import into a clean root",
      "art_item": 7,
      "primary_gate": "deterministic",
      "pass_criteria": [
        "no secret values in the bundle (key and value scan)",
        "section digests verify after import",
        "imported approvals/leases are tombstoned and cannot execute"
      ],
      "deterministic_probe": "portability_roundtrip"
    },
    {
      "id": "V23-A08",
      "title": "End-to-end trace chain",
      "art_item": 8,
      "primary_gate": "deterministic",
      "pass_criteria": [
        "trace graph links operator.action -> mission.created -> scheduler.decision -> attempt.started -> inference.call|tool.effect -> artifact.stored -> acceptance.recorded",
        "trace is complete (no missing links) using durable ids"
      ],
      "deterministic_probe": "trace_chain"
    },
    {
      "id": "V23-A09",
      "title": "Failure truth: provider unavailable and worker loss",
      "art_item": 9,
      "primary_gate": "deterministic",
      "pass_criteria": [
        "decision is DEFER with deferred_resource_unavailable, never ADMIT",
        "ops events record the blocked state; no mock success"
      ],
      "deterministic_probe": "failure_truth"
    },
    {
      "id": "V23-A10",
      "title": "Zero-spend operator profile",
      "art_item": 10,
      "primary_gate": "deterministic",
      "pass_criteria": [
        "route with billing paid or unknown is denied with paid_route_forbidden",
        "no fallback to a paid route"
      ],
      "deterministic_probe": "zero_spend"
    },
    {
      "id": "V23-A11",
      "title": "Multi-process / private live evidence",
      "art_item": 0,
      "primary_gate": "multi_process_private",
      "status": "pending_owner_approval",
      "pass_criteria": ["ART protocol items 1, 4, 5, 9 repeated with separate processes on private infrastructure"],
      "deterministic_probe": null
    }
  ]
}
```
Validate both files parse:
```bash
python3 -c "import json;[json.load(open(p)) for p in ('config/v23/scheduler_policy.v1.json','benchmarks/v23_acceptance/scenarios.freeze.json')];print('json ok')"
```

### Step 3 — `docs/v2.3/STATUS.md` (replace the file, keeping one section)
Write this structure (fill `<BASE_SHA>` with the Setup SHA). If the file ends with a section titled `## Plan and owner decisions (2026-09-26)` (added by the plan commit), copy that section unchanged to the end of the new file.
```markdown
# SwarmAI V2.3 Status — scaffold; implementation in progress

Verified against `cursor/sw-v23-integration-460c` @ `<BASE_SHA>`. Plan: `docs/plans/v2.3/PLAN.md`.

## Truth table (16-item checklist from FUTURE_VERSION_EXIT_CHECKLISTS_20260921.md)
| # | Item | State | Evidence / gap | Session |
|---|---|---|---|---|
| 1 | scheduler state durable | scaffold | `controller/fairness.py` is an in-memory dict | W0-S2, W1-S2, W2-S1 |
| 2 | project-level fairness defined | scaffold | `debt += 1/weight`; ranking ignored by `ResourceAllocator` | W0-S1, W1-S1 |
| 3 | aging/priority deterministic | missing | no aging; priority not used | W1-S1 |
| 4 | reservation intent transactional / fail-closed | scaffold | `controller/reservations.py` in-memory | W1-S3, W2-S1 |
| 5 | provider/worker/tool capacity integrated | missing | | W2-S1, W3-S1 |
| 6 | backpressure bounded | scaffold | single floor value | W1-S1, W2-S1 |
| 7 | cancellation/drain fenced | scaffold | | W1-S1, W1-S3, W1-S7, W2-S1 |
| 8 | scheduler bound to SiteEpoch | missing | | W1-S4, W2-S1 |
| 9 | decision receipts emitted | scaffold | receipts in memory only | W0-S2, W1-S2, W2-S1 |
| 10 | capability packs lifecycle complete | scaffold | unkeyed sha256 "signature" (F-02) | W1-S5 |
| 11 | portability export/import complete | scaffold | key-name-only secret scan (F-03) | W1-S6 |
| 12 | observability read surface complete | scaffold | unscoped ops events (F-01) | W0-S3, W1-S8, W3-S1, W1-S12 |
| 13 | dashboard mutation uses action boundary | scaffold | assert helper only | W3-S1, W1-S12 |
| 14 | fleet placement/trust/locality complete | scaffold | first-candidate placement | W1-S7 |
| 15 | pathological deterministic suite passes | missing | | W2-S1, W3-S4 |
| 16 | multi-process/private evidence complete or honestly pending | pending | owner approval needed | W4-S1 |

## Not claimed
Nothing in V2.3 is accepted. Harness results never imply acceptance.
```

### Step 4 — `docs/v3.0/STATUS.md`
Keep the file, but replace any sentence claiming "implementation-complete" with: `V3.0 work is blocked on V2.3; existing V3 modules are scaffolds and are not claimed complete.` Do not delete other content.

### Step 5 — `CHANGELOG.md`
Find the line(s) claiming V2.3 (and V3.0) "implementation-complete" (around line 9). Replace the claim with `V2.3/V3.0: scaffolds only — see docs/v2.3/STATUS.md`. Add at the top under an `## Unreleased` heading (create it if missing):
```
- docs: corrected V2.3/V3.0 status claims (scaffold, not implementation-complete).
- config: froze scheduler policy `v23-wdrr-1` and V2.3 deterministic acceptance manifest.
```

### Step 6 — `docs/agents/CURRENT.md` and `docs/agents/context.json`
- Replace `dd7726eb8c22986ef72847994c8e435a81a869b6` with the Setup SHA everywhere in both files, and the subject line with the Setup commit subject.
- Frontmatter/JSON: `pause: false` (the plan commit already set it in `CURRENT.md`; set it in `context.json` if that file has a `pause` key), `v20_work: "V23_ENGINEERING_ACTIVE"`, `verified_at` to now (UTC).
- In `context.json` add a top-level key (keep valid JSON; check with `python3 -m json.tool docs/agents/context.json >/dev/null`):
```json
"v23": {
  "status": "scaffold_implementation_in_progress",
  "plan": "docs/plans/v2.3/PLAN.md",
  "policy": "config/v23/scheduler_policy.v1.json",
  "acceptance_freeze": "benchmarks/v23_acceptance/scenarios.freeze.json",
  "accepted": false,
  "pause_lift": "owner decision B-01, 2026-09-26 (docs/swarm-mvp/DECISIONS.md); engineering only; HL-01..HL-06 unchanged; HL-07 superseded for V2.3 sessions by C1 (PRs target cursor/sw-v23-integration-460c)"
}
```
- In `CURRENT.md` add a `## v23` section with the same facts as a table, directly above the plan commit's `## owner_decisions_20260926` section. Leave `hard_limits` unchanged.

### Step 7 — `docs/agents/RESUME.md`, `docs/agents/README.md`, `docs/agents/V20_TODO.md`
- `RESUME.md`: update the tip SHA; add one line near the top: `Active work: V2.3 per docs/plans/v2.3/PLAN.md on cursor/sw-v23-integration-460c; each session writes docs/v2.3/sessions/<ID>.md.`
- `README.md`: add `docs/plans/v2.3/PLAN.md` and `docs/v2.3/sessions/` to the file index.
- `V20_TODO.md`: in the table, set the "owner/next" note of V20-E03 → `SW-W1-S9 + SW-W3-S2`, E04 → `SW-W1-S10 + SW-W3-S2`, E05 → `SW-W1-S11 + SW-W2-S2 + SW-X1-S1`, E06 → `SW-W1-S4 + SW-W3-S2`, E07 → `SW-W2-S2 + SW-X2-S1 (fake first; live through SplitSignal after SP4)`, E08 → `SW-W1-S13`, E09 → `SW-W1-S12`, E10 → `SW-W3-S5`, E11 → `deferred`. Do not change their status column (they are still open).

### Step 8 — `docs/v2.3/sessions/README.md` (create)
```markdown
# V2.3 session handoffs
One file per session: `<SESSION_ID>.md` (for example `SW-W1-S1.md`), written by that session only.
Each handoff has: Done, Verification, Acceptance, Decisions, Needs other owner, Status.
Status is never "accepted"; Codex reviews each PR (owner decision D2).
```

### Section-5 acceptance
- [ ] Both JSON files exist and parse; `policy_version` is `v23-wdrr-1`; `version_claim_policy` is `never_mark_accepted_from_harness`.
- [ ] No file in the repo still says V2.3 or V3.0 is "implementation-complete" (`git grep -n -i "implementation-complete" -- docs CHANGELOG.md README.md` shows only historical/quoted lines or the new "not claimed" wording).
- [ ] `docs/agents/*` show the Setup SHA, `pause: false`, and a v23 block with `accepted: false`.
- [ ] `docs/plans/v2.3/PLAN.md` (from the plan merge) and `docs/v2.3/sessions/README.md` exist.
- [ ] No Python, test, workflow or lock file changed.

## 6. Verify (run exactly; all must pass)
```bash
git clean -fdX -- var/            # F-15: stale runtime state breaks re-runs
# Private database for this session: concurrent sessions on one host must never share one.
sudo -u postgres psql -c "CREATE DATABASE swarm_sw_w0_s1 OWNER swarm;" || true
export SWARM_DATABASE_URL=postgresql+psycopg://swarm:swarm@127.0.0.1:5432/swarm_sw_w0_s1
uv run ruff check .
uv run mypy src/swarm
uv run alembic heads               # must print exactly ONE line ending in (head)
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
git add docs/agents/CURRENT.md docs/agents/context.json docs/agents/RESUME.md docs/agents/V20_TODO.md docs/agents/README.md docs/v2.3/STATUS.md docs/v2.3/sessions/README.md docs/v3.0/STATUS.md CHANGELOG.md config/v23/scheduler_policy.v1.json benchmarks/v23_acceptance/scenarios.freeze.json docs/v2.3/sessions/SW-W0-S1.md
git status --porcelain            # nothing unexpected staged or left over
git commit -m "docs(v2.3): reset agent tracking, honest V2.3 status, freeze scheduler policy v23-wdrr-1 and acceptance manifest" -m "Session: SW-W0-S1. Plan: docs/plans/v2.3/PLAN.md."
git push -u origin cursor/v23-w0-s1-tracking-policy
gh pr create --draft --base cursor/sw-v23-integration-460c --head cursor/v23-w0-s1-tracking-policy --title "[SW-W0-S1] Tracking reset, lift-pause record, honest V2.3 status, frozen scheduler policy + acceptance manifest" --body-file docs/v2.3/sessions/SW-W0-S1.md
git ls-remote origin refs/heads/cursor/v23-w0-s1-tracking-policy   # must print the same SHA as: git rev-parse HEAD
```
If `gh pr create` is refused (read-only `gh`), the environment opens the PR: check that its base is `cursor/sw-v23-integration-460c` and that it is a draft, and put the PR URL (or the compare URL from section 10, step 4) into the handoff.
If push fails for network reasons, retry up to 4 times waiting 4 s, 8 s, 16 s, 32 s; then STOP (S8).
Docs to update: only your handoff file, plus any doc listed in section 3.

## 9. Handoff file (create before committing)
Create `docs/v2.3/sessions/SW-W0-S1.md` with exactly these headings:
```markdown
# SW-W0-S1 handoff
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
1. Commit whatever is complete inside your own files: `git add <your files> docs/v2.3/sessions/SW-W0-S1.md` then `git commit -m "WIP(SW-W0-S1): <one-line reason>"`.
2. Write the handoff (section 9) with `## Status` = `BLOCKED: <condition id> <one-line reason>`, and under `## Needs other owner` the exact file, function and change you need. Commit it.
3. Push: `git push -u origin cursor/v23-w0-s1-tracking-policy` (plus your suffix).
4. Open the draft PR against `cursor/sw-v23-integration-460c` with the title prefix `[BLOCKED]`, or record the compare URL `https://github.com/pri8771/swarmai/compare/cursor/sw-v23-integration-460c...cursor/v23-w0-s1-tracking-policy?expand=1` in the handoff.
5. End the session with a final message: the condition id, the reason, the branch and the head SHA.
Never work around a STOP by editing other files, weakening tests, or adding `skip`/`xfail`.

If `tests/tools/test_v20_cancel_killbound.py` fails once in the full run and you did not touch `sandbox_runner.py` or that test, re-run the full list once. If it passes, record both result lines in the handoff under Verification and continue; if it fails twice, STOP (S3). (The known race was fixed by SW-FIX-FLAKE; a new failure is worth reporting.)

## 11. Codex review packet (put this in the PR description and in the handoff)
```markdown
### Codex review packet — SW-W0-S1
- PR: <PR URL — fill in after the PR exists>
- Branch: <exact branch name>  Base: origin/cursor/sw-v23-integration-460c @ <base SHA from Setup>
- Head SHA: <output of `git rev-parse HEAD`; must equal `git ls-remote origin refs/heads/<branch>`>
- Diff for review: `git diff <base SHA>...<head SHA>`
- Files to review: `docs/agents/CURRENT.md`, `docs/agents/context.json`, `docs/agents/RESUME.md`, `docs/agents/V20_TODO.md`, `docs/agents/README.md`, `docs/v2.3/STATUS.md`, `docs/v2.3/sessions/README.md`, `docs/v3.0/STATUS.md`, `CHANGELOG.md`, `config/v23/scheduler_policy.v1.json`, `benchmarks/v23_acceptance/scenarios.freeze.json`, `docs/v2.3/sessions/SW-W0-S1.md`
- Review focus (AGENTS.md Code Review Rules): cross-tenant/project access; secret disclosure; financial accounting (unknown usage or cost is never zero); unbounded retries; silently changed model behaviour; recovery gaps after a crash/restart; unsupported release claims ("accepted", "complete"). Session-specific: status docs must not claim V2.3 done; pause lift cites the 2026-09-26 owner decision; the plan-branch merge commit is docs-only.
- Checks run: <paste the final result line of every command in section 6>
- Verdict requested: `RECOMMEND_ACCEPT <head SHA>` or `REQUEST_CHANGES` with file:line findings.
```
