# ART-V30-LEARNING-GOVERNANCE — versioned operational learning

Status: drafting  
Target: V3.0  
Owner: ChatGPT lead  
Last advanced: 2026-09-21

## Goal

Allow SwarmAI to learn from observed missions and propose better operating procedures without converting model output, historical correlation, or a single successful run into production policy. Learning changes are immutable, versioned proposals that move through preregistered evaluation, independent review, bounded canary and reversible promotion.

This artifact defines the authority and evidence boundary. It does **not** authorize self-release, spending, permission changes, secret access or public deployment.

## Learnable targets

Permitted proposal targets, subject to their owning policy:
- prompt/template version;
- exact model-route profile and routing preference;
- decomposition/graph heuristic;
- repair/escalation rule;
- reusable procedure/runbook;
- capability-pack configuration;
- scheduler parameter inside an already-authorized envelope;
- context-selection/retrieval policy inside an existing project/data scope;
- deterministic tool selection or pre/post-processing rule.

Never self-learnable without an external authority change:
- authentication/authorization/approval bypass;
- project/tenant/data-boundary relaxation;
- secret access or retention expansion;
- spending, billing, quota-evasion or paid-fallback authority;
- hidden evaluation answers or scorer manipulation;
- evidence-retention deletion to hide failures;
- release/merge/deployment authority;
- safety-policy or human-approval removal.

A proposal that would indirectly change one of these protected dimensions is classified as an authority change and is ineligible for autonomous promotion even if measured quality improves.

## LearningProposal schema

Every proposal must persist:
- `proposal_id`, `target_type`, `target_id`;
- `parent_version` and immutable `candidate_version`/content hash;
- exact diff/parameter delta;
- source mission IDs and evidence refs;
- hypothesis and causal mechanism claimed;
- primary metric and direction of improvement;
- guardrail metrics and maximum tolerated regressions;
- risk class and affected project/data/tool/provider scopes;
- calibration dataset/version/hash;
- held-out dataset/version/hash, held-out access policy and scorer version;
- sample-size/confidence rule and stop conditions frozen **before** held-out execution;
- total request/token/time/cost envelopes;
- canary population/scope, duration/event count and rollback trigger;
- rollback artifact/version and restore procedure;
- proposer identity/runtime version;
- creation time, evaluation state and independent reviewer decision.

The held-out answer/reference corpus is not exposed to the proposer/worker. A proposal that observed its held-out answers is contaminated and cannot be promoted on that evidence.

## Proposal state machine

`observed -> proposed -> static_validated -> calibration_passed -> frozen -> heldout_running -> heldout_passed -> independently_reviewed -> canary_running -> accepted`

Terminal/side states: `rejected`, `contaminated`, `expired`, `rolled_back`, `superseded`, `blocked`.

Only software-enforced transitions are valid. Models may recommend a transition; they cannot write an accepted state directly. Every state transition records actor, source version, evidence hashes and wall-clock timestamp.

## Evaluation pipeline

1. Collect operational observations with provenance; observations are evidence, not truth.
2. Form one bounded hypothesis and candidate change. Multi-change proposals must be decomposed when attribution would be ambiguous.
3. Run static/policy/schema/security checks and reject protected-authority changes.
4. Run calibration experiments. Calibration can tune the candidate and scorer but cannot count as held-out evidence.
5. Freeze candidate content, metric definitions, scorer, datasets, sample/confidence rule, resource envelope and stop conditions.
6. Execute held-out evaluation and retain **all** attempts, failures and early stops.
7. Compute primary/guardrail results with the preregistered rule; do not change thresholds after seeing held-out results.
8. Independent reviewer checks provenance, leakage, selection bias, multiple-comparison risk, resource overhead and security/policy effects.
9. If eligible, run a limited canary under explicit rollback triggers. No canary may exceed the target's existing authority envelope.
10. Accept the version only after canary evidence passes; otherwise reject or roll back. Accepted version and parent remain reproducibly retrievable.
11. Continue drift/regression monitoring. Drift can trigger an alert/proposal or pre-authorized rollback, never an unrestricted rewrite.

## Statistical and selection discipline

- Compare against the current accepted parent and any declared simple baseline, not only against a weak historical run.
- Report effect size, sample count and uncertainty, not just pass/fail percentage.
- Multiple competing proposals require a preregistered selection rule or correction; do not run many candidates and publish only the winner without accounting for selection.
- Sequential stopping is allowed only if the stopping rule was frozen first.
- Missing/failed attempts remain in the denominator where the metric contract says they should.
- Resource savings count only when total orchestration, retries, review and repair overhead are included.
- Provider/model changes must preserve exact route/config identity; a model-family label alone is insufficient.
- A proposal can be **useful but unproven**; that state remains drafting/proposed rather than being promoted through optimistic language.

## Guardrails and rollback

Every target class declares non-negotiable guardrails. Default guardrail families:
- authorization and data-scope violations: zero tolerated;
- forbidden/unapproved side effects: zero tolerated;
- unapproved spend: zero tolerated;
- acceptance/evidence fabrication: zero tolerated;
- duplicate consequential effects: zero tolerated;
- latency/cost/token/error regressions: target-specific preregistered limits.

Canary rollback triggers must be executable without model judgment for safety-critical guardrails. Rollback restores the prior accepted version and fences stale workers/schedulers from continuing the rejected candidate. Rollback itself creates an immutable receipt; it does not erase failed canary evidence.

## Interaction with persistent objectives

A persistent objective may propose learning work only when its ObjectiveContract allows it. Learning proposals cannot expand the objective's allowed tools, data, spend, cadence or external-action scope. If a learned procedure would change objective semantics, create a new objective version requiring the normal objective-approval path instead of silently mutating the active one.

Scheduler/fleet optimization proposals must preserve fairness and quota invariants from V2.3. An apparent throughput win caused by starving another project, evading provider limits or shifting hidden cost is a guardrail failure.

## Drift and revalidation

Accepted learned versions record:
- baseline input/performance distributions;
- dependency/provider/tool versions;
- recheck time/event triggers;
- minimum fresh sample requirement;
- rollback version and expiry criteria.

Trigger revalidation on material model/provider version change, scorer change, tool/API behavior change, data-distribution shift, repeated repair escalation, security-policy change, or observed guardrail breach. Stale evidence can downgrade a learned version to `blocked`/`expired`; it cannot be silently grandfathered forever.

## Controlled self-development

Code-changing proposals use the same LearningProposal discipline plus:
- isolated branch/worktree;
- explicit files/ownership and no concurrent writer conflict;
- deterministic tests plus relevant integration/security tests;
- independent code/security review by a reviewer that did not author the change;
- immutable before/after source SHAs;
- no self-merge, tag, release or production deploy.

A self-development proposal may improve SwarmAI's implementation, but it may not modify this governance contract, its own evaluation evidence, or its reviewer/approval policy inside the same proposal.

## Acceptance protocol for ART-V30-LEARNING-GOVERNANCE

Before this artifact can move from drafting to reviewable/verified, demonstrate at least these synthetic-or-isolated governance scenarios (not a production learning claim):
1. a quality-improving prompt proposal passes calibration and held-out evaluation but violates a cost guardrail and is rejected;
2. a route proposal with hidden held-out contamination is marked contaminated and cannot be accepted;
3. two competing proposals use a frozen selection rule and retain losing-candidate evidence;
4. a bounded canary triggers a deterministic rollback and stale candidate execution is fenced;
5. a protected authority-change proposal (for example spend or permission expansion) is blocked before held-out execution;
6. an accepted procedure is later expired by dependency drift and requires fresh evidence;
7. a self-development proposal produces a reviewed PR candidate but cannot merge itself.

Evidence must include exact schema/version hashes, transition receipts, all attempts, reviewer identity/decision and rollback proof. Passing governance tests does not prove any particular learned policy is beneficial in production.

## Examples

- Routing proposal improves held-out family/size quality with lower total overhead; canary passes; exact version is accepted.
- Prompt proposal improves quality but doubles cost/latency past a frozen guardrail -> rejected.
- Scheduler tweak increases aggregate throughput by starving a low-priority project beyond the fairness contract -> rejected.
- Learned procedure later becomes stale after a provider/tool change -> expired; old evidence remains preserved.
- Canary regression crosses a deterministic guardrail -> execution is fenced and the parent version restored with a rollback receipt.
