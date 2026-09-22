# R30a — live local fixture service + evidence-level markers

Packet: R30a · Artifact: ART-V17-INTEGRATION-MANIFEST (live-evidence infrastructure) · Worker engine: fable
Base source SHA: `e405077f8fbab4b9aa9630666fd697527c01b623` · Tested source SHA: see `verify-receipt.json`.

## Source changes
- `sandbox/live_fixture/{__init__,app,__main__}.py`, `README.md`: a real FastAPI/uvicorn HTTP service run as a separate OS process on `127.0.0.1:<free port>` (prints one JSON line `{url,pid}`), in-memory state, empty at start. API-style `/api/notes` with required `Idempotency-Key` (replay returns the original, never a second row), session-style `/login` (`FIXTURE_USER`/`FIXTURE_PASSWORD` from the environment per run), `/app/form`, `/app/submit` (no de-duplication, by design), `/app/submissions`, safe-`next` validation, `/redirect` trap, fault header `X-Fixture-Fault` (`drop_response_after_commit`, `fail_before_commit`, `reject_403`, `redirect`, `delay_ms`, `delay_before_commit_ms`), per-write `X-Fixture-Request-ID` receipts (`phase` in_flight|terminal, `outcome` applied|not_applied|null; terminal only after the handler stopped; duplicate/conflicting ids rejected with 409; missing ids 404), `/_fixture/state`, `/healthz`.
- `tests/conftest.py`: `integration` skips unless `SWARM_DATABASE_URL`; `live_local` skips unless `SWARM_LIVE_LOCAL=1`; `live_fixture_url` starts/stops the subprocess with random per-run credentials. `pyproject.toml`: `live_local` marker registered.
- `tests/live_fixture/test_fixture_service.py`: the 11 spec cases (idempotent replay, response loss stores + client transport error + receipt still in flight, fail-before-commit stores nothing, no-session submit redirects and stores nothing, TTL expiry, no dedupe, unsafe `next`/redirect trap, loopback-only bind, terminal non-application only after stopped handler, delayed commit is in-flight not negative proof, request-id conflict/duplicate rejection).
- Nothing under `src/` imports the fixture (grep = 0).

## Honest note on "dropped" responses
uvicorn cannot silently close a connection from a handler, so `drop_response_after_commit` commits and then holds the response for `FIXTURE_DROP_HOLD_S` (longer than any client timeout). The client observes a transport error (timeout); the receipt stays `in_flight` until the hold ends. Real adapters must not assume a real service exposes request-id receipts.

## Checks (this packet's own runs)
- `SWARM_LIVE_LOCAL=1 uv run pytest tests/live_fixture -v` → 11 passed (`pytest-output.txt`).
- Full suite with `SWARM_DATABASE_URL` set and `SWARM_LIVE_LOCAL` unset → 433 passed, 13 skipped (11 `live_local` + 2 pre-existing `tests/ui`): skips are reported, never counted as passes.
- Without `SWARM_DATABASE_URL`: integration tests skip with an explicit reason. Ruff clean; mypy clean.

## Not claimed
No adapter uses this yet (R30b/R31a/R31b wait on R29a/R28a behind the REV-R27C hold). Fixture mechanics are not product evidence.
