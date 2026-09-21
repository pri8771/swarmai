# SwarmAI future transactional algorithms

Date: 2026-09-21
Status: PLANNING ONLY

These algorithms express invariants, not mandatory function names.

## A18-01 acquire writable SiteEpoch

Important:
The canonical V1.8 contract intentionally leaves the concrete fencing authority mechanism configurable. Do not assume a restored copy of the same database can safely mint a globally newer epoch without an authority mechanism that can fence the old site.

Pseudo-flow:

```
assert control_plane.mode == recovery_or_candidate

verified = recovery_integrity_checks()
if not verified:
    fail_closed("recovery_integrity_failed")

new_authority = configured_site_authority.acquire_new_epoch(
    site_id=this_site,
    prior_epoch=restored_epoch,
    recovery_id=recovery_id,
)

transaction(application_db):
    lock SiteAuthority/current authority state
    verify new_authority proof/token/version
    persist local authority binding
    mark restored prior authority stale
    persist AuthorityTransitionReceipt
    outbox(site_authority_activated)

enable_writes_only_after_commit()
```

Every dispatch/result/effect checks the current authority binding.

If the configured authority mechanism cannot prove old-site fencing, site remains read-only/recovery.

## A18-02 accept result/effect with epoch fence

```
transaction:
    current = load_current_site_authority_for_update()
    attempt = load_attempt_for_update()
    submitted = result_or_effect.authority_binding

    require submitted.site_epoch == current.epoch
    require attempt.project/task/source/generation/cancellation bindings current
    require lease/effect reservation valid
    require not already accepted under same uniqueness scope

    write accepted pointer/receipt
    outbox(accepted_event)
commit
```

Stale epoch is a terminal rejection for that submission, not a retry hint.

## A18-03 restore/reconcile

```
validate BackupManifest digests
restore DB/artifact state
validate schema/migration heads
start recovery mode (read-only for consequential writes)

transaction:
    mark in-flight leases/reservation intents from restored snapshot
        uncertain/expired/reconciliation_required per frozen policy
    preserve unknown external effect states
    create RecoveryRun

acquire new writable SiteEpoch via configured authority mechanism
reconcile:
    safe read/compute tasks -> eligible for new attempts
    unknown consequential effects -> poll/reconcile, never blind fresh retry
    stale worker/result bindings -> reject
activate writes
finalize RecoveryReceipt
```

## A23-01 select project/task

Persisted inputs only.

```
transaction:
    reconcile/lock scheduler policy + epoch
    eligible_projects = query admitted projects with runnable eligible work

    for each eligible project:
        once per persisted scheduler ROUND (not each poll/call), increment bounded deficit by base_quantum * weight
        apply bounded urgency/aging bonus
        cap accumulated credit after downtime

    project = deterministic_best_eligible_project()
    task = deterministic_best_eligible_task(project)

    create DispatchIntent(state="preparing", policy_version, scheduler_epoch)
commit
```

Do not charge fair-share service until dispatch becomes ready/succeeds according to frozen policy.

## A23-02 multi-resource reservation intent

```
intent = durable DispatchIntent(preparing)

for resource_class in required_order:
    reservation = reserve_idempotently(resource_class, intent.id)
    persist component state

    if denied:
        compensate every acquired component idempotently
        set intent released/blocked
        stop

    if unknown:
        set intent unknown/reconciliation_required
        stop without executing inference/tool

if every component reserved:
    transaction:
        verify task/project/generation/epoch still current
        set intent ready
        bind attempt/dispatch
commit

only now may worker/inference/tool execution begin
```

Crash recovery:
- preparing intent: reconcile components before retry;
- ready not dispatched: deterministic idempotent dispatch or expiry;
- unknown: poll/reconcile, never mint fresh intent until resolved/fenced.

## A23-03 fair-share reconciliation

After completed/accepted service:

```
observed_service_class = normalize(worker/provider/tool usage)
transaction:
    load project scheduling state
    reconcile estimated charged service with observed class
    do not reward denied/failed admission
    retries/repair stay charged to same project
    persist decision/service receipt
```

No raw token cost should silently become scheduling authority; broker budgets remain separate.

## A30-01 event/schedule trigger dedupe

Use a durable unique constraint/CAS on objective-version + occurrence/event dedupe scope.

```
transaction:
    claim dedupe_key
    if duplicate:
        return existing TriggerReceipt

    objective = load immutable version
    current_authority = load project/owner policy

    validate:
        active/not expired/not revoked/not paused
        source authenticated
        rate/max-active
        stop conditions
        payload/input project scope
        authority intersection

    write TriggerReceipt(valid or rejected)

    if valid:
        write MissionProposal(
            scopes = intersection(
                objective frozen scopes,
                current authority,
                template requested scopes
            )
        )
        outbox(mission_proposal_created)
commit
```

No model/tool/external effect inside trigger transaction.

## A30-02 schedule restart reconciliation

```
for objective schedule:
    derive deterministic occurrence_id(objective_version, schedule_version, due_instant)

    apply frozen missed-run policy:
        skip_missed
        OR coalesce_latest
        OR bounded_catchup(max_count=N)

    attempt trigger transaction for each selected occurrence_id
```

Never replay every missed tick without an explicit bounded policy.

## A30-03 mission proposal admission

```
transaction:
    proposal = lock proposal
    objective = load exact objective version
    current_project_authority = load current policy

    re-check objective state + current revocation
    effective = intersect(
        proposal requested scopes/resources,
        objective frozen authority,
        current project/owner authority
    )

    if any requested dimension exceeds effective:
        reject proposal

    normal_mission = create_via_existing_mission_admission(...)
    link proposal -> mission
    mark proposal admitted
    outbox(mission_created)
commit
```

A once-valid TriggerReceipt never grandfathers revoked authority.

## A30-04 learning transition

```
transition(proposal_id, expected_from, to, evidence_refs):
    transaction:
        proposal = lock row
        require proposal.state == expected_from
        require transition allowed by frozen state machine

        if to >= frozen:
            require candidate/scorer/dataset/sample/stop/resource digests frozen

        if to >= heldout_running:
            require heldout access policy sealed
            require no contamination marker

        if to == independently_reviewed:
            require reviewer != proposer where policy requires
            require independent review receipt

        if to == canary_running:
            require authority diff clean
            require rollback target executable

        if to == accepted:
            require canary passed
            require no guardrail violation
            require no contamination

        write LearningTransitionReceipt
        update state
commit
```

Models may request/recommend a transition; they do not bypass this function.

## A30-05 deterministic canary rollback

```
monitor canary guardrails

if safety_critical_guardrail_breach:
    transaction:
        mark candidate rollback_pending
        activate parent accepted version
        increment/fence candidate execution generation
        write RollbackReceipt
        outbox(rollback_activated)
    cancel/fence stale candidate workers/schedulers
    preserve all failed canary evidence
```

Rollback must not depend on model judgment for frozen safety-critical triggers.

## A30-06 self-development governance check

Before selfdev held-out/canary:

```
protected_paths = governance + reviewer + evidence + hidden_eval_access + release_authority
changed_paths = diff(candidate, parent)

if changed_paths intersects protected_paths:
    classify authority/governance change
    autonomous promotion prohibited
```

A separate externally authorized governance change may still be possible; it is not part of the selfdev proposal that benefits from it.


## Closure-sweep safety contract (proposed; required input to final Fable audit)

A17 effect invariants: exactly one execution admission wins per effect/generation. This is not a universal exactly-once external API guarantee. Lack of destination idempotency means an ambiguous result may remain unknown indefinitely rather than duplicating a write. Recompute semantic payload/destination binding before replay; require current authenticated identity and read permission to return a prior receipt. All mutating operational actions use durable state and current leases, including idempotent writes.

Execution attempts and receipt events differ: attempt_number counts attempts; receipt_sequence orders immutable observations/transitions; transition_key deduplicates receipt append; one attempt can have many reconciliation observations. CAS state writes require the matching executor/attempt/execution_generation. Late observations never overwrite a successor attempt.

A17 cancellation linearizes at durable execution admission. It prohibits future admissions, not an already-issued remote effect. Timeout is not proof of termination; absence in a listing is not proof of non-application. Reconciliation grants safe retry only when old send capability is quiescent and destination proof is definitive, or the destination itself enforces idempotency. Irreversible retry also needs a separately authenticated operator disposition and new approval. No arbitrary daemon/thread takes over on wall-clock expiry alone.

A18 first supported profile: one private deployment, same primary authority DB for normal restart; backup restore starts read-only. Writability requires externally observed isolation of the old site's compute/credentials/network path as defined by a signed deployment fencing record. A restored DB cannot prove global freshness. Automatic multi-site failover remains unsupported without an approved independent fencing mechanism. Fable must trace the chosen mechanism against two writable copies before closing this design.

A23 scheduling detail: persisted round number and round cursor grant bounded quantum once per eligible project per round, weighted by policy. Deficit cost is estimated frozen service units, debit exactly once when DispatchIntent becomes ready, reconcile actual usage once by settlement receipt; all retries remain charged to the origin. Failed admission without service refunds once; unknown usage remains conservatively reserved. Task tie break: bounded urgency/aging, enqueue time, task ID. Cap max credited rounds on restart; do not accrue by API polling. All capacities reuse existing owners. State-machine fixtures must demonstrate no credit minting, duplicate debit or quota bypass.

A30 runtime authority: objective trigger/lifecycle transactions reference immutable version plus mutable revocation generation. Event uniqueness includes authenticated source and project; schedule identity includes exact UTC due instant and schedule version with explicit DST policy. Proposal-to-mission is transactional/idempotent with outbox; duplicate deliveries find the existing mission. Active slot and remaining objective budget are reserved atomically, with terminal release idempotency. Model-suggested stop conditions are advisory until deterministic authorized policy acts.

A30 learning review: static -> calibration -> freeze -> sealed evaluation -> independent review -> bounded canary -> accepted runtime version. These runtime learned-version states are distinct from repository artifact acceptance. Protected authority cannot be a learnable target. Refusal to improve is a valid learning result; it cannot be relabeled as a successful promotion. Private digest-pinned packs are the initial ecosystem scope; public marketplace/signing distribution is deferred, with explicit schema/trust interface.
