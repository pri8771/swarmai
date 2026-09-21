# Future execution packet catalog — V1.8 through V3.0

Generated from the two planning packet JSON files by `tools/validate_plan.py --render`.
Do not hand-edit packet cards. Proposed closure revision; not independent acceptance.
Packet contract digest: `6a54c7cbf9c1f0b2abbd7e080ffd2233bbf4f976cbd961fd379f765d0cd1ec1b`

Read only the active card, its referenced algorithm/contract and owned source. Shared rules:
- One implementation session; one bounded concern per commit; source changes stay on the worker branch.
- Listed paths marked new are proposed. Verify exact brownfield imports before implementation. Directory surfaces mean one bounded slice, not whole-directory rewrite.
- If the slice needs more than three production files or lacks a frozen interface, split it during the final Fable sweep; later source surprises require a narrow amendment.
- Routine code: Sonnet 4.6 medium effort. Transactions, security, scheduler and recovery: high effort plus independent diff review. Packaging: lower tier.
- Run focused negative cases, Ruff and mypy; real DB/process tests for state boundaries. Record commands, exit codes and every skip. No product checks are claimed by this documentation generator.
- Shared contracts: FUTURE_SCHEMA_CONTRACTS_V18_TO_V30_20260921.md, FUTURE_TRANSACTION_ALGORITHMS_V18_TO_V30_20260921.md and FUTURE_MIGRATION_SEQUENCE_V18_TO_V30_20260921.md. Packet JSON retains verification commands, owner and rollback fields; read that one object with this card.
- Evidence: `docs/evidence/packets/<packet>/<run-id>/` with manifest, commands, redacted environment, receipts and summary; source SHA and evidence-commit SHA are separate.
- Required identity: source/schema/lock/config/policy/route/manifest/protocol digests. Preserve all failed runs; never mint elapsed evidence or self-accept.
- Rollback: disable the new path or restore the previous compatible snapshot; never erase unknown effects, lower generations or copy grants across projects.

## 18-00

Artifact(s): handoff. SP1. Depends: R34b. Type: code.
Entry gates: REV-V18-HANDOFF. Claim gates: none. Source state: planned.

**Owned surfaces:** `docs/evidence/v18/base-manifest.json (new)`.

**Required behavior:** Bind CP6 source, migrations, policy, artifact claim matrix and unresolved gate IDs; identify the reviewed source base, never copy acceptance from a branch label.

**Negative cases:** Reject dirty/unpushed source or mismatched CP6 hashes; an open gate remains open.

**Evidence and exit:** Read-only manifest verification; V1.8 base is reproducible and does not claim V1.7 acceptance.

## 18-00a

Artifact(s): ART-V18-RECOVERY-ARCH. SP2. Depends: none. Type: lead_decision.
Entry gates: none. Claim gates: none. Source state: planned.

**Owned surfaces:** `docs/artifacts/future/ART-V18-RECOVERY_ARCHITECTURE.md`; `docs/coordination/FUTURE_OPEN_DECISIONS_FREEZE_POINTS_20260921.md`.

**Required behavior:** Freeze the supported recovery mode: same authority DB may use transactional epoch CAS; restoring that DB requires independent proof that the old deployment cannot write or reach effect destinations. Unknown old-site isolation keeps recovery read-only.

**Negative cases:** A larger integer in a restored DB is insufficient; stale or missing fencing proof denies activation.

**Evidence and exit:** Architecture decision with threat trace and recovery profile; cross-site automatic failover remains unsupported until independently fenced.

## 18-01

Artifact(s): ART-V18-SITE-EPOCH. SP2. Depends: 18-00, 18-00a. Type: code.
Entry gates: none. Claim gates: none. Source state: planned.

**Owned surfaces:** `src/swarm/contracts/site_authority.py (new)`.

**Required behavior:** Define authority_domain_id, site_id, epoch, state, proof_ref, policy_digest and immutable AuthorityBinding. transition(expected_epoch, target, proof_ref) returns receipt; a missing binding denies new dispatch/effects.

**Negative cases:** Unknown state, epoch regression, domain mismatch and missing proof fail validation.

**Evidence and exit:** Focused contract tests and serialized fixtures; one vocabulary consumed by all fences.

## 18-02

Artifact(s): ART-V18-SITE-EPOCH. SP2. Depends: 18-01. Type: code.
Entry gates: none. Claim gates: none. Source state: planned.

**Owned surfaces:** `src/swarm/db/models.py`; `src/swarm/db/site_authority.py (new)`; `migrations/versions/ (new revision)`.

**Required behavior:** Implement transition CAS under the domain row lock; unique(domain,epoch), one active owner per domain. Install nullable authority binding on lease/result/effect records here, not in three later competing migrations. Legacy rows cannot authorize fresh work.

**Negative cases:** Concurrent activation has one winner; duplicate transition is idempotent; legacy NULL fence denies.

**Evidence and exit:** Real Postgres race and upgrade with existing data; one migration head; restart retains owner.

## 18-03

Artifact(s): ART-V18-SITE-EPOCH. SP2. Depends: 18-02. Type: code.
Entry gates: none. Claim gates: none. Source state: planned.

**Owned surfaces:** `src/swarm/controller/scheduler.py`; `src/swarm/db/lease_fencing.py`.

**Required behavior:** Claim dispatch and lease renewal against the active domain/epoch in their existing transaction. Propagate immutable binding into attempts; workers cannot replace it.

**Negative cases:** Old epoch, expired authority proof, renewal after fencing and missing binding deny without a dispatch.

**Evidence and exit:** Two-connection race at transition/claim; dispatch receipt pins the selected binding.

## 18-04

Artifact(s): ART-V18-SITE-EPOCH. SP2. Depends: 18-02. Type: code.
Entry gates: none. Claim gates: none. Source state: planned.

**Owned surfaces:** `src/swarm/db/lease_fencing.py`; `src/swarm/tools/fences.py`; `src/swarm/tools/effects.py`.

**Required behavior:** Add domain/epoch checks to current result acceptance and effect begin/reconcile transitions. Use rows introduced by 18-02 and same lock order as cancellation. Fence local finalization separately from external outcome observations.

**Negative cases:** Stale-site result and effect rejected; a late executor cannot finalize a newer execution token; unknown external outcome remains unknown.

**Evidence and exit:** Real-DB negatives across two processes; no second gateway, result repository or authority store.

## 18-05

Artifact(s): ART-V18-DEPLOYMENT-MANIFEST. SP2. Depends: 18-02. Type: code.
Entry gates: none. Claim gates: none. Source state: planned.

**Owned surfaces:** `src/swarm/contracts/recovery.py (new)`; `src/swarm/deploy/manifest.py (new)`.

**Required behavior:** Define DeploymentManifest and BackupManifest with source/schema/lock/config/component digests, consistency point, artifact inventory, exclusions, encryption/key references and timestamps. Secret values excluded; encrypted payload is not committed.

**Negative cases:** Missing component, secret value, mismatched policy digest and noncanonical digest rejected.

**Evidence and exit:** Redacted manifest fixtures and digest verification; all durable state contributors enumerated.

## 18-06

Artifact(s): ART-V18-BACKUP-RESTORE. SP2. Depends: 18-05. Type: code.
Entry gates: none. Claim gates: none. Source state: planned.

**Owned surfaces:** `src/swarm/deploy/backup.py (new)`; `src/swarm/cli.py`.

**Required behavior:** Reuse pg_dump plus immutable artifact inventory under a declared consistency barrier; content is staged privately then manifest published atomically. Verify hashes before calling backup usable. In-flight effects retain their state.

**Negative cases:** Interrupted dump, missing blob, bit corruption and unreadable key produce unusable backup; no partial manifest accepted.

**Evidence and exit:** Real disposable DB backup and restore-readback; sanitized commands/durations; secret-bearing backups outside Git.

## 18-07

Artifact(s): ART-V18-BACKUP-RESTORE. SP3. Depends: 18-04, 18-06. Type: code.
Entry gates: none. Claim gates: none. Source state: planned.

**Owned surfaces:** `src/swarm/deploy/recovery.py (new)`; `src/swarm/deploy/backup.py`; `src/swarm/cli.py`.

**Required behavior:** Restore into isolated read-only recovery mode, validate digests/migration head, expire old leases, reconcile reservations, preserve unknown effects. Acquire authority through 18-00a proof before enabling writes; reuse subsystem services.

**Negative cases:** Unfenced old site, corrupt snapshot, incompatible head or unresolved effect cannot silently activate or replay writes.

**Evidence and exit:** Real DB restore twice is idempotent; receipt lists every reconciled state class and required operator action.

## 18-08

Artifact(s): ART-V18-SPLIT-BRAIN-SAFETY. SP2. Depends: 18-03, 18-04, 18-07. Type: code.
Entry gates: none. Claim gates: none. Source state: planned.

**Owned surfaces:** `tests/integration/recovery/ (new tests)`.

**Required behavior:** Exercise old/new deployment authority with independent DB connections/processes, including restore-copy divergence. Verify stale process cannot dispatch, accept result or start effects after isolation proof.

**Negative cases:** Two restored DB copies incrementing epoch must still fail activation without external fencing; interrupted activation does not create two owners.

**Evidence and exit:** Adversarial authority matrix with exact denial receipts; all five authority boundaries covered.

## 18-09

Artifact(s): ART-V18-OUTAGE-DRILL. SP2. Depends: 18-08. Type: code.
Entry gates: none. Claim gates: none. Source state: planned.

**Owned surfaces:** `scripts/cp18_recovery.py (new)`; `docs/evidence/v18/ (new run directory)`.

**Required behavior:** Run backup, actual deployment stop, restore and fenced activation on declared topology. Calculate RPO from committed watermark loss and RTO from observed usable-service times; retain pending external outcomes.

**Negative cases:** Old process resumed, missing blob, recovery interrupted and duplicate activation tested; unknown topology is not a pass.

**Evidence and exit:** CP18 real outage/recovery bundle and independent review; second-site claims only with actual isolation evidence.

## 19-00

Artifact(s): ART-V19-BETA-ACCEPTANCE. SP1. Depends: none. Type: lead_decision.
Entry gates: none. Claim gates: none. Source state: planned.

**Owned surfaces:** `docs/artifacts/future/ART-V19-BETA_SELFDEV_ACCEPTANCE.md`.

**Required behavior:** Freeze private beta journeys, supported capability claims, environment matrix and defect severity rubric. Separate candidate issue/PR preparation from approval to publish/merge.

**Negative cases:** Unsupported OS must remain unknown; fixture install cannot count as external user install.

**Evidence and exit:** Versioned acceptance contract and run IDs required before any counted CP19 run.

## 19-01

Artifact(s): ART-V19-EXTENSION-CONTRACT. SP2. Depends: R28d, R27d. Type: code.
Entry gates: none. Claim gates: none. Source state: planned.

**Owned surfaces:** `src/swarm/contracts/extensions.py (new)`.

**Required behavior:** ExtensionManifest is a superset of AdapterManifest; exact digest, core compatibility range, entrypoints, permission/data/resource declarations and dependency digests. Manifest parsing performs no imports.

**Negative cases:** Unknown executable entrypoint, undeclared scope, dependency cycle and incompatible core reject before loading.

**Evidence and exit:** Contract tests with versioned manifests; R29a vocabulary preserved.

## 19-02

Artifact(s): ART-V19-EXTENSION-CONTRACT. SP2. Depends: 19-01. Type: code.
Entry gates: none. Claim gates: none. Source state: planned.

**Owned surfaces:** `src/swarm/extensions/registry.py (new)`; `src/swarm/db/models.py`; `migrations/versions/ (new revision)`.

**Required behavior:** Persist install separately from project grant. Lifecycle installed->enabled->draining->disabled or quarantined; grant changes bump generation. Immutable digest/version binding and transactional transition receipt.

**Negative cases:** Concurrent enable/disable, package digest substitution, cross-project lookup and stale grant replay fail closed.

**Evidence and exit:** Real-DB lifecycle/restart tests and migration; disabled installation grants zero authority.

## 19-03

Artifact(s): ART-V19-EXTENSION-CONTRACT. SP2. Depends: 19-02. Type: code.
Entry gates: none. Claim gates: none. Source state: planned.

**Owned surfaces:** `src/swarm/tools/adapter_registry.py`; `src/swarm/tools/fences.py`; `src/swarm/extensions/registry.py`.

**Required behavior:** Load only approved digest-pinned built-ins/private extensions through AdapterRegistry. Effective permission is intersection with the current project grant; revocation rechecked before every new action. Untrusted code uses existing sandbox, never host import.

**Negative cases:** Extension requests denied provider, network, filesystem or project scope; disabled/revoked package cannot execute from cache.

**Evidence and exit:** Gateway integration with one real builtin migrated; no independent extension scheduler or policy engine.

## 19-04

Artifact(s): ART-V19-INSTALL-UPGRADE. SP2. Depends: 18-07, 19-00. Type: code.
Entry gates: none. Claim gates: none. Source state: planned.

**Owned surfaces:** `src/swarm/product/install.py (new)`; `src/swarm/cli.py`; `deploy/ (existing private deployment configuration)`.

**Required behavior:** Doctor inspects supported Python/DB/artifact store/config without guessing credentials. Init creates explicit project/operator identity, runs migrations once and checks authenticated readiness; no demo project fallback.

**Negative cases:** Existing installation not overwritten; insufficient permissions, dirty config and missing DB yield actionable failure.

**Evidence and exit:** Fresh isolated environment transcript; setup rerun idempotent; operator can start/inspect/stop a mission.

## 19-05

Artifact(s): ART-V19-INSTALL-UPGRADE. SP2. Depends: 19-04. Type: code.
Entry gates: none. Claim gates: none. Source state: planned.

**Owned surfaces:** `src/swarm/product/upgrade.py (new)`; `src/swarm/cli.py`.

**Required behavior:** Upgrade preflight pins old/new manifests, drains writes, makes verified backup, applies one migration chain, runs readiness and records outcome. Resume interrupted upgrade from durable phase receipt.

**Negative cases:** Concurrent upgrade, missing backup, failed migration and mixed binaries leave service fenced and recovery instructions intact.

**Evidence and exit:** Real predecessor-to-candidate upgrade with representative data; evidence binds both versions.

## 19-06

Artifact(s): ART-V19-INSTALL-UPGRADE. SP2. Depends: 19-05. Type: code.
Entry gates: none. Claim gates: none. Source state: planned.

**Owned surfaces:** `src/swarm/product/upgrade.py`; `src/swarm/product/support_bundle.py (new)`.

**Required behavior:** Rollback uses supported backward compatibility or restores exact prior snapshot and binary; never assumes destructive downgrade. Support bundle uses an allowlist and redacts credentials/content.

**Negative cases:** Rollback across incompatible schema requires restore; seeded secret, cookie and token-bearing URL never export.

**Evidence and exit:** Real rollback/readback plus secret-sentinel scan; operational state and unknown effects preserved.

## 19-07

Artifact(s): ART-V19-SELFDEV-PR-EVIDENCE. SP3. Depends: 19-03, R02a, R17c, R28d. Type: code.
Entry gates: none. Claim gates: none. Source state: planned.

**Owned surfaces:** `src/swarm/selfdev/runner.py`; `src/swarm/mission/acceptance.py`.

**Required behavior:** Use SwarmAI's brokered leased mission path for inspect->isolated patch->red/green defect proof->protected verifier->independent review candidate. Output local commit/PR description; publishing PR only under active explicit authority.

**Negative cases:** Governance/test-oracle edits, direct primary-checkout write, self-review, merge or release denied.

**Evidence and exit:** One real bounded selfdev candidate from original goal with source/evidence refs; external IDE work does not count.

## 19-08

Artifact(s): V1.9-live. SP2. Depends: 19-03, 19-06, 19-07. Type: code.
Entry gates: none. Claim gates: none. Source state: planned.

**Owned surfaces:** `scripts/cp19_productization.py (new)`; `docs/evidence/v19/ (new run directory)`.

**Required behavior:** Run install, extension grant for project A, denial for B, drain, upgrade, rollback and selfdev journey through CLI/API on one candidate identity.

**Negative cases:** Stale grant, restart during upgrade and support bundle leaks included; partial journey cannot count as complete.

**Evidence and exit:** CP19 candidate bundle; independent review and environment-specific results, no fabricated support rows.

## 19-09

Artifact(s): ART-V19-EXTERNAL-INSTALLS. SP1. Depends: 19-06. Type: external_live.
Entry gates: EXT-V19-FRESH-ENVIRONMENTS. Claim gates: none. Source state: planned.

**Owned surfaces:** `docs/evidence/v19/external-installs/ (new run directory)`.

**Required behavior:** Run 19-04..19-06 on a genuinely fresh operator-provided environment using the written runbook. Record assistance and failures as usability evidence.

**Negative cases:** No inherited DB/env/container volume; copied developer state disqualifies fresh install.

**Evidence and exit:** External install transcript, environment identity and resulting mission receipts; blocked when environment unavailable.

## 19-10

Artifact(s): ART-V19-WINDOWS-CLEAN-INSTALL. SP1. Depends: 19-06. Type: external_live.
Entry gates: EXT-V19-WINDOWS-HOST. Claim gates: none. Source state: planned.

**Owned surfaces:** `docs/evidence/v19/windows/ (new run directory)`.

**Required behavior:** Run the same private install/upgrade/rollback journey on real Windows with declared runtime/sandbox prerequisites; record platform deltas in support matrix.

**Negative cases:** Path quoting, drive letters, permissions, process teardown and newline handling tested; emulation is not Windows evidence.

**Evidence and exit:** Windows environment and source bound readback; no Windows support claim without pass.

## 20-01

Artifact(s): ART-V20-INTEGRATED-CANDIDATE, ART-V20-FOUNDATION-HARDENING. SP3. Depends: 18-08, 19-03, 19-06, 19-07. Type: code.
Entry gates: none. Claim gates: none. Source state: planned.

**Owned surfaces:** `docs/evidence/v20/integration/ (new report)`; `docs/coordination/V2_FOUNDATION_HARDENING_PACKETS.md`.

**Required behavior:** Inventory reviewed lower-version commits and unresolved hardening defects; verify one service authority and migration head. Existing defect fixes become bounded packets with exact surfaces; this packet cannot authorize a broad refactor.

**Negative cases:** Unreviewed donor source, duplicate authority, stale manifests and silently dropped required artifact block candidate freeze.

**Evidence and exit:** Integration report with source graph and every finding disposition; zero unresolved release-blocking implementation defects.

## 20-02

Artifact(s): ART-V20-INTEGRATED-CANDIDATE. SP1. Depends: 20-01. Type: code.
Entry gates: none. Claim gates: none. Source state: planned.

**Owned surfaces:** `src/swarm/release/candidate.py (new)`; `src/swarm/cli.py`.

**Required behavior:** Freeze content-addressed CandidateManifest (source/schema/lock/config/policy/model/tool/protocol/registry snapshot digests) in existing artifacts; later review refs append separately. No candidate database required.

**Negative cases:** Mutated source/config invalidates identity; evidence commit SHA is not misrepresented as execution SHA.

**Evidence and exit:** Manifest validation and repeatable digest; exact run deployment can be reconstructed.

## 20-03

Artifact(s): ART-V20-INTEGRATED-CANDIDATE. SP2. Depends: 20-02. Type: code.
Entry gates: none. Claim gates: none. Source state: planned.

**Owned surfaces:** `scripts/cp20_checks.py (new)`; `docs/evidence/v20/ (new run directory)`.

**Required behavior:** Run configured lint/type/unit/integration/security/migration checks on candidate source, recording command, exit, duration and skip names. Confirm operational wiring and clean upgrade.

**Negative cases:** Required skipped tests, wrong source, divergent migration head or unavailable CI cannot be labeled green.

**Evidence and exit:** Exact candidate deterministic report; infrastructure blockage distinct from product test failure.

## 20-04

Artifact(s): ART-V20-SUPPORT-MATRIX, ART-V20-INSTALL-JOURNEY. SP2. Depends: 20-03. Type: code.
Entry gates: none. Claim gates: none. Source state: planned.

**Owned surfaces:** `docs/artifacts/future/ART-V20-SUPPORT_MATRIX_TEMPLATE.md`; `docs/evidence/v20/install/ (new run directory)`.

**Required behavior:** Populate only evidenced OS/runtime/provider/tool/extension combinations; perform real fresh operator install to completed mission and diagnostic recovery.

**Negative cases:** Unsupported combination fails with clear error; no inference of Linux/Windows support from macOS pass.

**Evidence and exit:** Candidate-bound install journey and truthful supported/unknown/unsupported matrix.

## 20-05

Artifact(s): ART-V20-UPGRADE-ROLLBACK. SP2. Depends: 20-03. Type: code.
Entry gates: none. Claim gates: none. Source state: planned.

**Owned surfaces:** `scripts/cp20_upgrade.py (new)`; `docs/evidence/v20/upgrade/ (new run directory)`.

**Required behavior:** Run prior supported version->candidate->prior state recovery with real missions, knowledge, approvals and uncertain effects. Keep reliability campaign deployment separate unless preregistered.

**Negative cases:** Pending external effect not replayed after rollback; old binaries cannot write incompatible schema.

**Evidence and exit:** Candidate-bound upgrade/rollback bundle and measured downtime/data preservation.

## 20-06

Artifact(s): ART-V20-SECURITY-REVIEW. SP3. Depends: 20-03. Type: code.
Entry gates: none. Claim gates: none. Source state: planned.

**Owned surfaces:** `docs/artifacts/future/ART-V20-SECURITY_THREAT_MODEL.md`; `docs/evidence/v20/security/ (new report)`.

**Required behavior:** Independent reviewer traces authentication, project scope, model/tool inputs, sandbox, tokens, approvals, restore and supply-chain loading through operational entrypoints; bind each invariant to a negative test.

**Negative cases:** Cross-project existence leak, stale authority and adversarial extension/selfdev paths tested; no test waiver without explicit disposition.

**Evidence and exit:** Security review for exact candidate; release-blocking findings cause successor candidate and affected evidence rerun.

## 20-07

Artifact(s): ART-V20-PERFORMANCE-BASELINE. SP2. Depends: 20-03. Type: code.
Entry gates: none. Claim gates: none. Source state: planned.

**Owned surfaces:** `benchmarks/ (bounded candidate profile)`; `docs/evidence/v20/performance/ (new run directory)`.

**Required behavior:** Freeze workload/resource envelope before measuring throughput, p50/p95 latency, memory and orchestration/token overhead vs single-worker baseline. Exclude warmup explicitly; preserve all repetitions.

**Negative cases:** No dropping slow failures, mixing different route/model configs or treating unknown usage as zero.

**Evidence and exit:** Resource-normalized performance report with limits, baseline and environment; claims restricted to measured setup.

## 20-08a

Artifact(s): ART-V20-RELIABILITY-PROTOCOL. SP2. Depends: none. Type: lead_decision.
Entry gates: none. Claim gates: none. Source state: planned.

**Owned surfaces:** `docs/artifacts/future/ART-V20-RELIABILITY_PROTOCOL.md`.

**Required behavior:** Freeze seven-day protocol, supported profile, fault schedule, monitoring gaps, zero-tolerance invariants and restart rules. Specify which drills run on campaign or cloned deployment.

**Negative cases:** Do not shorten duration or tune thresholds after results; missing support/security preflight blocks start.

**Evidence and exit:** Lead-reviewed protocol digest and independent candidate-start checklist; planning may complete while clock remains unstarted.

## 20-08b

Artifact(s): ART-V20-RELIABILITY-PROTOCOL. SP1. Depends: 20-03, 20-08a. Type: wall_clock_start.
Entry gates: REV-V20-CAMPAIGN-START. Claim gates: WC-V20-RELIABILITY-168H. Source state: planned.

**Owned surfaces:** `docs/evidence/v20/reliability/ (new start manifest)`.

**Required behavior:** After all frozen protocol prerequisites and start review, launch actual frozen deployment; observe started_at, attach read-only monitors and immutable 24h checkpoints. Implementation continues on a descendant checkout only.

**Negative cases:** Missing monitoring, ambiguous identity or unapproved profile prevents counted start; heartbeat timestamp is not campaign start.

**Evidence and exit:** Campaign ID and observed start evidence; earliest start consistent with policy, not unconditional start after unit tests.

## 20-08c

Artifact(s): ART-V20-RELIABILITY-PROTOCOL. SP1. Depends: 20-08b. Type: wall_clock.
Entry gates: none. Claim gates: WC-V20-RELIABILITY-168H. Source state: planned.

**Owned surfaces:** `docs/evidence/v20/reliability/ (new completion evidence)`.

**Required behavior:** Observe >=168 consecutive hours of one compatible candidate; execute preregistered drills, retain downtime and gaps, verify identity continuity. No elapsed time borrowed from predecessor.

**Negative cases:** Changed behavior restarts affected identity; missing continuity may require successor campaign; backdated timestamps invalid.

**Evidence and exit:** Completed real campaign and gap dispositions are reviewable, not automatic acceptance.

## 20-09

Artifact(s): ART-V20-RELEASE-REVIEW. SP2. Depends: 20-04, 20-05, 20-06, 20-07, 20-08c, 18-09, 19-08. Type: code.
Entry gates: none. Claim gates: none. Source state: planned.

**Owned surfaces:** `docs/evidence/v20/release-review/ (new report)`.

**Required behavior:** Independent artifact-by-artifact release review reconciles lower-version requirements, real campaigns, support/security/performance/install evidence and remaining gates. Produce private candidate handoff/runbooks.

**Negative cases:** Open required acceptance gate, mismatched source or self-review prevents accepted/release recommendation.

**Evidence and exit:** Review receipt and operator decision package; main merge/public release remain separate actions requiring authorization.

## 23-01

Artifact(s): ART-V23-MULTIMISSION-OPS. SP2. Depends: 20-03. Type: code.
Entry gates: none. Claim gates: none. Source state: planned.

**Owned surfaces:** `src/swarm/contracts/scheduling.py (new)`; `src/swarm/db/models.py`; `migrations/versions/ (new revision)`.

**Required behavior:** Add versioned SchedulerPolicy, project credits/round cursor, scheduler generation, decision receipt and unique dispatch identity. Keep existing controller scheduler as owner.

**Negative cases:** Negative weights, duplicate receipt/dispatch IDs and legacy rows creating fresh authority rejected.

**Evidence and exit:** Real-DB migration/restart tests; fields support algorithm A23-01 without a parallel scheduler.

## 23-02

Artifact(s): ART-V23-MULTIMISSION-OPS. SP2. Depends: 23-01. Type: code.
Entry gates: none. Claim gates: none. Source state: planned.

**Owned surfaces:** `src/swarm/controller/scheduler.py`; `src/swarm/contracts/scheduling.py`.

**Required behavior:** Implement weighted-deficit round-robin using persisted round/cursor, bounded credit, deterministic project tie break. Credit accrues once per round, debit once per dispatched service unit, atomic receipt.

**Negative cases:** Polling frequency cannot mint credit; idle backlog cannot hoard unbounded credit; equal inputs yield equal choice.

**Evidence and exit:** Frozen equal-cost trace plus weighted tests; implement algorithm independently from later counted tolerance evidence.

## 23-03

Artifact(s): ART-V23-MULTIMISSION-OPS. SP2. Depends: 23-02. Type: code.
Entry gates: none. Claim gates: none. Source state: planned.

**Owned surfaces:** `src/swarm/controller/scheduler.py`; `src/swarm/controller/graph.py`.

**Required behavior:** Inside selected project choose dependency-ready task by bounded aging/deadline bonus then enqueue time/id; skip blocked head work and inspect next eligible project. Scope/privacy/resource checks precede ranking.

**Negative cases:** Blocked large job cannot hide small eligible jobs; child tasks cannot reset project credit; unmet DAG dependency denies.

**Evidence and exit:** Deterministic anti-head-of-line/starvation/cancellation tests and explain receipts.

## 23-04

Artifact(s): ART-V23-MULTIMISSION-OPS. SP3. Depends: 23-03. Type: code.
Entry gates: none. Claim gates: none. Source state: planned.

**Owned surfaces:** `src/swarm/controller/reservations.py (new)`; `src/swarm/db/models.py`; `migrations/versions/ (new revision)`.

**Required behavior:** Durable DispatchIntent and components reserve existing worker/broker/tool capacity in frozen order with key(intent,component). Ready only after all reserved and current fences verified; compensate only components acquired by this intent.

**Negative cases:** Failure at every acquisition boundary; repeated compensate; ready before all components; leaked shared reservation.

**Evidence and exit:** Real-DB/provider-fake boundary tests; no effect execution inside reservation transaction and no second budget ledger.

## 23-05

Artifact(s): ART-V23-MULTIMISSION-OPS. SP3. Depends: 23-04. Type: code.
Entry gates: none. Claim gates: none. Source state: planned.

**Owned surfaces:** `src/swarm/controller/reservations.py`; `src/swarm/controller/scheduler.py`.

**Required behavior:** On restart reconcile preparing/ready/unknown intents using existing component receipts; unknown capacity remains charged until resolved. Stable dispatch ID handles crash after commit before delivery.

**Negative cases:** Lost reservation response, crash mid-compensation, duplicate delivery and expired intent cannot oversubscribe or issue fresh duplicate intent.

**Evidence and exit:** Multi-process kill/restart tests for every phase; complete disposition receipt per component.

## 23-06

Artifact(s): ART-V23-MULTIMISSION-OPS. SP2. Depends: 23-03. Type: code.
Entry gates: none. Claim gates: none. Source state: planned.

**Owned surfaces:** `src/swarm/controller/scheduler.py`; `src/swarm/runtime/backpressure.py`.

**Required behavior:** Persist project/site/worker drain state and reject new dispatch; cancellation increments existing generation before notifications. Bounded queues with explicit rejection reason; draining lets authorized in-flight work settle.

**Negative cases:** Cancel racing with ready, nested fanout, full queue and drain resume cannot bypass fences or starve others.

**Evidence and exit:** Deterministic plus real-DB cancellation races; no new timers/scheduler ownership.

## 23-07

Artifact(s): ART-V23-MULTIMISSION-OPS. SP3. Depends: 23-01, 23-04. Type: code.
Entry gates: none. Claim gates: none. Source state: planned.

**Owned surfaces:** `src/swarm/controller/scheduler.py`; `src/swarm/db/site_authority.py (new by 18-02)`.

**Required behavior:** Recover round cursor, credits and reservations under current site epoch; take one scheduler generation and reject stale instance CAS. Do not mint catch-up credits on restart.

**Negative cases:** Dual schedulers, stale epoch, restart mid-debit and paused clock produce no duplicate dispatch or doubled credit.

**Evidence and exit:** Two scheduler process race and crash test; same persisted workload remains fair after restart.

## 23-08

Artifact(s): ART-V23-OBSERVABILITY. SP2. Depends: 23-02, 23-07. Type: code.
Entry gates: none. Claim gates: none. Source state: planned.

**Owned surfaces:** `src/swarm/observability/read_model.py (new)`; `src/swarm/api/routes_v1.py`; `apps/console/ (bounded read view)`.

**Required behavior:** Expose scoped receipt graph and queue decisions with denied/deferred reasons, freshness and usage unknowns; cursor-pagination. Console mutations use authenticated command/action boundary.

**Negative cases:** Cross-project IDs/counts, stale cursor, raw prompt/secret export and write from read endpoint denied.

**Evidence and exit:** API schema/permission tests plus console journey to inspect/retry via permitted boundary.

## 23-09

Artifact(s): ART-V23-CAPABILITY-PACKS. SP2. Depends: 19-03, 20-03. Type: code.
Entry gates: none. Claim gates: none. Source state: planned.

**Owned surfaces:** `src/swarm/extensions/registry.py (new by 19-02)`; `src/swarm/contracts/extensions.py (new by 19-01)`.

**Required behavior:** Represent capability pack as extension kind with exact dependency DAG, procedures and adapters. Reuse install/grant/drain/revoke tables; project enablement distinct from installed bytes.

**Negative cases:** Pack cycle, transitive digest substitution, disabled dependency and migration on untrusted import denied.

**Evidence and exit:** Lifecycle tests with two projects, existing extension semantics and no competing pack authority.

## 23-10

Artifact(s): ART-V23-PORTABILITY. SP2. Depends: 19-03, R25b, 20-03. Type: code.
Entry gates: none. Claim gates: none. Source state: planned.

**Owned surfaces:** `src/swarm/knowledge/service.py (new by R25a)`; `src/swarm/product/portability.py (new)`; `src/swarm/cli.py`.

**Required behavior:** Export permitted immutable refs/content and provenance to versioned manifest. Import into target project with fresh IDs/mapping and fresh grants; strip approvals, leases, cookies, secrets and accepted authority. Imported facts are untrusted pending validation.

**Negative cases:** Path traversal/symlink archive, missing blob, wrong tenant, replay duplicate and copied grant rejected.

**Evidence and exit:** Roundtrip to fresh project with digest/provenance checks, zero permission carryover and deterministic import receipt.

## 23-11

Artifact(s): ART-V23-FLEET-POLICY. SP3. Depends: 23-07, 18-08. Type: code.
Entry gates: none. Claim gates: none. Source state: planned.

**Owned surfaces:** `src/swarm/workers/service.py`; `src/swarm/controller/scheduler.py`; `src/swarm/contracts/scheduling.py (new by 23-01)`.

**Required behavior:** Placement intersects worker trust/capability, privacy/locality and free capacity; draining yields replacement attempt only after fence. Broker credentials remain control-plane owned.

**Negative cases:** Worker claims higher trust, wrong site, stale generation and forbidden data egress rejected; no copying auth to workers.

**Evidence and exit:** Physical host placement/drain evidence at CP23 plus deterministic policy matrix.

## 23-12

Artifact(s): ART-V23-MULTIMISSION-OPS. SP2. Depends: 23-05, 23-06, 23-07. Type: code.
Entry gates: EXT-D23-FAIRNESS. Claim gates: none. Source state: planned.

**Owned surfaces:** `benchmarks/ (frozen fairness profile)`; `docs/coordination/FUTURE_ACCEPTANCE_WORKLOADS_V23_V30.json`.

**Required behavior:** Preregister service-unit cost, weights, tolerance and sample boundary; exercise >=200 decisions for the proposed equal-cost profile plus unequal-cost, retries, backpressure and gaming cases. Freeze before counted execution.

**Negative cases:** Post-hoc tolerance changes invalidate run; retries charged to origin project; polling cannot bias service.

**Evidence and exit:** All preregistered traces incl. failures, expected/observed shares; lead freezes D23 tolerances before counting.

## 23-13

Artifact(s): V2.3-live. SP2. Depends: 23-08, 23-09, 23-10, 23-11, 23-12. Type: code.
Entry gates: EXT-V15-SECOND-HOST, EXT-V23-EXTERNAL-RESOURCE. Claim gates: none. Source state: planned.

**Owned surfaces:** `scripts/cp23_operations.py (new)`; `docs/evidence/v23/ (new run directory)`.

**Required behavior:** On >=2 physical nodes run competing projects under constrained real capacity; use non-fixture external action/provider, restart scheduler, drain worker, enable pack and export/import scoped knowledge.

**Negative cases:** No cross-project content/effect/receipt leakage; lost host and duplicate delivery do not duplicate external action.

**Evidence and exit:** CP23 physical identities, commands and exact policy/config/source refs; unavailable host/route blocks this claim only.

## 23-14

Artifact(s): V2.3-integrated-audit. SP2. Depends: 23-13. Type: code.
Entry gates: none. Claim gates: none. Source state: planned.

**Owned surfaces:** `docs/evidence/v23/independent-review/ (new report)`.

**Required behavior:** Independently reconcile scheduler/pack/portability/observability/fleet artifacts, lower candidate compatibility and external gates; freeze V3 source base.

**Negative cases:** Synthetic fleet cannot satisfy physical gate; open lower release gate remains visible; no worker self-review.

**Evidence and exit:** V2.3 review and V3 base handoff; formal acceptance only via canonical registry.

## V30A-001

Artifact(s): ART-V30-OBJECTIVE-CONTRACT. SP2. Depends: 23-14. Type: code.
Entry gates: none. Claim gates: none. Source state: planned.

**Owned surfaces:** `src/swarm/contracts/objectives.py (new)`; `src/swarm/db/models.py`; `migrations/versions/ (new revision)`.

**Required behavior:** Immutable ObjectiveVersion plus lifecycle row, TriggerReceipt and MissionProposal; unique(project,objective,version,occurrence), proposal->mission mapping. IDs never confer authority.

**Negative cases:** Duplicate trigger, cross-project FK, version overwrite, missing expiry/budget/trigger policy denied.

**Evidence and exit:** Real-DB unique/restart tests; expand repository separately if >3 production surfaces required.

## V30A-002

Artifact(s): ART-V30-OBJECTIVE-CONTRACT. SP2. Depends: V30A-001. Type: code.
Entry gates: none. Claim gates: none. Source state: planned.

**Owned surfaces:** `src/swarm/objectives/triggers.py (new)`; `src/swarm/controller/scheduler.py`.

**Required behavior:** One existing scheduler poll creates occurrences keyed by objective/version/schedule version/due instant. Explicit UTC/timezone and DST policy; skip/coalesce/bounded catchup required. No hidden cron daemon.

**Negative cases:** DST fold, clock rollback, missed week, concurrent polls and restart cannot multiply occurrences.

**Evidence and exit:** Fixed-clock algorithm tests plus real elapsed schedule later at CP30; no unit timestamp claimed live.

## V30A-003

Artifact(s): ART-V30-OBJECTIVE-CONTRACT. SP2. Depends: V30A-001, V30A-002. Type: code.
Entry gates: none. Claim gates: none. Source state: planned.

**Owned surfaces:** `src/swarm/objectives/triggers.py (new by V30A-002)`; `src/swarm/api/routes_v1.py`.

**Required behavior:** Authenticate event source and project before storing bounded payload refs; dedupe authenticated source event ID, not user-chosen global key. Transaction A30-01 emits proposal once.

**Negative cases:** Forged signature, replay across projects, oversize payload and stale objective version denied.

**Evidence and exit:** API contract and DB concurrency tests; source credentials never appear in trigger receipt.

## V30A-004

Artifact(s): ART-V30-OBJECTIVE-CONTRACT. SP2. Depends: V30A-002, V30A-003. Type: code.
Entry gates: none. Claim gates: none. Source state: planned.

**Owned surfaces:** `src/swarm/objectives/admission.py (new)`; `src/swarm/mission/runtime.py`.

**Required behavior:** Lock proposal/lifecycle; recheck current grants and intersect frozen objective limits, current project policy, template request and remaining resource envelope. Normal mission admission persists idempotent proposal link/outbox.

**Negative cases:** Revoked-after-trigger, crash after mission insert, changed template and duplicated delivery admit zero/one mission as appropriate.

**Evidence and exit:** Real-DB race/restart proof using existing kernel admission; no mission writer outside that boundary.

## V30A-005

Artifact(s): ART-V30-OBJECTIVE-CONTRACT. SP2. Depends: V30A-004. Type: code.
Entry gates: none. Claim gates: none. Source state: planned.

**Owned surfaces:** `src/swarm/objectives/admission.py`; `src/swarm/objectives/lifecycle.py (new)`.

**Required behavior:** Pause/revoke/expire updates durable generation before notifications; deterministic stop predicates checked on trigger and admission; in-flight work follows existing cancellation/effect fences.

**Negative cases:** Pause racing trigger, expiry before dispatch, stale cached lifecycle and model-requested self-extension denied.

**Evidence and exit:** Race tests with attempted tool effect; already-issued uncertain effects reconciled rather than claimed undone.

## V30A-006

Artifact(s): ART-V30-OBJECTIVE-CONTRACT. SP2. Depends: V30A-004, 23-12. Type: code.
Entry gates: none. Claim gates: none. Source state: planned.

**Owned surfaces:** `src/swarm/objectives/admission.py`; `src/swarm/controller/scheduler.py`.

**Required behavior:** Reserve objective max-active/rate/budget atomically with admitted mission and charge all children/retries to project scheduling state. Release slot idempotently on terminal mission.

**Negative cases:** Two triggers contend last slot, nested fanout and retry after crash cannot exceed envelope or reset fair share.

**Evidence and exit:** Objective/project ledger reconciliation tests and frozen fairness trace.

## V30A-007

Artifact(s): ART-V30-OBJECTIVE-CONTRACT. SP2. Depends: V30A-005, V30B-001, V30B-002. Type: code.
Entry gates: none. Claim gates: none. Source state: planned.

**Owned surfaces:** `src/swarm/objectives/lifecycle.py`; `src/swarm/learning/validation.py (new)`.

**Required behavior:** A learned objective/template becomes a proposed immutable version; authority diff must be subset/equal; activation requires completed learning workflow. Rollback returns exact predecessor and fences candidate generation.

**Negative cases:** Learning widens tools/spend, unknown predecessor or proposer-signed approval cannot activate.

**Evidence and exit:** Version/diff/rollback contracts with pending-learning negative; source implementation need not wait for live canary.

## V30A-008

Artifact(s): ART-V30-OBJECTIVE-CONTRACT. SP2. Depends: V30A-005. Type: code.
Entry gates: none. Claim gates: none. Source state: planned.

**Owned surfaces:** `src/swarm/objectives/read_model.py (new)`; `src/swarm/api/routes_v1.py`; `apps/console/ (bounded objective view)`.

**Required behavior:** Operator sees current objective version, next due time, missed policy, proposals, budget, stopped reason and evidence links. Pause/revoke through existing authenticated command boundary.

**Negative cases:** Cross-project timeline/counts and read-view mutation denied; unknown next run displayed as unknown.

**Evidence and exit:** API permission tests and operator journey to create/observe/pause/revoke without implementation detail in UI.

## V30B-001

Artifact(s): ART-V30-LEARNING-GOVERNANCE. SP2. Depends: 23-14, R05. Type: code.
Entry gates: none. Claim gates: none. Source state: planned.

**Owned surfaces:** `src/swarm/contracts/learning.py (new)`; `src/swarm/db/models.py`; `migrations/versions/ (new revision)`.

**Required behavior:** LearningProposal immutable candidate/scorer/dataset/parent digests and transition receipts; CAS expected_state. No worker-readable held-out answers; opaque sealed refs only.

**Negative cases:** State skip, duplicate transition, mutating frozen candidate and proposer pretending reviewer fail.

**Evidence and exit:** State-machine contract and DB tests; each evidence transition is separately auditable.

## V30B-002

Artifact(s): ART-V30-LEARNING-GOVERNANCE. SP2. Depends: V30B-001. Type: code.
Entry gates: none. Claim gates: none. Source state: planned.

**Owned surfaces:** `src/swarm/learning/validation.py (new)`; `src/swarm/review/ (bounded validator)`.

**Required behavior:** Validate learned target allowlist and authority diff. Protected scope includes permissions, spend, secrets, releases, graders, evidence collection and reviewer rules; transitive dependencies included.

**Negative cases:** Renamed governance file, path alias, config-only escalation and mixed code/governance diff rejected before eval.

**Evidence and exit:** Adversarial validation fixtures and policy digest; fixed rules, not model discretion.

## V30B-003

Artifact(s): ART-V30-LEARNING-GOVERNANCE. SP2. Depends: V30B-002, R05. Type: code.
Entry gates: none. Claim gates: EXT-G13-SEALED-DIGEST. Source state: planned.

**Owned surfaces:** `src/swarm/learning/evaluation.py (new)`; `src/swarm/evals/ (existing evaluator bridge)`.

**Required behavior:** Reuse calibrated reviewer and sealed evaluator. Freeze candidate/scorer/sample/threshold/stop digests before heldout; output signed/bound metrics, not answer data. Failed/contaminated candidate creates successor proposal.

**Negative cases:** Retune after freeze, leak references, sequential peeking and sample replacement invalidate run.

**Evidence and exit:** Separated evaluator process evidence for counted evaluation; deterministic harness work continues while sealed material pending.

## V30B-004

Artifact(s): ART-V30-LEARNING-GOVERNANCE. SP2. Depends: V30B-003. Type: code.
Entry gates: none. Claim gates: WC-V30-CANARY. Source state: planned.

**Owned surfaces:** `src/swarm/learning/canary.py (new)`; `src/swarm/learning/validation.py`.

**Required behavior:** Require independent review before canary; restrict candidate traffic/scope by frozen policy; deterministic guardrail breach atomically activates prior accepted version and fences candidate. No model-controlled rollback.

**Negative cases:** Self-review, missing rollback target, partial activation, stale worker and disabled guardrail fail closed.

**Evidence and exit:** Real bounded canary and observed rollback timestamps; test code passes before duration gate can close.

## V30B-005

Artifact(s): ART-V30-LEARNING-GOVERNANCE. SP2. Depends: V30B-004. Type: code.
Entry gates: none. Claim gates: none. Source state: planned.

**Owned surfaces:** `src/swarm/learning/canary.py`; `src/swarm/learning/lifecycle.py (new)`.

**Required behavior:** Pin model/tool/data-policy validity tuple to accepted learning version; material drift marks revalidation required and returns to safe predecessor. Preserve rejected/contaminated histories.

**Negative cases:** Changed provider version, expired evidence, missing predecessor and repeated drift cannot keep serving stale behavior.

**Evidence and exit:** Deterministic drift/restart tests; operator can inspect why learning version stopped.

## V30C-001

Artifact(s): ART-V30-RESOURCE-ALLOCATOR. SP2. Depends: V30A-006. Type: code.
Entry gates: none. Claim gates: none. Source state: planned.

**Owned surfaces:** `src/swarm/controller/scheduler.py`; `src/swarm/contracts/objectives.py`.

**Required behavior:** Allocator produces ObjectiveResourceRequest/scheduler preference inputs and a receipt; caps benefit/urgency by frozen policy and current grants. Existing V2.3 reservation/admission remains sole execution path.

**Negative cases:** Allocation cannot authorize denied provider/tool/privacy class or exceed project budget.

**Evidence and exit:** Reproducible allocation trace and scheduler receipt linkage; no allocator DB or second scheduler.

## V30C-002

Artifact(s): ART-V30-RESOURCE-ALLOCATOR. SP2. Depends: V30C-001. Type: code.
Entry gates: none. Claim gates: none. Source state: planned.

**Owned surfaces:** `tests/objectives/ (new allocation tests)`; `benchmarks/ (bounded allocation profile)`.

**Required behavior:** Run equal/unequal demand, starvation, unavailable capacity, child task amplification and privacy/cost shift cases with frozen policy.

**Negative cases:** Urgent objective cannot take unauthorized capacity; failures/retries charged to origin; denied route never treated as free.

**Evidence and exit:** Invariant/property traces plus CP30 comparison to scheduler-only baseline; no fabricated optimality claim.

## V30D-001

Artifact(s): ART-V30-CONTROLLED-SELFDEV. SP2. Depends: V30B-004, 19-07. Type: code.
Entry gates: none. Claim gates: none. Source state: planned.

**Owned surfaces:** `src/swarm/selfdev/runner.py`; `src/swarm/learning/validation.py`.

**Required behavior:** Represent bounded code fix as LearningProposal over 19-07 isolated path. Freeze source/diff/test/scorer/permissions and preserve protected verifier independence; no auto-publish.

**Negative cases:** Candidate code cannot edit protected acceptance tools or obtain producer credentials; external IDE output not counted as SwarmAI authorship.

**Evidence and exit:** Real selfdev candidate plus learning/eval/canary refs; reviewable commit/PR candidate, never self-merge.

## V30D-002

Artifact(s): ART-V30-CONTROLLED-SELFDEV. SP2. Depends: V30D-001. Type: code.
Entry gates: none. Claim gates: none. Source state: planned.

**Owned surfaces:** `tests/selfdev/ (new governance tests)`; `docs/evidence/v30/selfdev/ (new run directory)`.

**Required behavior:** Attack governance via renamed files, imports, dependencies, workflow and tool policy edits; prove mixed authority changes cannot enter autonomous promotion.

**Negative cases:** Disabling tests, altering hidden grader, widening release policy and gaining signing authority rejected.

**Evidence and exit:** Negative matrix on real candidate diff + independent security review.

## V30E-001

Artifact(s): ART-V30-CAPABILITY-ECOSYSTEM. SP2. Depends: 23-09, 19-03. Type: code.
Entry gates: none. Claim gates: none. Source state: planned.

**Owned surfaces:** `src/swarm/extensions/registry.py`; `src/swarm/contracts/extensions.py`.

**Required behavior:** Private digest-pinned publisher identity and revocation extend existing extension/pack registry. Public signature/distribution scope remains disabled until trust policy explicitly chosen.

**Negative cases:** Untrusted publisher, transitive digest swap, expired trust and signature metadata without validation cannot load.

**Evidence and exit:** Private provenance/lifecycle tests; shared registry and no public marketplace dependency.

## V30E-002

Artifact(s): ART-V30-CAPABILITY-ECOSYSTEM. SP2. Depends: V30E-001. Type: code.
Entry gates: none. Claim gates: none. Source state: planned.

**Owned surfaces:** `src/swarm/extensions/registry.py`; `src/swarm/tools/fences.py`.

**Required behavior:** Revoke publisher/package version, bump grant generation, deny new loading and action starts, drain in-flight work and invalidate cached versions across projects.

**Negative cases:** Offline worker, cached pack, nested dependency and restart cannot bypass revocation; old effects retained for reconcile.

**Evidence and exit:** Multi-process revocation propagation receipts with zero unauthorized starts after durable boundary.

## V30F-001

Artifact(s): ART-V30-FLEET-TENANCY-AUDIT. SP2. Depends: 23-11, 23-08, V30A-008. Type: code.
Entry gates: none. Claim gates: none. Source state: planned.

**Owned surfaces:** `src/swarm/observability/read_model.py`; `src/swarm/product/portability.py`.

**Required behavior:** Produce tenant/project scoped audit export linking objective triggers, mission admission, allocation, learning transitions and external effects. Stable IDs/digests allow reconstruction without raw model reasoning.

**Negative cases:** Cross-tenant identifiers, secret values, missing causal link and dangling receipt digest invalidate export.

**Evidence and exit:** Independent readback reconstructs one whole objective/effect chain and hashes exported artifacts.

## V30F-002

Artifact(s): ART-V30-FLEET-TENANCY-AUDIT. SP2. Depends: V30F-001. Type: code.
Entry gates: none. Claim gates: none. Source state: planned.

**Owned surfaces:** `tests/integration/tenancy/ (new tests)`; `docs/evidence/v30/tenancy/ (new run directory)`.

**Required behavior:** Cross-tenant matrix across triggers, learning, pack grants, allocator, worker placement and audit export, including existence inference and stale policy caches.

**Negative cases:** No content, counts, resource explanation or effects leak; restore/import cannot carry source authority.

**Evidence and exit:** Real-DB/multi-process negatives and CP30 adversarial project pair.

## V30X-001

Artifact(s): V3-integrated-evidence. SP1. Depends: V30A-008, V30B-005, V30C-002, V30D-002, V30E-002, V30F-002, V30A-007. Type: lead_decision.
Entry gates: none. Claim gates: none. Source state: planned.

**Owned surfaces:** `docs/coordination/FUTURE_ACCEPTANCE_WORKLOADS_V23_V30.json`; `docs/evidence/v30/candidate/ (new manifest)`.

**Required behavior:** Freeze V3 supported private profile, all six artifact criteria, objective templates, route/model/grader/workload digests, canary duration and stop rules before counted execution.

**Negative cases:** Unset thresholds, mutable source, absent external action authorization or unresolved critical defect blocks counted start.

**Evidence and exit:** Candidate/workload digest plus independent start receipt; cannot overwrite failed campaigns.

## V30X-002

Artifact(s): V3-integrated-evidence. SP2. Depends: V30X-001. Type: wall_clock.
Entry gates: EXT-V17-REALWORLD-GITHUB, REV-V30-CAMPAIGN-START. Claim gates: WC-V30-SCHEDULE. Source state: planned.

**Owned surfaces:** `scripts/cp30_objectives.py (new)`; `docs/evidence/v30/ (new run directory)`.

**Required behavior:** Real elapsed schedule and authenticated event create normal missions, constrained multi-project resource use and one reversible real external effect; restart/replay no duplicates; actual canary rollback observed.

**Negative cases:** Duplicate event, pause/revoke mid-run, failed provider and candidate rollback preserve bounds and receipts.

**Evidence and exit:** CP30 end-to-end real-world bundle for all six artifacts; unresolved external/canary gates stay pending.

## V30X-003

Artifact(s): V3-integrated-evidence. SP2. Depends: V30X-002. Type: audit.
Entry gates: none. Claim gates: none. Source state: planned.

**Owned surfaces:** `docs/evidence/v30/independent-review/ (new report)`; `docs/operator/ (final private runbook)`.

**Required behavior:** Independent artifact/evidence crosswalk through V3, all lower required gates dispositioned, no orphan critical defect. Verify install/operate/recover/export/private selfdev runbooks; produce operator handoff.

**Negative cases:** Missing artifact, mismatched evidence identity, self-review or open mandatory elapsed gate prevents acceptance.

**Evidence and exit:** V3 private operational candidate + independent review; product accepted only by registry, publishing remains separately authorized.
