---
doc: agents_current
audience: ai_agent
repo: pri8771/swarmai
verified_at: 2026-09-25T21:07Z
pause: true
v20_work: STOPPED
---

# CURRENT

## refs

| key | value |
|---|---|
| origin/dev | `dd7726eb8c22986ef72847994c8e435a81a869b6` |
| origin/dev_subject | Merge PR #60: feat(L6) product Compose console + SDK/UI control parity |
| origin/main | `08b910f981eff2ab66873a71055090f2c60f2a91` |
| origin/main_status | UNTOUCHED |
| alembic_head | `a20pursuitpersist0001` |

## version_flags

| key | value | cite |
|---|---|---|
| v17_eng | done | tip `dd7726eb`; not operator/version accepted |
| v17_accepted | false | harness + matrices |
| v20_eng_complete | false | gap audit @ tip |
| v20_harness | `harness_ready_external_gates_blocked` | S01–S11 green; S12 `blocked_live_grant` |
| v20_accepted | false | explicit |
| versions_accepted.V1.7 | false | |
| versions_accepted.V1.8 | false | |
| versions_accepted.V1.9 | false | |
| versions_accepted.V2.0 | false | |
| any_version_accepted | false | |

## hard_limits

| id | rule |
|---|---|
| HL-01 | no merge to `main` |
| HL-02 | no paid / public deploy / account creation |
| HL-03 | LiveGrant fail-closed; do not invent |
| HL-04 | job-bot out of scope |
| HL-05 | LiveGrant / R730 / CF / Linear mutations = deploy/live-only gates; eng may proceed without them |
| HL-06 | do not claim version-accepted from harness_* |
| HL-07 | PRs target `dev` only |

## fast_track_merged_order

| order | pr | lane | merge_sha | on_tip |
|---|---|---|---|---|
| 1 | #61 | L5 verify/accounting | `c294d8ca` | true |
| 2 | #63 | L1 durable storage | `3357d944` | true |
| 3 | #62 | L3 workers/perms | `53401981` | true |
| 4 | #64 | L4 comms/memory | `45efb242` | true |
| 5 | #65 | L2 R20-01 pursuit | `ad0ed567` | true |
| 6 | #60 | L6 UI/SDK/Docker | `dd7726eb` | true (=tip) |

## r20_defects

| id | status | note |
|---|---|---|
| R20-01 | done | ops `NativeMissionDispatchExecutor`; `RecordingExecutor` fixture/mock only |
| R20-02 | done | #61 protected verification |
| R20-03 | done | #62 capability/path |
| R20-04 | done | file durable + clock; PG write-through still open → V20-E03 |
| R20-05 | done | #62 enrollment qualification |

## mission_path

| field | value |
|---|---|
| status | tip_proven |
| tip | `dd7726eb` |
| path | claim → execute → CAS → protected verify |
| evidence | `tests/mission/test_v17_mission_path.py` (+ related) 17 passed @ tip |

## pause_state

| field | value |
|---|---|
| operator | STOP V2.0 eng; push session state |
| eng_lanes | do_not_restart |
| resume | see `RESUME.md` |
| sot | `docs/agents/` (this tree) |
| tip_sync_pr | #66 |
| related_open | #59 #66 #67 #68 |
