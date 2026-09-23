# ART-V30-OBJECTIVE-CONTRACT — persistent authorized objectives

Status: drafting
Target: V3.0
Owner: ChatGPT lead
Depends on: ART-V23-MULTIMISSION-OPS, ART-V30-LEARNING-GOVERNANCE, V2 authorization/effect boundaries

## Goal

A persistent objective is a durable owner-authorized policy that may propose bounded missions over time. It is **not** a long-running super-agent, a standing browser session, a source of new authority, or a way to bypass normal mission admission. Every trigger becomes a recorded proposal; normal Swarm project, resource, provider, tool, approval, site-epoch and acceptance fences still decide whether anything executes.

The V2.3 multi-mission scheduler determines fair ordering among admitted work. The V3 objective layer decides only whether a valid trigger may propose a mission under already granted authority. Governed learning may propose a new objective/template/policy version, but it cannot activate or broaden that version by itself.

## Durable objective model

`PersistentObjective`:
- `objective_id`
- immutable `version`
- `project_id`
- `owner_actor_id` / owning authority reference
- `name`
- `desired_outcome` / goal contract
- `trigger_policy_ref`
- `mission_template_ref`
- `resource_policy_ref`
- `provider_policy_ref`
- `tool_integration_allowlist`
- `data_scope_ids` / privacy labels / locality constraints
- `notification_policy_ref`
- `approval_policy_ref`
- `max_active_missions`
- `max_proposals_per_window`
- `min_interval_seconds`
- optional `start_at`, `expires_at`
- `stop_conditions[]`
- `cancel_existing_on_revoke` policy
- state: `draft | active | paused | expired | revoked`
- `created_at`, `activated_at`, `updated_at`
- `authority_snapshot_digest`
- `policy_version`

Mutable edits never rewrite the active version. A material edit creates a new objective version and passes the same authorization/admission checks before activation. Old trigger receipts remain bound to the old version and authority snapshot.

## Trigger boundary

Allowed trigger classes:
- explicit manual trigger;
- durable schedule occurrence;
- authenticated event/webhook;
- artifact/state condition evaluated from authorized project data.

Every observed trigger creates an immutable `TriggerReceipt` before any mission proposal:
- `trigger_receipt_id`
- `objective_id` / `objective_version`
- project/authority snapshot reference
- source class and authenticated source identity/reference
- `observed_at`
- source event/schedule occurrence ID
- dedupe/idempotency key
- payload digest and safe payload reference
- validation/policy result
- rejection reason when invalid
- scheduler/site epoch where relevant

Raw event payload storage follows project data policy. Receipts contain no credential, cookie, browser state or sensitive token.

### Schedule semantics

A schedule occurrence has a deterministic occurrence ID derived from objective version + schedule rule version + due instant. After restart, the scheduler reconciles missed/claimed occurrences from durable state rather than replaying all wall-clock ticks blindly.

Policy must explicitly define one of:
- `skip_missed`;
- `coalesce_latest`;
- bounded catch-up with a fixed maximum count.

No default may generate an unbounded mission burst after downtime.

### Event semantics

Webhook/event triggers require authenticated source identity, replay protection, payload-size bounds and a versioned mapping into a project-scoped input reference. Duplicate/retried events yield one trigger receipt/proposal for the same dedupe scope. Cross-project source references fail closed.

## Mission proposal contract

Triggers do not call models, tools, browsers or workers directly. A validated trigger may create a `MissionProposal`:
- `proposal_id`
- `project_id`
- objective/version and trigger-receipt references
- `mission_template_version`
- goal + input/artifact references
- requested resource envelope
- requested provider/tool capability classes
- data/privacy/locality labels
- requested priority/deadline class
- proposal dedupe key
- reason / trigger class
- `created_at` / `expires_at`
- state: `proposed | admitted | rejected | superseded | expired`

Normal mission admission re-checks current project authority and converts an admitted proposal into a normal bounded mission. The proposal cannot carry a broader resource/tool/provider/data scope than the active objective snapshot, even if the mission template was edited later.

## Authority monotonicity

A persistent objective can never increase its own effective authority.

Required rules:
- objective authority is the intersection of current owner/project policy and the objective's frozen authorization snapshot;
- template/provider/tool/resource-policy changes can only narrow authority without new owner approval;
- adding a project, data scope, tool, provider, side-effect class, spending authority, public-posting/deployment authority or larger hard resource envelope requires an externally authorized new version;
- objective code/model output cannot change its own stop, revoke or expiry controls;
- paused/revoked/expired objectives cannot reactivate from an event or learned policy;
- mission admission always re-checks current revocation/project state; a once-valid trigger receipt does not grandfather stale authority.

Main merge, public release/deployment, additional spend and other owner-gated actions remain separately gated unless a future explicit owner policy changes that boundary. No V3 artifact may infer those permissions from objective activation.

## Relationship to V2.3 fairness

Objective priority is an input to the V2.3 scheduler, never a bypass. Persistent objectives share the same project-level fair-service entitlement as manual missions.

Anti-gaming invariants:
- many objective versions cannot multiply a project's fair-share credit;
- many triggers cannot bypass `max_active_missions`, project quotas or provider/tool reservations;
- retries, repair missions and follow-up missions remain charged to the same project fairness/resource policy;
- objective priority/deadline bonuses are bounded by the scheduler contract;
- blocked objectives consume no runnable share;
- scheduler credit cannot authorize a route/tool denied by the broker/gateway.

## Learning-governance boundary

`ART-V30-LEARNING-GOVERNANCE` may create a versioned `LearningProposal` suggesting changes to prompts, decomposition, routing, templates, trigger filters or objective parameters. It may not mutate an active objective in place.

Any learned change that affects behavior becomes a candidate version with:
- parent objective/template/policy version;
- exact changed fields/digest;
- calibration/held-out evidence references;
- protected-authority diff;
- rollout/canary policy;
- rollback target;
- independent review/owner approval state where authority or consequence expands.

A learned version cannot see held-out answers used to accept itself. Acceptance/rollback follows the frozen learning-governance contract and leaves the prior version available for deterministic rollback.

## Concurrency and duplicate prevention

Two schedulers/processes may observe the same event or due schedule. Exactly one durable trigger receipt/proposal becomes authoritative for a dedupe scope.

Recommended transaction boundary:
1. claim occurrence/event dedupe key with durable unique constraint or equivalent CAS;
2. load objective/version/current authority;
3. validate state/rate/expiry/stop conditions;
4. write TriggerReceipt;
5. write MissionProposal if valid;
6. emit outbox event;
7. commit.

External effects never occur inside this transaction. Mission creation/admission is an idempotent later transition.

## Lifecycle

`draft -> active -> paused | expired | revoked`.

Pause:
- blocks new proposals immediately;
- preserves schedule/event receipts as rejected/paused evidence where useful;
- existing missions follow the objective's explicit drain/cancel policy.

Revoke:
- is irreversible for that objective version;
- blocks new proposals immediately;
- fences pending unadmitted proposals;
- existing missions are cancelled or drained under the frozen revoke policy, with normal cancellation-generation/effect fencing.

Expiry behaves like a deterministic time-based revocation for new proposals. No trigger extends expiry.

## Stop conditions

Stop conditions are deterministic/project-scoped predicates evaluated before proposal creation and at policy-defined mission completions. Examples:
- target artifact accepted;
- bounded count reached;
- deadline reached;
- error/denial threshold reached;
- operator stop flag;
- resource/quota policy enters terminal blocked state.

Model-generated text alone cannot be a privileged stop-condition interpreter. If semantic evaluation is necessary, the result is advisory and a deterministic policy transition consumes it.

## Observability and audit

Every objective version exposes safe status:
- current state/version;
- last trigger receipt and last admitted mission refs;
- next schedule occurrence when applicable;
- active/pending mission counts;
- proposal/rejection counts by reason;
- current hard rate/resource caps;
- current authority snapshot digest;
- last policy/learning rollout version.

Audit export links trigger -> proposal -> mission -> scheduling/admission receipts -> artifacts/results without embedding private raw content.

## Threat model / required negatives

- duplicate webhook delivery;
- duplicate schedule runner after restart;
- stale trigger from old objective version;
- event references another project's artifact;
- objective edited to add a tool/provider/data scope without approval;
- learned policy proposes an authority expansion;
- project/operator revokes authority after trigger but before mission admission;
- thousands of rapid triggers attempt scheduler/share amplification;
- restart after trigger receipt but before proposal write;
- restart after proposal write but before mission admission;
- objective paused/revoked while active missions/effects exist;
- stale site/scheduler epoch attempts to admit or effect work;
- clock jump/downtime tries to create unbounded missed schedules.

All must fail closed on authority and duplicate effects while retaining an explainable receipt.

## Acceptance protocol

V3 objective acceptance requires deterministic and private-live evidence on a candidate-bound source/config set:

1. Duplicate event produces exactly one authoritative proposal/mission.
2. Scheduled objective survives real process restart with no duplicate occurrence; chosen missed-run policy is observed.
3. Rate/max-active bounds hold under a trigger burst.
4. Pause blocks new proposals immediately; revoke cannot be undone for that version.
5. Objective edit creates a new immutable version; old receipts cannot use new authority.
6. Owner/project authority revoked after trigger but before admission causes proposal rejection/fencing.
7. Cross-project trigger/data scope fails without content/count/existence leak.
8. Multiple objectives in one project do not multiply project fairness entitlement.
9. Learning proposal cannot activate an authority-expanding objective/template version; independent approval boundary is enforced.
10. A learned non-authority behavior change canary can roll back deterministically to the parent version after a forced regression.
11. Trigger/proposal/mission/scheduling receipts form a complete trace with no secrets.
12. Wall-clock schedule evidence records actual elapsed time; no simulated timestamp is presented as live acceptance.

## Bounded implementation packets (future)

- `V30A-001` SP2: objective/version + TriggerReceipt durable contracts/repository and dedupe constraints.
- `V30A-002` SP2: schedule occurrence/restart/missed-run reconciliation.
- `V30A-003` SP2: authenticated event trigger/replay/cross-project validation.
- `V30A-004` SP2: MissionProposal + normal mission-admission bridge with authority intersection.
- `V30A-005` SP2: pause/revoke/expiry/stop-condition fencing.
- `V30A-006` SP2: V2.3 fairness/resource integration and anti-amplification tests.
- `V30A-007` SP2: learning-candidate version/authority diff/rollback integration.
- `V30A-008` SP2: audit/status/operator surface.

Do not schedule these source packets ahead of the V2.0/V2.3 dependencies unless they can be isolated behind frozen interfaces without competing persistence authorities.
