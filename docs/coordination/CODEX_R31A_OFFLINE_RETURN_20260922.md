# R31a offline HTTP session return — 2026-09-22

READY_FOR_LEAD_REVIEW. PR31: https://github.com/pri8771/swarmai/pull/31

Source `3c79a88`; tree `bc690d6c86fc95db1df307745c101b2fd383f291`; parent PR30 `4d16fe85188861df6e123b4454c6bdc416e6c639` (formal composition verdict still requested). Native R31A_CONTRACT_DISPOSITION_20260922.md governs this source, superseding the original packet's unsafe zero-row rule.

## Bounded implementation

New fixed-origin HttpSessionAdapter, SessionJar, existing-vocabulary http.session@1 manifest, exports and offline/PG tests. Exact literal127.0.0.1 origin and operation paths only; port bound, proxies and redirect following disabled. No login operation. SessionJar exposes only a future separately authorized auth callback hook; the adapter never invokes it.

Submit requires a positive gateway-owned durable execution attempt. Derived request ID and client reference remain wire-only; no Idempotency-Key. Reconciliation GETs the exact attempt receipt and matching rows. Only terminal not_applied plus zero rows yields not_applied; missing/in-flight/inconsistent/duplicate/auth-redirect cases remain unknown. Submit requires both web.submit and web.read.

Independent review caught arbitrary cookie reflection and then an intermediate cookie rotation across reconciliation GETs. Both were reproduced with MockTransport before repair. Each response now records cookie values only in memory, including replacements; only fixture-shaped external IDs containing no remembered cookie value can enter receipts. Errors never echo rejected values. The existing gateway unknown/reconciliation exception behavior is preserved.

## Settled evidence

- 50 focused offline adapter tests pass.
- Full offline:494passed,213skipped.
- Focused owned PostgreSQL suite:111passed.
- Full owned PostgreSQL:694passed,13existingliveUIskips.
- Ruffall, mypy175sourcefiles, allchangedPythonformat/diff checks clean.
- PostgreSQL56421 socket-only; dedicated test database removed; cleanup_remaining=0 and public_tables_after_tests=0.
- MockTransport cookie-negative checks also inspect actual persisted gateway effects/receipts and preserve onePOST/attempt1.
- Independent exact-tree recommendation: ACCEPT bounded offline source, no remaining findings.

Logs: `/tmp/swarm-r31a-evidence-20260922/settled/`; earlier red evidence retained in parent directory and `/tmp/swarm-r31a-cookie-red-20260922.log`, `/tmp/swarm-r31a-rotation-red-20260922.log`.

Exact-head hosted CI readback: runs `35777255861` and `35777260132` succeeded. Offline and console checks are green. The live-gated guard job is not genuine live execution evidence. Formal PR30 and PR31 lead verdicts remain outstanding as of this readback.

## Limits and request

All adapter HTTP was in-process MockTransport. No fixture server, actual HTTP/session authentication/cookie-bearing live request, external model/provider/public action, scheduler, spend, deployment or main merge. Genuine live-local test execution and R31b recovery remain held. This submits offline engineering only, not the full live R31a artifact. Please disposition PR30 composition first, then PR31 against that exact parent. Provider/CP grants remain unchanged.
