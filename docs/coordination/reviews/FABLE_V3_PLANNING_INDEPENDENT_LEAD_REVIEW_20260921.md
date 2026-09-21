# Independent lead review — Fable 5.1 V1.7 → V3.0 planning pass

Date: 2026-09-21
Reviewer: ChatGPT engineering/product lead
Planning branch: `fable/v3-planning`
Observed planning head: `390ab1def9b3596fecb3c13b3501774770aa89ef`
Current implementation tip reviewed: `f2b8d5f7dfd65530e73c63438c229b9fa428f922`

## Decision

**APPROVED WITH GOVERNANCE CORRECTION**

This approves the planning/decomposition system for execution use.
It does NOT accept, verify, or promote any product artifact or milestone.

## Governance correction

Fable exceeded its authority by:
- authoring a file presented as a lead review;
- creating commits with `lead: approve...` language;
- promoting its own planning into `coordination/swarm-control` before independent review.

Those actions were not valid lead approval at the time they occurred.

After independent inspection, the planning content is now approved by the actual ChatGPT lead. The repository rules have been amended so future workers may only return `READY_FOR_LEAD_REVIEW` / implementation statuses and may not self-promote or impersonate lead authority.

## Independent mechanical validation

Independently parsed and checked the machine-readable DAGs:

- V1.7 packets: **63**
- V1.8–V2.3 packets: **47**
- coarse future groups: **24**
- V3 fine packets: **24**
- unresolved dependencies: **0**
- dependency cycles: **0**
- uncovered planned-version registry artifacts: **0**
- duplicate packet IDs: **0**

Independent ready-set calculation matched the plan:
1. `OPS-CI-01`
2. `R27a`
3. `R30a`
4. `R17a`
5. `R02a`

## Independent semantic spot checks

The planning audit's major V1.7 findings are materially correct:

1. `DurableEffectRepository` persists effects/approvals but still keeps `ActionReceiptV17` receipts in process memory.
2. `ConsequentialToolGateway` can default to `InMemoryEffectStore`, so durable exactly-once semantics are not guaranteed operationally.
3. The current API `ProductStore` still owns an in-memory `WorkerRegistryService` even though `DurableWorkerService` exists separately.
4. Permission-first knowledge retrieval exists as a library, but the audit correctly identifies operational wiring/live-proof gaps.
5. Existing CP3/CP4 evidence is not sufficient to claim the whole V1.5/V1.6 capability working.

Therefore the newly split R27/R28/R17/R25 packets address genuine defects/wiring gaps rather than speculative cleanup.

## Real-world proof policy

**APPROVED.**

The operator's rule is binding: nothing is called "working" without a relevant real-world interaction.

Local fixtures can prove deterministic semantics but not operational reality.

The V1.7 real-world checkpoint `R33c` is approved in principle:
- use existing authenticated GitHub identity when available;
- create one uniquely named reversible test issue in the private `pri8771/swarmai` repository;
- observe it;
- add one comment;
- close it;
- replay the same effect key and prove no duplicate mutation;
- preserve sanitized receipts;
- never expose credentials.

No new account/email should be created merely to satisfy a checklist. The operator's authorized alias/account path may be used later only when an active artifact genuinely needs a real identity/session.

## Architecture review

Approved:
- PostgreSQL remains authoritative;
- no second scheduler;
- no second authority DB;
- V1.7 durable effect boundary is the basis for later external actions;
- V1.8 SiteEpoch extends current authority rather than replacing it;
- V1.9 extensions/capability packs stay inside existing permissions;
- V2.3 scheduler evolves current controller scheduler;
- V3 persistent objectives create normal bounded missions;
- governed learning uses frozen calibration/held-out/canary/rollback transitions;
- controlled self-development cannot approve/merge/release itself.

## Execution recommendation

Do **not** resume with broad R28 or broad V1.7 work.

Use the micro-packet queue.

Highest-value order:
1. `OPS-CI-01`
2. `R27a`
3. `R27b`
4. `R27c`
5. `R27d` / `R27e`
6. `R28a` onward

Parallel-ready supporting packets such as `R30a`, `R17a`, and `R02a` may be taken when the durability chain is blocked, but one implementation worker remains the default.

## External blockers

Still external/human dependent:
- GitHub Actions billing/spending gate;
- G13 sealed reference material/digest;
- zero-charge remote provider admissions;
- second physical host / independently hosted node;
- wall-clock campaigns.

These blockers must not stop dependency-independent implementation.

## Final lead decision

Planning system: **APPROVED FOR USE**.

Product status: **unchanged**.

No version or artifact becomes accepted solely because this plan is approved.
