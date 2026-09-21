# CP0 / R00 — exact-tip deterministic health

- Session: `CURSOR-V17-SINGLE`
- Host: Darwin / Apple-M5-Pro-87 (real Mac; not Origin Linux)
- Pre-commit tip observed: `4eb3f1c620df35d2ebb2b0998fea5e6c4a839ead`
- Evidence run: `cp0-20260921T192044Z`
- Spend USD: 0

## GitHub Actions

**Not green.** Sample run [35642708049](https://github.com/pri8771/swarmai/actions/runs/35642708049) on tip `4eb3f1c`: all three jobs (`offline`, `console`, `live-gated`) completed failure in ~4s with **0 steps** and empty `runner_name`.

Annotation (authoritative):
> The job was not started because recent account payments have failed or your spending limit needs to be increased. Please check the 'Billing & plans' section in your settings

Classification: `github_actions_account_billing_or_spending_limit`
- Workflow config defective: **no**
- Source/test failure: **no**
- Rerun spam authorized: **no**
- USER_ACTION: operator restores GitHub Actions billing / spending limit

Last known green Actions on this branch: run `35632562088` at `2026-09-21T17:31:32Z` (pre-billing-block).

## Local deterministic health (this Mac)

| Check | Exit |
| --- | --- |
| `uv run ruff check .` | 0 |
| `uv run mypy src/swarm` | 0 |
| focused offline pytest (contracts/workers/tools/memory/mission) | 0 — 94 passed |

Also fixed one E501 in `scripts/coordination/heartbeat.py` status renderer so local ruff is clean.

Exact-tip CI must **not** be claimed green until billing is restored.
