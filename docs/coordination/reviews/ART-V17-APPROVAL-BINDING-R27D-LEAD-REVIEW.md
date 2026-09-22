# ART-V17-APPROVAL-BINDING — R27d lead review

Decision: **BOUNDED SLICE ACCEPTED; parent artifact unchanged**
Reviewed implementation: `cursor/v17-single-session@1b9afc510b5cac875ae5b6291c123f132938ede1`
Evidence: `docs/evidence/v17-recovery/R27d/`
Parent artifact lifecycle: `ART-V17-APPROVAL-BINDING` remains `drafting`.

## Accepted evidence

R27d closes the bounded approval-integrity concerns it claims:

- approval IDs are insert-only rather than merge/upsert authority;
- persisted `used_count` starts at zero and cannot be reset by re-putting a grant;
- revocation is monotonic, project-scoped, and records who/why metadata;
- project-scoped lookup gives the same non-operational result for foreign and unknown IDs;
- legacy rows missing required V1.7 binding columns are not silently defaulted into operational grants;
- revoked/expired/unknown approvals remain unable to create an effect through the gateway negative path.

The bound local receipt reports real PostgreSQL focused verification (`6 passed`), full offline suite (`422 passed, 2 skipped`), Ruff clean, and mypy clean. Source inspection matches those claims: durable insert uses `session.add` with duplicate-key rejection, reads filter by project and `_operational`, and revocation locks the matching active row before the monotonic update.

## Parent artifact is NOT accepted

This decision does not waive either R27c blocker already recorded in `ART-V17-APPROVAL-BINDING-R27C-LEAD-REVIEW.md`:

1. the operational `ConsequentialToolGateway` still calls committed admission with `fence_reader=None`, so authoritative durable generation fencing is not wired into the real gateway admission transaction;
2. a retry of an already-consumed effect under a distinct fresh approval can validate the replacement grant without consuming/rebinding that new grant.

Current source still exhibits both behaviors. Therefore `R27e` and `R28a` remain held and `ART-V17-APPROVAL-BINDING` stays `drafting`.

## Required next repair

Execute `R27c-R1` exactly as previously specified:

- inject the authoritative durable lease/cancellation fence reader into the committed admission transaction and prove a precheck-to-admission generation change blocks the adapter and consumes no approval;
- make each distinct replacement grant that authorizes a new retry consume exactly one use while preserving same-effect/same-grant no-double-consume;
- run focused transaction/reservation tests at least x5, the two new regressions, full offline pytest, Ruff and mypy;
- package tested-source SHA separately from evidence-only commits.

Only after independent review of that repaired source may the R27c review receipt be added to execution control and the R27e/R28a hold be released.
