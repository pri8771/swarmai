# SW-X1-S1 handoff
- Branch: `cursor/sw-x1-s1-460c`   Base SHA: `10fd924efd866fbaa8ce7348b24aad3019a13ecc`   Head SHA (code): `2a4d3e50fbd10ad908bf92009cd49dca2b1da575`
- PR: draft PR to `cursor/sw-v23-integration-460c` (see PR body `pr_bodies/SW-X1-S1.md` in the coordinator audit dir; opened by the environment/coordinator)
- Integration branch stands in for `dev` (coordinator override); session branch name uses the `-460c` suffix.
## Done
- `src/swarm/providers/splitsignal_client.py`: `SplitSignalClient(RouterClient)` — strips `/v1`, bearer from `SPLITSIGNAL_API_KEY` (never logged), accepts `V1ModelList` and `ModelPage`, builds `RouterCallReceipt` from `splitsignal` metadata, refuses known non-zero cost (`paid_route_forbidden`), unknown cost → `cost_amount=None`, `usage_known=False`; `classify_splitsignal_error` fixed code map; missing `[DONE]`/`event: error` → `partial_stream`.
- `src/swarm/pursuit/native_loop.py`: one import + `native_loop_from_env` now prefers `SPLITSIGNAL_*` over `SWARM_ROUTER_*` (the "currently reads" block matched exactly).
- `tests/pursuit/test_v20_native_loop.py`: one `monkeypatch.delenv("SPLITSIGNAL_BASE_URL", raising=False)` line (F-19).
- New: `tests/fixtures/splitsignal_http/{__init__,fake_splitsignal}.py`, `tests/providers/test_splitsignal_client.py`, `tests/pursuit/test_v20_native_loop_splitsignal.py` (27 tests); `docs/swarm-mvp/INFERENCE_SERVER_CONTRACT_SNAPSHOT.md` section appended.
## Verification
Checks run by `/agent/wt/check.sh` on commit `2a4d3e50fbd10ad908bf92009cd49dca2b1da575` (Postgres 127.0.0.1:5432 available):
```
ruff: All checks passed!
mypy: Success: no issues found in 257 source files
alembic heads: a23opsplatform0001 (head) 
session tests: 87 passed in 1.20s
offline CI: 699 passed, 1 skipped in 35.96s
integration (Postgres): 88 passed in 21.46s
tree: ebe199b404c718912a893afef76ebbd2d4dfee3e dirty=0
```
- Step 0: **SP1 MISSING** — `docs/api/v1/consumers/swarmai.md` is not on `cursor/is-v23-integration-460c` (tip `a685c88`); IS-W1-S10 exists only on the unmerged branch `cursor/is-w1-s10-460c` (`8844eadb`). Per coordinator override the adapter was implemented against its own fakes and this PR is **awaiting SP1; not merged**.
- Read-only comparison with the unmerged contract (blob `1a4a31c9836555d5389d24e91ee5774959e6bb93`): env names `SPLITSIGNAL_BASE_URL/API_KEY/MODEL`, bearer `ss_live_…`, OpenAI list `/v1/models` example, `ErrorEnvelope{code,message,request_id,retryable}` all match. No STOP-level difference.
- Fake bodies: validated against SplitSignal `docs/api/v1/openapi.yaml` by the audit (not re-run here).
- `tests/providers/test_splitsignal_client.py tests/pursuit/test_v20_native_loop_splitsignal.py` → 27 passed; `SPLITSIGNAL_BASE_URL=http://x.test/v1 pytest tests/pursuit/test_v20_native_loop.py` → 8 passed; `-k unknown_cost` → 2 passed; `grep -rn ss_live_ src/` → nothing.
- Step 8 (informational; SP2 not reached on the integration branch): the real `scripts/mock_splitsignal.py` from the unmerged `cursor/is-w1-s10-460c`, run on 127.0.0.1:8089 with the contract's synthetic key → `['mock/ok', 'mock/quota', 'mock/unavailable']` and `mock/ok free False` (matches the expected output). Localhost only; no real SplitSignal call.
## SP1 re-check and real-mock run (2026-09-26 ~03:05 UTC, integrator)
- Step 0 against `cursor/is-v23-integration-460c` @ `9ca126718163223aa2a9a4fca9f6a901636a9782` (IS-W2-MERGE): `gh api …/contents/docs/api/v1/consumers/swarmai.md?ref=cursor/is-v23-integration-460c --jq .path` → `docs/api/v1/consumers/swarmai.md`, **SP1 OK**; `scripts/mock_splitsignal.py` present, **SP2 OK**.
- Contract diff: merged `swarmai.md` blob is `1a4a31c9836555d5389d24e91ee5774959e6bb93`, identical to the blob this adapter was built against. `git diff origin/cursor/is-w1-s10-460c origin/cursor/is-v23-integration-460c -- docs/api/v1/consumers scripts/mock_splitsignal.py` → empty (fixtures and mock unchanged). No adapter change needed.
- Step 8 with the real mock, run from a detached worktree of the IS integration branch (so `docs/api/v1/consumers/fixtures` resolves), `127.0.0.1:8089`, synthetic contract key, no external network:
  - `list_models()` → `['mock/ok', 'mock/quota', 'mock/unavailable']`
  - `chat(mock/ok)` → `mock/ok free False` (fixture reports no cost → `usage_known False`, never settled as zero)
  - `chat(mock/quota)` → `RouterClientError quota_exhausted` (`error_code quota_exhausted`, `retry_after_s 30.0`, within the RetryOwner cap)
  - `chat(mock/unavailable)` → `RouterClientError transient` (`error_code provider_unavailable`)
  - `chat_stream(mock/ok)` → `StreamResult`, `mock/ok free False`, 20 chars of text
  - wrong synthetic key → `RouterClientError authentication` (`error_code unauthenticated`)
  - mock stopped afterwards.
## Acceptance
- [x] Step 0 printed `SP1 OK`, and the contract facts match (or the differences are recorded).
- [x] `uv run pytest tests/providers/test_splitsignal_client.py tests/pursuit -q` passes (27 new tests in the two new files, plus the existing ones).
- [x] `SPLITSIGNAL_BASE_URL=http://x.test/v1 uv run pytest tests/pursuit/test_v20_native_loop.py -q` passes.
- [x] `tests/providers/test_router_client.py` is unchanged and still passes (the legacy path works).
- [x] No real network call: every test uses `FakeSplitSignal().transport()` or an explicit `env` dict.
- [x] `grep -rn "ss_live_" src/` prints nothing (the synthetic key lives only in tests).
- [x] `test_chat_unknown_cost_never_settles_as_zero` and `test_unknown_cost_keeps_loop_usage_unknown` pass.
- [x] The handoff records D-SS1, the contract blob SHA and the Step 8 result (or `SP2 not reached`).
- [x] Every step in section 5 done; every acceptance box in section 5 ticked.
- [x] `uv run ruff check .` and `uv run mypy src/swarm` pass.
- [x] `uv run alembic heads` prints exactly one head.
- [x] Full offline CI list passes (paste the final `N passed` line into the handoff).
- [x] Integration run passed, or SKIPPED with reason in the handoff.
- [x] `git status --porcelain` lists only files from section 3 + the handoff.
- [x] No secrets, no network calls beyond section 5, no `accepted`/`complete` claims.
- [x] The Codex review packet (section 11) is in the PR description and the handoff.
## Decisions
- D-SS1 (coordinator-accepted 2026-09-26, C3; the owner may override): a route listed by SplitSignal's `/v1/models` under SwarmAI's key is admitted as `billing: free`; a response whose `splitsignal.cost.amount` is a known non-zero decimal is refused after the fact with `policy_denied / paid_route_forbidden` (receipt keeps `billing: paid`); an unknown cost (`amount: null`) is recorded as unknown (`cost_amount = None`, `cost_source = "unknown"`, never 0) and the receipt has `usage_known = False`, so accounting keeps the hold committed (F-13); a `ModelPage` body's `cost_class` is authoritative (adapter accepts both shapes, C4).
- Retry-After: `RetryOwner.decide` (SW-W0-S3) clamps waits to `max_retry_after_seconds` (30 s), so a `Retry-After` above 30 s **does** lead to an early retry at the cap, contrary to the SplitSignal rule "never retry before Retry-After has elapsed". (Follow-up: fixed on the integration branch by SW-FIX-RETRY; see Needs other owner.)
- Tests ran against the private Postgres DB `swarm_sw460c`.
## Needs other owner
- ~~`src/swarm/broker/retry.py`: when retry_after exceeds max_retry_after_seconds, give up instead of retrying at the cap (SplitSignal contract).~~ Resolved by SW-FIX-RETRY (`cursor/sw-fix-retry-after-460c` head `a42a94bd`, merged into `cursor/sw-v23-integration-460c` at `b3162712`): over-cap or non-finite `Retry-After` → give-up `retry_after_exceeds_cap`. This adapter does not call `decide` itself (it only records `retry_after_s` on the receipt), so no code change here; trial merge of this branch with the fix is clean and `tests/providers tests/pursuit tests/broker` → `162 passed`.
- Coordinator: merge only after SP1 (IS-W1-S10 merged into `cursor/is-v23-integration-460c`) and a re-read of the merged `swarmai.md`.
## Status
implemented / offline-tested; SP1 and SP2 reached (IS integration `9ca12671`); merged into `cursor/sw-v23-integration-460c` (Codex review pending). Live use still needs SP4 and SW-PREAPPROVAL-A3 (SW-X2-S1).
