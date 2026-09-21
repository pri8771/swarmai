# OPS-CI-01 — stop heartbeat commits from triggering CI

| Field | Value |
|---|---|
| Artifact | ART-OPS-HEARTBEAT (cross-version verification) |
| Advances | ops hygiene; prerequisite for gate `EXT-ACTIONS-BILLING` |
| SP | 1 |
| Depends | none — **do this first** |
| Fixes | O1 |
| Tier | small / low effort |

## Why

`ci.yml` runs on every push with no filter, and `heartbeat.py` writes three files through the GitHub contents API (three commits) every five minutes. GitHub recorded 1,023 workflow runs in 24 hours on this private repository; CP0 then recorded "job was not started because ... spending limit". If the operator restores billing before this lands, the quota is consumed again in about a day.

## Surfaces

- `.github/workflows/ci.yml` (implementation branch)
- `scripts/coordination/heartbeat.py` (commit message strings only)
- new `tests/coordination/test_heartbeat_skip_ci.py`

## Exact behavior

1. `ci.yml`: under `on.push` and `on.pull_request` add
   `paths-ignore: ['docs/**', '**/*.md']`. Add top-level
   `concurrency: { group: ci-${{ github.ref }}, cancel-in-progress: true }`. Change no job.
2. `heartbeat.py`: every commit message passed to `put_file(...)` ends with the literal suffix ` [skip ci]`. Build the suffix in one helper `ci_skip(message: str) -> str` that is idempotent (never appends twice).
3. Write the identical `ci.yml` change for the coordination branch as `docs/evidence/ops/OPS-CI-01/coordination-ci.patch`. **Do not push to `coordination/swarm-control` workflow files**; the lead applies that patch.

## Negative tests

- `test_ci_skip_suffix_is_appended_once` — `ci_skip(ci_skip(m)) == ci_skip(m)`.
- `test_all_put_file_messages_use_ci_skip` — parse `heartbeat.py` with `ast`; every `put_file` call's `message=` argument is wrapped by `ci_skip(`.
- `test_ci_workflow_ignores_docs_paths` — load `ci.yml` with a YAML parser (PyYAML is already transitively available; if not, parse the two lines textually) and assert both triggers contain `docs/**`.

## Evidence gate (live, zero cost)

Record `gh api "repos/pri8771/swarmai/actions/runs?created=>=<T0>" --jq .total_count` at `T0` = first heartbeat after the change and again 20 minutes later. Expected: the count does not grow from heartbeat commits (runs appear only for pushes touching non-doc paths). Save both numbers and timestamps to `docs/evidence/ops/OPS-CI-01/run-counts.json`. Timestamps are observed, never computed.

## Exit

Tests green; run-count evidence shows zero heartbeat-triggered runs over ≥ 20 observed minutes; patch file for the coordination branch present; heartbeat still publishes on its normal cadence.

## Do not

Do not change heartbeat cadence, file set, or ledger schema. Do not retry failed Actions runs. Do not touch the billing setting.
