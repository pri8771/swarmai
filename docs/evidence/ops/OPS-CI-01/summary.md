# OPS-CI-01 — stop heartbeat commits from triggering CI

Packet: OPS-CI-01 · Artifact: ART-OPS-HEARTBEAT · Worker: Fable 5.1 (engine `fable`, epoch `fable-v17-20260922-01`)
Base source SHA: `f2b8d5f7dfd65530e73c63438c229b9fa428f922`

## Problem measured

- `gh api "repos/pri8771/swarmai/actions/runs?per_page=1" --jq .total_count` at `2026-09-22T00:31:31Z` = **1383** (was 1023 at `2026-09-21T20:2xZ`, i.e. ~360 runs in ~4 h, all on `coordination/swarm-control`, all `failure` with zero steps = billing block).
- Cause: `ci.yml` had `on: push` with no path filter; the heartbeat publishes three files through the contents API every five minutes = three commits = three runs.

## Change

1. `.github/workflows/ci.yml`: `paths-ignore: ["docs/**", "**/*.md"]` on `push` and `pull_request`; `concurrency` group per ref with cancel-in-progress. No job changed.
2. `scripts/coordination/heartbeat.py`: every `put_file` commit message is wrapped by `ci_skip()` which appends ` [skip ci]` exactly once. Same file also gains the engine/epoch takeover record required by `FABLE_DELIVERY_CONTRACT.md` §3 (`SWARM_HB_ENGINE`, `SWARM_HB_EPOCH`, `--trigger takeover`), so the existing stream is reused instead of a second producer.
3. `tests/coordination/test_heartbeat_skip_ci.py`: three tests (suffix idempotent, every `put_file` wrapped — AST check —, workflow filters present).
4. `coordination-ci.patch`: identical trigger change for `coordination/swarm-control`; verified with `git apply --check` against `43e1c46`. **Not pushed to the coordination branch by the worker** — lead applies it.

## Deterministic checks

- `uv run pytest tests/coordination -q` → 3 passed.
- `uv run ruff check .` → clean. `uv run mypy src/swarm` → clean (configured target). Note: `scripts/coordination/heartbeat.py` has 8 pre-existing mypy `type-arg` notes at the tip; it is outside the configured mypy target and was not changed in that respect.

## Live evidence (`run-counts.json`)

Observed run counts at T0 (before the change) and after ≥20 minutes of heartbeats on the new producer. Timestamps are observed clock readings. See `run-counts.json`.
