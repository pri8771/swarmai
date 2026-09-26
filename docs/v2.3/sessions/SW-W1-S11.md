# SW-W1-S11 handoff
- Branch: `cursor/sw-w1-s11-460c`   Base SHA: `fb55bd45f1db573d73a3338a19deaa23805a6c66`   Head SHA (code): `bcc6c6a8b353a911745f13383fdab7b842478d84`
- PR: draft PR to `cursor/sw-v23-integration-460c` (see PR body `pr_bodies/SW-W1-S11.md` in the coordinator audit dir; opened by the environment/coordinator)
- Integration branch stands in for `dev` (coordinator override); session branch name uses the `-460c` suffix.
## Done
- `src/swarm/contracts/router_capabilities.py`: `RouteBilling`, `RouteCapabilities.admissible()` (free-only; aliases unknown → not admissible), `RouterCallReceipt` from `X-Router-*` headers, `classify_error` → `ErrorClass`.
- `src/swarm/providers/router_client.py`: `RouterClient` on `httpx` (`list_models`, `chat`, `chat_stream`); no retries; non-free routes refused (`paid_route_forbidden`); timeout → `unknown_outcome`; missing usage → `usage_known=False` (never 0); stream without `[DONE]` → `partial_stream` with partial text. Overrides fill context/tool metadata but never billing.
- Offline fixture `tests/fixtures/router_http/fake_router.py` (`httpx.MockTransport`, 10 scenarios) + empty `tests/fixtures/__init__.py`, `tests/fixtures/router_http/__init__.py`.
- `tests/providers/test_router_client.py` (12), `config/router_context_overrides.example.json`, `docs/swarm-mvp/INFERENCE_SERVER_CONTRACT_SNAPSHOT.md`.
- No real network: tests use `http://router.invalid` via the mock transport; the API key is a fake literal set with `monkeypatch`.
## Verification
Checks run by `/agent/wt/check.sh` on commit `bcc6c6a8b353a911745f13383fdab7b842478d84` (Postgres 127.0.0.1:5432 available):
```
ruff: All checks passed!
mypy: Success: no issues found in 251 source files
alembic heads: a23opsplatform0001 (head) 
session tests: 48 passed in 0.19s
offline CI: 608 passed, 3 skipped in 29.71s
integration (Postgres): 85 passed in 19.19s
tree: 7bed174350a2e96db1901f9c5bd6a41c9f6e49ca dirty=0
```

## Acceptance
- [x] `list_models` parses route and alias entries; only `billing == "free"` with `admission` of `admitted` or absent is admissible, and aliases are unknown and therefore not admissible.
- [x] Overrides fill missing context and tool metadata but can never change billing.
- [x] `chat` returns a `RouterCallReceipt` from `X-Router-*` headers; missing `usage` gives `usage_known=False`.
- [x] A paid response raises `paid_route_forbidden`; each error scenario sends exactly one request (no retries) and maps to the documented `ErrorClass`.
- [x] A complete stream returns the text and usage; a stream without `[DONE]` raises `partial_stream` with the partial text.
- [x] No real network, no API key in code (the test key is a fake literal via `monkeypatch`).
- [x] Every step in section 5 done; every acceptance box in section 5 ticked.
- [x] `uv run ruff check .` and `uv run mypy src/swarm` pass.
- [x] `uv run alembic heads` prints exactly one head.
- [x] Full offline CI list passes (paste the final `N passed` line into the handoff).
- [x] Integration run passed, or SKIPPED with reason in the handoff.
- [x] `git status --porcelain` lists only files from section 3 + the handoff.
- [x] No secrets, no network calls beyond section 5, no `accepted`/`complete` claims.
- [x] The Codex review packet (section 11) is in the PR description and the handoff.
## Decisions
- Tests ran against the private Postgres DB `swarm_sw460c`.
## Needs other owner
none
## Status
implemented / offline-tested only (NOT accepted; needs independent Codex review)
