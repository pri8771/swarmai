# Durable remote multi-quota accounting, 2026-09-22

Remote admission locks every configured account bucket in stable ID order
and consumes request, total-token, and concurrency allowances atomically.
Each bucket must carry fresh exact remaining capacity and the evidence
reference named in the one-use grant. Probe calls may use a request bucket;
mission and production calls require all three dimensions.

A certified receipt retains one request charge, refunds unused reserved
tokens using reported total-token usage, and releases the concurrency slot.
A missing/over-bound token report or uncertain send remains UNKNOWN and keeps
all holds. An unsent release refunds only the amounts persisted in PostgreSQL
and never renews the grant.

Owned isolated-schema PostgreSQL: 16 passed, including mission denial with
missing dimensions, concurrency contention, exact settlement/refund, and
token overage UNKNOWN. Full offline: 485 passed, 4 skipped, 223 deselected.
Ruff and mypy clean.

These tests use synthetic account, price, quota, and grant rows. They do not
establish live free eligibility or available token/concurrency allowance.
Provider-specific quota observation and account charge readback still need
exact authorization, followed by independent review and a bounded live run.
