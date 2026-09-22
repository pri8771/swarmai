# Codex assignment — R30b offline diagnostic only

Date: 2026-09-22
Status: diagnostic/preparation only; no implementation release.
Diagnostic base: accepted descendant `6dbf8c43463cbdbd8c87561af2abcdde59969765`.
Dependencies: R30a accepted; R29a accepted; R28a accepted.
Native packet: `docs/coordination/packets/R30b.md`.

Perform one bounded **offline** diagnostic for the future `HttpApiAdapter`. Do not start the live fixture service and do not make network requests.

Inspect current adapter/gateway/manifest code and write a source-bound causal/design packet covering:
- exact new `http.notes@1` manifest shape under the current strict manifest schema;
- destination validation and loopback/HTTPS rules;
- where `client_ref=sha256(effect_key)[:32]` and Idempotency-Key bind;
- exact mapping of HTTP status/transport errors into R28a outcomes;
- observation/reconciliation behavior;
- how response-loss -> unknown -> reconcile and fail-before-commit -> unknown/not_applied/retry fit current R27e/R28a state machine;
- approval payload/destination binding negatives;
- exact files/tests that a later implementation would change;
- any incompatibility with current manifest vocabulary, gateway timeout model, or durable effect API.

You may add diagnostic evidence/docs only. Do not add `src/`, config manifest, or product test implementation in this task.

No live_local process, provider/model call, scheduler, spend, public action, merge, deploy, CP1 attempt3 or Fable dispatch. Return the diagnostic SHA and concrete implementation blockers/contract questions.
