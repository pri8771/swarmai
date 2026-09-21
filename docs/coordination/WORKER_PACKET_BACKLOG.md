# SwarmAI worker packet backlog

Updated: 2026-09-20T23:51:30Z. Artifact registry is canonical. Packets exist only to advance artifact state; story points are complexity/risk metadata, not hours. Packet completion never self-accepts an artifact.

## Mapping and reviewed results

- W-041A/B/C -> `ART-V10-WORKER-HEARTBEAT` — blocked on live Cursor CLI auth.
- W-111A -> `ART-V11-MULTISURFACE-EVIDENCE` — **completed, lead verified**.
- W-111B -> `ART-V11-CONTROL-EVIDENCE` + partial `ART-V11-RESTART-EVIDENCE` — **changes required only for process-restart portion**; split to W-111C.
- W-121A -> `ART-V12-PROVIDER-ELIGIBILITY` — **completed, lead verified as truthful 0-admissible-remote state**; does not unblock W-121B.
- W-122A -> `ART-V12-BROKER-CONTRACT` — new ready repair packet from independent source review.
- W-131A -> `ART-V13-SCREENING-MATRIX` — **completed, lead verified** (72 n=5 provisional cells; no qualification claim).
- W-131B -> `ART-V13-QUALIFIED-MATRIX` — blocked until qualification pool/versions freeze.
- W-131C1 -> `ART-V13-TASK-POOL` — new ready bounded split.
- W-131C2 -> `ART-V13-REVIEWER-QUALIFICATION` — new ready bounded split.
- W-141A -> `ART-V14-ROLE-MANIFEST`; W-141B1-B4 -> `ART-V14-LIVE-ADAPTIVE-PROOF`; W-141C -> `ART-V14-MODE-COMPARISON`; W-142A-D -> `ART-LIVE142-CAMPAIGN`.

## Dependency-ready packets — keep these stocked

### W-111C — Actual service-process restart/reopen
- Gate/artifact: G11 / `ART-V11-RESTART-EVIDENCE`
- SP: 1
- Worker: Cursor
- Transition: `drafting -> reviewable`
- Why: existing `restart-reopen-operational.json` creates a new `create_app`/MissionStore instance but does not prove the acceptance plan's **actual service process restart** requirement.
- Do: create/retain one durable operational mission, start the real API service process, observe mission from a second interface, terminate that process cleanly, start a new process using the same persistent store/config, reopen the exact same mission ID/status/artifacts via API or CLI.
- Evidence: exact app/code tree SHA, config/store path alias, process start/stop commands, distinct process IDs or equivalent process-instance evidence, timestamps, before/after mission ID/status/artifact hash, exit codes, mode=`live_local operational`, no model rerun required solely to prove reopen.
- Done when: evidence cannot be satisfied by constructing another app object in the same process and current tests remain green.

### W-122A — Close operational broker bypass
- Gate/artifact: G12 / `ART-V12-BROKER-CONTRACT`
- SP: 2
- Worker: Cursor
- Transition: `drafting -> reviewable`
- Independent lead finding: `ProductStore.execute_mission()` currently constructs `RepoWorker(repo, model=model)` without broker/project ID; `RepoWorker._chat()` therefore falls back to direct `local_chat`. This violates G12's “every model attempt through governed broker” rule even though `MissionRuntime` itself is brokered.
- Do: inject/reuse the governed project-scoped broker for the ProductStore/API/CLI generic operational execution path. Avoid a second broker implementation. Ensure project ID and route/account admission flow through the same boundary.
- Tests: negative regression proving operational generic execution cannot reach inference if broker admission denies/has no eligible route; positive local admitted route; route/usage identity recorded; no mock/known-answer fallback. Search all operational model-call sites for equivalent bypasses and either route them or mark unsupported before calling the contract reviewable.
- Done when: exact source diff + tests + current-tip lint/mypy/offline/console CI are green and no operational direct-model bypass remains in supported G11/G12 mission paths.

### W-131C1 — Freeze product qualification task pool/version manifest
- Gate/artifact: G13 / `ART-V13-TASK-POOL`
- SP: 2
- Worker: Cursor, lead reviews/freeze semantics
- Transition: `drafting -> reviewable`
- Do: create a machine-readable manifest that separates calibration/screening IDs from qualification-held-out IDs for required `coding/planning/reasoning/extraction` × S/M/L/XL; bind dataset/task hashes, size-classifier version, scorer/grader version, prompt version, tool contract/version, exact model config identifiers and acceptance protocol v1.0.
- Rules: no plaintext hidden answers exposed to worker prompts; no qualification task previously used for prompt/routing calibration; duplicate/retry attempt is not an independent observation; preserve source/license metadata.
- Done when: lead can verify future W-131B samples against a frozen version and detect calibration leakage/version drift.

### W-131C2 — Reviewer benchmark calibration and freeze
- Gate/artifact: G13/G14 / `ART-V13-REVIEWER-QUALIFICATION`
- SP: 3
- Worker: Cursor; lead owns final benchmark contract
- Transition: `drafting -> reviewable` for benchmark design only, **not reviewer qualification**
- Current evidence: existing review screening is weak (best S ~0.2; M/L/XL 0.0), so do not spend held-out qualification calls on the current scorer/task design.
- Do: debug only on calibration tasks; identify whether task construction, expected decision contract, evidence bundle or grader causes systematic failure; version the corrected reviewer benchmark and scorer; include wrong-result rejection, evidence/acceptance consistency, forbidden-action detection and size classification; freeze held-out IDs/hashes after calibration.
- Done when: benchmark/scorer version is reviewable and held-out qualification can begin without contamination. Do not claim a reviewer route qualified.

## Blocked / follow-on packets

### W-041A — Authenticate Cursor CLI
- Gate/artifact: G10 / `ART-V10-WORKER-HEARTBEAT`
- SP: 1 + external human auth
- Blocked: `cursor agent status`/`whoami` reported Not logged in.
- Done: both authenticated without exposing credentials. Lead cannot perform password/passkey/MFA/CAPTCHA/consent.

### W-041B — Authenticated manual worker receipt
- SP2; depends W-041A. One bounded authenticated invocation, lease/no-overlap respected, sanitized receipt.

### W-041C — Two genuine hourly authenticated worker receipts
- SP2; depends W-041B. Two distinct real scheduler-triggered hourly invocations; do not accelerate cadence.

### W-121B — Dual-remote overlap mission
- Gate/artifact: G12 / `ART-V12-REMOTE-OVERLAP`
- SP3
- Depends: W-122A reviewable + two exact remote routes independently admissible + local route.
- Current blocker: W-121A correctly reports **0 admissible remote routes**.
- Lead checklist: `docs/artifacts/current/ART-V12-REMOTE-ADMISSION-RESEARCH.md` prioritizes exact OpenRouter `:free`, Groq Free-plan exact model, then Gemini exact Flash Free-tier route. Public docs alone do not admit anything.
- Done: one mission has provably overlapping real calls to two independent remote routes plus an actually available local route/fallback, all broker-admitted/reconciled, no paid fallback.

### W-131B — Candidate-cell qualification batches
- Gate/artifact: G13 / `ART-V13-QUALIFIED-MATRIX`
- SP2 **per 5-observation batch**
- Depends: W-131C1 review/freeze. Do not run qualification volume before this dependency.
- Frozen criterion: n>=15 minimum, batches of five, one-sided 90% Wilson lower bound >=0.80, max n=60, zero forbidden actions, all mandatory checks, full overhead/provenance.
- First lead-selected candidate cells after W-131C1:
  1. planning / XL / `gemma3:4b` (screen 5/5);
  2. coding / XL / `qwen3.5:4b` (screen 5/5);
  3. reasoning / L / `qwen3.5:9b` (screen 5/5).
- One W-131B invocation advances one cell by one independent batch. Stop/continue only under frozen protocol. Extraction/XL screening is weak; do not prioritize it blindly.

## Later G14/LIVE-142 packets

### W-141A — Qualified role manifest
SP1, blocked on product/reviewer qualification.

### W-141B concept split
- W-141B1 SP2: live mission input + graph/event instrumentation.
- W-141B2 SP3: two qualified planner/reviewer configs + qualified workers through broker.
- W-141B3 SP3: evidence-driven expansion and convergence-driven merge/retire/cancel.
- W-141B4 SP2: logical-agent/session/request/process counters and admission-denial evidence.
All remain blocked on G12/G13 where applicable.

### W-141C — Single vs fixed vs elastic comparison
SP3, blocked on live adaptive proof; same task set and full overhead, no cherry-picking.

### W-142A-D — final campaign
Candidate freeze; positives; negatives; 24-hour real observation. All blocked until G10-G14 required artifact set is ready.

## Lead-side work completed/active

- **L-121R completed first research draft:** `ART-V12-REMOTE-ADMISSION-RESEARCH.md`; it narrows provider verification but does not self-admit a route.
- **L-131R first candidate selection completed:** planning/XL gemma3:4b; coding/XL qwen3.5:4b; reasoning/L qwen3.5:9b after task-pool freeze.
- L-131V: independently review/freeze reviewer benchmark after W-131C2 calibration.
- L-142S: select final hidden payloads only after candidate freeze.
- L-142R: independent campaign review/defect triage.

## Future preparation — no V1.5+ code

The lead may advance design artifacts without changing the active candidate. `ART-V15-ARCH` and the new `ART-V15-WORKER-PROTOCOL` are drafting. Future Cursor source implementation remains unauthorized until the owner activates V1.5.

## Queue rule

When a packet blocks on human auth/provider eligibility/review, Cursor moves to another dependency-ready packet **inside V1.4**. Routine SP1-SP3 implementation/test work stays with Cursor. The lead should preserve at least three ready packets when practical, resolve architecture/evidence contracts, and must not invent worker execution or start future-version code.## V2 acceleration packets — two Cursor sessions

### Session A — Runtime / Control Plane / Integration

#### V2A-001 — close operational broker bypass
- Artifact: ART-V12-BROKER-CONTRACT
- SP2
- Branch: cursor/v2-runtime-lane
- Ready: yes
- Acceptance: ProductStore/generic API+CLI path uses governed project-scoped broker; direct fallback cannot execute if broker denies; focused regression + full lane CI.

#### V2A-002 — actual service process restart
- Artifact: ART-V11-RESTART-EVIDENCE
- SP1
- Branch: cursor/v2-runtime-lane
- Ready: yes
- Acceptance: stop real API process, start fresh process against same durable store, reopen same mission from another surface with exact evidence.

#### V2A-003a — durable worker schema/repository
- Artifact: ART-V15-LEASE-FENCING
- SP2
- Branch: cursor/v2-runtime-lane
- Ready: yes after reading lead ADR
- Acceptance: SQLAlchemy/Alembic worker/attempt/lease/result persistence; migrations and repository tests.

#### V2A-003b — atomic lease claim/renew/expire
- Artifact: ART-V15-LEASE-FENCING
- SP2
- Depends: V2A-003a
- Acceptance: transactional single-winner claim, renewal/expiry semantics, race tests.

#### V2A-003c — result acceptance fence
- Artifact: ART-V15-LEASE-FENCING
- SP2
- Depends: V2A-003b
- Acceptance: stale generation/lease/cancel/source/duplicate result cannot become accepted.

#### V2A-004 — worker protocol service/client
- Artifact: ART-V15-WORKER-PROTOCOL
- SP3
- Depends: V2A-003c
- Acceptance: registration/heartbeat/claim/result/drain against durable store; restart-safe tests.

#### V2A-018a — site authority epoch
- Artifact: ART-V18-SITE-EPOCH
- SP2
- Depends: durable worker/control store
- Acceptance: only current epoch may accept new consequential effects.

#### V2A-018b — backup manifest/CLI
- Artifact: ART-V18-SITE-EPOCH
- SP2

#### V2A-018c — restore/reconcile CLI
- Artifact: ART-V18-SITE-EPOCH
- SP3

### Session B — Knowledge / Tools / Product / Beta

#### V2B-001 — freeze qualification held-out manifest
- Artifact: ART-V13-TASK-POOL
- SP2
- Branch: cursor/v2-product-lane
- Ready: yes
- Acceptance: separate calibration vs held-out IDs/hashes plus scorer/prompt/tool/size/model versions; no worker-visible hidden answers.

#### V2B-002 — reviewer calibration + benchmark freeze
- Artifact: ART-V13-REVIEWER-QUALIFICATION
- SP3
- Branch: cursor/v2-product-lane
- Ready: yes (calibration only)
- Acceptance: diagnose weak current reviewer screening on calibration tasks, freeze new benchmark/scorer version; no qualification claim yet.

#### V2B-003a — provenance repository
- Artifact: ART-V16-PROVENANCE
- SP2
- Ready: yes after lead schema
- Acceptance: versioned knowledge classes/provenance/permission labels/tombstones behind non-shared module.

#### V2B-003b — permission-first retrieval
- Artifact: ART-V16-PERMISSION-RETRIEVAL
- SP2
- Depends: V2B-003a

#### V2B-003c — supersession/deletion migration
- Artifact: ART-V16-SUPERSESSION
- SP2
- Depends: V2B-003a

#### V2B-004a — action/approval/receipt contracts
- Artifact: ART-V17-APPROVAL-BINDING
- SP2
- Ready: yes after lead contract

#### V2B-004b — ToolGateway adapter
- Artifact: ART-V17-APPROVAL-BINDING / ART-V17-TOOL-CONTRACT
- SP2
- Depends: V2B-004a

#### V2B-019a — extension manifest
- Artifact: ART-V19-EXTENSION-CONTRACT
- SP2
- Depends: V2B-004a

## Shared integration packets

Session A owns integration branch `cursor/v2-integration`.

At each artifact review boundary:
1. lead reviews lane artifact;
2. Session B provides exact commit/integration note when applicable;
3. Session A integrates reviewed commits;
4. full integrated CI;
5. artifact source ref moves to integration SHA.

Do not continuously merge half-finished work.



