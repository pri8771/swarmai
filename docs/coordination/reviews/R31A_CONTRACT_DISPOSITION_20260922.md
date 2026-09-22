# R31a contract disposition — session request identity and negative proof

Date: 2026-09-22
Lead: ChatGPT engineering/product lead
Status: CONTRACT FROZEN / OFFLINE IMPLEMENTATION RELEASE REMAINS ACTIVE
Live/network/session execution: HELD

Basis: native R31a packet, accepted R30a fixture, accepted R30b-P0 durable execution-attempt context, and frozen R30b identity/negative-proof rules.

The packet's original zero-submission => not_applied rule is unsafe against the accepted fixture's delayed, deliberately non-deduplicated submit behavior. R31a must use the same durable request-proof principle as R30b.

## 1. Logical and transport identity

- normalized_payload contains only caller-approved logical session action data; derived client_ref/request_id are wire-only.
- client_ref = sha256(effect_key)[:32].
- X-Fixture-Request-ID = sha256(effect_key + ":attempt:" + str(execution_attempt))[:32].
- form.submit requires a non-null gateway-owned durable execution_attempt. Caller-supplied attempt metadata is not authority.
- retries preserve effect_key/client_ref but receive a fresh request id from the incremented durable attempt_count.
- do not add Idempotency-Key to the session fixture unless the fixture/contract is separately changed; the session submit proof is request-receipt + client_ref based.

## 2. Fixed destinations

For this fixture integration:
- page.open caller destination is exactly http://127.0.0.1:<port>/app/form.
- form.submit caller destination is exactly http://127.0.0.1:<port>/app/submit.
- literal localhost, IPv6 aliases, alternate paths, caller query/fragment/userinfo/backslash/control/traversal and redirects are not equivalent destinations.
- port remains part of approval/payload binding.
- follow_redirects=False and trust_env=False.

Internal same-origin observation/reconciliation reads may derive only:
- /app/submissions?client_ref=<derived client_ref>
- /app/requests/<derived request_id>

Those internal reads are not caller-selectable destinations and may not change origin/port.

## 3. Manifest scopes

- page.open: side effect none / risk low / scopes [web.read].
- form.submit: consequential / medium / scopes [web.submit, web.read].

web.read is mandatory for form.submit because safe reconciliation performs request/submission reads. Do not perform observation reads under web.submit-only authority.

Existing AdapterManifest vocabulary is sufficient; no schema/vocabulary expansion is authorized.

## 4. Submit and reconciliation semantics

POST /app/submit sends JSON {client_ref, text} plus X-Fixture-Request-ID derived from effect_key + durable execution_attempt.

Immediate outcomes:
- 2xx valid response => succeeded.
- 302 to same-origin /login... => unknown/session_expired_during_submit; never infer not_applied from the redirect alone.
- unexpected redirect => denied/unexpected_redirect, with no redirect follow.
- timeout/transport loss/5xx after dispatch uncertainty => unknown.

Reconciliation for the current durable attempt must use both the exact request receipt and client_ref submission rows.

Freeze these proof rules:
- >=1 matching submission row plus terminal applied request receipt => succeeded; exactly one is the normal case.
- multiple matching rows, conflicting external ids, or receipt/row disagreement => unknown/anomaly; never silently exactly-once.
- terminal request receipt outcome=not_applied AND zero matching submission rows => not_applied.
- request receipt missing, in_flight, unreadable, transport-failed, or auth-redirected => unknown even when submission rows are zero.
- terminal applied receipt with temporarily absent rows => unknown/inconsistent, not not_applied.
- a matching row with missing/in-flight receipt => unknown until the exact request receipt becomes terminal; do not create another POST.

Only a confirmed terminal not_applied + zero rows may release the existing consequential retry path. The next retry uses the next durable execution_attempt/request id while preserving effect_key/client_ref.

## 5. Session expiry and recovery boundary

R31a does not log in. SessionJar cookies remain in-process only and never enter envelopes, receipts, effect rows, logs or evidence.

If reconciliation redirects to /login, return unknown with reason reauth_required_to_reconcile and the fixed safe destination /app/form. R31b may later perform the human-auth recovery step; R31a must not post during reauthentication.

## 6. Redirect negative

The packet's original live negative using caller destination /redirect?to=... conflicts with the now-frozen exact destination allowlist.

Replace it for R31a engineering tests with a deterministic mocked transport response on an otherwise allowed fixed destination that returns an unsafe/unexpected redirect. Assert the adapter denies it and never follows it.

Do not broaden the caller destination allowlist merely to exercise the fixture's /redirect endpoint.

## 7. Offline implementation release

R31a offline implementation remains released. It may implement http_session.py, http.session@1.json, exports, deterministic mocked-transport tests and live-test source.

Required additional offline negatives:
- missing execution_attempt for form.submit fails before transport;
- request id changes between durable attempt 1 and 2 while client_ref stays constant;
- zero rows + missing/in-flight request receipt remains unknown;
- terminal not_applied + zero rows is the only not_applied proof;
- duplicate/multiple rows or receipt disagreement is unknown/anomaly;
- web.submit without web.read cannot authorize form.submit;
- localhost/alternate path/query/redirect target is denied;
- cookies absent from serialized envelope/receipt/effect/evidence representations.

No fixture server, network call, real session authentication, cookie-bearing live request, model/provider action or live_local evidence is authorized by this ruling.