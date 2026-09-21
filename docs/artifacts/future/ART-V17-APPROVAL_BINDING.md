# ART-V17-APPROVAL-BINDING — unified consequential action schema

Status: drafting
Target: V1.7
Owner: ChatGPT lead
Depends on: ART-V17-TOOL-CONTRACT

## ActionEnvelope

Required:
- action_id
- mission_id / task_id / attempt_id
- project_id
- actor
- integration_id / integration_version
- operation
- destination canonical form
- normalized_payload
- payload_hash
- requested_scopes[]
- side_effect_class: none|idempotent|consequential|irreversible
- risk_class
- idempotency_key/effect_key
- lease_generation
- cancellation_generation
- policy_version
- created_at

## ApprovalGrant

Binds:
- approval_id
- project_id
- actor/grantor
- integration/version
- operation
- destination
- exact payload_hash OR explicit constrained payload schema/hash
- maximum effect count
- allowed effect key
- expiry
- revocation state
- policy_version

Changing destination, operation, effect key or payload outside the approved constraint requires a new approval.

## ActionReceipt

- action_id / effect_key
- approval_id optional
- pre-observation
- execution_started_at / finished_at
- external_id optional
- outcome: succeeded|failed|unknown|denied|cancelled
- post-observation
- reconciliation_state
- attempt refs
- tool/integration version
- evidence digest

Unknown external outcome must enter reconciliation; blind retry is forbidden.

## Adapter interface

Every integration adapter implements:
- normalize(request) -> ActionEnvelope
- validate(envelope)
- observe_pre_state(envelope)
- execute(envelope)
- observe_post_state(envelope)
- reconcile(envelope, prior_receipts)

Adapter never decides project authorization or approval validity; ToolGateway/policy owns that.

## Session/browser addition

BrowserSessionRef contains safe alias/profile reference only; credentials/cookies stay outside Git. Recovery preserves intended destination and exact approved action envelope.

## Session B packets

- V2B-004a SP2: shared ActionEnvelope/ApprovalGrant/Receipt contracts.
- V2B-004b SP2: adapt existing ToolGateway to contracts.
- V2B-004c SP2: adapter interface + two built-in adapters.
- V2B-004d SP2: negative suite for payload/destination/expiry/idempotency/cancel.

Session A performs shared API/schema wiring only if required.

## Acceptance

Three integration classes eventually use the same boundary:
- local/sandbox;
- API/MCP read/write;
- browser/session-aware.

No consequential retry duplicates an accepted effect.


## Implementation status (CURSOR-V17-SINGLE)

- Branch: `cursor/v17-single-session`
- Packets: V2B-004a–e / Phase D1–D5
- Status: **reviewable candidate** — local implementation-complete; **no self-accept**; independent review required
- Evidence: `docs/evidence/v17/v2b004a-e-action-gateway.json`
- Frozen gates unchanged: ART-V14 drafting, G13 HOST-WIN-DEV blocked, B3 live multi-host UNKNOWN, spend \$0, SWARM_ALLOW_PAID=false
