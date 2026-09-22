# Codex assignment — R31a offline implementation/test-source only

Owner target: V1.7 only.
Packet: docs/coordination/packets/R31a.md
Dependencies: accepted R30a + R29a + R28a.
Execution: offline/source only.

Implement the HttpSessionAdapter contract and manifest plus offline tests/test source without performing any session authentication, HTTP server/network call, cookie-bearing real session or live_local execution.

Allowed:
- src/swarm/tools/adapters/http_session.py;
- config/integrations/http.session@1.json;
- adapter export if needed;
- unit/offline tests using deterministic fake/mock transport;
- author the live_local test file/source, but do not execute it;
- Ruff/mypy/offline pytest.

Preserve the packet's security boundary: SessionJar cookies remain in-process only and never serialize into envelope/receipt/evidence; redirects are never followed; login is not an adapter operation; session-expiry submit is unknown until reconciliation.

Before implementation, reconcile R31a destination validation with the already-frozen R30b destination principles: literal loopback only for this fixture contract, no implicit localhost/IPv6 alias expansion, no environment proxy, redirects disabled. Do not broaden network authority.

Do not implement R31b recovery. Do not start R30a fixture service. No network/session/model/provider/public action, scheduler, spend, deploy or main merge.

Return READY_FOR_LEAD_REVIEW with exact SHA/tree/base and offline evidence. Live evidence remains separately held.


## Lead contract clarification — mandatory

Read and implement against:
`docs/coordination/reviews/R31A_CONTRACT_DISPOSITION_20260922.md`

It supersedes the native packet where the packet says zero submission rows alone prove `not_applied`, and where the original redirect negative uses caller destination `/redirect?... `.

Key frozen deltas:
- wire-only `client_ref = sha256(effect_key)[:32]`;
- `X-Fixture-Request-ID = sha256(effect_key + ":attempt:" + str(execution_attempt))[:32]`;
- exact caller destinations only: `/app/form` for open and `/app/submit` for submit;
- internal same-origin reads only to derived `/app/submissions?client_ref=...` and `/app/requests/<request_id>`;
- form.submit requires both `web.submit` and `web.read`;
- zero rows alone is never `not_applied`;
- only terminal exact-request `not_applied` + zero matching rows permits `not_applied`;
- missing/in-flight/auth-redirect request proof remains `unknown`;
- duplicate/conflicting rows or receipt disagreement is `unknown/anomaly`;
- unsafe redirect negative must use mocked transport on an allowed fixed destination, not broaden the destination allowlist.

No vocabulary expansion is needed.
