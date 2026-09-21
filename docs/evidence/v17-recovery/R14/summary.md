# R14 — claim/renew/expire

Donors: `7dcefe4c` + `e764834a` + `685810cc`

## Result

Claim/renew/expire already on tip. Tests byte-identical to `685810cc`. Evidence JSON identical.

`lease_fencing.py` is later-superset (includes V2A-003c). Not downgraded.

## Tests

`17 passed` — `tests/integration/db/test_lease_claim_renew_expire.py` on `swarmai_v17_r13`.

No invent-accept. Next: R15 durable result acceptance fence verify.

Evidence tip: `ac1656d3c580ea421f1fe61f91db9661c9331ecb`.
