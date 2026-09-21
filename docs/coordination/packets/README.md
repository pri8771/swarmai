# Packet spec conventions (read once per session)

Status: LEAD APPROVED 2026-09-21. Execute only packets that the active queue marks dependency-ready; future-version packets remain inactive until their handoff/dependencies.
Applies to every spec in this directory whose ID appears in `../V17_RECOVERY_PACKET_QUEUE.json`.
Older files here (`V2B-*`, `EXT-WORKER-*`, `OPS-AUTO-*`, `HB-CI-001`, `V14-REAL-001-R`, `B-OPS-*`) are historical two-lane packets; do not execute them.

## How to pick work

1. Read `../V17_RECOVERY_PACKET_QUEUE.json`. Take the first packet, in file order, whose `status` is `ready`, or `planned` with every `depends` entry at `impl_complete` or later.
2. Read **only** that packet's spec file plus the source files it lists under *Surfaces*.
3. A packet with an unmet `gate` is not yours to unblock. Record the blocker once, then take the next dependency-independent packet.

## Hard rules for every packet

- Edit only the files listed under *Surfaces*. If the work needs another production file, stop and split the packet (write the proposed split into your handoff); do not widen silently.
- Behavior under *Exact behavior* is normative. Names, error-code strings, column names and state names must match exactly; tests and later packets depend on them.
- Every test listed under *Negative tests* must exist with that function name and must fail if the behavior is removed.
- No mocks in `live_local` or `integration` tests: real PostgreSQL, real OS processes, real HTTP to the local fixture. In-memory fakes are allowed only in plain unit tests.
- Never self-accept. The highest status a worker may set is `impl_complete`, `live_checkpointed` or `review_pending`.
- `SWARM_ALLOW_PAID=false`. No new dependencies unless the spec names them. No secrets in Git.
- One migration chain. Before adding a migration run `uv run alembic heads`; there must be exactly one head before and after.

## Commands (run from repo root on the implementation branch)

```
uv run ruff check .
uv run mypy src/swarm
uv run pytest <focused test files> -q
SWARM_DATABASE_URL=... uv run pytest -m integration <files> -q      # real Postgres
SWARM_LIVE_LOCAL=1 SWARM_DATABASE_URL=... uv run pytest -m live_local <files> -q
```

## Commit, evidence, handoff

- Commit subject: `feat(<PACKET>/<ARTIFACT>): <what>` (or `fix`, `test`, `ops`). One packet per commit; a second `docs(<PACKET>): bind evidence tip SHA` commit is allowed.
- Evidence folder: `docs/evidence/v17-recovery/<PACKET>/` for packets, `docs/evidence/v17-checkpoints/<CP>/<run-id>/` for checkpoints. Required files: `summary.md`, `commands.json` (argv, exit code, duration), `pytest-output.txt` produced by **this** packet's run (never copied from another packet), `verify-receipt.json` with `source_sha`, `migration_head`, `self_accept: false`.
- A packet that changed no file under `src/`, `migrations/`, `tests/`, `scripts/`, `sandbox/` or `config/` is `evidence_only`, not `impl_complete`.
- Handoff (heartbeat `short_note`, max 6 lines): packet/artifact · source SHA · files changed · tests and evidence path · blockers · next packet.

## Status vocabulary (queue `status` field)

`planned` · `ready` · `in_progress` · `impl_complete` (source + deterministic tests pushed) · `live_checkpointed` (live evidence packaged and SHA-bound) · `evidence_only` · `gaps_found` (audited; see `remediation`) · `split` (see `split_into`) · `blocked_external` (see `gate`) · `wall_clock_pending` · `review_pending` · `changes_required`.

`verified` and `accepted` never appear in a queue. They exist only in `ARTIFACT_REGISTRY.json` and only the lead sets them.

## Spec template

`Artifact` · `Advances` · `SP` · `Depends` · `Fixes` (finding IDs from `../V17_CODE_AUDIT_20260921_2030_FABLE.md`) · `Tier` — then sections *Why*, *Surfaces*, *Exact behavior*, *Negative tests*, *Evidence gate*, *Exit*, *Do not*, and *Forward-compat* where a later version depends on a seam.
