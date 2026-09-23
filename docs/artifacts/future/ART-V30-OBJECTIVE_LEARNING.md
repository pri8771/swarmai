# ART-V30-OBJECTIVE-LEARNING — persistent objectives and governed learning

Status: drafting
Target milestone: V3.0
Owner: ChatGPT lead

## Purpose

V2 completes bounded missions. V3 manages continuing authorized objectives that create many bounded missions over time and improves procedures under independent evidence.

The objective layer must never become an unbounded self-permission mechanism.

## Persistent objective contract

Objective:
- objective_id/version
- project_id
- owner
- goal
- trigger policy: schedule|event|manual
- permitted mission template(s)
- resource/spend envelope
- allowed tools/integrations
- data/privacy policy
- notification policy
- stop conditions
- expiry
- human approval rules
- active/paused/revoked state

An objective can create a mission only when the trigger + policy + current resource admission all pass.

## Mission creation boundary

Objective scheduler emits a proposed mission artifact.
Software validates:
- objective still active;
- trigger authentic/current;
- rate/cadence bounds;
- resource budget;
- task/tool scopes;
- duplicate event/idempotency;
- project/site policy.

Then it creates a normal bounded mission. V3 does not invent a second unsafe execution path.

## Governed learning

LearningProposal:
- proposal_id
- source missions/evidence
- target: prompt|routing|decomposition|procedure|capability config
- current version
- proposed version/diff
- rationale
- calibration evidence
- held-out evaluation plan
- risk class
- rollback artifact

Flow:
1. propose;
2. test on calibration;
3. freeze;
4. held-out evaluation;
5. independent acceptance;
6. limited rollout/canary;
7. monitor drift;
8. accept or rollback.

Model-generated memory or "this worked once" is never automatically promoted into production policy.

## Controlled self-development

Self-development produces:
- issue/problem;
- isolated branch/worktree;
- code/artifacts;
- tests;
- independent reviewer evidence;
- PR candidate.

It cannot:
- change its own permission boundary;
- approve credentials/spend;
- merge/release itself;
- alter hidden grader answers;
- change evaluation thresholds after results.

## Cross-project resource allocator

Allocator operates on resource metadata, not pooled private content.

Inputs:
- mission/project priority;
- deadlines;
- provider quotas;
- worker capacity;
- data locality/trust;
- fairness policy.

Outputs are reservations/admission decisions with explanations/audit.

## Capability ecosystem

Signed/versioned packs with:
- manifest;
- provenance;
- compatibility;
- permissions;
- tests;
- migration;
- publisher identity/trust policy.

No unrestricted arbitrary-code marketplace.

## V3 exit examples

- scheduled objective creates bounded mission and stops at objective expiry;
- event duplicate creates one mission;
- two projects share provider quota fairly without data leakage;
- a routing change is proposed, evaluated, canaried and rolled back on regression;
- Swarm prepares its own useful PR but cannot merge it;
- operator can pause/revoke objective and prevent future mission creation.
