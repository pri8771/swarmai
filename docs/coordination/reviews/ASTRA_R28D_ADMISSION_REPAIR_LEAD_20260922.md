# R28d local admission atomicity repair — formal lead review

Date: 2026-09-22
Reviewer: ChatGPT engineering/product lead / formal acceptance authority
Decision: **BOUNDED ENGINEERING REPAIR ACCEPTED**
Reviewed exact source: `codex/swarm-r28d3-async-gateway-20260922@fb58a751d40f1828990d7a0d687ad30de6eb6103`
Tree: `4fd0b56f909c8026e4893540d587d93d5180c73b`
Rejected predecessor: `86f8e0c90e399c683d68ba9628ef48af4723f33f`
PR: #27
Live/version acceptance: **NOT GRANTED**
Owner state: **PAUSED_BY_OWNER; target V2.0**

## Exact-SHA verdict

The candidate closes the reproduced local cancellation/admission race without changing durable lease authority.

`RevocableFenceProvider` owns a re-entrant admission guard and `cancel()` uses the same lock. Both in-memory and durable effect repositories enter the optional provider guard before their own store/transaction locks and retain it through the committed admission return. The gateway supplies that guard to `begin_execution`.

For the local provider, the fence reader re-enters the same RLock while admission holds it. Therefore cancellation cannot return after advancing the generation while a not-yet-committed admission is still using a stale local snapshot.

The guard exits when `begin_execution` returns, before pre-observation or adapter I/O. A locally admitted effect may therefore drain/account under the existing already-admitted semantics, while cancellation that wins before admission causes the stale effect to fail closed with no adapter/file/receipt/approval use.

`StaticFenceProvider` and `LeaseFenceProvider` use no-op guards. The durable lease reader and its established database lock order/authority are unchanged.

The repair is the requested serialization fix, not a second unlocked generation check.

## Regression quality

The deterministic race regression exercises both serialized winners against memory and owned PostgreSQL.

Admission-first:
- cancellation cannot return while committed admission is paused;
- admission state is executing and approval is consumed;
- cancellation completes before adapter observation is allowed to proceed;
- the admitted effect completes and is durably accounted.

Cancellation-first:
- cancellation completes before admission enters the guard;
- stale fence is rejected;
- adapter/file/receipt are absent;
- approval remains unused.

The async runtime regressions also correct their own test-schema setup rather than adding a production missing-schema fallback.

## Evidence considered

Native exact-source packet: `codex/portfolio-review-20260922@d40d571511dfbe6f04d019413de704f56ecdb5e4`.

Settled evidence reports:
- focused offline: 13 passed / 2 PostgreSQL skips;
- focused owned PostgreSQL: 23 passed;
- full offline: 431 passed / 210 prerequisite skips;
- full owned PostgreSQL: **628 passed / 13 explicit live/UI environment skips / 28.89s**;
- disposable DB cleanup remaining: 0; public tables: 0;
- mypy: 174 source files clean;
- Ruff: all six changed files clean.

The red-before regression copied onto rejected `86f8e0c...` reproduces the stale-admission defect. Initial harness mistakes and intermediate test-key/schema failures are retained separately rather than rewritten as production failures or clean first-pass evidence.

This lead review independently inspected the exact repair diff, provider/store/gateway lock placement and deterministic race tests. It did not rerun the 628-test suite.

## Full Ruff disposition

Full-repository Ruff still reports `src/swarm/api/store.py` I001. That file is unchanged by this repair and the touched repair surface is Ruff-clean.

Disposition: **non-blocking inherited lint debt for this bounded exact-SHA repair**. It is not called green and must not be represented as such. No unrelated cleanup is authorized by this review.

## Hosted CI disposition

GitHub Actions runs `35759387329` / `35759392432` expose failed jobs with no executable steps; native evidence records runner_id 0 and the account payment/spending-limit gate.

Disposition:
- hosted CI is **not green**;
- no checkout/test source failure is observed;
- the account infrastructure failure is non-blocking for this bounded engineering verdict because acceptance is grounded in executed exact-source owned evidence;
- no billing change or rerun is authorized;
- no merge is authorized.

## Scope and pause

This acceptance supersedes the prior `REWORK_FOUND` finding only for the repaired successor at exact `fb58a751...`. The historical rejected source/evidence remains immutable.

It does not:
- accept R28d live evidence or V1.7/V2.0;
- restore or create a live/model/provider grant;
- authorize CP1 attempt3;
- authorize merge, deploy, scheduler changes, spend, public actions or Fable/Claude dispatch.

Owner pause remains authoritative. No successor implementation packet is released by this verdict.
