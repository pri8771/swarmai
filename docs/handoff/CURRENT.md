# Handoff — V1.4 zero-spend slice (off main)

**Date:** 2026-09-23  
**Branch:** `cursor/v1.4-zero-spend-slice-main` (off `main` @ `b9141fa`)  
**Operator request:** resume track (B) — live zero-spend / V1.4–V2 integration; **not** public launch  
**Spend:** `SWARM_ALLOW_PAID=false`; no purchases; OpenAI remains payment-gated  

## What this branch is

Smallest safe vertical slice from `cursor/v1.4-live-integration-11e2` **re-applied onto main**, not a blind merge of PR #14 / the unfinished V1.4 tip.

**Included (code + targeted tests):**
- G10 FIX-001–005 honesty path (auth isolation, scoped idempotency, fail-closed readiness, parser fixture-only, no known-answer, no auto-promote, FIX-003 evidence identity)
- Durable MissionStore + console live IDs + loopback private console bootstrap
- Brokered local inference + acceptance controls (local $0 path)
- FIX-004 hourly runner scripts (CLI login still **not** accepted)
- Gate / LEAD package docs for review (not lead acceptance)

**Excluded on purpose:**
- Full V1.4 docs/evidence bulk (eval-131 screening JSON, G11 LEAD-012 browser package, G12/G14 remote/live qual scripts)
- G13 qualification claim, live G14, LIVE-142
- Tag / publish / marketing / public launch

## Proof this session

| Check | Result |
|---|---|
| Targeted pytest (57) | **passed** |
| `ruff` / `mypy` on key modules | **passed** |
| `swarm release verify` | **fails honestly** — missing `var/evidence/offline_ci_pass.json` + `live_local_pass.json` bound to tip (FIX-003); packaging items ok |
| Live canary `rt_ollama_default` `--billing-known-zero` | **passed** → `live_local_zero_cost` (evidence: `var/onboarding/canaries/rt_ollama_gemma3_4b.json`) |

## Gates (honest)

| Gate | Slice advance | Still blocked |
|---|---|---|
| G10 | Source/control path landed on branch off main | Lead accept; FIX-004 Cursor CLI login |
| G11 | Durable missions + brokered local execute path | Lead accept; full LEAD-012 multisurface evidence package not re-landed |
| G12 | Local brokered inference only | Remote INF-121 dual |
| G13 | — | EVAL qualification |
| G14 / LIVE-142 | — | Live multi-planner / LIVE-142 |

See `docs/evidence/GATE_MATRIX.md`, `docs/evidence/V1_4_ABRUPT_STOP.md`, `docs/evidence/g10/LEAD_ACCEPT_PACKAGE.md`.

## Stop / next operator decision

- **Do not** merge to main, tag, or launch without explicit ask.
- Changes are **uncommitted** on this branch (per operator: commit only when asked).
- Suggested next: (1) commit this slice + bind CI/live evidence artifacts, or (2) continue live qual (Ollama mission E2E), or (3) switch to launch checklist track (A) — separate from this branch.
