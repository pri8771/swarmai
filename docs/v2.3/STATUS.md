# SwarmAI V2.3 Status — scaffold; implementation in progress

Verified against `dev` @ `8e1c0fdec24c131e7612d88076220945230f4c3b`. Plan: `docs/v2.3/PLAN.md`.

## Truth table (16-item checklist from FUTURE_VERSION_EXIT_CHECKLISTS_20260921.md)
| # | Item | State | Evidence / gap | Session |
|---|---|---|---|---|
| 1 | scheduler state durable | scaffold | `controller/fairness.py` is an in-memory dict | W0-S2, W1-S2, W2-S1 |
| 2 | project-level fairness defined | scaffold | `debt += 1/weight`; ranking ignored by `ResourceAllocator` | W0-S1, W1-S1 |
| 3 | aging/priority deterministic | missing | no aging; priority not used | W1-S1 |
| 4 | reservation intent transactional / fail-closed | scaffold | `controller/reservations.py` in-memory | W1-S3, W2-S1 |
| 5 | provider/worker/tool capacity integrated | missing | | W2-S1, W3-S1 |
| 6 | backpressure bounded | scaffold | single floor value | W1-S1, W2-S1 |
| 7 | cancellation/drain fenced | scaffold | | W1-S1, W1-S3, W1-S7, W2-S1 |
| 8 | scheduler bound to SiteEpoch | missing | | W1-S4, W2-S1 |
| 9 | decision receipts emitted | scaffold | receipts in memory only | W0-S2, W1-S2, W2-S1 |
| 10 | capability packs lifecycle complete | scaffold | unkeyed sha256 "signature" (F-02) | W1-S5 |
| 11 | portability export/import complete | scaffold | key-name-only secret scan (F-03) | W1-S6 |
| 12 | observability read surface complete | scaffold | unscoped ops events (F-01) | W0-S3, W1-S8, W3-S1, W1-S12 |
| 13 | dashboard mutation uses action boundary | scaffold | assert helper only | W3-S1, W1-S12 |
| 14 | fleet placement/trust/locality complete | scaffold | first-candidate placement | W1-S7 |
| 15 | pathological deterministic suite passes | missing | | W2-S1, W3-S4 |
| 16 | multi-process/private evidence complete or honestly pending | pending | owner approval needed | W4-S1 |

## Not claimed
Nothing in V2.3 is accepted. Harness results never imply acceptance.
