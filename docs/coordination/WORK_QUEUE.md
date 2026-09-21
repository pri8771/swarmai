# SwarmAI lead work queue — **OPERATOR ABRUPT STOP**

> **STOP (UTC 2026-09-21T00:12:38Z):** Operator directed abrupt halt of V1.4 implementation. Cursor must not continue G10–G14 engineering. See `V1_4_ABRUPT_STOP.md` and `CURSOR-20260920-024`. LEAD-016 packets below are **frozen / not to be started** until an explicit resume directive. Incomplete gates remain open; do not invent completions.


Updated 2026-09-20T23:51:30Z after LEAD-20260920-016. `ARTIFACT_REGISTRY.json` is canonical. This file is only the current execution view; packet detail lives in `WORKER_PACKET_BACKLOG.md`, performance in `WORKER_PERFORMANCE.json`.

Owner authorization: implementation through V1.4 inclusive. Independent review gates acceptance. Main merge/release/public exposure/additional spend/destructive actions/V1.5+ source work remain unauthorized.

Current PR #14: `cursor/v1.4-live-integration-11e2` @ `03d85540e36c36fa3a5c92a3082be9959d93f66d`. Actions `35545174895` is green offline+console; DB integration is skipped without DSN; live-gated job is a notice only. Application tree is unchanged after `d9da26c…` except evidence/docs.

## Highest-priority ready Cursor packets

Cursor should work the highest-priority non-conflicting packet and keep routine SP1-SP3 execution. Do not wait idle on human auth or remote eligibility.

### W-111C / SP1 — actual process restart -> ART-V11-RESTART-EVIDENCE

Transition: `drafting -> reviewable`.

Current evidence proves a fresh `create_app`/MissionStore object can reopen the mission, but not an actual service-process restart. Start the real API service process against the durable store, create/observe one operational mission, stop the process, start a new process, then reopen the exact mission ID/status/artifacts from API or CLI. Bind PIDs/process-instance evidence, commands, timestamps, candidate/code-tree SHA, config/store alias and artifact hash. No model rerun is required just to prove reopen.

Acceptance by worker packet does not accept V1.1; lead reviews the artifact.

### W-122A / SP2 — close generic operational broker bypass -> ART-V12-BROKER-CONTRACT

Transition: `drafting -> reviewable`.

Independent lead source finding: `ProductStore.execute_mission()` currently creates `RepoWorker(..., model=model)` without broker/project ID, while `RepoWorker._chat()` falls back to direct `local_chat`. This violates G12's every-model-attempt-through-broker rule.

Wire/reuse the existing governed project-scoped broker for the operational generic API/CLI execution path; do not invent a second broker. Add a negative regression proving broker denial/no eligible route prevents model execution, plus a positive admitted-local-route test and exact route/usage evidence. Search supported operational model-call sites for equivalent bypasses. Finish with current-tip Ruff/mypy/offline/console CI green.

### W-131C1 / SP2 — freeze qualification data/version manifest -> ART-V13-TASK-POOL

Transition: `drafting -> reviewable`.

Produce a machine-readable manifest separating calibration/screening IDs from qualification-held-out IDs for required product families `coding/planning/reasoning/extraction` × S/M/L/XL. Bind dataset/task hashes, source/license metadata, size-classifier version, scorer/grader version, prompt version, tool contract/version, exact model config IDs and qualification protocol v1.0. Hidden answers must not be available to worker prompts. Future W-131B attempts must be rejectable if identities drift.

### W-131C2 / SP3 — reviewer benchmark calibration/freeze -> ART-V13-REVIEWER-QUALIFICATION

Transition: `drafting -> reviewable benchmark design only`; **not** reviewer qualification.

Current reviewer screening is unusably weak (best S about 0.2; M/L/XL 0). Debug only on calibration data: task construction, expected decision schema, evidence bundle, grader/scorer and size classification. Include wrong-result rejection, evidence/acceptance consistency and forbidden-action detection. Version/freeze the corrected benchmark/scorer and its held-out IDs after calibration. Do not spend held-out qualification samples before lead review/freeze.

## Human-blocked G10 packet

### W-041A/B/C -> ART-V10-WORKER-HEARTBEAT

Current: scheduler invocation mechanism exists, but Cursor CLI `status/whoami` still report Not logged in; authenticated manual/hourly worker receipts = 0.

Human step: complete a live `cursor agent login` while the CLI waiter remains active, then verify both status commands authenticate. Only after that:
- W-041B SP2: one bounded authenticated manual worker receipt;
- W-041C SP2: two distinct genuine hourly scheduler-triggered authenticated worker receipts with no overlap/lease violation.

Do not accelerate hourly timing, prewrite receipts, or clear probe skip before auth.

## G11 status

Verified artifacts:
- ART-V11-MISSION-PATH
- ART-V11-MULTISURFACE-EVIDENCE
- ART-V11-CONTROL-EVIDENCE
- ART-V11-APPLY-BOUNDARY

Drafting: ART-V11-RESTART-EVIDENCE. V1.1 remains unaccepted until W-111C is independently reviewed and all required artifacts become accepted in order.

## G12 status

- ART-V12-PROVIDER-ELIGIBILITY: verified as truthful current state; **0 admissible remote routes**.
- ART-V12-BROKER-CONTRACT: drafting due the ProductStore generic-execution bypass; W-122A ready.
- ART-V12-REMOTE-OVERLAP: blocked.
- ART-V12-LOCAL-FALLBACK / ADMISSION-RECONCILIATION: reviewable but must be rebound/reviewed after W-122A.

Lead research `docs/artifacts/current/ART-V12-REMOTE-ADMISSION-RESEARCH.md` narrows candidate admission work to exact OpenRouter `:free`, Groq Free-plan exact model and Gemini exact Flash Free-tier routes. Public docs alone never prove the operator's account is eligible. Before W-121B, each exact route needs current account/tier, zero-additional-spend price/charge prevention, quota/health, privacy suitability and bounded canary evidence. No paid fallback or generic auto-router.

## G13 status

Frozen qualification protocol is accepted. Screening matrix is independently verified as **provisional only**: 72 n=5 cells, three local model configs, S/M/L/XL, six families, `qualification_claimed=false`.

W-131B qualification is blocked until W-131C1 is independently reviewed/frozen. Then run one five-observation held-out batch per packet, following the frozen min n=15 / max n=60 / one-sided 90% Wilson lower bound >=0.80 criterion with zero forbidden actions and full overhead/provenance.

Initial lead-selected candidate order after freeze:
1. planning / XL / `gemma3:4b`;
2. coding / XL / `qwen3.5:4b`;
3. reasoning / L / `qwen3.5:9b`.

Do not blanket-expand all cells. Extraction XL screening is weak; reviewer qualification has its own repaired benchmark path.

## G14 and LIVE-142

G14 graph/load artifacts remain offline preparation. Qualified role manifest and live adaptive proof are blocked on G12/G13. Do not treat 10/50/100 logical assignment load as real model concurrency.

LIVE-142 campaign is preregistered but **not started**. It starts only after integrated required artifacts are ready and candidate is frozen. Exact hidden payloads are lead-selected after freeze. Twelve positive slots, six negative scenarios and actual 24-hour observation remain mandatory; no time acceleration or cherry-picking.

## Worker performance

Reviewed packets recorded this heartbeat:
- W-111A SP2: first-review accepted.
- W-111B SP2: changes required for restart portion; one rework cycle; W-111C split created.
- W-121A SP2: first-review accepted as truthful blocked-state provider ledger.
- W-131A SP1: first-review accepted screening/gap artifact.

Each SP bucket still has <5 completed packets; do not call performance estimates stable.

## Lead-side current/future artifacts

Lead advanced:
- `ART-V12-REMOTE-ADMISSION-RESEARCH.md` — current G12 public-doc/checklist research, not account admission.
- `ART-V15-WORKER_PROTOCOL.md` — future distributed-worker enrollment/generation/heartbeat/lease/result/acceptance-fence design.

Future design work may continue, but Cursor must not implement V1.5+ source while V1.4 tranche is active unless owner explicitly authorizes it.

## Immediate worker directive

ACK LEAD-20260920-016 and claim one of W-111C, W-122A, W-131C1 or W-131C2 with artifact ID, intended transition, base SHA/worktree and first test. If one packet conflicts with active files or becomes blocked, move to another ready packet. Do not self-accept artifact transitions; return exact source/evidence SHA and current-tip checks for lead review.
