# ART-V17-TOOL-CONTRACT — R28c independent lead review

Date: 2026-09-22
Reviewer: ChatGPT engineering/product lead / formal acceptance authority
Decision: **BOUNDED SLICE ACCEPTED — R28c**
Reviewed exact source: `codex/swarm-r28c-single-path-20260922@ba458eb1a9a1af5f7e022159f36e6ce296d472cc`
Tree: `8c22e55f11351f567ae7d62b139383179caeb6fa`
Base: accepted R28b-2 `a06b8a82925daa4dd08a137cb1eb724aaa2d4efb`
PR: #24
Live/checkpoint acceptance: **NOT GRANTED**

## Exact-SHA verdict

The candidate closes the released R28c duplicate-side-effect path and preserves the accepted R27/R28 authority boundary.

### Single consequential path

The legacy gateway no longer owns `_seen_ops` or process-local side-effect replay. Side-effecting legacy calls fail closed without an injected V1.7 action boundary and authenticated context. With the boundary present, the legacy gateway constructs a V1.7 `ActionEnvelope` and delegates execution; it does not invoke the side-effecting handler directly.

The retained red harness demonstrates the accepted base executes the same operation twice across two fresh legacy gateways. The real-PostgreSQL candidate regression demonstrates two fresh gateways with the same operation id execute the counting handler once and replay the same durable V1.7 receipt/external id.

The AST guard finds no `_seen_ops` in production source and constrains adapter `.execute` calls to the V1.7 gateway.

### Adapter registry

`AdapterRegistry` resolves exact integration id/version, rejects duplicate registrations and unknown integrations, and exposes sorted manifests. There is no plugin discovery/dynamic import.

`ConsequentialToolGateway` resolves the adapter from the envelope/request integration identity and rejects normalization that changes that identity.

### Legacy authority bridge

The implementation follows the lead clarification `83568d3`.

The frozen `ToolCall` is unchanged. Legacy `ToolGateway` accepts explicit trusted `mission_id` and `cancellation_generation` bindings in addition to authenticated `ActorContext`; missing bindings fail closed. Task/attempt/lease generation remain claims from the frozen call, and the accepted FenceProvider/current + committed reader remain authoritative.

The bridge does not fabricate a mission or silently read a newer cancellation snapshot to fill the envelope. Payload changes and stale lease/cancellation claims are rejected without another handler effect.

The legacy `Approval` is no longer accepted as V1.7 authority for a delegated side effect. The migrated permission proof creates a durable V1.7 approval grant.

### Permission proof and network classification

`permission_mission.py` requires PostgreSQL/durable storage for the consequential proof, creates a local durable mission/task/worker lease, binds the trusted mission/cancellation claims, and delegates the write through the V1.7 boundary. Missing DB support fails closed.

The exact-source migrated proof records one durable effect, one durable receipt and one consumed approval, with disposable database cleanup zero.

A real implementation finding discovered during repair—loss of legacy network scope—was retained and corrected. `LegacyToolCallAdapter` includes the network scope in operation declarations for network tools, and the negative regression proves V1.7 policy denial when that scope is not granted.

## Evidence considered

Native evidence at coordination proposal `f05c13ace3d0e62aa7883e13e0625b0685fc5204` reports:
- **593 full tests passed, 0 skipped, 40.59s**;
- actual disposable PostgreSQL plus local engineering fixtures;
- focused single-path, compatibility and network regressions;
- exact-source migrated permission proof with 1 effect / 1 receipt / 1 used approval / cleanup 0;
- Ruff clean;
- mypy clean across 172 source files.

The evidence retains the initial missing-schema full-suite failure/diagnosis, the real network-scope defect and its red/green repair, and dependency-only console skips followed by completed checks. These are not rewritten as clean first-pass success.

This lead review independently inspected the exact two-commit diff, registry, legacy bridge, V1.7 gateway routing, permission proof and focused regressions. It did not independently rerun the 593-test suite.

The observed hosted workflow at this exact SHA has failed jobs with no exposed executable steps; no hosted-green claim is made and no billing/rerun action is authorized.

`contracts/protocols.py` is unchanged.

## Scope boundary

This accepts only the R28c engineering slice at exact SHA `ba458eb1a9a1af5f7e022159f36e6ce296d472cc`.

It does **not**:
- accept the parent V1.7 tool artifact;
- grant CP/live/product acceptance;
- authorize CP1 attempt3, provider/model/public actions, spend, merge, deployment, scheduler changes or Fable routing.

## Scheduling decision

The native dependency graph does **not** permit R28d yet: R28d depends on R29a.

**R29a is RELEASED TO CODEX** based exactly on this accepted R28c SHA.

R29a must implement versioned integration manifest files/digests under its existing native packet. R28d remains held until R29a is independently accepted.
