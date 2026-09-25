# SwarmAI MVP / two-host + V2 + portable state

**Owner:** Cursor Project P5 tracking (`bc-e1ed8584-abe5-5d33-94cb-2ea10d429bf5`)  
**Integration:** `origin/dev` @ `f39e003249b73849a699bb554dddcdfbfffa502c`  
**Active tracking branch:** `cursor/v2-portable-tracking-9bf5`  
**Updated:** 2026-09-25T18:55:00Z  
**Post-merge verify:** PASS (Mac 2026-09-25T18:49Z; 78 passed)  
**Public hostname (deploy config):** `swarm.splitsignal.ai` (operator; freeze is **config-driven** — PORT-01 closed)  
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
| PORT-01 | **done** | PR #55; Mac verify PASS — defects closed |
| PORT-02 | **eng_done** | PR #57; matrix cells experimental (not `supported`) |
| PORT-03 | **eng_done** | PR #56; particular-deploy evidence external |
| PORT-04 | **eng_done** | PR #54; Docker two-container proven on Mac |
| PORT-05 | **in_progress** | Tip-sync refresh this branch after verify PASS |

## Gate snapshot

| Gate class | Status |
|---|---|
| Product correctness | PORT-01 defects **closed**; live adapter dispatch still missing (`blocked_missing_implementation`) |
| Supported-platform qualification | Linux container / enrollment **experimental** — do not claim `supported` |
| Particular deployment (R730/CF) | blocked — does not stop portable eng |
| Live inference | LiveGrant blocked; fake-upstream wiring proven (spend 0) |
| Independent review | required for version accept |
| Operator acceptance | not done |

## Checks this session (P5 tip sync)

| Check | Result |
|---|---|
| Tip SHA recorded | `f39e0032` (≥ verify tip) |
| Post-merge verify handoff | PASS — Context `internal/v2-portable-post-merge-verify-handoff.md` |
| Packet queue / matrix / Linear / STATE / EXECUTION_MAP | refreshed to eng-landed honesty |
| Linear MCP | needsAuth (queue only) |
| Version accept flipped | **no** — remain false |
| False `supported` claims | **no** |

## FAST_TRACK (2026-09-25)

| Lane | Status | Notes |
|---|---|---|
| L4 comms/memory/succession | **eng_in_progress** | Durable authenticated mailbox, layered memory provenance, X/Y KT1/KT2 fencing on branch `cursor/v2-ft-comms-memory-4a67` — not version-accepted |

## Next action

Keep live path honest (optional dispatcher only with authentic LiveGrant). Independent review + operator accept remain promotion gates. Do not merge `main`. Particular R730/CF/DNS evidence remains external. Coordinator integrates FAST_TRACK lane PRs → `dev`.
