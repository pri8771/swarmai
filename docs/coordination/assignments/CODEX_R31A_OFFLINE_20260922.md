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
