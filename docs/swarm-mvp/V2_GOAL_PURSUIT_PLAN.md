# SwarmAI V2.0 goal-pursuit plan

**Date:** 2026-09-25  
**Status:** active — operator mandate supersedes stop-after-foundation; **portable product mandate** now active for independent eng (see Project Context `docs/v2-portable-product-plan.md`)  
**Repo:** `pri8771/swarmai`  
**Integration branch:** `dev` @ `58f72fa5`  
**Hostname:** deploy may use `swarm.splitsignal.ai` (operator-clarified; not `.com`); freeze must not hardcode (PORT-01)  
**Do not:** implement V3/V4; merge to `main`; spend money; publish without auth; claim V1.7–V2.0 accepted  
**Portable packets:** PORT-01–05 in `docs/swarm-mvp/PACKET_QUEUE.json` / `EXECUTION_MAP.md`

## Mandate summary

Continue through a working, reviewable **V2.0 goal-pursuit product**. Closing R1–R9 is the first gate, not the finish line. Preserve valid review findings, evidence rules, and ownership boundaries from the 2026-09-25 Cursor review of PR #44 @ `180eb73a`.

Review provenance (Mac bundle):  
`/Users/pchordia/Documents/Codex/2026-09-24/referenced-chatgpt-conversation-this-is-an/outputs/`  
Imported under repo `docs/reviews/CURSOR_REVIEW_2026-09-25/`.

## Version meanings (authoritative)

| Version | Responsibility | Exit signal |
|---|---|---|
| **Foundation (R1–R9)** | Trustworthy local operational path | Protected regressions green; no forged completion; durable authority on HTTP path |
| **V1.7** | Complete the mission | Human goal → plan → execute → artifacts → protected verify → accept/blocker; ≥1 native model-backed mission on authorized route |
| **V1.8** | Durable goals across missions | Persistent Goal entity; pause/resume/cancel/restart; mission ≠ goal achievement |
| **V1.9** | Autonomously pursue the goal | Bounded observe→assess→propose→execute→verify→adapt loop; evaluated lessons |
| **V2.0** | Integrated usable product | UI/SDK goal create → agents → resources → progress/blockers → interrupt/resume → verified outcomes |
| **V3.0 / V4.0** | Multi-goal / delegated ops | **Future only — do not implement** |

Note: the independent review’s cumulative 0.1 roadmap (V1.0–V2.0 packaging labels) remains useful as a capability checklist, but **version names follow this mandate**.

## Execution order

1. **Reconcile one execution map on `dev`** — TH/P packets + redesign planning branch as donor input only; no competing backlog.
2. **Close R1–R9** with protected regressions converted from review probes.
3. **V1.7 → V1.8 → V1.9 → V2.0** with checkpoint evidence after each.
4. Freeze V2.0 acceptance scenarios before claiming campaign runs.

## R1–R9 disposition targets

| ID | Defect | Fix direction |
|---|---|---|
| R1 | Mission acceptance forged via worker `required_checks` | Freeze verifier specs; bind to attempt/artifact; reject overrides |
| R2 | HTTP path uses in-memory authority | Wire API/connector to durable PG; continuous lease loop |
| R3 | Artifact metadata lost across writers/retries | Locked/merge-safe index; durable idempotency; immutable IDs |
| R4 | Deleted artifact content still served | Enforce tombstone/scope on every content read |
| R5 | Grader spoof + weak sandbox | Verifier-owned verdict; OS isolation |
| R6 | Native admitted with unproven caps | Admission from proven capabilities only |
| R7 | Ruff/mypy/CI failures | Repair without weakening; PG integration job |
| R8 | Zero-$ grant rejected; unreproducible report hash | Allow free-route zero grants + ceilings; freeze timestamps |
| R9 | Tracking/packaging/hash drift | Manifest refresh; scoped connector mounts; Linear queue |

## Packet reconciliation

| Source | Role |
|---|---|
| TH-01–07 | Two-host deployment increments — **eng evidence retained**; disputed acceptance returned to **review-required** until R1–R4 closed |
| P00–P19 | Product MVP packets — remain the product build spine |
| `plan/swarmai-v2-redesign-20260925` | Planning donor only (97 packets); map requirements; do not replace contracts or run as parallel authority |

## Deployment / access gates (continue Mac eng)

| Gate | Status | Policy |
|---|---|---|
| Mac loopback server | available | Primary eng surface |
| R730 | blocked | Record separately; no two-host claim from two local processes |
| DNS/CF `swarm.splitsignal.ai` | blocked | Config external; no publish without auth |
| Linear MCP | needsAuth | Reconciliation queue only |
| Live provider / paid | blocked | Fake upstreams + free-only; no silent paid fallback |

## Acceptance discipline

Separate explicitly:

1. **Product correctness** (portable eng — PORT-*)  
2. **Supported-platform qualification**  
3. **Particular deployment** (R730/CF — does not block generic eng)  
4. **Live inference** (LiveGrant only)  
5. **Independent review**  
6. **Operator acceptance**

Code existing ≠ version accepted. No self-approval where independent review is required.  
Portable plan: Project Context `docs/v2-portable-product-plan.md`.

### V2.0 acceptance campaign freeze (Lane F)

**Freeze ID:** `v20-acceptance-campaign-20260925`  
**Catalog:** `benchmarks/v20_acceptance/scenarios.freeze.json`  
**Doc:** `docs/v2.0/ACCEPTANCE_CAMPAIGN.md`  
**Harness:** `src/swarm/acceptance/` · `uv run swarm acceptance run`

| Gate | Meaning | Campaign default |
|---|---|---|
| deterministic | Local mechanics / fake upstreams | Executable product probes (S01–S11; scaffolds retired) |
| live | Approved LiveGrant only | Blocked — never invented |
| host | R730 / two-host / DNS | Blocked — two local processes ≠ proof |
| elapsed | Wall-clock reliability | Not started — never simulated |

| Version | Required §10 scenarios | Accepted by harness |
|---|---|---|
| V1.7 | V20-S05, S06, S07, S08, S12 | **false** |
| V1.8 | V20-S01, S03, S04, S08, S09 | **false** |
| V1.9 | V20-S01–S05, S08–S10 | **false** |
| V2.0 | V20-S01–S12 | **false** |

Scenarios frozen before campaign reliance: finite multi-mission goal; failed approach→strategy change; ongoing goal across cycles; blocked then available prerequisite; collaboration+bounded delegation; context succession; server restart/worker disconnect/stale return; duplicate triggers/lost acks; pause/redirect/cancel/budget exhaustion; memory correction/lesson rollback; SDK/UI parity; authorized model/tool execution with artifacts.

## Checkpoints to publish

After each major gate: branch SHA, R-matrix or version matrix, evidence paths, CI results, remaining blockers, Linear queue status.
