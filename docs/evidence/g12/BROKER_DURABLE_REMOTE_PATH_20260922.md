# Broker remote path, 2026-09-22

This branch connects PR36's PostgreSQL gate and PR35's provider receipts to
`SharedInferenceBroker`. Remote Groq/OpenRouter admission requires an explicit
gate and a grant ID on the individual `reserve` call. Remote reservations do
not enter the in-memory quota ledger. The broker persists SENDING before
calling the adapter, records the result in PostgreSQL, and refuses a repeat
send or direct in-memory reconciliation. OpenRouter adapter model/backend pin
is checked again just before SENDING.

Owned PostgreSQL integration: 10 cases passed. One case uses the actual
OpenRouter adapter with `httpx.MockTransport`; it proves exactly one pinned
HTTP payload behind grant/quota admission. No request reached OpenRouter.
Full offline: 483 passed, 4 skipped, 217 deselected. Ruff and mypy clean.

This is still a draft prerequisite. The source tree is supplied to the gate by
its caller and must be verified by a trusted launch path. Only request-count
quota is reserved; token and concurrent-call limits need verified provider
data and subsequent accounting work. Groq responses without reported zero
cost remain UNKNOWN. Account tier, quota and charge evidence are not fresh
until an authorized authenticated readback. HTTP execution in the provider
adapter remains synchronous and does not yet establish real overlap.
No live model request, provider session probe, or operator grant occurred.
