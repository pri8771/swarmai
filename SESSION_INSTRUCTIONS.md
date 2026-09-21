# SESSION_INSTRUCTIONS — Cursor Session B / HOST-WIN-DEV

This is the standing entrypoint for this Cursor session.
Role: evaluation/qualification/knowledge/tools/product/extensions/beta.
Working branch: `cursor/v2-product-lane`
Lead: ChatGPT via `coordination/swarm-control`.
Session A owns shared runtime/API/DB migration/integration surfaces.

## On every pull / continue
1. Preserve dirty work; never reset/clean unrelated files.
2. `git fetch --all --prune` and inspect status/branch/HEAD.
3. If clean: `git pull --ff-only origin cursor/v2-product-lane`.
4. Read fresh `HEARTBEAT_PROTOCOL.md`, `HEARTBEAT_STATE.json`, `ARTIFACT_REGISTRY.json`, `WORK_QUEUE.md`, `WORKER_PACKET_BACKLOG.md`, and newest `AGENT_MESSAGES.md` from `origin/coordination/swarm-control`.
5. Newest coordination state overrides older bootstrap text.

## Heartbeat client update — reinstall once

The heartbeat client was corrected so manual/forced packet updates no longer reset or suppress the scheduler's 15-minute proof clock. Windows scheduler diagnostics were also added.

After pulling this revision, rerun once:
`powershell -ExecutionPolicy Bypass -File scripts\coordination\install_heartbeat_windows.ps1`

Record the printed Task state / Next run. If the scheduled heartbeat fails, inspect the printed scheduler.log path and report the sanitized error. Manual packet heartbeats may continue, but only scheduler heartbeats count toward the 3-consecutive 15-minute bootstrap proof.

## Heartbeat — required
Install/verify once: `powershell -ExecutionPolicy Bypass -File scripts\coordination\install_heartbeat_windows.ps1`.
Before a packet publish context:
`python scripts\coordination\heartbeat.py --host HOST-WIN-DEV --session B --branch cursor/v2-product-lane --packet <PACKET> --artifact <ARTIFACT> --status working --force`
After push/review request publish again with `--status review_requested`.
The scheduler wakes every 15 minutes during bootstrap; the client self-throttles to hourly only after lead verification of three consecutive valid 15-minute heartbeats for BOTH A and B.
Heartbeat is liveness/coordination only, not implementation acceptance.

## B0 — sync the reviewed V2 integration baseline first
The product lane had no product implementation when the reviewed integration baseline was created.
After heartbeat/bootstrap files are pulled and the worktree is clean:
1. fetch `origin/cursor/v2-integration`;
2. merge that reviewed integration branch into `cursor/v2-product-lane`;
3. keep the heartbeat/session files;
4. run baseline Ruff/mypy/pytest and console lint/test/build as available;
5. push and report exact SHA as `V2B-000 / integration-sync`.
Do NOT import unreviewed runtime-lane V15 work.

## Product packet order after B0
B1: `V2B-001 / ART-V13-TASK-POOL / SP2` — freeze calibration vs qualification-held-out task/version manifest, IDs/hashes/source/license, size/scorer/prompt/tool/model identities, hidden answers inaccessible; no counted qualification before lead freeze.
B2: `V2B-002 / ART-V13-REVIEWER-QUALIFICATION / SP3` — calibration-only reviewer benchmark/scorer repair/freeze; no held-out contamination or qualification claim.
B3: `V2B-003a+H1 / ART-V16-PROVENANCE / SP2` — versioned project-scoped knowledge/provenance/tombstones/permission labels, permission filter before ranking, no hard-coded proj_local, two-project no-content/count/preference/tag/existence leak; expose KnowledgeService and hand central migration delta to A.
B4: `V2B-004a+H4 / ART-V17-APPROVAL-BINDING / SP2` — ActionEnvelope/ApprovalGrant/ActionReceipt with mandatory project identity, no production proj_demo default, exact actor/project/integration/operation/destination/payload/effect binding, expiry/revocation.
Then continue newest B queue: permission-first retrieval -> supersession/deletion -> effect-key semantics -> extensions -> beta/non-demo selfdev.

## Owner priority override — G13 critical path

G13 is now higher priority than V1.6/V1.7 product expansion.

After B0 integration sync:
1. **B1 / V2B-001** freeze calibration vs held-out task/version manifest.
2. **B2 / V2B-002** repair/freeze reviewer benchmark/scorer using calibration only.
3. As soon as B1 is lead-verified, start **W-131B counted held-out qualification** in frozen five-observation batches; do not defer this behind provenance/tools work.
4. After B2 freeze, run held-out reviewer-role qualification needed for G14.
5. Only then return to B3 provenance / B4 approval contracts unless a newer lead message explicitly reorders.

Preserve all failures and all overhead. No held-out contamination, threshold changes after results, or qualification self-claims.

## Ownership boundary
Do NOT edit without explicit handoff: `src/swarm/api/store.py`, `routes_v1.py`, `schemas.py`, `cli.py`, `src/swarm/db/models.py`, `migrations/**`, `pyproject.toml`, `uv.lock`.
Implement owned domain modules/tests and send Session A an integration note.

## Repo-driven autonomous execution — install once

This branch now includes a self-waking Cursor CLI daemon. After pulling this revision:

1. Verify Cursor CLI exists: `agent --version`.
2. If CLI auth is missing, run the normal human login once: `agent login`.
3. Install the daemon:
   `powershell -ExecutionPolicy Bypass -File scripts\coordination\install_autonomous_worker_windows.ps1`

The daemon polls `docs/coordination/assignments/HOST-WIN-DEV.json` through GitHub every minute, executes exactly one bounded assigned packet with `agent -p`, and stops after pushing that packet. Safe dependency-ready packets may be preloaded so it can continue without waiting for the hourly lead review. It never self-accepts or selects project priorities.

Current preloaded queue: V2B-000 -> V2B-001 -> V2B-002.

## Continuous work rule
After every packet: push exact source/evidence, post CURSOR-B message, publish heartbeat `review_requested`, fetch coordination, and claim the next dependency-ready B packet.
Do not wait on remote-provider/G10/live gates when independent B work exists.
No main merge/public release/deploy/paid fallback/force push/mock-success/hidden-answer leakage/invented acceptance.
