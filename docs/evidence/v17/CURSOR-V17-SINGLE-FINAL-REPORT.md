# CURSOR-V17-SINGLE — Final Report (implementation scope through V1.7)

**Session:** `CURSOR-V17-SINGLE`  
**Branch:** `cursor/v17-single-session`  
**Report tip (this document commit):** `7587d0264c04d41b368d836249cad0b6c66d7541`  
**V1.7 implementation tip:** `546a2cc8545154bb28cb70c785682162385bbc0c` (docs bind) / feat `1b1050d8087cb80ceb8e6706d93f8747f2504427`  
**Spend:** `$0.00` · `SWARM_ALLOW_PAID=false` · **no self-accept** · **no main merge** · **no V1.8+ in this session**

## Purpose

Maps every required artifact from V1.0-repair through V1.7 (per `VERSION_ARTIFACT_MATRIX.md` / `ARTIFACT_REGISTRY.json`) to an honest closeout state for this single-session lane:

| State | Meaning |
|-------|---------|
| **implemented** | Source landed on this branch |
| **evidence produced** | Evidence files on this branch |
| **reviewable** | Ready for independent lead review (not lead-accepted) |
| **blocked** | Cannot complete here (environment / external host / sealed data) |
| **external-acceptance pending** | Reviewable or prior evidence exists; lead accept not invented |
| **UNKNOWN** | Honest unknown (not claimed pass) |

Coordination registry statuses may lag this branch’s implementation reality; this report is the **session-authoritative closeout**.

---

## Executive summary

| Milestone | Session outcome |
|-----------|-----------------|
| V1.0 worker heartbeat normalization | **implemented** — single producer `com.swarmai.coord-heartbeat-v17`; ledger `CURSOR-V17-SINGLE` |
| V1.1–V1.2 (prior verified set) | **external-acceptance pending** / registry-verified where noted; not re-worked this session |
| V1.3 / ART-V13-TASK-POOL | **blocked** on Darwin (needs HOST-WIN-DEV); registry remains reviewable |
| V1.4 / ART-V14-REAL-E2E | **reviewable candidate** via `v14-real-005` pass; still **drafting** pending lead |
| V1.5 / ART-V15-* | **implemented + local evidence**; live multi-host **UNKNOWN** |
| V1.6 / ART-V16-* | **implemented + local evidence**; task quality **UNKNOWN** |
| V1.7 / ART-V17-* | **implementation-complete / reviewable candidate** tip `546a2cc` |

**Next (session stop):** Await independent lead review. Implementation scope through V1.7 is complete for this session. Do **not** start V1.8+ unless the operator expands scope.

---

## V1.0 repair — worker heartbeat normalization (single-session)

| Artifact | Session state | Notes / evidence |
|----------|---------------|------------------|
| ART-V10-CANDIDATE | external-acceptance pending (registry: verified) | Prior lane; not reopened |
| ART-V10-SECURITY | external-acceptance pending (registry: verified) | Prior lane |
| ART-V10-EVIDENCE-CONTRACT | external-acceptance pending (registry: verified) | Prior lane |
| ART-V10-RUNTIME-TRUTH | external-acceptance pending (registry: verified) | Prior lane |
| **ART-V10-WORKER-HEARTBEAT** / ops single-session | **implemented** + **evidence produced** | Producer label `com.swarmai.coord-heartbeat-v17` (loaded; not re-bootstrapped this closeout). Scripts: `scripts/coordination/heartbeat.py`, `install_heartbeat_macos.sh`. Coord ledger/status: `docs/coordination/heartbeats/CURSOR-V17-SINGLE.json`, `docs/coordination/status/CURSOR-V17-SINGLE.md`. Commit lineage includes `ed08880` feat(coordination) CURSOR-V17-SINGLE heartbeat. |

**Honest note:** Registry may still show ART-V10-WORKER-HEARTBEAT as `blocked` from legacy dual-host tooling; this session **normalized to exactly one producer** and publishes only the V17 ledger.

---

## V1.1 generic mission / V1.2 inference (matrix required set)

Not the active V17 product focus; recorded for completeness from registry + prior evidence on branch.

| Artifact | Registry (coord) | Session disposition |
|----------|------------------|---------------------|
| ART-V11-* (mission path, multisurface, control, restart, apply) | mostly verified | **external-acceptance pending** — prior evidence under `docs/evidence/g11`, `run-111`; tip binds historically (e.g. `ee5a066`, `48a02e3`) |
| ART-V12-BROKER-CONTRACT | verified | **external-acceptance pending** |
| ART-V12-PROVIDER-ELIGIBILITY | verified | **external-acceptance pending** |
| ART-V12-REMOTE-OVERLAP | blocked | **blocked** / not claimed this session |
| ART-V12-LOCAL-FALLBACK / ADMISSION-RECONCILIATION | drafting | **not claimed complete** this session |

Spend on this session’s work: **$0**.

---

## V1.3 qualification — ART-V13-TASK-POOL (G13)

| Artifact | Session state | Evidence / SHAs |
|----------|---------------|-----------------|
| ART-V13-QUAL-PROTOCOL | external-acceptance pending (registry: accepted) | Prior protocol; not reopened |
| **ART-V13-TASK-POOL** | **blocked** (HOST-WIN-DEV) + registry **reviewable** | `docs/evidence/g13/v17-mac-host-win-dev-blocker.json` — Darwin/arm64 must not impersonate Windows; held-out answers sealed; counted qualification prohibited until lead freeze |
| ART-V13-SCREENING-MATRIX | external-acceptance pending (registry: verified) | Prior screening docs under `docs/evidence/eval-131` |
| ART-V13-QUALIFIED-MATRIX | blocked / drafting | Depends on HOST-WIN-DEV freeze + sealed reference |
| ART-V13-OVERHEAD-REPORT | planned | **not implemented** this session |
| ART-V13-REVIEWER-QUALIFICATION | drafting | Machinery only if offline; no held-out open |

**Blocker (frozen):** G13 HOST-WIN-DEV executable verification not captured on this host.

---

## V1.4 elastic swarm — ART-V14-REAL-E2E (and related)

| Artifact | Session state | Evidence / SHAs |
|----------|---------------|-----------------|
| **ART-V14-REAL-E2E** | **reviewable candidate**; **external-acceptance pending** (drafting awaiting lead) | Successful run: `docs/evidence/v14-real-e2e/v14-real-005/` — `manifest.json` status **pass**, `candidate_sha` `9e82a5c…`, spend `$0`. Bind: `1c63159`, restore `fe6acbf`. Earlier fails preserved as honest history (002–004). |
| ART-V14-GRAPH-CONTRACT | reviewable (registry) | Not re-proved this session |
| ART-V14-ROLE-MANIFEST / LIVE-ADAPTIVE-PROOF | blocked (registry) | **blocked** — not claimed |
| ART-V14-LOAD-10-50-100 | reviewable (registry) | Not re-run this session |
| ART-V14-MODE-COMPARISON | planned | **not implemented** |
| ART-LIVE142-* | protocol accepted; campaign blocked; final report planned | Live campaign **not** claimed |

**Frozen:** ART-V14 real E2E remains drafting pending independent lead review — **no self-accept**.

---

## V1.5 distributed workers — ART-V15-* (Phase B / V2A-003–005)

| Artifact / packet | Session state | Evidence path | Candidate SHA |
|-------------------|---------------|---------------|---------------|
| ART-V15-DURABLE-SCHEMA / lease schema | implemented + evidence | `docs/evidence/v15/v2a003a-lease-fencing-schema.json` | `630ab78…` |
| ART-V15-LEASE-FENCING repair (003a-R) | implemented + evidence | `v2a003a-r-lease-foundation-repair.json` | `92f59fa…` |
| ART-V15-LEASE-FENCING claim/renew/expire (003b) | implemented + evidence | `v2a003b-lease-claim-renew-expire.json` | `7dcefe4…` |
| ART-V15-LEASE-FENCING result accept (003c / B1) | implemented + **reviewable** local | `v2a003c-result-acceptance-fence.json` | `ddd96a6…` |
| ART-V15-WORKER-PROTOCOL (004 / B2) | implemented + **reviewable** local | `v2a004-worker-service-client.json` | `a26f21a…` |
| ART-V15-RECOVERY-EVIDENCE harness (005 / B3) | implemented harness; **live multi-host UNKNOWN** | `v2a005-multihost-recovery-harness.json` status `harness_pass_live_multihost_UNKNOWN` | `ab6cd8d…` |
| ART-V15-MULTIHOST-EVIDENCE | **blocked / UNKNOWN** | No live dual-host claim | — |
| ART-V15-ARCH / DBOS-REUSE | drafting docs / prior decisions | Under `docs/artifacts` donors / ADRs | — |

**Tests (representative):** worker/knowledge suites green on branch during Phase B/C (e.g. `tests/workers/`, `tests/integration/db/` lease fencing).  
**Frozen:** B3 live multi-host remains **UNKNOWN**.

---

## V1.6 scoped knowledge — ART-V16-* (Phase C / V2B-003a–e)

| Artifact / packet | Session state | Evidence path | Candidate SHA |
|-------------------|---------------|---------------|---------------|
| ART-V16-DURABLE-SCHEMA / knowledge repo (003a / C1) | implemented + **reviewable** local | `docs/evidence/v15/v2b003a-knowledge-repository.json` | `7f86981…` |
| ART-V16-PERMISSION-RETRIEVAL (003b / C2) | implemented + evidence | `v2b003b-permission-first-retrieval.json` | `198df7f…` |
| ART-V16-SUPERSESSION / lifecycle (003c / C3) | implemented + evidence | `v2b003c-knowledge-lifecycle.json` | `198df7f…` |
| ART-V16-PROVENANCE / MemoryStore adapter (003d / C4) | implemented + evidence | `v2b003d-memorystore-adapter.json` | `198df7f…` |
| ART-V16-CONTEXT-BUDGET-EVIDENCE (003e / C5) | implemented budget math; **task quality UNKNOWN** | `v2b003e-context-budget.json` | `198df7f…` |
| ART-V16-KNOWLEDGE-CONTRACT | drafting design + implemented contracts in `src/swarm/contracts/knowledge.py` | Donor + code | tip through `d4440bf` bind |

**Tests:** knowledge suite exercised during C landings (`tests/knowledge/`).  
**Honest UNKNOWN:** live **task quality** eval not claimed.

---

## V1.7 tools / browser — ART-V17-* (Phase D / V2B-004a–e)

| Artifact (matrix) | Session state | Mapping |
|-------------------|---------------|---------|
| ART-V17-DURABLE-EFFECT-SCHEMA | **implemented** + migration | Alembic `a17effect004a0001`; models `ApprovalRow` V17 cols + `ActionEffectRow`; `DurableEffectRepository` |
| ART-V17-TOOL-CONTRACT / TOOL_PERMISSION_CONTRACT | **implemented** + donor on branch | `docs/artifacts/future/ART-V17-TOOL_PERMISSION_CONTRACT.md` + `ConsequentialToolGateway` |
| ART-V17-APPROVAL-BINDING | **implemented** | `docs/artifacts/future/ART-V17-APPROVAL_BINDING.md` + exact binding in gateway |
| ART-V17-INTEGRATION-MANIFEST | **implemented** (three classes) | Local sandbox, API/MCP-style, browser/session-aware simulator |
| ART-V17-SESSION-RECOVERY | **implemented** | `SessionRecoveryService` — login ≠ submit |
| ART-V17-PERMISSION-NEGATIVES | **implemented** + tests | `tests/tools/test_v17_gateway_negatives.py` |

**Aggregate evidence:** `docs/evidence/v17/v2b004a-e-action-gateway.json`  
**Packets:** V2B-004a–e · **Phase D1–D5**  
**Feat SHA:** `1b1050d` · **Tip bind:** `546a2cc`  
**Tests:** `pytest tests/tools/` → **24 passed**; ruff pass; mypy pass (9 source files)  
**Status:** **implementation-complete / reviewable candidate** — **no self-accept**

**Remaining (non-blocking for Sp2 reviewable):** optional `ActionAttemptRow`; central API/CLI wiring; live multi-host durable-effect crash (inherits B3 UNKNOWN); browser = session-aware simulator not live browser automation.

---

## Spend, policy, and non-claims

- **Spend USD:** `0.0` throughout CURSOR-V17-SINGLE evidence cited above  
- **`SWARM_ALLOW_PAID`:** `false`  
- **No self-accept** of ART-V14 / ART-V15 / ART-V16 / ART-V17  
- **No merge to main** / no force-push  
- **No V1.8+** (recovery/site-epoch, V1.9, V2.0 integrated candidate) in this session

---

## Artifact → disposition quick index

| ID | Disposition |
|----|-------------|
| ART-V10-WORKER-HEARTBEAT (single-session) | implemented |
| ART-V13-TASK-POOL | blocked (HOST-WIN-DEV); registry reviewable |
| ART-V14-REAL-E2E | reviewable candidate; external-acceptance pending |
| ART-V15-LEASE-FENCING / WORKER-PROTOCOL | implemented + local evidence / reviewable |
| ART-V15-MULTIHOST / live B3 | UNKNOWN |
| ART-V15-RECOVERY-EVIDENCE | harness implemented; live UNKNOWN |
| ART-V16-* C1–C5 | implemented + local evidence; task quality UNKNOWN |
| ART-V17-* D1–D5 | reviewable candidate tip `546a2cc` |

---

## Closeout statement

**CURSOR-V17-SINGLE implementation scope is stopped pending independent lead / operator review.**  
This report satisfies the session completion requirement to publish a final artifact-by-artifact map through V1.7. Further product work (V1.8+) requires an explicit operator scope expansion.

*Generated for coordination closeout — documentation only; does not invent lead acceptance.*
