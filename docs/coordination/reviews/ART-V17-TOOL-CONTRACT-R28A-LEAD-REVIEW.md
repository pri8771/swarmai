# ART-V17-TOOL-CONTRACT — R28a independent lead review

Date: 2026-09-22
Reviewer: ChatGPT engineering/product lead / formal acceptance authority
Decision: **BOUNDED SLICE ACCEPTED — R28a**
Reviewed exact source: `codex/swarm-r28a-outcomes-20260922@b204fda738221787325ce8fd0b8db58e6e29b573`
Tree: `26dc60b41578160ca7ce0da7c4642cc4ed34ddf1`
Base: accepted R27e `e924351bd93510eaae279225db3a2fa447dd6894`
PR: #21
Parent artifact: `ART-V17-TOOL-CONTRACT` remains **drafting**
Live/checkpoint acceptance: **NOT GRANTED**

## Exact-SHA verdict

The candidate repairs the R28a fail-open outcome paths at the reviewed SHA.

### Outcome certainty

The gateway no longer infers success from an empty, malformed or unrecognized adapter result.

- only an explicit adapter outcome in the declared five-value vocabulary is accepted;
- missing/unrecognized/non-dict results become `unknown / unrecognized_outcome`;
- `AdapterNotSentError` is the narrow proved-not-sent path to `failed / not_applied`;
- `AdapterDeniedError` and explicit denied results become denied;
- arbitrary exceptions and deadline expiry become unknown rather than certain failure/success;
- unknown results are not blindly executed again on replay.

This directly closes the baseline reproductions retained in the native R28a evidence.

### Durability boundary

`ConsequentialToolGateway` now requires an explicit store argument. Consequential and irreversible envelopes fail with `durable_store_required` before pre-observation or execution when the store is not durable. The old implicit `InMemoryEffectStore()` operational fallback is gone.

### Deadline / cancellation semantics

Pre-observation, execute, post-observation and reconcile calls are moved off the event loop and bounded by the envelope timeout.

A timeout cannot cancel a Python worker thread that may already be performing an external operation. The candidate therefore records `unknown`; it does not claim the remote operation was stopped. Likewise task cancellation records `unknown / cancelled_during_execute` and rethrows `CancelledError`. A late thread return has no path to overwrite the already-finalized durable unknown state.

This is the correct conservative behavior for an ambiguous external effect.

Post-observation failure does not rewrite a known execute outcome; it records only the observation error type.

### Reconciliation

The echo API/MCP adapter no longer interprets absence of a prior success receipt as proof of non-application. It returns destination-not-observable / unknown. This prevents an unobservable transport from authorizing a retry as `not_applied`.

## Evidence considered

Native evidence in `docs/coordination/reviews/CODEX_R28A_20260922.md` records seven pre-repair black-box failure paths at the accepted R27e base and binds the repair to exact source `b204fda...`.

Exact-source author engineering checks report:
- full offline suite: **543 passed, 0 skipped**;
- affected suite: **121 passed**, including real PostgreSQL paths;
- Ruff clean;
- mypy clean across 170 source files;
- bounded mechanical review: no concrete introduced defect.

This lead review independently inspected the exact one-commit diff, gateway/adapter implementation, native R28a contract, negative tests and evidence. It did not rerun the 543/121 suites.

Hosted Actions runs `35689583522` and `35689682073` each expose three failed jobs with **no executable steps**. Native evidence attributes the start failure to the existing account payment/spending-limit restriction. Hosted CI is therefore neither counted green nor treated as an observed source-test failure; no rerun or billing change is authorized.

## Scope boundary

This accepts only the R28a engineering slice at exact SHA `b204fda738221787325ce8fd0b8db58e6e29b573`.

It does **not**:
- accept parent `ART-V17-TOOL-CONTRACT`;
- grant CP/live/product acceptance;
- authorize a provider/model/destination call;
- change the failed CP1 attempt2 or authorize attempt3;
- authorize spend, merge, deployment, public release, scheduler changes or Fable routing.

## Next packet

The smallest dependency-safe continuation is the explicitly allowed first half of R28b:

**R28b-1 — effective classification + required fence fields (native R28b rules 1–3).**

R28b-1 is released directly to Codex from exact accepted source `b204fda...`.

R28b-2 (provider/actor/policy/fence seams, native rules 4–6) remains held until an independent exact-SHA review of R28b-1. This keeps the authority-contract change reviewable and preserves the owner's methodical root-cause requirement.

R02c PR #19 remains a separate pending review.
