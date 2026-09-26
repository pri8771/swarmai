# SwarmAI MVP / two-host + V2 + portable state

**Owner:** Cursor Project V2.0 eng (`bc-5513fdae-823c-5454-8e5f-91feccf64635`)  
**Integration:** `origin/dev` @ `dd7726eb8c22986ef72847994c8e435a81a869b6`  
**Active tracking branch:** `cursor/v20-tracking-tipsync-4635`  
**Updated:** 2026-09-25T21:10:00Z  
**Post-merge verify (portable):** PASS (Mac 2026-09-25T18:49Z; 78 passed @ older tip `f39e0032`)  
**FAST_TRACK tip CI:** green on merges #65 / #60 (2026-09-25T20:39Z)  
**Public hostname (deploy config):** `swarm.splitsignal.ai` (operator; freeze is **config-driven** — PORT-01 closed)  
**Loopback server:** `http://127.0.0.1:18766`  
**Versions accepted:** V1.7–V2.0 = **false**

## Mandate

Portable product + FAST_TRACK continue independent eng.  
User plan: Project Context `docs/v2-fast-track-plan.md` / `docs/v2-portable-product-plan.md`.  
Prior goal-pursuit plan remains for version meanings: `docs/v2-goal-pursuit-plan.md`.  
Execution map: `docs/swarm-mvp/EXECUTION_MAP.md`.  
Gap audit: Project Context `internal/v20-gap-audit.md`.

## Packet status

| Packet | Status | Notes |
|---|---|---|
| P00 | impl_complete | Docs + baseline frozen |
| TH-01–07 | eng_complete / **review-required** | Particular deployment evidence; R730 still blocked |
| R1–R9 foundation | eng landed on tip | R9 Linear residual |
| V1.7 | eng_landed | Mission path + R20-01 closed @ tip; **not accepted** |
| V1.8–V1.9 | eng_landed | Goals + pursuit; **not accepted** |
| V2.0 | eng_in_progress | L1–L6 on tip; remaining depth E03–E06+; **not accepted** |
| P01–P19 | planned / partial eng | Product spine |
| PORT-01 | **done** | PR #55; Mac verify PASS — defects closed |
| PORT-02 | **eng_done** | PR #57; matrix cells experimental (not `supported`) |
| PORT-03 | **eng_done** | PR #56; particular-deploy evidence external |
| PORT-04 | **eng_done** | PR #54; Docker two-container proven on Mac |
| PORT-05 | **eng_done** (continuous) | Tip-sync @ `dd7726eb`; keep refreshing |

## Gate snapshot

| Gate class | Status |
|---|---|
| Product correctness | PORT-01 closed; FT L1–L6 eng_landed; live adapter dispatch still missing (`blocked_missing_implementation`) |
| Supported-platform qualification | Linux container / enrollment **experimental** — do not claim `supported` |
| Particular deployment (R730/CF) | blocked — does not stop portable eng |
| Live inference | LiveGrant blocked; fake-upstream / preflight only (spend 0) |
| Independent review | required for version accept |
| Operator acceptance | not done |

## Checks this session (V20-E01 tip sync)

| Check | Result |
|---|---|
| Tip SHA recorded | `dd7726eb` (FAST_TRACK L1–L6 absorbed) |
| Prior portable verify | PASS @ `f39e0032` (retained; not re-run this pass) |
| Packet queue / matrix / Linear / STATE / EXECUTION_MAP | refreshed to tip honesty |
| Linear MCP | needsAuth (queue only) |
| Version accept flipped | **no** — remain false |
| False `supported` claims | **no** |

## FAST_TRACK (2026-09-25) — eng landed on tip

| Lane | PR | Status | Notes |
|---|---|---|---|
| L1 durable storage | #63 | **eng_landed** | File pursuit durability + DB-down fence; PG write-through still open (V20-E03) |
| L2 real pursuit / R20-01 | #65 | **eng_landed** | Ops `NativeMissionDispatchExecutor`; extract path proven; native model/tool loop open (V20-E05) |
| L3 workers / perms / cancel | #62 | **eng_landed** | Capability conjunction, enrollment fences, drain/revoke/rotate |
| L4 comms / memory / succession | #64 | **eng_landed** | Mailbox, layered memory, X/Y KT1/KT2 |
| L5 verify / accounting | #61 | **eng_landed** | Protected receipts; usage ledger process-local (V20-E04); LiveGrant preflight |
| L6 UI / SDK / Docker | #60 | **eng_landed** | Product compose + console/SDK control parity |

## Next action

Continue V2.0 eng depth from gap audit: E03 PG write-through → E04 ledger/lesson durability → E05 native model/tool loop (fake HTTP) → E06 coordinator singleton. Keep LiveGrant/operator/version-accept out of eng claims. Do not merge `main`.

## V2.3 plan and owner decisions (2026-09-26)

- Pause lifted by the owner (B-01). Decisions D1–D6 and C1–C5 are in `DECISIONS.md` DEC-V23-001.
- Plan: `docs/plans/v2.3/PLAN.md`; audit: `docs/plans/v2.3/AUDIT.md`. The truth table for V2.3 is `docs/v2.3/STATUS.md`, owned by SW-W0-S1/SW-W4-S1 on the integration branch.
- Integration: `cursor/sw-v23-integration-460c` (from `origin/dev` @ `8e1c0fde`). Session PRs target it; the owner merges it into `dev` (C1). `main` untouched.
- Only inference dependency: SplitSignal (D3), sync points SP1–SP6 (PLAN §5.2). Live use only in SW-X2-S1 under SW-PREAPPROVAL-A3.
- Versions accepted: none. Reviewer: Codex (D2).

## Next action (2026-09-26, supersedes the "Next action" above)

Owner: complete `docs/plans/v2.3/OWNER_PREFLIGHT.md`. Agents: run the remaining V2.3 waves from `docs/plans/v2.3/prompts/` on the integration branch, each wave followed by its `SW-MERGE-<wave>` prompt. V20-E03..E10 are covered by those sessions.
