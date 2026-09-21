# ART-V20-INTEGRATION-CONTRACT — cross-lane service boundaries

Status: drafting
Target: V2.0
Owner: ChatGPT lead
Purpose: keep Session A and Session B independently implementable and make integration boring.

## Rule

Feature modules expose narrow services/contracts. Shared API/store/CLI surfaces compose those services; they do not absorb feature logic.

Session A owns shared integration files. Session B supplies modules + tests + integration notes.

## Worker/control-plane service boundary

Session A service interfaces should separate:

### WorkerLeaseRepository
- register_worker(...)
- get_worker(...)
- heartbeat(...)
- claim_eligible_attempt(...)
- renew_lease(...)
- expire_leases(...)
- submit_result(...)
- accept_result(...)
- drain_worker(...)
- revoke_generation(...)

No Session B subsystem reads worker DB tables directly.

### BrokerService
- admit(request)
- execute(request)
- settle(result/usage)
- disable_route(route)
- explain(...)

Operational feature modules call this boundary rather than provider SDKs directly.

## Knowledge service boundary

Session B should expose a service approximately equivalent to:

### KnowledgeService
- append(item, actor/project context)
- revise(item_id, ...)
- supersede(item_id, replacement...)
- delete(item_id, ...)
- retrieve(query, project_id, actor_scopes, token_budget, options)
- get_provenance(item_id/version)
- export_project(project_id)
- import_project(bundle, project_id)

Requirements:
- project/scope mandatory;
- permission filtering before ranking;
- retrieval returns a receipt with selected IDs/versions/token cost;
- no caller gets raw cross-project store access.

Session A/API integration depends on this service, not MemoryStore implementation details.

## Tool/action service boundary

Session B should expose:

### ActionGateway
- normalize(request) -> ActionEnvelope
- authorize(envelope, actor/project/approval context)
- execute(envelope)
- reconcile(effect_key/action_id)
- receipt(action_id/effect_key)

Shared API passes actor/project context explicitly. No global/default demo project.

Durable effect acceptance may delegate persistence to Session A infrastructure through an injected EffectRepository, but tool adapters do not own DB transactions.

## Extension service boundary

### ExtensionRegistry
- validate_manifest(...)
- install/enable/disable(...)
- list_compatible(core_version)
- load(extension_id/version, requested_capabilities)
- report_support_bundle()

Loading an extension returns declared capabilities; it does not mutate core authorization.

## Backup/recovery contribution boundary

Every durable subsystem implements a manifest contributor:

### BackupContributor
- component_id/version
- checkpoint()
- validate_checkpoint(...)
- restore(...)
- reconcile_after_restore(site_epoch)

V2 backup manifest aggregates:
- control/worker state;
- missions/artifacts;
- knowledge;
- extension config;
- approvals/effect receipts where policy permits.

Secrets remain external refs, not embedded in export/backup by default.

## Event/trace boundary

Every subsystem emits EventEnvelope-compatible events with:
- project_id;
- mission/task/attempt where relevant;
- actor;
- correlation/causation;
- event type/version;
- bounded scrubbed payload.

V2.3 observability should consume these without subsystem-specific scraping.

## Shared-source ownership

Only Session A edits:
- api/store.py
- api/routes_v1.py
- api/schemas.py
- cli.py
- shared migration ordering
- pyproject/uv.lock
unless ownership is explicitly transferred for one packet.

Session B integration note must specify:
- module import path;
- constructors/dependencies;
- public methods;
- config/env refs;
- exceptions/status semantics;
- migrations requested (if any);
- API/CLI/console hooks requested;
- tests that prove module behavior without shared wiring.

## Integrated acceptance

ART-V20-INTEGRATED-CANDIDATE cannot be reviewable until:
- both lanes expose the documented service boundaries or a reviewed versioned replacement;
- integrated tests use the same services as actual API/CLI/console;
- no lane bypasses authorization/broker/effect/knowledge boundaries through direct lower-level calls;
- no duplicate persistence authorities exist for the same state.
