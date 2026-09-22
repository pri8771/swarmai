# V1.7 source composition return — 2026-09-22

Status: READY_FOR_LEAD_REVIEW; recommendation only, no self-acceptance.

- Draft PR: https://github.com/pri8771/swarmai/pull/30
- Source: `4d16fe85188861df6e123b4454c6bdc416e6c639`
- Tree: `05d97987e006853da51a4b7df12b7e80506bc7c0`
- Base: accepted `fb58a751d40f1828990d7a0d687ad30de6eb6103`.
- Release/disposition: canonical `93d4e6e`; PR28 P0 and PR29 lint accepted separately. This candidate composes their changes with the released make_approval integrity check and selective R02c behaviors.

## Production changes and preserved boundaries

Gateway overwrites execution-attempt context from durable storage, excludes it from logical identity, rejects stale payload/destination hashes, and now applies the same integrity check before approval creation. Empty hashes and custom idempotency keys remain supported.

R02c was ported semantically onto the rewritten worker: prompt path/indentation guidance, validation of every proposed edit path before any edit, and bounded retry guidance. The current async chat, cancellation checks, gateway write routing, frozen fences and admission guard remain intact. This was not a wholesale historical worker replacement.

Eight source/test files only. Five final store formatting wraps are AST-identical to accepted lint source. Independent mechanical review recommends acceptance on the exact tree above; implementation and formal acceptance remain separate.

## Settled verification

- New behavioral regressions: 4 failed / 16 passed before repair; repaired set passed.
- Full offline: 444 passed / 211 skipped.
- Focused PostgreSQL integration: 70 passed.
- Full PostgreSQL: 642 passed / 13 live-UI skips.
- Ruff all, mypy (174 source files), all eight changed-file format checks and git diff checks clean.
- Owned socket-only PostgreSQL 56421; dedicated proof database removed; cleanup_remaining=0 and public_tables_after_tests=0.
- Exact imported source location verified; per-file hashes stable across the settled checks.
- Exact-head hosted runs 35774451108 and 35774510966: console/offline checks successful. The successful `live-gated` job is its guard/skip path, not live execution proof. No billing settings were changed.

Retained local logs: `/tmp/swarm-v17-composition-evidence-20260922/settled/`. Earlier logs retain the inherited formatting failure and its subsequent AST-preserving correction.

## Remaining boundary

No external inference, real mission, browser/session fixture execution, R33c action, second-host access, scheduler, deployment, spend or main merge. CP1/CP3/CP4/CP5 and version promotions remain governed by canonical exact evidence and separate grants. R31a contract is now frozen by the native R31A_CONTRACT_DISPOSITION_20260922.md; its offline source task is released, implementation is separate from this PR.
