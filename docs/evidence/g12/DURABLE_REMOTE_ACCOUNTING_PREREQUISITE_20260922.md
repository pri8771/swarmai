# Durable remote call fence, 2026-09-22

This branch adds an offline PostgreSQL prerequisite for Groq and OpenRouter
remote admission. It does not activate a remote route or issue an operator grant.

`DurableRemoteCallGate.reserve` requires an exact one-use stored grant, matching
source Git tree, a fresh free account and zero-price route observation, and a
fresh account request quota observation. It locks and decrements the shared
quota row and consumes the grant in one transaction. `mark_sending` commits a
single-use send fence before network I/O. Once SENDING, a restart cannot resend
or refund it. Success is committed only when a receipt reports zero provider
cost; OpenRouter additionally needs an explicit selected backend and no BYOK.
Otherwise the attempt remains UNKNOWN and the quota hold stays consumed.

The integration test uses a unique, disposable PostgreSQL schema. It proves
parallel reservations have one winner when one request remains, stale evidence
fails before reservation, edited requests fail the grant hash, a caller-edited
ticket cannot inflate a refund, and SENDING cannot be replayed after restart.

Still required: wire this gate into the broker and provider adapter, verify
account tier and quota through an authorized authenticated observation, obtain
an exact owner grant for the source tree and request, run one bounded live
canary, reconcile its account cost and rate-limit evidence, and obtain
independent review. None of those is claimed by the local PostgreSQL test.
