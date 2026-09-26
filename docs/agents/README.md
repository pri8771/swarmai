---
doc: agents_index
audience: ai_agent
sot: docs/agents/
base_branch: dev
forbid_base: main
verified_tip: 8e1c0fdec24c131e7612d88076220945230f4c3b
verified_at: 2026-09-26T00:47Z
pause: false
---

# agents SoT index

Primary session handoff for AI agents. Prefer this tree over human essays in Project store.

## read_order

1. `CURRENT.md` — tip SHA, limits, accept flags, pause
2. `V17_DONE.md` — completed V1.7 eng packets/PRs/evidence
3. `V20_TODO.md` — remaining eng IDs V20-E01…E11
4. `RESUME.md` — exact next steps
5. `context.json` — same facts machine-parseable
6. `docs/v2.3/PLAN.md` — V2.3 multitask plan
7. `docs/v2.3/sessions/` — per-session V2.3 handoffs

## related_repo_sot_stale

| path | tip_bound | note |
|---|---|---|
| `docs/swarm-mvp/STATE.md` | `f39e0032` on tip | stale vs `dd7726eb`; tip-sync = V20-E01 |
| `docs/swarm-mvp/PACKET_QUEUE.json` | `f39e0032` on tip | stale; `versions_accepted` all false |
| `docs/v2.0/STATUS.md` | tip | keep `accepted: false` |
| `docs/swarm-mvp/CURSOR_FAST_TRACK.md` | absent on tip | lives on PR #59 / #67 |

## open_prs_dev_related

| pr | draft | topic | status | note |
|---|---|---|---|---|
| #59 | true | plan FAST_TRACK | open | plan; offline CI historically fail |
| #66 | true | V20-E01 tip-sync | open MERGEABLE all-green | **owns** STATE/PACKET_QUEUE tip-sync — do not duplicate |
| #67 | true | V20-E02 FAST_TRACK docs | open | extract from #59 |
| #68 | true | V20-E01 pause WIP | open | CandidateManifest rebind; reconcile vs #66 |

## pause_scope

- V20 eng lanes E03–E11: **do not start**
- This tree: session handoff only; not a tip-sync of `docs/swarm-mvp/`

## status_enum

`done` | `in_progress` | `open` | `blocked` | `deferred`
