# R30b contract disposition — identity, attempt proof and HTTP semantics

Date: 2026-09-22
Reviewer: ChatGPT engineering/product lead
Diagnostic: `codex/portfolio-review-20260922@4f017c95ac472b976b564c1bd59693a941ffef1e`
Inspected base: accepted `6dbf8c43463cbdbd8c87561af2abcdde59969765`
Status: **CONTRACT FROZEN FOR PREREQUISITE; R30b PRODUCT IMPLEMENTATION HELD UNTIL PREREQUISITE REVIEW**
Live execution: **HELD**

The diagnostic is accepted as source-bound planning evidence. It correctly identifies three issues that must not be papered over: the client_ref/effect-key cycle, stale supplied payload hashes, and the inability to infer not_applied from an empty search while a remote handler may still be in flight.

## 1. Logical identity — wire-only client_ref

Freeze the **wire-only derivation**, not a two-stage effect-key exception.

- `normalized_payload` contains only the caller's logical approved payload. It does **not** contain derived `client_ref`.
- Gateway/default hashing derives `payload_hash` and `effect_key` from that logical payload using the existing canonical rule.
- Adapter wire body derives `client_ref = sha256(effect_key)[:32]`.
- `Idempotency-Key = sha256(effect_key)`.
- A caller-supplied `client_ref` is rejected/ignored as an unsupported logical field; it may not select identity.
- Observation and reconciliation derive the same client_ref from effect_key.

This removes the cycle and keeps approval binding over the user-controlled logical payload/destination while making transport identity deterministic.

## 2. Canonical payload integrity — shared prerequisite

The diagnostic exposed a generic boundary issue: `ensure_hashes()` fills missing hashes but does not prove that a supplied non-empty `payload_hash` still matches integration/version/operation/destination/normalized_payload.

Before R30b implementation, add a shared gateway integrity check:
- recompute the canonical payload hash from the current envelope fields;
- empty payload_hash may be filled by existing behavior;
- non-empty mismatch fails closed before adapter validation, policy, approval, reserve or I/O;
- run the same check on execute and reconcile paths.

Do **not** require effect_key to equal the default formula: accepted mission paths intentionally use scoped custom effect keys. Exact approvals/effect binding continue to bind the supplied effect key. Do not change that contract in this prerequisite.

## 3. Durable execution-attempt identity — shared prerequisite

R30b needs a fresh request identity for a real retry while preserving the same logical effect/idempotency identity. In-memory counters are not restart-safe.

Add a runtime-only optional field to `ActionEnvelope`:

`execution_attempt: int | None = None`

Rules:
- it is not part of payload_hash, effect_key, approval binding or persisted logical effect binding;
- callers/adapters may not use it to gain authority;
- after `begin_execution` returns, the gateway copies the durable effect `attempt_count` into a runtime envelope used for pre-observation/execute/post-observation;
- unknown reconciliation receives the persisted effect attempt_count in the same runtime-only field;
- recursive retry gets the next durable attempt_count.

R30b request id is then:

`sha256(effect_key + ":attempt:" + str(execution_attempt))[:32]`

and is sent as `X-Fixture-Request-ID` for this controlled fixture. This is evidence/transport correlation, not idempotency authority.

The prerequisite must prove the value survives durable restart/reconciliation through the effect row rather than adapter process memory.

## 4. Destination and transport

For `http.notes@1`, freeze the narrow current integration:
- destination is the **exact collection endpoint** `http://127.0.0.1:<port>/api/notes`;
- no caller-supplied query, fragment, userinfo, backslash/control/traversal, alternate path or redirect;
- literal `localhost` is **not** an alias for this manifest; it is denied unless a future manifest explicitly grants it;
- IPv6/other loopback spellings are not implicitly equivalent;
- port remains part of the exact destination/approval binding even though the manifest loopback network scope is `http://127.0.0.1`;
- `follow_redirects=False`;
- `trust_env=False`;
- fresh client per adapter call; no cookie/shared retry state.

No non-loopback destination is part of R30b evidence.

## 5. Permission scope for observations

`notes.create` requires both:
- `notes.write`
- `notes.read`

because its pre/post/reconciliation proof performs reads. The manifest operation declaration must include both scopes and read/write data classes accordingly. Do not perform observation reads under write-only authority.

`notes.list` requires only `notes.read`.

## 6. Negative proof and retry

**Bare zero rows are never proof of not_applied after an uncertain create.**

For the controlled R30a fixture:
- positive matching note => succeeded;
- request receipt `in_flight`, missing, transport failure or unknown => unknown;
- terminal request receipt `outcome=not_applied` **and** zero matching notes => not_applied;
- terminal applied receipt or any matching note => succeeded;
- conflicting/multiple matching rows => unknown/anomaly, never silently exactly-once.

The durable execution_attempt-derived request id selects the exact request receipt for the current attempt. A confirmed terminal not_applied result may release the existing consequential retry path; the next durable attempt receives a fresh request id while preserving effect_key, client_ref and Idempotency-Key.

For a generic future API that lacks an authoritative request-status endpoint, absence remains unknown. R30b must not pretend the fixture's proof endpoint is universally available.

Fault injection remains test-harness configuration, not approved logical payload. Do not expose arbitrary caller-selected fault headers as production action authority.

## 7. notes.list

Freeze `notes.list` as a non-mutating read:
- GET the exact collection endpoint, with caller-approved/normalized read filter only;
- 2xx valid body => succeeded; receipt post-observation carries bounded `count` and `ids` (not an external_id);
- redirect/auth denial => denied;
- malformed response, 408/425/429/5xx or transport timeout/error => explicit failed/not_applied read outcome; do **not** enter consequential reconciliation or claim remote mutation uncertainty;
- no automatic hidden retry inside the adapter; caller may issue a new read action.

This behavior is specific to side-effect class `none`: read transport failure means the read did not yield a usable result, not that a remote write may be ambiguous.

## 8. Deadlines

Use an adapter transport/observation budget strictly below the gateway's outer timeout:

`inner_timeout_s = max(0.1, min(5.0, envelope.timeout_seconds / 2))`

Use this for each HTTP call. The gateway's existing outer timeout remains unchanged in R30b. This does not claim to cancel a remote handler when the outer wait expires.

## 9. R30b implementation scope after prerequisite acceptance

Once the shared prerequisite is independently accepted, R30b implementation may be released for:
- `src/swarm/tools/adapters/http_api.py`;
- `config/integrations/http.notes@1.json`;
- adapter export;
- offline adapter/hash/URL/status tests;
- live test source may be written but **must not be executed** while the current live/network hold remains active.

The original packet's zero-row retry test is superseded by the terminal-request-proof rule above.

No live_local/server/network execution is authorized by this contract.
