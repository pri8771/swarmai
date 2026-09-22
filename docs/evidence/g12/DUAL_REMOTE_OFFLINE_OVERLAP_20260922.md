# Dual remote offline overlap, 2026-09-22

Groq and OpenRouter now use explicit model pins, finite output limits, and a
single broker-facing multiplex adapter. Groq discovery no longer performs an
implicit authenticated `/models` call. Their synchronous HTTP transports run
in separate worker threads after durable PostgreSQL admission. No transport
retry was added.

An owned PostgreSQL test uses exact synthetic one-use grants and account/quota
rows for both routes. Both `httpx.MockTransport` handlers must enter a
two-party barrier before either can return. The test then verifies both
receipts and reservations commit through one broker. This proves HTTP-level
overlap for the current source, with no external provider call.

Owned isolated-schema PostgreSQL: 11 passed. Full offline: 485 passed,
4 skipped, 218 deselected. Ruff and mypy clean.

This is not a live route qualification or an account price claim. Fresh
authenticated tier/quota observations, exact live-action grants, real
provider receipts, account charge readback, token/concurrency accounting,
and independent review are still required before a V1.7 acceptance verdict.
