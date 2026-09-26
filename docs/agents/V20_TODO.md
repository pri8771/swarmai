---
doc: agents_v20_todo
audience: ai_agent
eng_complete: false
accepted: false
tip: 8e1c0fdec24c131e7612d88076220945230f4c3b
harness: harness_ready_external_gates_blocked
verified_at: 2026-09-26T00:47Z
---

# V20_TODO

## verdict

| key | value |
|---|---|
| v20_eng_complete | false |
| accepted | false |
| s01_s11 | pass_deterministic |
| s12 | blocked_live_grant |
| spend_usd | 0.0 |

## remaining_eng

| id | pri | status | deps | owner_hint | deliverable |
|---|---|---|---|---|---|
| V20-E01 | P0 | in_progress | none | docs/PORT-05 | tip-sync owned by **#66** (MERGEABLE all-green); #68 WIP overlap — do not re-do STATE tip-sync here |
| V20-E02 | P0 | in_progress | offline CI or docs-only | docs | land FAST_TRACK docs via **#67**; plan source **#59** |
| V20-E03 | P1 | open | tip | SW-W1-S9 + SW-W3-S2 | PG write-through when db up: wire GoalAuthority/PursuitState repos (zero call sites today) |
| V20-E04 | P1 | open | E03 helpful | SW-W1-S10 + SW-W3-S2 | persist usage ledger holds + pursuit lessons across restart |
| V20-E05 | P1 | open | L3 fences present | SW-W1-S11 + SW-W2-S2 | bounded native model/tool loop behind fake HTTP (not extract-only) |
| V20-E06 | P1 | open | E03/E04 preferred | SW-W1-S4 + SW-W3-S2 | singleton coordinator pursuit service (HTTP tick ≠ scheduler) |
| V20-E07 | P1 | open | E05 preferred | SW-W2-S2 (fake/free first; live blocked) | live adapter after approved grant OR honest blocked_missing_implementation; fake/free first; no invent grant |
| V20-E08 | P2 | open | — | SW-W1-S13 | cancel child-process kill-bound ≤10s non-Python |
| V20-E09 | P2 | open | L3 APIs | SW-W1-S12 | console/SDK drain+revoke parity |
| V20-E10 | P2 | open | tip as-is | SW-W3-S5 | product compose full-path smoke (Docker); packaging-only ≠ smoke |
| V20-E11 | P2 | deferred | E03 | deferred | optional mailbox/succession PG tables |

## suggested_pr_order_dev_only

**Pause:** do not open new eng PRs for E03–E11 until resume.

1. Merge **#66** V20-E01 tip-sync (MERGEABLE all-green); reconcile/close **#68**
2. Merge **#67** V20-E02 or fix **#59**
3. After resume: V20-E03 PG write-through (+ start E04)
4. V20-E05 native model/tool loop fake HTTP
5. V20-E06 coordinator singleton
6. V20-E07 live adapter wire (grant-gated)
7. V20-E10 compose smoke evidence
8. V20-E09 console drain/revoke
9. V20-E08 cancel kill-bound
10. V20-E11 optional later

## do_not

| id | rule |
|---|---|
| DN-01 | reopen merged L1–L6 PRs |
| DN-02 | invent LiveGrant / flip accepted |
| DN-03 | merge main |
| DN-04 | treat harness_* as version accept |
| DN-05 | claim packaging validate as product compose smoke |
| DN-06 | job-bot work |

## operator_external_gates

| gate | status | blocks_eng |
|---|---|---|
| LiveGrant S12 | blocked | no |
| R730/CF/DNS two-host | blocked | no |
| elapsed reliability | not_started | no |
| independent review | required | no |
| operator version accept | false | no |
| Linear MCP live | needsAuth | no (queue only) |

## harness_cite

| check | result | cite |
|---|---|---|
| tip CI #65/#60 | green | gh @ 2026-09-25T20:39Z |
| acceptance S01–S11 | pass_deterministic | evidence @ tip |
| S12 | blocked_live_grant | ok=true; not fail |
| invent LiveGrant | refused | LiveGateBlocked |
| CandidateManifest tip bind | gap | frozen older sha → E01 |
