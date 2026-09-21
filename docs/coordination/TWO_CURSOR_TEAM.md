## Physical host mapping

### HOST-MAC-DEV — Cursor Session A
- Existing configured Mac development environment.
- Branch: `cursor/v2-runtime-lane`.
- Owns `cursor/v2-integration`.
- Runtime/control-plane/distributed/recovery.
- Current reviewed progress includes broker closure, process restart proof and reviewed integration baseline.

### HOST-WIN-DEV — Cursor Session B
- Brand-new Windows instance; no existing Git/repo/toolchain assumptions.
- Branch: `cursor/v2-product-lane`.
- Product/evals/knowledge/tools/extensions.
- Bootstrap prompt: `CURSOR_WINDOWS_PRODUCT_BOOTSTRAP_PROMPT.md`.
- This setup run is also useful V1.9 clean-install/Windows portability evidence.
- Later, after the durable worker protocol is reviewable, this host should become the first real second-host SwarmAI worker for V1.5 multi-host evidence.

Never share one working directory between the hosts. Each clones/fetches from GitHub and pushes its own lane.


# Two-Cursor-session execution contract

## Session A — Runtime & Integration

Branch: `cursor/v2-runtime-lane`
Integration branch owner: `cursor/v2-integration`

First claim:
1. ART-V12-BROKER-CONTRACT — packet V2A-001 / SP2.
2. ART-V11-RESTART-EVIDENCE — packet V2A-002 / SP1 if non-conflicting.
3. ART-V15-LEASE-FENCING — packet V2A-003 / SP3 after lead ADR.
4. ART-V15-WORKER-PROTOCOL implementation — packet V2A-004 / SP3.
5. ART-V18-SITE-EPOCH/BACKUP — follow-on packets after lead contract.

Primary write surface:
- workers/
- mission broker/runtime only as needed;
- db/migrations/deploy;
- worker/distributed/recovery tests.

Session A owns shared-file integration.

## Session B — Knowledge, Tools & Product

Branch: `cursor/v2-product-lane`

First claim:
1. ART-V13-TASK-POOL — packet V2B-001 / SP2.
2. ART-V13-REVIEWER-QUALIFICATION calibration tooling — V2B-002 / SP3.
3. ART-V16-PROVENANCE — V2B-003 / SP3 after lead schema.
4. ART-V17-APPROVAL-BINDING / tool adapter interfaces — V2B-004 / SP3.
5. ART-V19-EXTENSION-CONTRACT implementation / install-beta tooling — follow-on.

Primary write surface:
- memory/
- tools/
- selfdev/
- new extension modules;
- console feature components where needed;
- their tests.

Session B avoids shared API/store/CLI/lockfile edits. Put requested wiring in an integration note for Session A.

## Shared rules

- Artifact registry is canonical.
- Every commit/message names artifact ID + packet ID.
- Story points are secondary complexity only.
- No self-acceptance.
- No force-push.
- No main merge/public release/spend.
- Preserve zero-spend/fail-closed policy.
- Unit tests/mocks do not satisfy live gates.
- Commit independently useful modules/contracts before integration.
- If a packet grows above SP3, split it.

## Integration cadence

Session A pulls/merges Session B only at artifact-review boundaries, not continuously while files are half-written.

Integration steps:
1. Session B posts exact commit + tests + integration note.
2. Lead reviews artifact contract/evidence.
3. Session A integrates into `cursor/v2-integration`.
4. Run full CI.
5. Update exact artifact source ref.

Do not use a green lane CI result as proof the integrated tree is green.
