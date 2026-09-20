# Worker story-point protocol and performance calibration

Version: 1.0
Adopted: 2026-09-20
Scope: SwarmAI implementation workers, currently Cursor.

## Purpose

The engineering lead should spend lead time on architecture, ambiguity removal, debugging hard failures, evidence design, independent review and acceptance. The implementation worker should receive the bulk of executable work, especially routine and well-bounded work.

Story points measure task complexity/risk/coordination, not elapsed time.

## Story-point scale

### SP1 — trivial / mechanical
Typical characteristics:
- one small file or one narrowly scoped configuration/document/test;
- known pattern, no architectural decision;
- deterministic acceptance command;
- no live external dependency.

Examples: add a regression case, update one schema field, bind an evidence hash, fix a localized type/lint error.

Default owner: worker.

### SP2 — straightforward bounded implementation
Typical characteristics:
- one subsystem, usually 1–4 files;
- clear contract and test plan;
- low ambiguity;
- may require a local tool/browser action but no cross-system redesign.

Examples: add one API route with tests, add a console control using an existing API, add a provider eligibility probe, install/verify a local scheduler.

Default owner: worker.

### SP3 — moderate integration
Typical characteristics:
- several files or two adjacent subsystems;
- integration tests/evidence needed;
- some failure-mode reasoning;
- limited coordination with shared contracts.

Examples: cross-interface mission flow, broker reservation/reconcile behavior, provider adapter plus acceptance proof, evaluation batch runner with evidence binding.

Default owner: worker, with lead-provided acceptance contract.

### SP4 — complex cross-subsystem task
Typical characteristics:
- security/runtime/storage/UI or provider interactions;
- meaningful design ambiguity;
- high regression surface;
- live external evidence or migration risk.

Default handling: lead first tries to split into SP1–SP3 packets. If irreducible, worker receives an explicit design/acceptance packet and the lead reviews intermediate checkpoints.

### SP5 — system-level / high-uncertainty task
Typical characteristics:
- architecture-wide behavior;
- several independent failure modes;
- external systems + live evidence;
- difficult to test atomically;
- likely to create hidden rework if assigned as one blob.

Default handling: do **not** hand a vague SP5 directly to the worker. Lead decomposes it into independent SP1–SP3 packets plus one bounded integration/acceptance task. An irreducible SP5 experiment is allowed only with a preregistered stop condition, resource envelope and evidence plan.

## Assignment policy

1. Keep a ready queue of at least 3 bounded worker packets while implementation is active.
2. Prefer SP1–SP3 worker tasks.
3. Give mechanical/easy work to the worker even when the lead could do it faster, unless the work is needed immediately to unblock review.
4. Lead should directly perform:
   - independent code/evidence review;
   - acceptance protocol design;
   - hard debugging where worker retries are not converging;
   - external research that prevents wasted implementation;
   - task decomposition and dependency removal;
   - statistical/evaluation analysis;
   - conflict resolution on shared contracts.
5. When a worker fails/reworks an SP4–SP5 task repeatedly, split it before assigning another attempt.
6. Do not create artificial work merely to keep the worker busy. Future backlog work starts only when it cannot distract from current authorized release gates.
7. V1.5+ implementation remains version-gated by owner authorization. Lead may prepare research/decomposition/backlog items ahead of time, but must not silently turn planning into unauthorized implementation.

## Worker performance ledger

Every substantive worker packet should record:

- packet_id
- story_points_estimated (1–5)
- version/gate
- task_family (code/test/docs/infra/live-evidence/research/integration)
- source/base SHA
- acceptance criteria
- external dependency / human dependency
- started_at
- completed_at
- final SHA(s)
- first_pass_ci (pass/fail/not-applicable)
- first_lead_review (accepted/changes-required/blocked)
- rework_cycles
- reopened_defect (yes/no)
- evidence_complete_first_submission (yes/no)
- status (completed/blocked/split/abandoned)
- notes/blocker class

Do not infer elapsed work time from commit timestamps when the worker may have been idle/offline. Track wall-clock only for explicitly observed runs.

## Aggregation by story-point size

After at least five completed packets at a point size, report:

- completed count;
- first-lead-review acceptance rate;
- first-pass CI rate where applicable;
- median rework cycles;
- defect reopen count;
- evidence-completeness rate;
- blocker distribution (code, environment, auth, external provider, ambiguous contract).

Do not compare SP levels as a contest: higher points intentionally contain more uncertainty. The goal is to learn what size of packet the worker executes reliably and where decomposition improves throughput.

## Initial calibration policy

Prospective tracking begins with packets created after this protocol. Older V1 repair work may be listed as historical context but must not be assigned precise performance metrics unless evidence supports them.

Every lead heartbeat should:
- inspect newly completed worker packets;
- update the performance ledger only from evidence;
- assign the next ready SP1–SP3 packets;
- split any blocked SP4–SP5 packet;
- keep later work queued without jumping current acceptance gates.
