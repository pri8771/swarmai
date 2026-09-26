"""Assemble /agent/audit/swarmai/prompts/<SESSION>.md from metadata + body files.

Body files live in tools/bodies/<SESSION>.md. ``{{FILE:rel/path}}`` inside a body
is replaced by the verbatim contents of tools/ref/rel/path.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REF = ROOT / "ref"
BODIES = ROOT / "bodies"
OUT = ROOT.parent / "prompts"

DEV_SHA = "8e1c0fdec24c131e7612d88076220945230f4c3b"
CI_OFFLINE = (
    "tests/contracts tests/spikes tests/api tests/broker tests/controller tests/chaos "
    "tests/deployment tests/evals tests/extensions tests/foundation tests/goals tests/pursuit "
    "tests/sdk tests/knowledge tests/load tests/memory tests/mission tests/objectives "
    "tests/onboarding tests/product tests/providers tests/recovery tests/regressions "
    "tests/release tests/runtime tests/selfdev tests/tools tests/ui tests/workers "
    "tests/workspace tests/e2e tests/acceptance tests/portability"
)

# id: (title, branch, deps, dep_paths, owned, tests, integration_tests, console, commit, optional)
S: dict[str, dict] = {}


def sess(sid: str, **kw: object) -> None:
    kw["sid"] = sid
    kw.setdefault("deps", [])
    kw.setdefault("dep_paths", [])
    kw.setdefault("tests", [])
    kw.setdefault("itests", [])
    kw.setdefault("console", False)
    kw.setdefault("optional", False)
    kw.setdefault("extra_commits", [])
    S[sid] = kw


C23 = "src/swarm/contracts/v23.py"
MEM = "src/swarm/scheduling/memory_store.py"

sess(
    "SW-W0-S1",
    title="Tracking reset, lift-pause record, honest V2.3 status, frozen scheduler policy + acceptance manifest",
    branch="cursor/v23-w0-s1-tracking-policy",
    wave="0",
    owned=[
        "M docs/agents/CURRENT.md",
        "M docs/agents/context.json",
        "M docs/agents/RESUME.md",
        "M docs/agents/V20_TODO.md",
        "M docs/agents/README.md",
        "M docs/v2.3/STATUS.md",
        "C docs/v2.3/sessions/README.md",
        "M docs/v3.0/STATUS.md",
        "M CHANGELOG.md",
        "C config/v23/scheduler_policy.v1.json",
        "C benchmarks/v23_acceptance/scenarios.freeze.json",
    ],
    tests=[],
    commit="docs(v2.3): reset agent tracking, honest V2.3 status, freeze scheduler policy v23-wdrr-1 and acceptance manifest",
)
sess(
    "SW-W0-S2",
    title="V2.3 shared contracts, scheduling package, in-memory store, ORM rows, single migration a23opsplatform0001",
    branch="cursor/v23-w0-s2-contracts-schema",
    wave="0",
    owned=[
        "C src/swarm/contracts/v23.py",
        "C src/swarm/scheduling/__init__.py",
        "C src/swarm/scheduling/memory_store.py",
        "M src/swarm/db/models.py (append at end of file only)",
        "C migrations/versions/a23opsplatform0001_v23_ops_platform.py",
        "M tests/integration/db/test_action_receipts_durable.py (only the NEW_HEAD constant)",
        "C tests/contracts/test_v23_contracts.py",
        "C tests/controller/test_v23_store_memory.py",
        "C tests/integration/db/test_v23_schema.py",
    ],
    tests=["tests/contracts/test_v23_contracts.py", "tests/controller/test_v23_store_memory.py"],
    itests=["tests/integration/db/test_v23_schema.py", "tests/integration/db/test_action_receipts_durable.py"],
    commit="feat(v2.3): shared scheduler/intent/epoch/pack/fleet/ops contracts, in-memory store, migration a23opsplatform0001",
)
sess(
    "SW-W0-S3",
    title="Security hotfixes: ops-events cross-project leak (F-01) and Retry-After cap (F-06)",
    branch="cursor/v23-w0-s3-security-hotfixes",
    wave="0",
    owned=[
        "M src/swarm/api/routes_v1.py (only the function list_ops_events)",
        "M src/swarm/broker/retry.py",
        "C tests/api/test_v23_ops_events_scope.py",
        "C tests/broker/test_retry_after_cap.py",
    ],
    tests=["tests/api/test_v23_ops_events_scope.py", "tests/broker/test_retry_after_cap.py", "tests/broker", "tests/api"],
    commit="fix(security): scope GET /v1/ops/events to principal projects (F-01); cap upstream Retry-After (F-06)",
)
sess(
    "SW-W1-S1",
    title="Weighted-deficit round-robin selector (pure, deterministic)",
    branch="cursor/v23-w1-s1-wdrr",
    wave="1",
    deps=["SW-W0-S1", "SW-W0-S2"],
    dep_paths=[C23, "config/v23/scheduler_policy.v1.json"],
    owned=["C src/swarm/scheduling/wdrr.py", "C tests/controller/test_v23_wdrr.py"],
    tests=["tests/controller/test_v23_wdrr.py"],
    commit="feat(v2.3): weighted deficit round-robin selector (project then mission) with bounded urgency/aging",
)
sess(
    "SW-W1-S2",
    title="Durable SchedulingStore on PostgreSQL (SqlSchedulingStore)",
    branch="cursor/v23-w1-s2-sql-store",
    wave="1",
    deps=["SW-W0-S2"],
    dep_paths=[C23, MEM, "migrations/versions/a23opsplatform0001_v23_ops_platform.py"],
    owned=["C src/swarm/scheduling/store.py", "C tests/integration/db/test_v23_store_sql.py"],
    tests=[],
    itests=["tests/integration/db/test_v23_store_sql.py"],
    commit="feat(v2.3): PostgreSQL SchedulingStore with optimistic versions and row locks",
)
sess(
    "SW-W1-S3",
    title="DispatchIntent reservation / compensation service",
    branch="cursor/v23-w1-s3-dispatch-intent",
    wave="1",
    deps=["SW-W0-S2"],
    dep_paths=[C23, MEM],
    owned=["C src/swarm/scheduling/dispatch_intent.py", "C tests/controller/test_v23_dispatch_intent.py"],
    tests=["tests/controller/test_v23_dispatch_intent.py"],
    commit="feat(v2.3): transactional dispatch intents with all-or-nothing reservation and compensation",
)
sess(
    "SW-W1-S4",
    title="Scheduler epoch lease + singleton ticker (V20-E06 infra)",
    branch="cursor/v23-w1-s4-scheduler-epoch",
    wave="1",
    deps=["SW-W0-S2"],
    dep_paths=[C23, "migrations/versions/a23opsplatform0001_v23_ops_platform.py"],
    owned=[
        "C src/swarm/scheduling/epoch.py",
        "C src/swarm/scheduling/singleton.py",
        "C tests/controller/test_v23_epoch.py",
        "C tests/integration/db/test_v23_epoch_sql.py",
    ],
    tests=["tests/controller/test_v23_epoch.py"],
    itests=["tests/integration/db/test_v23_epoch_sql.py"],
    commit="feat(v2.3): fenced scheduler epoch lease (memory + PostgreSQL) and singleton ticker",
)
sess(
    "SW-W1-S5",
    title="Capability-pack lifecycle + keyed HMAC signing (F-02)",
    branch="cursor/v23-w1-s5-pack-lifecycle",
    wave="1",
    deps=["SW-W0-S2"],
    dep_paths=[C23],
    owned=[
        "M src/swarm/capabilities/__init__.py",
        "C src/swarm/capabilities/signing.py",
        "C src/swarm/capabilities/lifecycle.py",
        "C tests/extensions/test_v23_pack_lifecycle.py",
        "C tests/integration/db/test_v23_pack_installs_sql.py",
    ],
    tests=["tests/extensions/test_v23_pack_lifecycle.py", "tests/controller/test_v18_v30_gaps.py", "tests/controller/test_v23_v20.py", "tests/portability"],
    itests=["tests/integration/db/test_v23_pack_installs_sql.py"],
    commit="feat(v2.3): capability pack lifecycle state machine and keyed publisher signatures (F-02)",
)
sess(
    "SW-W1-S6",
    title="Portability bundle v2: history, tombstones, remap, compatibility, value-based secret scan (F-03)",
    branch="cursor/v23-w1-s6-portability-v2",
    wave="1",
    owned=["M src/swarm/product/portability.py", "C tests/portability/test_v23_bundle.py"],
    tests=["tests/portability"],
    commit="feat(v2.3): portability bundle v2 with section digests, remap, compatibility checks and value secret scan (F-03)",
)
sess(
    "SW-W1-S7",
    title="Fleet trust classes (ART names), drain state machine, deterministic placement",
    branch="cursor/v23-w1-s7-fleet-policy",
    wave="1",
    deps=["SW-W0-S2"],
    dep_paths=[C23],
    owned=["M src/swarm/workers/fleet.py", "C tests/workers/test_v23_fleet_policy.py"],
    tests=["tests/workers", "tests/portability"],
    commit="feat(v2.3): ART fleet trust classes with legacy aliases, drain states and deterministic placement",
)
sess(
    "SW-W1-S8",
    title="Durable ops-event sink, trace graph, nested redaction",
    branch="cursor/v23-w1-s8-ops-trace",
    wave="1",
    deps=["SW-W0-S2"],
    dep_paths=[C23, "migrations/versions/a23opsplatform0001_v23_ops_platform.py"],
    owned=[
        "M src/swarm/observability/ops_events.py",
        "M src/swarm/observability/__init__.py",
        "C src/swarm/observability/trace_graph.py",
        "C tests/controller/test_v23_ops_trace.py",
        "C tests/integration/db/test_v23_ops_events_sql.py",
    ],
    tests=["tests/controller/test_v23_ops_trace.py", "tests/controller/test_v18_v30_gaps.py"],
    itests=["tests/integration/db/test_v23_ops_events_sql.py"],
    commit="feat(v2.3): pluggable ops-event sinks (memory/PostgreSQL), recursive redaction, trace graph",
)
sess(
    "SW-W1-S9",
    title="V20-E03 pursuit PostgreSQL write-through store",
    branch="cursor/v20-w1-s9-pursuit-writethrough",
    wave="1",
    owned=[
        "C src/swarm/pursuit/pg_mirror.py",
        "M src/swarm/pursuit/state_store.py",
        "C tests/pursuit/test_v20_writethrough.py",
        "C tests/integration/db/test_v20_pursuit_writethrough_sql.py",
    ],
    tests=["tests/pursuit"],
    itests=["tests/integration/db/test_v20_pursuit_writethrough_sql.py"],
    commit="feat(v2.0): E03 pursuit state write-through to PostgreSQL with fail-closed mirror",
)
sess(
    "SW-W1-S10",
    title="V20-E04 durable usage holds + pursuit lessons; unknown usage never frees budget (F-13)",
    branch="cursor/v20-w1-s10-durable-holds",
    wave="1",
    deps=["SW-W0-S2"],
    dep_paths=["migrations/versions/a23opsplatform0001_v23_ops_platform.py"],
    owned=[
        "C src/swarm/pursuit/durable_accounting.py",
        "M src/swarm/pursuit/accounting.py",
        "M src/swarm/pursuit/learning.py",
        "C tests/pursuit/test_v20_unknown_usage_budget.py",
        "C tests/pursuit/test_v20_durable_holds.py",
        "C tests/integration/db/test_v20_holds_sql.py",
    ],
    tests=["tests/pursuit"],
    itests=["tests/integration/db/test_v20_holds_sql.py"],
    commit="fix(v2.0): unknown usage keeps budget committed (F-13); feat: E04 durable holds and lessons stores",
)
sess(
    "SW-W1-S11",
    title="inference_server HTTP client + fake router fixture (packet P05)",
    branch="cursor/v23-w1-s11-router-client",
    wave="1",
    owned=[
        "C src/swarm/providers/router_client.py",
        "C src/swarm/contracts/router_capabilities.py",
        "C tests/fixtures/__init__.py",
        "C tests/fixtures/router_http/__init__.py",
        "C tests/fixtures/router_http/fake_router.py",
        "C tests/providers/test_router_client.py",
        "C config/router_context_overrides.example.json",
        "C docs/swarm-mvp/INFERENCE_SERVER_CONTRACT_SNAPSHOT.md",
    ],
    tests=["tests/providers/test_router_client.py", "tests/providers"],
    commit="feat(router): inference_server HTTP client, capability admission and offline fake router (P05)",
)
sess(
    "SW-W1-S12",
    title="Console: Ops tab (read-only) + worker drain/revoke parity (V20-E09)",
    branch="cursor/v20-w1-s12-console-ops",
    wave="1",
    console=True,
    owned=[
        "M apps/console/src/App.tsx",
        "M apps/console/src/api/client.ts",
        "M apps/console/src/api/types.ts",
        "M apps/console/src/data/fixtures.ts",
        "C apps/console/src/components/OpsPanel.tsx",
        "C apps/console/src/components/WorkerControls.tsx",
        "C apps/console/src/ops.test.tsx",
    ],
    tests=[],
    commit="feat(console): read-only Ops tab and worker drain/revoke controls via action boundary (E09)",
)
sess(
    "SW-W1-S13",
    title="V20-E08 sandbox cancel kill-bound (process group, <=10 s) — optional",
    branch="cursor/v20-w1-s13-sandbox-killbound",
    wave="1",
    optional=True,
    owned=["M src/swarm/tools/sandbox_runner.py", "C tests/tools/test_v20_cancel_killbound.py"],
    tests=["tests/tools", "tests/foundation"],
    commit="feat(v2.0): E08 sandbox runs in own process group; timeout/cancel kills the whole group within bound",
)
sess(
    "SW-W2-S1",
    title="SchedulerService (WDRR + store + intents + epochs + site epoch + receipts + ops events) + pathological suite",
    branch="cursor/v23-w2-s1-scheduler-service",
    wave="2",
    deps=["SW-W1-S1", "SW-W1-S2", "SW-W1-S3", "SW-W1-S4", "SW-W1-S7", "SW-W1-S8"],
    dep_paths=[
        "src/swarm/scheduling/wdrr.py",
        "src/swarm/scheduling/store.py",
        "src/swarm/scheduling/dispatch_intent.py",
        "src/swarm/scheduling/epoch.py",
        "src/swarm/observability/trace_graph.py",
    ],
    owned=[
        "C src/swarm/scheduling/service.py",
        "M src/swarm/controller/resource_allocator.py",
        "C tests/controller/v23_harness.py",
        "C tests/controller/test_v23_service.py",
        "C tests/controller/test_v23_pathological.py",
        "C tests/integration/db/test_v23_service_restart_sql.py",
    ],
    tests=["tests/controller"],
    itests=["tests/integration/db/test_v23_service_restart_sql.py"],
    commit="feat(v2.3): SchedulerService composing WDRR, durable store, intents, epochs, receipts; pathological suite",
)
sess(
    "SW-W2-S2",
    title="V20-E05 bounded native model/tool loop behind the fake router; honest E07 blocked path",
    branch="cursor/v20-w2-s2-native-loop",
    wave="2",
    deps=["SW-W1-S11"],
    dep_paths=["src/swarm/providers/router_client.py", "tests/fixtures/router_http/fake_router.py"],
    owned=[
        "C src/swarm/pursuit/native_loop.py",
        "M src/swarm/pursuit/native_dispatch.py",
        "C tests/pursuit/test_v20_native_loop.py",
    ],
    tests=["tests/pursuit"],
    commit="feat(v2.0): E05 bounded native model/tool loop over RouterClient (fake-router tested, live blocked)",
)
sess(
    "SW-X1-S1",
    title="SplitSignal consumer adapter (contract swarmai-consumer 1.x) + SPLITSIGNAL_* env in the native loop",
    branch="cursor/v23-x1-s1-splitsignal-adapter",
    wave="X (cross-repo: after W2, external gate SP1 = inference_server IS-W1-S10 merged)",
    deps=["SW-W1-S11", "SW-W2-S2"],
    dep_paths=[
        "src/swarm/providers/router_client.py",
        "src/swarm/contracts/router_capabilities.py",
        "src/swarm/pursuit/native_loop.py",
        "tests/pursuit/test_v20_native_loop.py",
    ],
    owned=[
        "C src/swarm/providers/splitsignal_client.py",
        "C tests/fixtures/splitsignal_http/__init__.py",
        "C tests/fixtures/splitsignal_http/fake_splitsignal.py",
        "C tests/providers/test_splitsignal_client.py",
        "C tests/pursuit/test_v20_native_loop_splitsignal.py",
        "M src/swarm/pursuit/native_loop.py (one import + function native_loop_from_env only)",
        "M tests/pursuit/test_v20_native_loop.py (one added delenv line only)",
        "M docs/swarm-mvp/INFERENCE_SERVER_CONTRACT_SNAPSHOT.md (append one section)",
    ],
    tests=["tests/providers", "tests/pursuit"],
    commit="feat(splitsignal): consumer adapter for contract swarmai-consumer 1.x; SPLITSIGNAL_* env wins in native loop",
)
sess(
    "SW-X2-S1",
    title="SplitSignal live smoke (SP4/SP5) and joint V2.3 finish record (SP6)",
    branch="cursor/v23-x2-s1-splitsignal-live",
    wave="X (after W4-S1 and X1-S1; external gates SP4/SP5/SP6; approval SW-PREAPPROVAL-A3)",
    deps=["SW-X1-S1", "SW-W4-S1"],
    dep_paths=[
        "src/swarm/providers/splitsignal_client.py",
        "tests/fixtures/splitsignal_http/fake_splitsignal.py",
        "docs/v2.3/EXIT_CHECKLIST.md",
    ],
    owned=[
        "C scripts/v23_splitsignal_smoke.py",
        "C tests/providers/test_v23_splitsignal_smoke.py",
        "C docs/evidence/v23/splitsignal_live.json",
        "M docs/v2.3/EXIT_CHECKLIST.md (the SplitSignal row only)",
        "M docs/v2.3/STATUS.md (append one section only)",
    ],
    env=["SPLITSIGNAL_BASE_URL", "SPLITSIGNAL_API_KEY"],
    live=True,
    tests=["tests/providers"],
    commit="test(splitsignal): bounded live smoke via SplitSignal (SP4/SP5) and joint V2.3 sync-point record (SP6)",
)
sess(
    "SW-W3-S1",
    title="API routes_v23 (scheduler/ops/trace/packs/portability/fleet/worker drain+revoke) + app wiring",
    branch="cursor/v23-w3-s1-api-routes",
    wave="3",
    deps=["SW-W2-S1", "SW-W1-S5", "SW-W1-S6", "SW-W1-S7", "SW-W1-S8", "SW-W0-S3"],
    dep_paths=[
        "src/swarm/scheduling/service.py",
        "src/swarm/capabilities/lifecycle.py",
        "src/swarm/capabilities/signing.py",
        "src/swarm/observability/trace_graph.py",
        "tests/api/test_v23_ops_events_scope.py",
    ],
    owned=[
        "C src/swarm/api/routes_v23.py",
        "M src/swarm/api/app.py",
        "C tests/api/test_v23_routes.py",
        "C tests/integration/db/test_v23_routes_durable_sql.py",
    ],
    tests=["tests/api", "tests/product"],
    itests=["tests/integration/db/test_v23_routes_durable_sql.py"],
    commit="feat(v2.3): /v1 scheduler, ops trace, packs, portability, fleet and worker drain/revoke routes",
)
sess(
    "SW-W3-S2",
    title="ProductStore durability wiring: E03 write-through, E04 holds/lessons restore, E06 singleton ticker",
    branch="cursor/v20-w3-s2-durable-wiring",
    wave="3",
    deps=["SW-W1-S4", "SW-W1-S9", "SW-W1-S10"],
    dep_paths=[
        "src/swarm/scheduling/singleton.py",
        "src/swarm/pursuit/pg_mirror.py",
        "src/swarm/pursuit/durable_accounting.py",
    ],
    owned=[
        "M src/swarm/api/store.py",
        "M src/swarm/pursuit/loop.py",
        "C tests/product/test_v20_durable_wiring.py",
        "C tests/integration/db/test_v20_durable_wiring_sql.py",
    ],
    tests=["tests/product", "tests/pursuit", "tests/api"],
    itests=["tests/integration/db/test_v20_durable_wiring_sql.py"],
    commit="feat(v2.0): wire E03 mirror, E04 durable holds/lessons and E06 singleton ticker into ProductStore",
)
sess(
    "SW-W3-S3",
    title="CLI `swarm v23 …` commands",
    branch="cursor/v23-w3-s3-cli",
    wave="3",
    deps=["SW-W2-S1", "SW-W1-S5", "SW-W1-S6", "SW-W1-S7"],
    dep_paths=["src/swarm/scheduling/service.py", "src/swarm/capabilities/lifecycle.py"],
    owned=["C src/swarm/cli_v23.py", "M src/swarm/cli.py (3 small hook edits only)", "C tests/product/test_v23_cli.py"],
    tests=["tests/product/test_v23_cli.py", "tests/product"],
    commit="feat(v2.3): offline swarm v23 CLI (scheduler policy/simulate, pack sign/verify, export/import)",
)
sess(
    "SW-W3-S4",
    title="V2.3 deterministic acceptance probes A01–A10",
    branch="cursor/v23-w3-s4-acceptance-probes",
    wave="3",
    deps=["SW-W2-S1", "SW-W1-S5", "SW-W1-S6", "SW-W1-S7", "SW-W1-S8", "SW-W1-S11", "SW-W0-S1"],
    dep_paths=[
        "src/swarm/scheduling/service.py",
        "src/swarm/capabilities/lifecycle.py",
        "src/swarm/contracts/router_capabilities.py",
        "src/swarm/observability/trace_graph.py",
        "benchmarks/v23_acceptance/scenarios.freeze.json",
    ],
    owned=["C src/swarm/acceptance/v23_probes.py", "C tests/acceptance/test_v23_acceptance.py"],
    tests=["tests/acceptance"],
    commit="feat(v2.3): deterministic acceptance probes A01-A10 bound to the frozen scenario manifest",
)
sess(
    "SW-W3-S5",
    title="V20-E10 product compose full-path smoke (Docker) — optional",
    branch="cursor/v20-w3-s5-compose-smoke",
    wave="3",
    optional=True,
    deps=["SW-W3-S1"],
    dep_paths=["src/swarm/api/routes_v23.py"],
    owned=[
        "C scripts/v20_compose_smoke.sh",
        "C docs/evidence/v20/compose-smoke/README.md",
        "C docs/evidence/v20/compose-smoke/latest.json",
    ],
    tests=[],
    commit="test(v2.0): E10 compose full-path smoke script and sanitized evidence",
)
sess(
    "SW-W4-S1",
    title="Campaign runner, V2.3 evidence, exit checklist, status/agents/CHANGELOG/README, candidate rebind",
    branch="cursor/v23-w4-s1-evidence-status",
    wave="4",
    deps=[
        "SW-W0-S3", "SW-W1-S12", "SW-W2-S2", "SW-W3-S1", "SW-W3-S2", "SW-W3-S3", "SW-W3-S4",
    ],
    dep_paths=[
        "src/swarm/api/routes_v23.py",
        "src/swarm/cli_v23.py",
        "src/swarm/acceptance/v23_probes.py",
        "src/swarm/pursuit/native_loop.py",
        "apps/console/src/components/OpsPanel.tsx",
    ],
    owned=[
        "C scripts/v23_acceptance_campaign.py",
        "C docs/evidence/v23/** (campaign outputs)",
        "C docs/v2.3/EXIT_CHECKLIST.md",
        "M docs/v2.3/STATUS.md",
        "M docs/v2.0/STATUS.md",
        "M docs/agents/CURRENT.md, docs/agents/context.json, docs/agents/RESUME.md, docs/agents/V20_TODO.md",
        "M CHANGELOG.md",
        "M README.md",
        "M src/swarm/release/candidate.py (add CURRENT_SCHEMA_REVISION)",
        "M src/swarm/cli.py and src/swarm/api/routes_v1.py (replace literal \"a18tov30schema0001\" with the constant; admin-gate candidate-freeze; nothing else)",
        "C tests/release/test_schema_revision.py",
    ],
    tests=["tests/release", "tests/acceptance"],
    commit="docs(v2.3): acceptance campaign evidence, exit checklist and honest status; bind candidate schema revision",
)


# Follow-up fixes after SW-W4-S1, executed by the integrator on 2026-09-26 (EXECUTED markers in PLAN.md).
sess(
    "SW-FIX-RETRY",
    title="RetryOwner gives up when upstream Retry-After exceeds the cap (SplitSignal rule)",
    branch="cursor/sw-fix-retry-after",
    wave="FIX",
    deps=["SW-W4-S1"],
    dep_paths=["src/swarm/broker/retry.py"],
    owned=[
        "M src/swarm/broker/retry.py",
        "M tests/broker/test_retry_after_cap.py",
        "M CHANGELOG.md (the F-06 line only)",
    ],
    tests=["tests/broker", "tests/providers"],
    commit="fix(broker): give up when upstream Retry-After exceeds max_retry_after_seconds (SW-FIX-RETRY)",
)
sess(
    "SW-FIX-COMPOSE",
    title="Compose worker gets its own connector process healthcheck; re-run V20-E10 smoke",
    branch="cursor/sw-fix-compose-healthcheck",
    wave="FIX",
    deps=["SW-W3-S5"],
    dep_paths=["deploy/compose/product.yml", "scripts/v20_compose_smoke.sh"],
    owned=[
        "M deploy/compose/product.yml (service worker only)",
        "M tests/deployment/test_product_compose.py",
        "M docs/evidence/v20/compose-smoke/latest.json",
        "M docs/evidence/v20/compose-smoke/README.md",
        "M docs/v2.3/EXIT_CHECKLIST.md (V20-E10 row only)",
        "M docs/agents/V20_TODO.md (V20-E10 row only)",
        "M docs/agents/context.json (V20-E10 entry only)",
    ],
    tests=["tests/deployment"],
    commit="fix(deploy): compose worker uses a connector process healthcheck (SW-FIX-COMPOSE)",
)
sess(
    "SW-FIX-ALEMBIC",
    title="Whole-repo pytest isolation: V20-S11 probe restores SWARM_*; Alembic tests pinned to their DB",
    branch="cursor/sw-fix-alembic-isolation",
    wave="FIX",
    deps=["SW-W4-S1"],
    dep_paths=["src/swarm/acceptance/probes.py", "tests/integration/db/test_v23_schema.py"],
    owned=[
        "M src/swarm/acceptance/probes.py (probe_sdk_ui_parity only)",
        "C tests/integration/db/conftest.py",
        "M tests/acceptance/test_campaign_harness.py (append one test)",
    ],
    tests=["tests/acceptance"],
    commit="fix(tests): whole-repo pytest isolation for Alembic schema tests (SW-FIX-ALEMBIC)",
)
sess(
    "SW-FIX-FLAKE",
    title="Deterministic V20-E08 kill-bound tests",
    branch="cursor/sw-fix-killbound-flake",
    wave="FIX",
    deps=["SW-W1-S13"],
    dep_paths=["tests/tools/test_v20_cancel_killbound.py"],
    owned=["M tests/tools/test_v20_cancel_killbound.py"],
    tests=["tests/tools/test_v20_cancel_killbound.py"],
    commit="test(sandbox): make the V20-E08 kill-bound tests deterministic (SW-FIX-FLAKE)",
)


INTEG = "cursor/sw-v23-integration-460c"
PLAN_BRANCH = "cursor/v23-plan-460c"
IS_INTEG = "cursor/is-v23-integration-460c"
PLAN_DOC = "docs/plans/v2.3/PLAN.md"
PREFLIGHT_DOC = "docs/plans/v2.3/OWNER_PREFLIGHT.md"
DECISIONS_DOC = "docs/swarm-mvp/DECISIONS.md"
BANNED = ("as appropriate", "etc.", "similar to", "if needed")

GENERIC_FOCUS = (
    "cross-tenant/project access; secret disclosure; financial accounting (unknown usage or cost "
    "is never zero); unbounded retries; silently changed model behaviour; recovery gaps after a "
    "crash/restart; unsupported release claims (\"accepted\", \"complete\")"
)
FOCUS: dict[str, str] = {
    "SW-W0-S1": "status docs must not claim V2.3 done; pause lift cites the 2026-09-26 owner decision; the plan-branch merge commit is docs-only",
    "SW-W0-S2": "migration is additive only, single Alembic head; ORM rows match the migration; no data loss on downgrade path",
    "SW-W0-S3": "GET /v1/ops/events returns only the principal's projects (F-01); Retry-After is capped (F-06)",
    "SW-W1-S2": "compare-and-set on version; no lost update under concurrency; tenant filter on every query",
    "SW-W1-S3": "reservation intent is fail-closed; no double dispatch; expiry handling",
    "SW-W1-S5": "pack signatures are keyed (F-02); unsigned or tampered packs are refused",
    "SW-W1-S6": "export redacts secrets by value, not only key name (F-03); import refuses foreign tenants",
    "SW-W1-S8": "trace graph never crosses projects; a foreign trace is 404",
    "SW-W1-S10": "unknown usage keeps budget committed (F-13); holds survive restart",
    "SW-W1-S11": "no HTTP-library retries; paid/unknown billing refused; API key never logged",
    "SW-W1-S12": "console mutations go only through the action boundary; live mode never falls back to fixtures",
    "SW-W2-S1": "fairness, fencing by epoch, receipts for every decision; no starvation",
    "SW-W2-S2": "loop bounds (turns/calls/tools); disallowed tool fails closed; no success invented",
    "SW-W3-S1": "every route checks project scope; admin-only routes; drain/revoke audited",
    "SW-W3-S2": "singleton ticker per site; durable flag off by default; restore after restart",
    "SW-W4-S1": "candidate-freeze admin gate (F-16); evidence and status make no acceptance claim",
    "SW-X1-S1": "D-SS1 free admission; known non-zero cost refused; unknown cost recorded as null and never settles as zero (C3/F-13); error classes; no retry after a 200 header; key never logged",
    "SW-FIX-RETRY": "over-cap or non-finite Retry-After is a terminal give-up (`retry_after_exceeds_cap`), never a retry at the cap; terminal classes and max_attempts keep precedence",
    "SW-FIX-COMPOSE": "worker healthcheck never probes the API port; `disable: true` is incompatible with `compose up --wait`; evidence has no secrets; VM-local changes recorded and reverted",
    "SW-FIX-ALEMBIC": "probe restores the caller's SWARM_* environment; Alembic migrates the database the test inspects; no assertion weakened",
    "SW-FIX-FLAKE": "test-only; the kill bound is measured from cancel; the grandchild exists before the kill; no assertion weakened",
    "SW-X2-S1": "at most 2 live calls, approval line checked before any network call, evidence has no prompt/response text and no key",
}


def _files_block(owned: list[str]) -> str:
    lines = []
    for o in owned:
        path, _, note = o[2:].partition(" (")
        verb = "create" if o.startswith("C ") else "modify"
        lines.append(f"- `{path}` — {verb}" + (f" ({note}" if note else ""))
    return "\n".join(lines)


def _dep_check(meta: dict) -> str:
    if not meta["deps"]:
        return "This session has **no dependencies**. Go to Step 1."
    lines = [
        f"Depends on: {', '.join(meta['deps'])}. Their PRs must already be merged into `{INTEG}` "
        "(by the wave MERGE prompt).",
        "Run every command below. Each must print `OK`. If any prints `MISSING`, STOP (condition S2 in section 10).",
        "",
        "```bash",
        f"git fetch origin {INTEG}",
    ]
    for p in meta["dep_paths"]:
        lines.append(f'git cat-file -e origin/{INTEG}:{p} && echo "OK {p}" || echo "MISSING {p}"')
    lines.append("```")
    return "\n".join(lines)


def _env_check(meta: dict) -> str:
    names = meta.get("env", [])
    if not names:
        return "This session needs **no** secrets or environment variables."
    lines = [
        "This session needs these environment variables (set by the owner preflight, "
        f"`{PREFLIGHT_DOC}`). Check names only; never print values:",
        "```bash",
    ]
    for n in names:
        lines.append(f'test -n "${n}" && echo "{n} SET" || echo "{n} MISSING"')
    lines += [
        "```",
        "If any prints `MISSING`, STOP (condition S6). Cursor may withhold secrets from this "
        "**public** repo; that is a preflight gap for the owner, not something to work around.",
    ]
    return "\n".join(lines)


def _db_name(ident: str) -> str:
    return "swarm_" + ident.lower().replace("-", "_")


def _db_setup(ident: str) -> list[str]:
    db = _db_name(ident)
    return [
        "# Private database for this session: concurrent sessions on one host must never share one.",
        f"sudo -u postgres psql -c \"CREATE DATABASE {db} OWNER swarm;\" || true",
        f"export SWARM_DATABASE_URL=postgresql+psycopg://swarm:swarm@127.0.0.1:5432/{db}",
    ]


def _verify(meta: dict) -> str:
    out = ["```bash", "git clean -fdX -- var/            # F-15: stale runtime state breaks re-runs"]
    if not meta["console"]:
        out += _db_setup(meta["sid"])
        out += [
            "uv run ruff check .",
            "uv run mypy src/swarm",
            "uv run alembic heads               # must print exactly ONE line ending in (head)",
        ]
        if meta["tests"]:
            out.append("uv run pytest " + " ".join(meta["tests"]) + " -q")
        out.append("uv run pytest " + CI_OFFLINE + " -q --ignore=tests/integration")
        out.append("")
        out.append("# PostgreSQL integration (install steps in “PostgreSQL” below)")
        out.append("uv run pytest tests/integration -q -m integration")
    else:
        out += [
            "cd apps/console",
            "npm ci",
            "npm run lint      # warnings allowed, errors not",
            "npm run test",
            "npm run build",
            "cd ../..",
            "uv run ruff check .   # sanity: python untouched",
        ]
    out += [
        "",
        "git checkout -- schemas/v1 docs/evidence/fix-004 var   # tests rewrite these tracked files",
        "git status --porcelain            # every path listed must be one of YOUR files",
        "```",
    ]
    return "\n".join(out)


def _identity(sid: str, meta: dict, handoff: str) -> list[str]:
    return [
        "| Field | Value |",
        "|---|---|",
        f"| Session ID | `{sid}` |",
        "| Repository | `pri8771/swarmai` (GitHub remote `origin`; **public** repo) |",
        f"| Base branch | `{INTEG}` — always the **current** `origin/{INTEG}` (plan baseline `dev` @ `{DEV_SHA[:8]}`) |",
        f"| Your branch | `{meta['branch']}` |",
        f"| Branch-suffix rule | If your environment forces a suffix (for example `-460c`), append it **once** to *your* branch and write the exact final name in the handoff. Never add a suffix to `{INTEG}`: it already ends in `-460c`. |",
        f"| PR target | `{INTEG}` — **draft** PR. Never `dev`, never `main`. |",
        f"| Wave | {meta['wave']} |",
        f"| Depends on | {', '.join(meta['deps']) or 'none'} |",
        f"| Handoff file | `{handoff}` |",
        "| Independent reviewer | Codex (owner decision D2). You never accept your own work. |",
        f"| Plan | `{PLAN_DOC}`; owner preflight `{PREFLIGHT_DOC}`; decisions `{DECISIONS_DOC}` |",
    ]


def _stop_section(sid: str, meta: dict) -> list[str]:
    return [
        "## 10. STOP conditions (never wait for a human)",
        "STOP immediately when any of these is true:",
        "- **S1** `git status --porcelain` is not empty before Setup. (Do not commit, stash or discard anything; skip steps 1–4 below and only report.)",
        "- **S2** a dependency check prints `MISSING`.",
        "- **S3** a command in section 6, or a check in section 5, still fails after **2 attempts**. One attempt = one edit to *your own files* followed by re-running the failing command.",
        "- **S4** a “currently reads” / before-block in section 5 does not match the file, or a function named in section 5 does not exist.",
        "- **S5** finishing would require editing a file that is not in section 3.",
        "- **S6** a required environment variable prints `MISSING`.",
        "- **S7** an external gate check (inference_server sync point or approval line) in section 5 fails.",
        "- **S8** `git push` still fails after 4 retries (waits 4 s, 8 s, 16 s, 32 s).",
        "",
        "What to do on STOP, in this order:",
        f"1. Commit whatever is complete inside your own files: `git add <your files> {'docs/v2.3/sessions/' + sid + '.md'}` then `git commit -m \"WIP({sid}): <one-line reason>\"`.",
        "2. Write the handoff (section 9) with `## Status` = `BLOCKED: <condition id> <one-line reason>`, and under `## Needs other owner` the exact file, function and change you need. Commit it.",
        f"3. Push: `git push -u origin {meta['branch']}` (plus your suffix).",
        f"4. Open the draft PR against `{INTEG}` with the title prefix `[BLOCKED]`, or record the compare URL `https://github.com/pri8771/swarmai/compare/{INTEG}...{meta['branch']}?expand=1` in the handoff.",
        "5. End the session with a final message: the condition id, the reason, the branch and the head SHA.",
        "Never work around a STOP by editing other files, weakening tests, or adding `skip`/`xfail`.",
        "",
        "If `tests/tools/test_v20_cancel_killbound.py` fails once in the full run and you did not touch `sandbox_runner.py` or that test, re-run the full list once. If it passes, record both result lines in the handoff under Verification and continue; if it fails twice, STOP (S3). (The known race was fixed by SW-FIX-FLAKE; a new failure is worth reporting.)",
        "",
    ]


def _review_packet(sid: str, meta: dict, owned_paths: list[str]) -> list[str]:
    focus = FOCUS.get(sid, "")
    return [
        "## 11. Codex review packet (put this in the PR description and in the handoff)",
        "```markdown",
        f"### Codex review packet — {sid}",
        "- PR: <PR URL — fill in after the PR exists>",
        f"- Branch: <exact branch name>  Base: origin/{INTEG} @ <base SHA from Setup>",
        "- Head SHA: <output of `git rev-parse HEAD`; must equal `git ls-remote origin refs/heads/<branch>`>",
        "- Diff for review: `git diff <base SHA>...<head SHA>`",
        "- Files to review: " + ", ".join(f"`{p}`" for p in owned_paths),
        f"- Review focus (AGENTS.md Code Review Rules): {GENERIC_FOCUS}."
        + (f" Session-specific: {focus}." if focus else ""),
        "- Checks run: <paste the final result line of every command in section 6>",
        "- Verdict requested: `RECOMMEND_ACCEPT <head SHA>` or `REQUEST_CHANGES` with file:line findings.",
        "```",
        "",
    ]


def build(sid: str) -> str:
    meta = S[sid]
    body = (BODIES / f"{sid}.md").read_text(encoding="utf-8")

    def _inline(m: re.Match[str]) -> str:
        return (REF / m.group(1)).read_text(encoding="utf-8").rstrip("\n")

    body = re.sub(r"\{\{FILE:([^}]+)\}\}", _inline, body)
    handoff = f"docs/v2.3/sessions/{sid}.md"
    owned_paths: list[str] = []
    for o in meta["owned"]:
        head = o[2:].split(" (")[0]
        for part in re.split(r",\s*|\s+and\s+", head):
            part = part.strip().replace("/**", "/")
            if part:
                owned_paths.append(part)
    optional = " (**optional** — run it only when the coordinator schedules it)" if meta["optional"] else ""
    spend_rule = (
        "3. Zero spend. The **only** network calls allowed are the ones section 5 names, only after "
        "the approval line `SW-PREAPPROVAL-A3: APPROVED` is present, and at most the number section 5 "
        "states. No account creation, no deploys, no paid APIs."
        if meta.get("live")
        else "3. Zero spend: no real model/provider calls, no paid APIs, no account creation, no deploys. "
        "`SWARM_ALLOW_PAID` stays `false`. Tests use fakes only."
    )
    parts = [
        f"# {sid} — {meta['title']}{optional}",
        "",
        "Copy this whole file into a fresh Cursor session opened on the **swarmai** repository. "
        "Follow it top to bottom. It is self-contained: do not read other plans to decide what to do.",
        "",
        *_identity(sid, meta, handoff),
        "",
        "## 0. Hard rules (read twice)",
        "1. Edit **only** the files listed in “Files you own” plus your handoff file. If another file must change, do not change it: write the exact change under “Needs other owner” in the handoff.",
        f"2. Never push to, or merge into, `main`, `dev` or `{INTEG}`. Never merge any PR, never force-push, never rewrite history, never delete branches. Only the wave MERGE prompts (`SW-MERGE-*`) push to `{INTEG}`.",
        spend_rule,
        "4. Never commit or print secrets, tokens, `.env` files, customer data or raw logs. Test tokens are fake literals such as `atk_policy_demo`. Check environment variables only with `test -n \"$NAME\"`.",
        "5. Passing tests are *not* acceptance. Never write “accepted”, “complete”, “released” or “V2.3 done”. Use “implemented” and “tested”.",
        "6. `src/swarm/contracts/v23.py`, `src/swarm/db/models.py` and `migrations/` belong to SW-W0-S2. Import from them; never edit them (unless you *are* SW-W0-S2).",
        "7. Do not edit `.github/workflows/`, `pyproject.toml`, `uv.lock`, `package.json` or lockfiles.",
        "8. If a step can be read two ways, choose the reading that changes fewer lines inside your own files, and write the choice under “Decisions” in the handoff.",
        "",
        "## 1. Setup",
        "```bash",
        "git status --porcelain            # must print nothing; otherwise STOP (S1)",
        f"git fetch origin {INTEG}",
        f"git ls-remote --exit-code origin refs/heads/{INTEG} >/dev/null && echo INTEG_OK || echo INTEG_MISSING",
        "```",
        (
            f"If it prints `INTEG_MISSING`, create the integration branch (only SW-W0-S1 may do this): "
            f"`git fetch origin dev && git push origin origin/dev:refs/heads/{INTEG}`, then run the fetch again."
            if sid == "SW-W0-S1"
            else "If it prints `INTEG_MISSING`, STOP (S2): SW-W0-S1 or the executor creates it."
        ),
        "```bash",
        f"git checkout -b {meta['branch']} origin/{INTEG}",
        "git log -1 --format='%H %s'       # record this SHA in the handoff as 'base'",
        "command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh   # then: export PATH=$HOME/.local/bin:$PATH",
        "uv sync",
        "git clean -fdX -- var/",
        "```",
        "",
        "## 2. Dependency and environment check",
        _dep_check(meta),
        "",
        _env_check(meta),
        "",
        "## 3. Files you own (the ONLY files you may create or modify)",
        _files_block(meta["owned"]),
        f"- `{handoff}` — create (your handoff)",
        "",
        "## 4. Do NOT touch",
        "- Any file not listed in section 3 (in particular: `src/swarm/api/app.py`, `src/swarm/api/store.py`, `src/swarm/cli.py`, `src/swarm/db/models.py`, `migrations/`, `docs/agents/*`, `docs/plans/v2.3/*`, `CHANGELOG.md`, `README.md`, `.github/`, unless listed above).",
        "- The `inference_server` repository: read-only, and only through the commands in section 5.",
        f"- The branches `main`, `dev`, `{INTEG}`, `{PLAN_BRANCH}`, and any other session's branch.",
        "- Generated files that tests rewrite: `schemas/v1/*`, `docs/evidence/fix-004/*`, `var/*` — always restore them before committing (section 6).",
        "",
        "## 5. Steps",
        body.rstrip("\n"),
        "",
        "## 6. Verify (run exactly; all must pass)",
        _verify(meta),
        "",
        "### PostgreSQL (for the integration line)",
        "```bash",
        "pg_isready -h 127.0.0.1 || {",
        "  sudo apt-get update && sudo apt-get install -y postgresql && sudo service postgresql start",
        "  sudo -u postgres psql -c \"CREATE USER swarm WITH PASSWORD 'swarm' SUPERUSER;\" || true",
        "}",
        "```",
        "Run this block before section 6. Section 6 creates your private database and exports `SWARM_DATABASE_URL` for **both** pytest lines; never unset it and never point it at the shared `swarm` database.",
        "If `pg_isready -h 127.0.0.1` still fails after running this block twice, write `integration: SKIPPED (postgres unavailable: <last error line>)` in the handoff and continue. Never claim integration passed without running it.",
        "",
        "## 7. Acceptance checklist (tick every box in the handoff)",
        "- [ ] Every step in section 5 done; every acceptance box in section 5 ticked.",
        "- [ ] `uv run ruff check .` and `uv run mypy src/swarm` pass." if not meta["console"] else "- [ ] `npm run lint` (no errors), `npm run test`, `npm run build` pass.",
        "- [ ] `uv run alembic heads` prints exactly one head." if not meta["console"] else "- [ ] No Python file changed.",
        "- [ ] Full offline CI list passes (paste the final `N passed` line into the handoff)." if not meta["console"] else "- [ ] Existing `src/console.test.tsx` still passes unchanged.",
        "- [ ] Integration run passed, or SKIPPED with reason in the handoff." if not meta["console"] else "- [ ] Mock mode renders the new UI; live mode never falls back to fixtures.",
        "- [ ] `git status --porcelain` lists only files from section 3 + the handoff.",
        "- [ ] No secrets, no network calls beyond section 5, no `accepted`/`complete` claims.",
        "- [ ] The Codex review packet (section 11) is in the PR description and the handoff.",
        "",
        "## 8. Commit, push, draft PR",
        "```bash",
        "git checkout -- schemas/v1 docs/evidence/fix-004 var",
        "git add " + " ".join(owned_paths) + f" {handoff}",
        "git status --porcelain            # nothing unexpected staged or left over",
        f'git commit -m "{meta["commit"]}" -m "Session: {sid}. Plan: {PLAN_DOC}."',
        f"git push -u origin {meta['branch']}",
        f'gh pr create --draft --base {INTEG} --head {meta["branch"]} --title "[{sid}] {meta["title"]}" --body-file {handoff}',
        f"git ls-remote origin refs/heads/{meta['branch']}   # must print the same SHA as: git rev-parse HEAD",
        "```",
        f"If `gh pr create` is refused (read-only `gh`), the environment opens the PR: check that its base is `{INTEG}` and that it is a draft, and put the PR URL (or the compare URL from section 10, step 4) into the handoff.",
        "If push fails for network reasons, retry up to 4 times waiting 4 s, 8 s, 16 s, 32 s; then STOP (S8).",
        "Docs to update: only your handoff file, plus any doc listed in section 3.",
        "",
        "## 9. Handoff file (create before committing)",
        f"Create `{handoff}` with exactly these headings:",
        "```markdown",
        f"# {sid} handoff",
        "- Branch: <exact branch name>   Base SHA: <from setup>   Head SHA: <git rev-parse HEAD>",
        "- PR: <url, or compare URL>",
        "## Done",
        "<bullet list of what you implemented>",
        "## Verification",
        "<each command from section 6 and its final result line; integration PASSED/SKIPPED(reason)>",
        "## Acceptance",
        "<copy the checkboxes from sections 5 and 7, ticked>",
        "## Decisions",
        "<choices you made under hard rule 8, or 'none'>",
        "## Needs other owner",
        "<files outside your scope that should change, with the exact change; or 'none'>",
        "## Codex review packet",
        "<the block from section 11, filled in>",
        "## Status",
        "implemented + tested (NOT accepted; needs Codex review)",
        "```",
        "",
        *_stop_section(sid, meta),
        *_review_packet(sid, meta, owned_paths + [handoff]),
    ]
    return "\n".join(parts)


WAVES: dict[str, list[str]] = {
    "W0": ["SW-W0-S1", "SW-W0-S2", "SW-W0-S3"],
    "W1": [f"SW-W1-S{i}" for i in range(1, 14)],
    "W2": ["SW-W2-S1", "SW-W2-S2"],
    "W3": ["SW-W3-S1", "SW-W3-S2", "SW-W3-S3", "SW-W3-S4", "SW-W3-S5"],
    "W4": ["SW-W4-S1"],
    "X": ["SW-X1-S1", "SW-X2-S1"],
}


def build_merge(wave: str) -> str:
    sids = WAVES[wave]
    mid = f"SW-MERGE-{wave}"
    handoff = f"docs/v2.3/sessions/{mid}.md"
    branch = f"cursor/v23-merge-{wave.lower()}"
    rows = "\n".join(
        f"| {i + 1} | `{s}` | `{S[s]['branch']}` | {'optional' if S[s]['optional'] else 'required'} |"
        for i, s in enumerate(sids)
    )
    console = any(S[s]["console"] for s in sids)
    plan_step = (
        [
            "### 3a. The plan branch (every wave; a no-op once it is merged)",
            "After section 3, check that the plan commit is in the tree:",
            "```bash",
            f"git ls-remote --exit-code origin refs/heads/{PLAN_BRANCH} >/dev/null && git fetch origin {PLAN_BRANCH} && "
            f"(git merge-base --is-ancestor origin/{PLAN_BRANCH} HEAD && echo PLAN_IN || echo PLAN_OUT) || echo PLAN_MISSING",
            "```",
            "- `PLAN_IN` or `PLAN_MISSING`: record it and continue.",
            f"- `PLAN_OUT`: `git merge --no-ff --no-edit origin/{PLAN_BRANCH} -m \"merge(plan): {PLAN_BRANCH} into integration (Codex review pending)\"`. "
            f"On a conflict: `git merge --abort`, then `git merge --no-ff --no-edit -X ours origin/{PLAN_BRANCH} -m \"merge(plan): {PLAN_BRANCH} into integration, integration side kept on conflicting hunks (Codex review pending)\"`. "
            "The integration side wins because the sessions own those files. Record `plan: merged with -X ours; conflicting files: <git diff --name-only HEAD^1 HEAD>` in the handoff. If this second merge also fails, run `git merge --abort` and STOP (M3).",
            "",
        ]
    )
    verify = [
        "```bash",
        "git clean -fdX -- var/",
        "uv sync",
        "uv run ruff check .",
        "uv run mypy src/swarm",
        "uv run alembic heads               # exactly ONE head",
        *_db_setup(mid),
        "uv run pytest " + CI_OFFLINE + " -q --ignore=tests/integration",
        "uv run pytest tests/integration -q -m integration",
    ]
    if console:
        verify += ["(cd apps/console && npm ci && npm run lint && npm run test && npm run build)"]
    verify += [
        "git checkout -- schemas/v1 docs/evidence/fix-004 var",
        "```",
    ]
    parts = [
        f"# {mid} — merge wave {wave} session PRs into `{INTEG}`",
        "",
        "Copy this whole file into a fresh Cursor session (or give it to the executor agent) on the **swarmai** repository. It is self-contained.",
        "",
        "| Field | Value |",
        "|---|---|",
        f"| Session ID | `{mid}` |",
        "| Repository | `pri8771/swarmai` (remote `origin`) |",
        f"| Target | `{INTEG}` (this prompt is the **only** kind of session that pushes to it) |",
        f"| Work branch | `{branch}` (local only; append a forced suffix once if your environment requires one) |",
        f"| Handoff | `{handoff}` (committed into `{INTEG}` together with the merges) |",
        "| Reviewer | Codex reviews the merged range (section 8). Merging does not mean accepted. |",
        f"| Never | merge into `dev` or `main`; force-push; rewrite history of `{INTEG}`; edit any file other than the handoff |",
        "",
        "Re-running this prompt is safe: branches already in the integration tree are detected and skipped. Run it again whenever a skipped session finishes.",
        "",
        "## 1. Sessions of this wave (merge in this order)",
        "| # | Session | Branch prefix | Kind |",
        "|---|---|---|---|",
        rows,
        "",
        "## 2. Setup",
        "```bash",
        "git status --porcelain            # must print nothing; otherwise STOP (M1)",
        "git fetch origin",
        f"git checkout -B {branch} origin/{INTEG}",
        "BASE=$(git rev-parse HEAD); echo \"BASE=$BASE\"",
        "uv sync && git clean -fdX -- var/",
        "```",
        "",
        "## 3. Merge each session, in the order of section 1",
        "For each row, run this block with `P` set to the branch prefix and `ID` to the session ID:",
        "```bash",
        "P=<branch prefix>; ID=<session id>",
        "L=$(echo \"$ID\" | tr 'A-Z' 'a-z')      # executor naming: cursor/<lowercase id>-<suffix>",
        "git cat-file -e \"HEAD:docs/v2.3/sessions/$ID.md\" 2>/dev/null && echo HANDOFF_IN || echo HANDOFF_OUT",
        "N=$(git ls-remote --heads origin \"$P*\" \"cursor/$L-*\" | wc -l); echo \"$ID branches=$N\"",
        "B=$(git ls-remote --heads origin \"$P*\" \"cursor/$L-*\" | awk '{print $2}' | sed 's#refs/heads/##')",
        "```",
        "- `HANDOFF_IN`: the session was already merged into the integration branch (possibly under another branch name). Record `$ID: already merged` and go to the next row.",
        "- `branches=0`: the session has not pushed. Record `$ID: not pushed` and go to the next row.",
        "- `branches` greater than 1: if the extra names differ only by a re-run suffix `-r2`, `-r3` …, set `B` to the one with the highest number and continue with the `branches=1` steps; otherwise record `$ID: ambiguous branches <names>` and go to the next row.",
        "- `branches=1`: run",
        "```bash",
        "git merge-base --is-ancestor \"origin/$B\" HEAD && echo ALREADY_IN || echo NEW",
        "git show \"origin/$B:docs/v2.3/sessions/$ID.md\" | sed -n '/^## Status/,+1p'",
        "```",
        "  - `ALREADY_IN`: record `$ID: already merged` and go to the next row.",
        "  - the Status line contains `BLOCKED`, or the handoff file does not exist: record `$ID: not ready (<status line>)` and go to the next row.",
        "  - otherwise: `git merge --no-ff --no-edit \"origin/$B\" -m \"merge($ID): into integration (Codex review pending)\"`. On a conflict: `git merge --abort`, record `$ID: conflict <files>`, and go to the next row.",
        "",
        *plan_step,
        "## 4. Verify the merged tree",
        *verify,
        "If Postgres is missing, install it with the block in section 7 first; if `pg_isready -h 127.0.0.1` still fails after 2 runs of that block, record `integration: SKIPPED (<reason>)`.",
        "",
        "If any command fails: run `git reset --hard $BASE` (local work branch only; nothing was pushed), then repeat section 3 **one session at a time**, running section 4 after each merge. Keep every merge that passes. When a merge makes section 4 fail, run `git reset --hard HEAD~1`, record `$ID: fails verify (<first failing test>)`, and continue with the next row. This is the only retry; do not edit code.",
        "",
        "## 5. Handoff and push",
        f"Write `{handoff}` with: BASE, the new head, one line per session (merged / already merged / not pushed / not ready / conflict / fails verify), every section 4 result line, and the section 8 packet. Then:",
        "```bash",
        f"git add {handoff} && git commit -m \"docs(v2.3): {mid} handoff\"",
        f"git push origin HEAD:{INTEG}",
        f"git ls-remote origin refs/heads/{INTEG}   # must equal git rev-parse HEAD",
        "```",
        f"If the push is rejected because `{INTEG}` moved: `git fetch origin {INTEG} && git merge --no-edit origin/{INTEG}`, run section 4 again, and push once more. If it is rejected again, STOP (M4).",
        "",
        "## 6. Wave-complete rule",
        f"The next wave may start only when every **required** session of this wave is `merged` or `already merged` in `{INTEG}`. Otherwise report the missing sessions; their owners re-run their prompts, then run this prompt again.",
        "",
        "## 7. PostgreSQL",
        "```bash",
        "pg_isready -h 127.0.0.1 || {",
        "  sudo apt-get update && sudo apt-get install -y postgresql && sudo service postgresql start",
        "  sudo -u postgres psql -c \"CREATE USER swarm WITH PASSWORD 'swarm' SUPERUSER;\" || true",
        "}",
        "```",
        "Run this block before section 4. Section 4 creates a database private to this merge run.",
        "",
        "## 8. Codex review packet (put it in the handoff)",
        "```markdown",
        f"### Codex review packet — {mid}",
        f"- Range: `git log --oneline $BASE..<new head>` on `{INTEG}`; diff `git diff $BASE...<new head>`",
        "- Session PRs merged: <list with PR URLs>",
        f"- Review focus: {GENERIC_FOCUS}; plus cross-session integration (shared contracts, one Alembic head).",
        "- Verdict requested per session PR and for the range: `RECOMMEND_ACCEPT <sha>` or `REQUEST_CHANGES`.",
        "```",
        "",
        "## 9. STOP conditions",
        "- **M1** the working tree is dirty at start (do nothing else; report).",
        "- **M3** the W0 plan-branch merge conflicts.",
        f"- **M4** the push to `{INTEG}` is rejected twice.",
        "On STOP: do not push; end with a final message giving the condition, the reason, and the per-session lines collected so far.",
        "",
    ]
    return "\n".join(parts)


def _lint(name: str, text: str) -> list[str]:
    low = text.lower()
    return [f"{name}: banned phrase {p!r}" for p in BANNED if p in low]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    missing = [sid for sid in S if not (BODIES / f"{sid}.md").exists()]
    problems: list[str] = []
    for sid in S:
        if sid in missing:
            continue
        text = build(sid)
        problems += _lint(sid, text)
        (OUT / f"{sid}.md").write_text(text, encoding="utf-8")
    for wave in WAVES:
        text = build_merge(wave)
        problems += _lint(f"SW-MERGE-{wave}", text)
        (OUT / f"SW-MERGE-{wave}.md").write_text(text, encoding="utf-8")
    print(f"wrote {len(S) - len(missing)} session prompts + {len(WAVES)} merge prompts; missing bodies: {missing}")
    if problems:
        raise SystemExit("\n".join(problems))


if __name__ == "__main__":
    main()
