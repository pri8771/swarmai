# ART-V30-OBJECTIVE-CONTRACT — persistent objective schema

Status: drafting
Target: V3.0
Owner: ChatGPT lead

## Objective model

PersistentObjective:
- objective_id
- version
- project_id
- owner_actor
- name
- goal/desired outcome
- trigger_policy_ref
- mission_template_ref
- resource_policy_ref
- tool/integration allowlist
- data/privacy labels
- notification policy
- approval policy
- max_active_missions
- min_interval / rate bounds
- start_at / expires_at
- stop_conditions[]
- state: draft|active|paused|expired|revoked
- created_at / updated_at
- policy_version

## Trigger types

- manual
- schedule
- authenticated event/webhook
- artifact/state condition

Every trigger produces a TriggerReceipt:
- trigger_id
- objective_id/version
- source type/identity
- observed_at
- dedupe key
- payload digest/ref
- validation outcome

Raw webhook/event payload storage follows project data policy.

## Mission proposal

Trigger does not execute tools/models directly.

It creates MissionProposal:
- proposal_id
- objective/trigger refs
- project
- goal/input refs
- requested resource envelope
- required tools/providers
- dedupe/idempotency key
- reason

Normal mission admission validates proposal and creates a bounded mission.

## Safety

Objective cannot:
- grant itself new tools/providers/projects;
- increase spend/resource envelope beyond owner policy;
- disable approvals;
- change its own stop/expiry to avoid revocation;
- directly merge/release/deploy unless an independently approved tool policy explicitly permits that action.

## Lifecycle

activate -> trigger receipts -> bounded mission proposals -> normal missions.

Pause/revoke:
- prevents new mission proposals immediately;
- existing missions follow explicit cancel/drain policy;
- future schedules/events do not reactivate objective automatically.

## Evidence

- duplicate event creates one mission proposal;
- schedule survives restart without duplicate ticks;
- rate bound enforced;
- pause blocks new missions;
- expiry blocks new missions;
- objective edit creates new version;
- old trigger cannot use new expanded authority;
- cross-project trigger rejected.
