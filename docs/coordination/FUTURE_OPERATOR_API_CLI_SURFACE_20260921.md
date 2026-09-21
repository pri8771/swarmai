# SwarmAI future operator/API/CLI surface sketch

Date: 2026-09-21
Status: PLANNING ONLY

Goal: give future implementation an end-user/operator shape early while preserving one underlying service boundary. CLI/API/UI should call shared domain services rather than implement separate semantics.

Names may change after current CLI conventions are re-inspected.

## V1.8 recovery

Suggested CLI:
- `swarm recovery status`
- `swarm recovery backup create`
- `swarm recovery backup verify <ref>`
- `swarm recovery restore <backup-ref> --recovery-mode`
- `swarm recovery reconcile <recovery-id>`
- `swarm recovery authority status`
- `swarm recovery authority activate <recovery-id>` (requires configured fencing proof/policy)
- `swarm recovery drill`

API concepts:
- read recovery/site status;
- create backup;
- restore/reconcile under operator authorization;
- no unauthenticated authority activation.

## V1.9 extensions/install

Suggested CLI:
- `swarm extensions list`
- `swarm extensions inspect <id@version>`
- `swarm extensions install <artifact>`
- `swarm extensions enable <id@version> --project <project>`
- `swarm extensions drain ...`
- `swarm extensions disable ...`
- `swarm extensions uninstall ...`
- `swarm deploy doctor`
- `swarm deploy support-bundle`
- `swarm upgrade plan`
- `swarm upgrade apply`
- `swarm upgrade rollback`

Every consequential command must use normal authorization/approval/effect semantics.

## V2.0 candidate/release

Suggested CLI:
- `swarm release candidate freeze`
- `swarm release candidate show`
- `swarm release candidate verify`
- `swarm release support-matrix`
- `swarm reliability protocol show`
- `swarm reliability campaign start`
- `swarm reliability campaign status`
- `swarm reliability campaign finalize`

Freeze must output exact CandidateManifest identity.

## V2.3 operations

Suggested CLI:
- `swarm scheduler status`
- `swarm scheduler explain <decision-id>`
- `swarm scheduler queues [--project]`
- `swarm scheduler policy show`
- `swarm scheduler drain --project|--worker|--site`
- `swarm packs list/install/enable/drain/disable`
- `swarm projects export <project>`
- `swarm projects import <bundle>`
- `swarm fleet list`
- `swarm fleet explain-placement <receipt-id>`

Read commands expose safe metadata only.

Mutation commands route through normal action/approval boundaries.

## V3 objectives

Suggested CLI:
- `swarm objectives create --file objective.yaml`
- `swarm objectives inspect <id>`
- `swarm objectives versions <id>`
- `swarm objectives activate <id@version>`
- `swarm objectives pause <id@version>`
- `swarm objectives revoke <id@version>`
- `swarm objectives trigger <id@version> --manual`
- `swarm objectives receipts <id@version>`
- `swarm objectives proposals <id@version>`

Revoke must be visually and semantically distinct from pause.

## V3 learning

Suggested CLI:
- `swarm learning proposals list`
- `swarm learning proposals inspect <id>`
- `swarm learning evaluate <id> --calibration`
- `swarm learning freeze <id>`
- `swarm learning heldout start <id>` (policy/reviewer gated)
- `swarm learning review <id>`
- `swarm learning canary start <id>`
- `swarm learning rollback <id>`
- `swarm learning drift status`

The CLI must not offer an "accept --force" bypass around transition requirements.

## V3 audit

Suggested:
- `swarm audit trace --trigger <id>`
- `swarm audit trace --mission <id>`
- `swarm audit export --project <id>`

Trace should link receipt IDs/digests:
trigger -> proposal -> mission -> scheduler -> reservations -> worker/provider/tool -> result/effect -> artifact.

No secret values, cookies, hidden answers, or private model chain-of-thought.
