# R14 — claim/renew/expire

Donors: `7dcefe4c` + `e764834a` + `685810cc`

## Result

Claim/renew/expire already on tip. Tests byte-identical to `685810cc`. Evidence JSON identical.

`lease_fencing.py` is later-superset (includes V2A-003c). Not downgraded.

## Tests

`17 passed` — `tests/integration/db/test_lease_claim_renew_expire.py` on `swarmai_v17_r13`.

No invent-accept. Next: R15 durable result acceptance fence verify.

Evidence tip: `297e6aeb0ee448a3b680e3ba2bb984b5199c2437`.
