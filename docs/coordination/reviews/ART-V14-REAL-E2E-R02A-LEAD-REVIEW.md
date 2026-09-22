# ART-V14-REAL-E2E — R02a defect-proof gate lead review

Decision: **BOUNDED RUNTIME GUARD ACCEPTED; ART-V14-REAL-E2E unchanged**
Reviewed source: `cursor/v17-single-session@ef8a2cc25c9caf8665804a28453c6f81f82d4a11`
Evidence: `docs/evidence/v17-recovery/R02a/`

R02a materially strengthens the real-mission acceptance path. For a defect-repair claim it now identifies regression tests carried by the proposed diff, creates a clean detached worktree at the pre-patch candidate, copies only those regression tests across, requires a clean pytest failure (`exit 1`) against pre-patch production source, then requires the same tests to pass in the patched worktree. Collection/configuration/internal pytest errors do not count as red evidence. Semantic review also remains required separately, so a mechanically red→green test is not by itself acceptance.

The bound local receipt reports 8 focused tests, 50 mission tests, full offline suite `433 passed, 2 skipped`, Ruff clean and mypy clean. The source inspection is consistent with those claims.

This is a guardrail, not a successful V1.4 mission. `v14-real-008` subsequently failed honestly before semantic review because the local model produced a verbatim/full-file echo with no material diff and no regression test in the patch. `ART-V14-REAL-E2E` therefore remains `drafting` / changes-required.

Next repair is `R02c`: detect verbatim/near-verbatim full-file echo before write, re-prompt for a bounded diff-shaped change plus regression, test that repair, then run a newly preregistered real mission. Do not relax the R02a red→green gate or count existing green tests as defect proof.
