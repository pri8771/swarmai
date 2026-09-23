# Live local fixture service (R30a)

Real HTTP server, separate OS process, in-memory state, loopback only. Used by
`live_local` tests to prove V1.7 adapter mechanics (idempotent replay, response
loss, pre-commit failure, delayed commit, session expiry, unsafe redirects).
It is **not** the product and nothing under `src/` imports it.

Run: `python -m sandbox.live_fixture --port 0` → prints `{"url": ..., "pid": ...}`.

Credentials for `/login` come from `FIXTURE_USER` / `FIXTURE_PASSWORD` set by the
test harness per run (random). Nothing is committed here. `FIXTURE_SESSION_TTL_S`
(default 2) controls session lifetime; `FIXTURE_DROP_HOLD_S` (default 5) is how
long a `drop_response_after_commit` response is held.

Fault header `X-Fixture-Fault`: `drop_response_after_commit`, `fail_before_commit`,
`reject_403`, `redirect`, `delay_ms=<n>`, `delay_before_commit_ms=<n>`.
Every write needs a unique `X-Fixture-Request-ID`; `GET /api/requests/{id}` and
`GET /app/requests/{id}` (session required) return that request's receipt
(`phase` in_flight|terminal, `outcome` applied|not_applied|null). These proof
endpoints are fixture mechanics; no real adapter may assume a real service has them.
