# R30b offline source and contract diagnostic

Date: 2026-09-22
Status: DIAGNOSTIC_COMPLETE / CONTRACT_DISPOSITION_REQUIRED; no implementation or live proof.
Assignment: `coordination/swarm-control@69d06a6e92abf856bf0496fe25ce9f813d41ef47:docs/coordination/assignments/CODEX_R30B_OFFLINE_DIAGNOSTIC_20260922.md`.
Packet: same coordination SHA, `docs/coordination/packets/R30b.md`.
Inspected application source: accepted `6dbf8c43463cbdbd8c87561af2abcdde59969765` only, through `git show`/`git grep`. Pending R28d repair was not imported.

R30a is now formally accepted as fixture infrastructure under `reviews/ART-V17-INTEGRATION-MANIFEST-R30A-LEAD-REVIEW.md`. That supersedes the earlier R30a reconciliation finding about missing acceptance. R30b remains released for this offline diagnostic only. No HTTP request, live fixture process, model/provider invocation, test execution, product/config/test edit or formal acceptance occurred. This diagnostic is submitted on the separate native evidence branch; its commit identity is carried by Git and the lead request.

## Existing seams and proposed manifest

`AdapterManifest` already admits `http_api`; its strict 14-field shape, operation declarations, recursive secret guard, filename identity and canonical receipt digest require no schema extension. `HttpApiAdapter` should accept an explicitly loaded manifest and reject foreign adapter classes, following accepted R29a constructor semantics. Exporting the type is not automatic registry installation. `ApiMcpAdapter` is imported/exported under `src/` but has no production constructor/default registration found at this accepted source; retain unit-test compatibility without adding default echo wiring.

The following is a proposed exact manifest for lead disposition, not a created config file:

```json
{
  "schema_version": "1.0",
  "integration_id": "http.notes",
  "integration_version": "1",
  "adapter_class": "http_api",
  "operations": {
    "notes.list": {
      "side_effect_class": "none",
      "risk_class": "low",
      "scopes": ["notes.read"],
      "read_data_classes": ["fixture.note"],
      "write_data_classes": []
    },
    "notes.create": {
      "side_effect_class": "consequential",
      "risk_class": "medium",
      "scopes": ["notes.write"],
      "read_data_classes": ["fixture.note"],
      "write_data_classes": ["fixture.note"]
    }
  },
  "read_data_classes": ["fixture.note"],
  "write_data_classes": ["fixture.note"],
  "network_scopes": ["http://127.0.0.1"],
  "filesystem_scopes": [],
  "secrets_refs_required": [],
  "risk_class": "medium",
  "sandbox_required": false,
  "host_requirements": [],
  "user_interaction_consequential": false
}
```

Medium manifest ceiling is required for medium `notes.create`. The packet specifies create's write class/scope but does not settle whether its observation/reconciliation reads need `notes.read` as an additional scope; proposed JSON preserves the packet's `notes.write` requirement while declaring the actual read data class. Lead must decide this permission interpretation before implementation.

## Destination and transport boundary

Validation must run before observation or execution, for both normalized requests and externally supplied envelopes. Parse the URL; reject missing/malformed host or port, credentials/userinfo, fragment, prohibited traversal and unexpected operation/path. Validate every URL the adapter derives, never concatenate untrusted absolute URLs. Retain the full normalized destination, including port, in approval/effect binding even when loopback manifest scope matching ignores the port.

The packet permits HTTP only for literal `127.0.0.1` or `localhost`; other hosts require HTTPS plus a matching manifest scope. The proposed manifest grants only `http://127.0.0.1`, so HTTPS by itself grants no remote destination. It also does not literally grant `http://localhost`: choose explicit denial or an explicit approved equivalence/additional manifest scope, never implicit DNS alias expansion. IPv6/other loopback spellings are not granted by the current contract. Encoded traversal/backslashes and controls need a declared reject policy so parser normalization does not turn a denied destination into an allowed one.

Unresolved endpoint convention: is destination exactly `/api/notes`, or a service base from which that path is derived? Freeze one convention; the smaller proposal is an exact `/api/notes` endpoint, with adapter-owned `client_ref` query parameters and no caller-supplied arbitrary path/query override. Non-loopback HTTPS origin matching should include its explicit non-default port; the packet's prose `scheme://host` is insufficiently precise here.

Create/close a fresh `httpx.Client` per adapter call with redirects disabled and bounded timeout, no cookie reuse or automatic retries. Recommend `trust_env=False` so a proxy environment cannot send an approved loopback fixture request through an external proxy; this is a proposed transport constraint for review, not a performed change.

## Identity and approval binding: circular derivation must be resolved

`ActionEnvelope.ensure_hashes` (`contracts/actions.py:53-78`) computes payload_hash over integration, operation, destination and the entire normalized_payload, then derives effect_key using that hash. R30b simultaneously requires client_ref to be SHA256(effect_key)[:32] inside normalized_payload. Literal use therefore introduces a circular derivation.

Two explicit choices exist:

1. Freeze a two-stage adapter identity: derive the default logical key from caller payload before derived fields, then append derived client_ref and recompute the final approval payload_hash while preserving that logical effect_key/idempotency_key. This is a deliberate specialization of the final default-key relationship and needs lead approval.
2. Derive client_ref only as a wire field from an already frozen default effect key, leaving it outside normalized_payload. This avoids the cycle but changes the packet's payload requirement and must be approved.

Do not call ensure_hashes twice and assume it recomputes non-empty hashes. Do not accept a caller-selected client_ref unrelated to the effect key. Stable Idempotency-Key on every actual POST is full SHA256(effect_key); observation query and body use its first32 characters. Same logical effect retry/restart must retain these identities.

Approval grants bind the final normalized destination/payload/effect key plus project/integration/version/operation/policy. Mutation-negative tests must cover both a freshly normalized changed payload/destination and a copied envelope with its old non-empty hash retained: the generic ensure_hashes helper fills missing values, it does not prove that a supplied hash still matches supplied body. Freeze whether R30b validates this canonical integrity locally or a separately released shared-boundary change is required. The adapter must not bypass gateway approval decisions.

## R28a execution outcomes

For notes.create, use existing AdapterNotSentError/AdapterDeniedError/explicit outcome protocol; do not return ad-hoc HTTP success booleans.

| Observed result | Adapter contract | Existing gateway result |
| --- | --- | --- |
| 2xx with valid id | outcome=succeeded, string external_id | succeeded immutable receipt |
| 3xx | denied, detail=unexpected_redirect; never follow | denied receipt |
| 401/403 | denied | denied receipt |
| 400/404/422 | not_applied | failed receipt, state_reason=not_applied; retry eligible |
| 408/409/425/429/5xx | exception/uncertainty | unknown receipt, reconciliation required |
| Proven connection failure before any application bytes sent | AdapterNotSentError | failed/not_applied |
| Other transport error/timeout | exception/uncertainty | unknown |
| Malformed 2xx body or missing/non-string id | fail closed as unknown proposed | no fabricated success |
| Unlisted status | unknown proposed | no implicit classification |

Do not classify every ConnectError as proof of no send without checking the chosen direct transport's error stage; do not infer no application from a timeout. `notes.list` has no external id or mutation: its successful body and uncertain-read semantics need explicit definition. Current gateway reconciliation treats every class other than consequential as operator-disposition on not_applied (`v17_gateway.py:453-471`), including none/idempotent. Do not accidentally route a timed-out list read through create's negative-result retry policy or broaden the gateway in this packet without release.

## Observation, timeouts and reconciliation

Pre/post observation should return `{count, ids}` from GET by the bound client_ref. Catch HTTP/schema errors inside the adapter and return a small observation-error dictionary; do not interpret an error as count0. The gateway treats a pre-observation exception/outer timeout as unknown without executing (`v17_gateway.py:248-267`); post-observation exceptions are recorded without overwriting a known execution outcome (`296-311`). Thus the packet's nonfatal observation promise needs a bounded adapter observation budget that finishes before the gateway timeout.

The gateway uses separate asyncio.wait_for deadlines around pre, execute, post and reconciliation. An httpx timeout value bounds individual transport phases, not necessarily the complete adapter operation; the outer wait_for can return while its thread/request is still running. Fixing or changing shared timeout semantics is outside the four-file R30b surface until specifically released. Do not equate a finished gateway wait with a stopped remote handler.

Response lost after commit: execution records unknown; a positive matching-note read can establish succeeded, then the gateway writes a reconciled succeeded receipt. Replaying later returns the original terminal receipt and performs no POST. Multiple matches need an explicit anomaly/duplicate report rather than silent exactly-once success, even though the current packet says one-or-more succeeds.

The packet's zero-rows -> not_applied rule is incompatible with accepted R30a delayed-commit semantics. Static source trace:

1. First POST enters fixture delay_before_commit_ms and has not yet inserted the note.
2. Client/gateway times out and records unknown while the handler remains active.
3. Reconciliation sees zero rows and returns not_applied under the current R30b prose.
4. Gateway immediately finalizes failed/not_applied and recursively executes again with the same effect (`v17_gateway.py:453-471`).
5. R30a checks its idempotency map before awaiting the fault delay (`app.py:181-197`). A second request can also see no existing key before the first commits, so two handlers can insert notes despite a stable logical idempotency key.

This is a source-derived incompatibility, not an executed reproduction. The accepted fixture deliberately exposes request-id in-flight/terminal receipts to demonstrate why absence is not proof. For fail-before-commit, a confirmed terminal not_applied observation may release one retry; zero search matches alone may not. Missing/unknown/in-flight request receipts stay unknown.

R30b omits the fixture's mandatory X-Fixture-Request-ID. Without it POST returns400; reusing the same ID for a new attempt returns409. A fresh transport attempt therefore needs a fresh request ID while preserving the same logical effect_key/Idempotency-Key/client_ref. If request receipts are used as negative proof, the exact per-attempt request ID must survive process loss before send; the existing adapter execute signature receives only envelope, not the durable effect's attempt_count or stored pre-observation. An in-memory adapter map or random ID recorded only after send is insufficient for restart reconciliation. Freeze a small durable request-attempt binding or retain unknown on absent rows; do not silently add a fixture-only negative-proof assumption to a generic API adapter.

Fault injection also needs a transport/harness-only mechanism: keeping fail_before_commit in the normalized approved body would repeat it on every retry; removing it from that body invalidates exact approval. Prefer a separately configured one-shot test transport/server fault seam with immutable logical action payload; do not expose arbitrary unapproved header injection as production authority.

## Later implementation surface and meaningful verification

Native four-file surface:
- add src/swarm/tools/adapters/http_api.py;
- add config/integrations/http.notes@1.json;
- export in src/swarm/tools/adapters/__init__.py;
- add tests/tools/test_http_api_adapter_live.py with both live_local and integration markers.

Potential additions requiring explicit scope: offline normalization/URL/hash/status tests in a separate test_http_api_adapter.py; integration-manifest foreign-class coverage; any durable request-attempt persistence/API seam; shared timeout/approval-hash validation or reconciliation changes. No second gateway, authority DB, scheduler or transport framework is needed.

Later focused cases should establish manifest strictness/digest; request identity stability; mutation of derived client_ref and stale supplied hashes denied; URL/redirect rejection before any request; notes.create requires durable store and exact approval/fences; response-loss one note and immutable receipt replay; delayed-commit absence remains unknown and cannot trigger overlap; confirmed stopped-handler failure retries once with fresh request ID, stable logical key, attempt_count2 and one used approval; revoked/expired/changed approval denied before retry; malformed HTTP evidence stays unknown; no stale per-process adapter state required after restart.

The native evidence exit remains three consecutive real loopback fixture + PostgreSQL runs, before/after fixture-state capture, Ruff and mypy. None were run or authorized by this diagnostic. The accepted base carries its own inherited Ruff I001 in src/swarm/api/store.py; report it separately unless a cleanup is released. The current R28d cancellation repair remains independent and is neither accepted nor imported by this document.

## Lead decisions needed before implementation

1. Choose two-stage logical identity or wire-only derived client_ref, and canonical integrity handling for supplied envelope hashes.
2. Define exact destination endpoint and localhost equivalence; approve create observation-read scope and no-environment-proxy transport policy.
3. Replace bare zero-row negative proof with a frozen terminal request-proof/retry contract; choose durable per-attempt request ID binding and one-shot fixture fault mechanism. If that expands gateway/store interfaces, release the smallest separate prerequisite packet.
4. Define notes.list result/retry behavior and observation deadline budget without silently changing shared R28a semantics.
5. Then release exact implementation source and surfaces. Keep live_local execution separately gated; this diagnostic cannot satisfy it.

## Source provenance

All application citations above refer to accepted6dbf8c43463cbdbd8c87561af2abcdde59969765. Key blobs:
- contracts/actions.py:584ccbc38eefe05c09a0c965a9f16905eece7d2a
- tools/v17_gateway.py:52d7633ae80ede49ae6f1e9fa151a00af96af3e8
- tools/effects.py:b4471e6d098b40efc88906fda3697b8768611980
- tools/manifests.py:464159877535e522b2044c50a1532522a9f3ed73
- sandbox/live_fixture/app.py:bc7f477ac0e765215b86f920dfd4c57adfa68b20

Read-only method: git show69d06a6:<assignment/packet/review>; git show6dbf8c4:<source>; git grep on that fixed source. A guessed effect_classifier.py path and source-branch R30b packet path did not exist; classification was inspected in v17_gateway.py and the contract was correctly read from the coordination branch. No missing file was treated as evidence.
