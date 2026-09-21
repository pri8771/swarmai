# ART-V30-LEARNING-GOVERNANCE — versioned operational learning

Status: drafting
Target: V3.0
Owner: ChatGPT lead

## Goal

Allow SwarmAI to propose improvements from observed missions without turning model output into unreviewed production policy.

## Learnable targets

- prompt/template
- model routing profile
- decomposition heuristic
- repair/escalation rule
- reusable procedure
- capability-pack config
- scheduler parameter within allowed range

Not learnable without explicit higher authority:
- permissions/approval bypass;
- secret access;
- spend authorization;
- tenant/project boundaries;
- hidden evaluation answers;
- release authority.

## LearningProposal

- proposal_id
- target type/id
- current version
- proposed version/diff
- source mission/evidence refs
- hypothesis/rationale
- expected benefit
- risk class
- calibration dataset/version
- held-out eval protocol ref
- rollout policy
- rollback artifact
- proposer
- created_at

## Pipeline

1. collect observations as evidence, not truth;
2. generate proposal;
3. static/policy validation;
4. calibration experiments;
5. freeze proposal/config/eval;
6. held-out evaluation;
7. independent review;
8. limited canary;
9. observe drift/regression;
10. accept new version or rollback.

No threshold changes after held-out results.

## Acceptance criteria

Target-specific, but always:
- improvement on declared primary metric;
- no regression past declared guardrails;
- no new policy/security violations;
- complete resource/cost overhead;
- reproducible exact versions;
- rollback tested where consequential.

## Drift

Accepted learned versions record:
- baseline distribution/performance;
- recheck triggers/time;
- rollback version.

Drift detector produces a proposal/alert, not an automatic unrestricted rewrite.

## Self-development

Code changes use the same LearningProposal discipline plus:
- isolated source branch;
- tests;
- independent code/security review;
- no self-merge/release.

## Evidence examples

- routing proposal improves held-out family/size cells, canary succeeds, version accepted;
- prompt proposal improves quality but doubles cost/latency past guardrail -> rejected;
- learned procedure later superseded due source change;
- canary regression automatically pauses rollout and restores previous version according to preapproved rollback policy.
