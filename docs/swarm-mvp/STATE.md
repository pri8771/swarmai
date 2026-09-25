# SwarmAI MVP / two-host + V2 + portable state

**Owner:** Cursor Project P5 tracking (`bc-3f6eb213-782f-56a7-b1bc-50935cbe3ac7`)  
**Integration:** `origin/dev` @ `58f72fa59691a3fd2af53c501598ffa225fdd9cc`  
**Active tracking branch:** `cursor/v2-portable-tracking-3ac7`  
**Updated:** 2026-09-25T18:29:00Z  
**Public hostname (deploy config):** `swarm.splitsignal.ai` (operator; **not** product hardcoded truth — PORT-01)  
**Loopback server:** `http://127.0.0.1:18766`  
**Versions accepted:** V1.7–V2.0 = **false**

## Mandate

Portable product mandate supersedes “wait on LiveGrant / eng exhausted” for independent eng.  
User plan: Project Context `docs/v2-portable-product-plan.md`.  
Prior goal-pursuit plan remains for version meanings: `docs/v2-goal-pursuit-plan.md`.  
Execution map: `docs/swarm-mvp/EXECUTION_MAP.md`.

## Packet status

| Packet | Status | Notes |
|---|---|---|
| P00 | impl_complete | Docs + baseline frozen |
| TH-01–07 | eng_complete / **review-required** | Particular deployment evidence; R730 still blocked |
| R1–R9 foundation | eng landed on tip | R9 Linear residual |
| V1.7–V2.0 | eng present | **not accepted** |
| P01–P19 | planned / partial eng | Product spine |
| PORT-01 | **open** | P1 defects |
| PORT-02 | **open** | P2 generic roles |
| PORT-03 | **open** | P3 install docs |
| PORT-04 | **open** | P4 portability tests |
| PORT-05 | **in_progress** | P5 this tracking pass |

## Gate snapshot

| Gate class | Status |
|---|---|
| Product correctness | portable defects open (PORT-01+) |
| Supported-platform qualification | Linux container baseline in progress |
| Particular deployment (R730/CF) | blocked — does not stop PORT eng |
| Live inference | blocked_live_grant / LiveGrant |
| Independent review | required for version accept |
| Operator acceptance | not done |

## Checks this session (P5)

| Check | Result |
|---|---|
| Tip SHA recorded | `58f72fa5` |
| Portable plan written (Context) | `docs/v2-portable-product-plan.md` |
| Packet graph / queue / matrix / Linear queue | updated in repo |
| Linear MCP | needsAuth (queue only) |
| Version accept flipped | **no** — remain false |

## Next action

P1–P4 land PORT-01–04; consolidate merges green PRs to `dev`; P5 refreshes tracking after each land.
