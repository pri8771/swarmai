---
doc: agents_resume
audience: ai_agent
pause: false
base: origin/dev
tip_floor: 8e1c0fdec24c131e7612d88076220945230f4c3b
accepted: false
---

# RESUME

Active work: V2.3 per docs/v2.3/PLAN.md; each session writes docs/v2.3/sessions/<ID>.md.

Next step: Codex review of the V2.3 candidate range on `cursor/sw-v23-integration-460c`; SW-X2-S1 (SplitSignal live smoke, SP4–SP6); owner merges `cursor/sw-v23-integration-460c` into `dev`; owner decision on the V23-A11 multi-process gate (SW-PREAPPROVAL-A5). SW-X1-S1 (SplitSignal adapter) is merged (`2b27bc20`) after SP1/SP2; SP3–SP6 pending. Follow-up fixes SW-FIX-RETRY/COMPOSE/ALEMBIC/FLAKE are merged into the integration branch (tip `1b3f48ad`) and need Codex review.

## preflight

```text
git fetch origin dev main
git rev-parse origin/dev
# must be >= 8e1c0fdec24c131e7612d88076220945230f4c3b
git rev-parse origin/main
# must remain 08b910f981eff2ab66873a71055090f2c60f2a91 unless operator moves it
```

Read order: `CURRENT.md` → `V17_DONE.md` → `V20_TODO.md` → this file → `context.json`.

## pause_now

| key | value |
|---|---|
| v20_eng_lanes | STOPPED — do not start E03–E11 code work this pause |
| this_pr_scope | `docs/agents/` only |
| tip_sync_owner | PR #66 (do not duplicate STATE/PACKET_QUEUE/EXECUTION_MAP tip-sync) |
| manifest_wip | PR #68 (CandidateManifest rebind; overlaps E01) |
| fast_track_docs | PR #67 (+ plan #59) |

## first_actions_when_resume_eng

| step | action | status_hint |
|---|---|---|
| 1 | Confirm tip ≥ `dd7726eb`; ignore stale `f39e0032` tracking until #66 lands | required |
| 2 | Merge/close E01: prefer #66 (all-green MERGEABLE); reconcile/supersede #68 | P0 — not this agents PR |
| 3 | E02: merge #67 or fix #59 offline CI | P0 parallel |
| 4 | Next depth eng only after pause lifted: **V20-E03** or **V20-E05** | P1 — blocked until resume |
| 5 | Keep `accepted: false` / `versions_accepted: false` | mandatory |

## branch_policy

| rule | value |
|---|---|
| branch_from | `origin/dev` |
| pr_base | `dev` |
| pr_base_forbid | `main` |
| force_push | forbid |
| small_prs | required |

## verify_minimal

```text
uv run pytest tests/mission/test_v17_mission_path.py \
  tests/pursuit/test_protected_verification.py \
  tests/mission/test_v17_protected_verify.py \
  tests/pursuit/test_pursuit_durability.py -q
# expect 17 passed on tip floor

# after eng changes: targeted suite for touched packages + required CI
```

## stop_conditions

| if | then |
|---|---|
| tip moved past `dd7726eb` | re-verify; update `CURRENT.md` + `context.json` SHAs |
| LiveGrant requested | refuse invent; wait operator-approved grant |
| urge to merge main | refuse |
| urge to flip accepted | refuse |

## pointers

| what | where |
|---|---|
| this SoT | `docs/agents/` |
| stale tracking | `docs/swarm-mvp/STATE.md` (fix via E01) |
| acceptance status | `docs/v2.0/STATUS.md` |
| open FT plan | PR #59 |
