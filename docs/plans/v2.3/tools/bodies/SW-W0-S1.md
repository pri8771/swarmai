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
{{FILE:config/v23/scheduler_policy.v1.json}}
```

### Step 2 — `benchmarks/v23_acceptance/scenarios.freeze.json` (create)
Paste this content, then replace the `frozen_at` placeholder with the current UTC time in ISO format (run `date -u +%Y-%m-%dT%H:%M:%S+00:00`).
```json
{{FILE:benchmarks/v23_acceptance/scenarios.freeze.json}}
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
