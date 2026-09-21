# R13 — durable lease schema foundation

Donors: `630ab780` (V2A-003a) + `92f59faf` (V2A-003a-R)

## Result

Foundation already present on `cursor/v17-single-session`. No re-transplant performed.

Byte-identical to donor tip `92f59faf` (else `630ab780` where file first appeared):

- `migrations/versions/a15lease003a0001_art_v15_lease_fencing_schema.py`
- `src/swarm/db/token_hash.py`
- `tests/db/test_token_hash.py`
- `tests/integration/db/test_lease_fencing_schema.py`
- V2A-003a / 003a-R evidence JSON

`src/swarm/db/lease_fencing.py` and `models.py` intentionally differ: tip already carries later V2A-003b/c + V17 effect extensions. Not downgraded.

## Tests

`11 passed` — `tests/db/test_token_hash.py` + `tests/integration/db/test_lease_fencing_schema.py` against local operator DB `swarmai_v17_r13` (demo `swarm:swarm` DSN forbidden by engine policy).

Alembic head: `a17effect004a0001`.

No invent-accept of `ART-V15-LEASE-FENCING`. Next: R14 claim/renew/expire selective verify/port.

Evidence tip: .
