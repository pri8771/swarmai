# Lead review — Fable 5.1 V1.7 → V3.0 planning pass

Date: 2026-09-21
Planning branch reviewed: `fable/v3-planning`
Decision: **APPROVED WITH LEAD AMENDMENTS**

## Scope of approval

This approves the planning/decomposition system for use by the implementation worker. It does **not** accept or verify any product artifact, version, live checkpoint, or release.

## Independent checks performed

- Compared planning branch against live `coordination/swarm-control`.
- Confirmed Fable audited implementation tip `f2b8d5f7dfd65530e73c63438c229b9fa428f922`, matching the active worker status during review.
- Independently spot-checked source claims:
  - `DurableEffectRepository` keeps receipts in process memory.
  - V1.7 gateway can default to `InMemoryEffectStore`.
  - mission worker still has direct `subprocess.run` and `write_text` effects.
  - `PermissionFirstRetriever` exists but is not on the operational mission path.
  - API store still owns an in-memory `WorkerRegistryService` while `DurableWorkerService` exists separately.
- Mechanically validated the combined V1.7, V1.8–V2.3, coarse future, and V3 packet graphs against all 86 canonical registry artifacts:
  - no duplicate packet IDs;
  - no unresolved dependencies;
  - no dependency cycles;
  - no undefined gates;
  - no uncovered planned-version registry artifacts;
  - no unmapped fine future packets.

## Fable findings accepted as materially correct

1. Broad R13–R27 evidence had overstated implementation progress: much of it re-verified source that landed earlier rather than implementing packet-specific behavior.
2. V1.5/V1.6/V1.7 are partially implemented as libraries but are not fully wired onto the operational mission path.
3. V1.7 exactly-once/effect semantics have real durability/atomicity gaps requiring R27a–R27e and R28a–R28d.
4. CP3 is real but incomplete; CP4 was not a real mission checkpoint; CP5/CP6 did not exist.
5. CI heartbeat churn likely contributed materially to the Actions spending-limit gate and should be corrected before billing is restored.

## Lead amendments

### A. Real-world acceptance policy
`REAL_WORLD_ACCEPTANCE_POLICY.md` is now binding.

Local fixtures are necessary engineering evidence but do not justify a milestone `working` claim.

### B. V1.7 R33c
After reproducible CP5 local-fixture semantics, run a reversible real GitHub external-action checkpoint through SwarmAI's own V1.7 boundary:
- create one uniquely named private-repo test issue;
- observe it;
- add one comment;
- close it;
- prove no duplicate external effect on replay;
- preserve receipts and never expose GitHub credentials.

### C. V2.3 and V3
- CP23 working proof requires physically distinct execution nodes plus a non-fixture external provider/tool interaction.
- CP30 counted evidence requires a real elapsed objective plus at least one reversible external action; restart/replay must not duplicate it.

## Immediate execution order

Do not resume with the old broad `R28` packet.

Use the approved micro-packet queue. Current high-value dependency-ready work includes:
1. `OPS-CI-01` — stop heartbeat commits from consuming CI runs.
2. `R27a` — durable immutable action receipts.
3. `R30a` — real local HTTP fixture infrastructure for deterministic fault semantics.
4. `R17a` — close CP3 cancellation/concurrent-accept gaps.
5. `R02a` — red→green defect proof gate before another V14 real mission.

After `R27a`, continue its durability chain before attempting CP5.

## External/user gates retained

- GitHub Actions billing/spending limit.
- G13 sealed-reference digest / qualification prerequisites.
- zero-charge remote provider admissions.
- second physical host where required.
- real elapsed wall-clock campaigns.

These gates must not idle dependency-independent implementation.

## Account/email authorization

The operator has authorized use of an existing test identity or a dedicated email/account alias when an artifact genuinely requires real identity/session proof. No account should be created merely to make a checklist green. Preferred V1.7 real-world proof uses the existing authenticated GitHub identity and requires no new account.

## Decision

Planning system: **APPROVED FOR CANONICAL PROMOTION**.

Product status: unchanged by this review.
