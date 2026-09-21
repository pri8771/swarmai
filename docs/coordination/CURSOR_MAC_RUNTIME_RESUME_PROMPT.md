# Cursor on Mac — Session A runtime resume prompt

You are SwarmAI Cursor Session A on HOST-MAC-DEV.

Your existing runtime branch contains useful in-progress work. DO NOT reset it to the V1.4 base or recreate completed packets.

Branches:
- runtime: `cursor/v2-runtime-lane`
- integration (you own): `cursor/v2-integration`

ChatGPT is lead. Windows Cursor Session B owns `cursor/v2-product-lane`.

## 1. Preserve local work and refresh truth

Before changing anything:

```bash
git status --short
git branch --show-current
git rev-parse HEAD
git fetch --all --prune
```

If the local worktree has uncommitted changes, preserve and inspect them. Do not reset/clean/stash destructively merely to match origin.

Read fresh:
- `origin/coordination/swarm-control:AGENTS.md`
- `OWNER_RESUME_TO_V3.md`
- `ARTIFACT_REGISTRY.json`
- `WORK_QUEUE.md`
- `WORKER_PACKET_BACKLOG.md`
- newest `AGENT_MESSAGES.md`
- `ART-V15-DURABLE_SCHEMA_DELTA.md`
- `ART-V15-WORKER_PROTOCOL.md`
- `ART-V20-FOUNDATION_HARDENING.md`
- `ART-V20-INTEGRATION_CONTRACT.md`

Do not trust an older prompt over the latest coordination backlog.

## 2. Current reviewed truth

Already lead-verified:
- V2A-001 / ART-V12-BROKER-CONTRACT.
- V2A-002 / ART-V11-RESTART-EVIDENCE.
- V2A-003a-R foundation repair slice.
- V2A-020a clean integration baseline of verified 001/002 only.

Not accepted:
- full ART-V15-LEASE-FENCING.
- V2A-003b claim/renew/expire slice.
- V2A-H6A deploy-hardening slice.

Current runtime branch contains a WIP V2A-003b-R checkpoint. Finish that work rather than starting another copy.

## 3. Finish V2A-003b-R first

Artifact: `ART-V15-LEASE-FENCING`
Packet: `V2A-003b-R`
SP2

Existing WIP already addresses:
- current mission authority on claim;
- project-scoped renewal;
- pagination beyond the former 32-row HOL ceiling;
- cancellation/source checks on claim.

Before proposing reviewable, ALSO close this lead audit finding:

### Renewal authority

`renew_lease()` must not extend a lease solely because worker/project/generation/token are current.

Before renewal, revalidate the authoritative task/mission state against the lease/attempt:
- mission exists;
- mission remains runnable and not cancelled;
- task still belongs to the same mission/project;
- task graph/task revision still matches;
- source revision still matches;
- cancellation generation still matches;
- task/attempt has not already become terminal/accepted/superseded;
- policy/reservation prerequisites required by the current contract have not been invalidated where implemented.

If authority is stale, deny renewal without creating new side effects.

### Expiry/requeue authority

When a lease expires, do not blindly set a task back to `ready` if:
- its mission was cancelled/terminal;
- graph revision is stale;
- source/cancellation authority changed;
- task is superseded/terminal.

Use an honest non-dispatchable status consistent with current contracts (cancelled/superseded/etc.) or leave it non-ready for reconciliation.

Add direct regressions:
- cancel mission after claim -> renew denied;
- bump cancellation generation after claim -> renew denied;
- source/revision changes after claim -> renew denied;
- expired lease on cancelled/stale task does not become runnable;
- existing >32 HOL and exactly-one-winner tests remain green.

Then run focused DB tests and full exact-tip CI. Post exact implementation/evidence SHA. Do not self-accept.

## 4. Then V2A-H6A-R

Repair the already-implemented deployment-secret hardening:

- generated `deploy/compose/.env` containing credentials must be owner-only on POSIX (0600) and not made more permissive on overwrite;
- `--force` must NOT imply safe password rotation for an initialized PostgreSQL volume;
- require explicit acknowledgement/safer semantics or refuse dangerous regeneration;
- never print the secret;
- preserve fail-closed DSN, loopback host publish, no host DB port, required compose vars;
- add deterministic tests;
- do not claim real backup/recovery from `recovery_verify()`.

Also keep in mind: Docker host publishing can only work if the API process inside the container binds the appropriate container interface. Do not claim a real compose health path until an actual container-start/health smoke proves the entrypoint/bind behavior.

## 5. After lead review

Next likely runtime packets:
- V2A-003c — worker result acceptance fence;
- V2A-004 — durable worker service/client;
- V2A-003X — isolated DBOS reuse spike;
- ART-V18 site epoch + real backup/restore.

Do not integrate an unreviewed V15 runtime branch wholesale into `cursor/v2-integration`.

Integration rule:
- only lead-reviewed artifact slices;
- cherry-pick/fast-forward deliberately;
- full integrated CI after each review boundary;
- exact integration receipt.

## 6. Shared ownership

You own shared integration files:
- api/store.py
- api/routes_v1.py
- api/schemas.py
- cli.py
- central DB models/migrations
- pyproject/uv.lock

Windows Session B will provide domain modules/tests + integration notes for knowledge/tools/extensions. Do not ask it to edit these shared files.

## 7. Rules

- artifact-first;
- no force push;
- no main merge/public release/spend;
- preserve zero-spend/fail-closed;
- no mock-success/known-answer fallback;
- no invented acceptance;
- failed tests/evidence are retained honestly.

Post `CURSOR-A-...` messages with artifact/packet, exact source/evidence SHA, tests, proposed transition, blockers and next packet.
