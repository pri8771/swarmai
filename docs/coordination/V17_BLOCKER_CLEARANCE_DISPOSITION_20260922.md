# V1.7 blocker-clearing disposition — 2026-09-22

Lead: ChatGPT engineering/product lead / formal acceptance authority
Owner directive: docs/coordination/OWNER_TARGET_V17_20260922.md@8cd88f0
Status: V1.7 ONLY / ENGINEERING RESUMED / LIVE & EXTERNAL GATES PRESERVED

This package supersedes the V2.0 pause for SwarmAI. V2.0/V2.3/V2.7/V3.0 are deferred. Stop forward engineering when V1.7 is genuinely accepted.

Codex is the single direct integrator. Claude/Fable handoff is complete. Preserve the one existing watcher/heartbeat producer if it exists; do not create, dispatch or modify a watcher/timer/scheduler.

No fresh model/provider/session/network/public-action/spend/main-merge grant is created here. CP1 remains exhausted. R33c public target approval-in-principle is not an execution grant.

## Formal verdict — PR28 R30b-P0

Exact source: 11bd4b5276458b2b7adc11528f117e919524f035
Tree: 33990992110084694910819d765361a50afa2762
Base: accepted 6dbf8c43463cbdbd8c87561af2abcdde59969765
Decision: BOUNDED PREREQUISITE ACCEPTED

Accepted: canonical payload integrity at execute/reconcile entry; empty hashes still fill; custom effect_key remains legal; execution_attempt is runtime-only and comes from durable attempt_count for execute/reconcile/retry; caller-supplied attempt metadata is not authority.

Evidence: red-on-base 7 intended failures; focused PG 38; full PG 623/13 live-UI skips, cleanup0/public tables0; full offline 427/209; mypy174; touched Ruff/format clean; independent multi-lens review; offline composition scratch with accepted fb58a751 437/211/0.

### Mandatory make_approval integrity follow-up

P0 identified a remaining seam: make_approval calls ensure_hashes but does not reject a supplied stale non-empty payload hash before minting a grant.

Disposition: REQUIRED ON THE V1.7 COMPOSITION TIP before that tip can be accepted.

Exact scope: call the same canonical payload-integrity check in make_approval immediately after actor/project context authorization and before ensure_hashes/grant construction/store write; stale non-empty hash plus changed payload or destination must fail payload_hash_mismatch and create no approval; empty hash remains fillable; valid custom effect_key remains legal. No effect-key canonicalization or adapter-mutation recheck.

## Formal verdict — PR29 inherited Ruff fix

Exact source: 349c732c335d83eaa431d30ea7f2b52b8d4431a3
Decision: ACCEPTED — MECHANICAL LINT SLICE

The only production change is import ordering in src/swarm/api/store.py. Hosted public Actions run 35767004625 is green. Local evidence reports full owned PostgreSQL 616/13 cleanup0; offline 421/208; mypy174. Public Actions omits PostgreSQL integration, so one owned-PG run on the final composed V1.7 tip remains mandatory.

## Composition freeze

Create one isolated composition branch/worktree. Do not merge main.

Order: (1) base exact accepted repair fb58a751d40f1828990d7a0d687ad30de6eb6103; (2) semantically apply P0 11bd4b5276458b2b7adc11528f117e919524f035; (3) apply lint 349c732c335d83eaa431d30ea7f2b52b8d4431a3; (4) implement make_approval integrity follow-up; (5) semantically port accepted R02c 1c9ff44ec787508fb874f5ac7fde849f89bdfe42.

R02c is NOT a blind cherry-pick. Its old-base mission/worker.py overlaps the later worker rewrite. Re-derive the accepted semantics on the composed worker: reject EDIT blocks naming another target before any write; retain exact-match behavior and strict indentation/no-Markdown-fence guidance; no fuzzy matching, reindentation or known-answer patch.

Before composition review: focused composition tests, full offline, full owned PostgreSQL, Ruff, format check and mypy on the exact composed SHA. Public Actions supplements but cannot replace owned PG.

## Evidence-batch dispositions

R02a: existing lead review accepts the bounded runtime guard at ef8a2cc25c9caf8665804a28453c6f81f82d4a11. Queue ready is stale. Mark implementation complete; ART-V14-REAL-E2E remains changes-required and CP1 exhausted.

R17a: existing lead review accepts the local harness checkpoint at e5bd6350569fb10146517430ca6f7fa097de84a4. Queue ready is stale. Mark harness checkpoint complete; final CP3 and physical multi-host proof remain separate.

R27a: BOUNDED ENGINEERING SLICE ACCEPTED at 0505c24576259d8cf54fa2ec07590a789b398d52 for durable immutable receipts/effect bookkeeping. Evidence: focused real-PG 6; full PG 400/2; one Alembic head; Ruff/mypy clean. Later accepted R27c/d/e supersede then-open transaction/approval/crash limitations.

R27b: BOUNDED ENGINEERING SLICE ACCEPTED at d3a7b56fa98feea332d819e5e8400fd2c1928bc7 for atomic reserve/CAS/binding mismatch. Evidence: focused real-PG 7 x5; full 407/2; Ruff/mypy clean. Later accepted R27c/d/e supersede then-open transaction/approval limitations.

MISSION-CANCEL-01: BOUNDED ENGINEERING SLICE ACCEPTED at 2237effbd09ea5fff90d132e88da2ac7996d4177, receipt binding e53da7305d138658edfb9bd8f47ebbd140a40a63. Evidence: 4 focused PG mission-cancel tests; full 437/13; Ruff/mypy clean. API route wiring remains R17b lineage.

CP3 rerun: owner record references cp3-20260922T020141Z / 9-of-9 product-cancel evidence, but located e53da73 is only the MISSION-CANCEL-01 verify receipt and explicitly says the CP3 rerun follows separately. EVIDENCE LOCATOR REQUIRED — NO STATUS-ONLY ACCEPTANCE.

## Lower-version registry promotion

Promote only already-verified artifacts with concrete evidence and no artifact-local blocker:
- V1.0-repair: ART-V10-CANDIDATE, ART-V10-SECURITY, ART-V10-EVIDENCE-CONTRACT, ART-V10-RUNTIME-TRUTH -> accepted.
- V1.1: ART-V11-MISSION-PATH, ART-V11-MULTISURFACE-EVIDENCE, ART-V11-CONTROL-EVIDENCE, ART-V11-RESTART-EVIDENCE, ART-V11-APPLY-BOUNDARY -> accepted.

Do not promote ART-V10-WORKER-HEARTBEAT; it remains blocked. Artifact promotions do not by themselves declare a whole release version accepted. Other reviewable lower-version artifacts remain pending evidence review.

## G13 platform ruling and sealed-reference gate

EVAL-131 contains no Windows-specific acceptance requirement. Windows was an execution/resource choice, not a semantic qualification property.

Lead ruling: G13 qualification verification is platform-neutral when the exact frozen candidate runs its deterministic verifier/tests in an executable environment and no artifact-specific OS behavior is claimed. Public Linux Actions or owned Linux/macOS can satisfy executable verification for platform-neutral task-pool code. Do not claim Windows compatibility from that evidence.

This removes HOST-WIN-DEV as a mandatory platform gate for G13 qualification. It does NOT satisfy the sealed-reference gate. Counted qualification remains blocked until a real lead/operator-controlled non-worker-readable sealed bundle exists and a binding receipt records actual bundle digest, membership commitment, scorer/grader digest, frozen identities and access boundary. No digest may be invented.

## R31a release

R31a dependencies R30a + R29a + R28a are accepted. Release R31a OFFLINE IMPLEMENTATION/TEST-SOURCE ONLY. Product code, manifest and offline/mock-transport tests may be implemented. Live-local test source may be authored but must not be executed.

No session authentication, HTTP server/network call, cookie-bearing real session, model/provider action or live evidence is authorized. R31b remains held.

## Held gates

CP1 attempt3; CP3 final evidence locator/review and physical second-host proof where applicable; R28d successor live mission; R30b product/live beyond released composition prerequisites; R31a live-local and R31b recovery execution; R33c public issue exact action; R34a real mission/model; G13 sealed bundle/digest; G12 remote provider aliases/quota; WC-LIVE142-24H elapsed campaign; scheduler/timer changes; spend; deployment; main merge.

## Direct execution state

Direct integrator: Codex. Engineering hold is lifted only for explicitly released offline/source/test packets and isolated composition work. Preserve the single existing watcher; no new dispatch, watcher, timer or scheduler.