# SW-W2-S2 — V20-E05 bounded native model/tool loop behind the fake router; honest E07 blocked path

Copy this whole file into a fresh Cursor session opened on the **swarmai** repository. Follow it top to bottom. It is self-contained: do not read other plans to decide what to do.

| Field | Value |
|---|---|
| Session ID | `SW-W2-S2` |
| Repository | `pri8771/swarmai` (GitHub remote `origin`; **public** repo) |
| Base branch | `cursor/sw-v23-integration-460c` — always the **current** `origin/cursor/sw-v23-integration-460c` (plan baseline `dev` @ `8e1c0fde`) |
| Your branch | `cursor/v20-w2-s2-native-loop` |
| Branch-suffix rule | If your environment forces a suffix (for example `-460c`), append it **once** to *your* branch and write the exact final name in the handoff. Never add a suffix to `cursor/sw-v23-integration-460c`: it already ends in `-460c`. |
| PR target | `cursor/sw-v23-integration-460c` — **draft** PR. Never `dev`, never `main`. |
| Wave | 2 |
| Depends on | SW-W1-S11 |
| Handoff file | `docs/v2.3/sessions/SW-W2-S2.md` |
| Independent reviewer | Codex (owner decision D2). You never accept your own work. |
| Plan | `docs/plans/v2.3/PLAN.md`; owner preflight `docs/plans/v2.3/OWNER_PREFLIGHT.md`; decisions `docs/swarm-mvp/DECISIONS.md` |

## 0. Hard rules (read twice)
1. Edit **only** the files listed in “Files you own” plus your handoff file. If another file must change, do not change it: write the exact change under “Needs other owner” in the handoff.
2. Never push to, or merge into, `main`, `dev` or `cursor/sw-v23-integration-460c`. Never merge any PR, never force-push, never rewrite history, never delete branches. Only the wave MERGE prompts (`SW-MERGE-*`) push to `cursor/sw-v23-integration-460c`.
3. Zero spend: no real model/provider calls, no paid APIs, no account creation, no deploys. `SWARM_ALLOW_PAID` stays `false`. Tests use fakes only.
4. Never commit or print secrets, tokens, `.env` files, customer data or raw logs. Test tokens are fake literals such as `atk_policy_demo`. Check environment variables only with `test -n "$NAME"`.
5. Passing tests are *not* acceptance. Never write “accepted”, “complete”, “released” or “V2.3 done”. Use “implemented” and “tested”.
6. `src/swarm/contracts/v23.py`, `src/swarm/db/models.py` and `migrations/` belong to SW-W0-S2. Import from them; never edit them (unless you *are* SW-W0-S2).
7. Do not edit `.github/workflows/`, `pyproject.toml`, `uv.lock`, `package.json` or lockfiles.
8. If a step can be read two ways, choose the reading that changes fewer lines inside your own files, and write the choice under “Decisions” in the handoff.

## 1. Setup
```bash
git status --porcelain            # must print nothing; otherwise STOP (S1)
git fetch origin cursor/sw-v23-integration-460c
git ls-remote --exit-code origin refs/heads/cursor/sw-v23-integration-460c >/dev/null && echo INTEG_OK || echo INTEG_MISSING
```
If it prints `INTEG_MISSING`, STOP (S2): SW-W0-S1 or the executor creates it.
```bash
git checkout -b cursor/v20-w2-s2-native-loop origin/cursor/sw-v23-integration-460c
git log -1 --format='%H %s'       # record this SHA in the handoff as 'base'
command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh   # then: export PATH=$HOME/.local/bin:$PATH
uv sync
git clean -fdX -- var/
```

## 2. Dependency and environment check
Depends on: SW-W1-S11. Their PRs must already be merged into `cursor/sw-v23-integration-460c` (by the wave MERGE prompt).
Run every command below. Each must print `OK`. If any prints `MISSING`, STOP (condition S2 in section 10).

```bash
git fetch origin cursor/sw-v23-integration-460c
git cat-file -e origin/cursor/sw-v23-integration-460c:src/swarm/providers/router_client.py && echo "OK src/swarm/providers/router_client.py" || echo "MISSING src/swarm/providers/router_client.py"
git cat-file -e origin/cursor/sw-v23-integration-460c:tests/fixtures/router_http/fake_router.py && echo "OK tests/fixtures/router_http/fake_router.py" || echo "MISSING tests/fixtures/router_http/fake_router.py"
```

This session needs **no** secrets or environment variables.

## 3. Files you own (the ONLY files you may create or modify)
- `src/swarm/pursuit/native_loop.py` — create
- `src/swarm/pursuit/native_dispatch.py` — modify
- `tests/pursuit/test_v20_native_loop.py` — create
- `docs/v2.3/sessions/SW-W2-S2.md` — create (your handoff)

## 4. Do NOT touch
- Any file not listed in section 3 (in particular: `src/swarm/api/app.py`, `src/swarm/api/store.py`, `src/swarm/cli.py`, `src/swarm/db/models.py`, `migrations/`, `docs/agents/*`, `docs/plans/v2.3/*`, `CHANGELOG.md`, `README.md`, `.github/`, unless listed above).
- The `inference_server` repository: read-only, and only through the commands in section 5.
- The branches `main`, `dev`, `cursor/sw-v23-integration-460c`, `cursor/v23-plan-460c`, and any other session's branch.
- Generated files that tests rewrite: `schemas/v1/*`, `docs/evidence/fix-004/*`, `var/*` — always restore them before committing (section 6).

## 5. Steps
**Goal.** Replace the "native dispatch records a plan and stops" behaviour with a **bounded native model/tool loop** that calls inference_server through `RouterClient` (SW-W1-S11).

Rules:
- The loop is hard-bounded by turns, model calls and tool calls. Only allow-listed tools ever execute.
- Any router error stops the loop and is recorded; it is never retried here.
- Missing `usage` is reported as `usage_known=False`, never as zero.
- The live path needs a ready `LiveGrant` plus `SWARM_ROUTER_BASE_URL` and `SWARM_ROUTER_MODEL`. Without them the executor records an honest blocker: `router_not_configured`, `router_model_not_configured` or the preflight reason (for example `missing_live_grant`).
- The executor **never invents success**. The mission outcome stays `submitted_pending` until acceptance, and `plan["native_loop"]` holds the loop summary plus a `native_loop.<status>` timeline entry.

The code below was compiled and run against `dev @ 8e1c0fde` plus the Wave-1 changes. `tests/pursuit tests/product tests/api` gives 82 passed (8 new), and ruff and mypy are clean. Paste it **exactly**.

### Step 1 — `src/swarm/pursuit/native_loop.py` (create, exactly)
```python
"""V20-E05: bounded native model/tool loop over RouterClient.

Hard bounds on turns, model calls and tool calls. Tools must be allowlisted; an
unknown or disallowed tool call stops the loop (fail closed) without executing.
The loop never decides goal success: callers keep outcomes pending until
protected verification. Only a transcript digest is kept, never raw content.

Live use (V20-E07) needs a usable LiveGrant; ``native_loop_from_env`` returns an
honest blocker instead of constructing a live client without one.
"""

from __future__ import annotations

import json
import os
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any, Literal

from swarm.contracts.common import payload_hash
from swarm.contracts.router_capabilities import RouterCallReceipt
from swarm.evals.synthetic_harness import LiveGrant
from swarm.providers.router_client import RouterClient, RouterClientError
from swarm.pursuit.live_grant import preflight_live_grant

ToolFn = Callable[[dict[str, Any]], str]
LoopStatus = Literal["completed", "budget_exhausted", "tool_denied", "router_error"]


@dataclass
class LoopResult:
    status: LoopStatus
    final_text: str = ""
    turns: int = 0
    model_calls: int = 0
    tool_calls: int = 0
    receipts: list[RouterCallReceipt] = field(default_factory=list)
    error_class: str | None = None
    error_code: str | None = None
    transcript_digest: str = ""

    @property
    def usage_known(self) -> bool:
        return bool(self.receipts) and all(r.usage_known for r in self.receipts)

    def summary(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "turns": self.turns,
            "model_calls": self.model_calls,
            "tool_calls": self.tool_calls,
            "usage_known": self.usage_known,
            "error_class": self.error_class,
            "error_code": self.error_code,
            "transcript_digest": self.transcript_digest,
            "routes": sorted({r.route_id for r in self.receipts if r.route_id}),
        }


class BoundedNativeLoop:
    def __init__(
        self,
        router: RouterClient,
        tools: Mapping[str, ToolFn],
        *,
        model: str,
        max_turns: int = 4,
        max_model_calls: int = 8,
        max_tool_calls: int = 8,
    ) -> None:
        self.router = router
        self.tools = dict(tools)
        self.model = model
        self.max_turns = max_turns
        self.max_model_calls = max_model_calls
        self.max_tool_calls = max_tool_calls

    def _tool_specs(self) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {"name": name, "parameters": {"type": "object"}},
            }
            for name in sorted(self.tools)
        ]

    def run(self, objective: str, *, system: str | None = None) -> LoopResult:
        messages: list[dict[str, Any]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": objective})
        result = LoopResult(status="budget_exhausted")

        def done(status: LoopStatus, **kw: Any) -> LoopResult:
            result.status = status
            for k, v in kw.items():
                setattr(result, k, v)
            result.transcript_digest = payload_hash({"messages": messages})
            return result

        for _ in range(self.max_turns):
            if result.model_calls >= self.max_model_calls:
                return done("budget_exhausted", error_code="max_model_calls")
            result.turns += 1
            body: dict[str, Any] = {"model": self.model, "messages": messages}
            if self.tools:
                body["tools"] = self._tool_specs()
            try:
                chat = self.router.chat(body)
            except RouterClientError as exc:
                result.model_calls += 1
                if exc.receipt is not None:
                    result.receipts.append(exc.receipt)
                return done("router_error", error_class=exc.error_class.value, error_code=exc.code)
            result.model_calls += 1
            result.receipts.append(chat.receipt)
            msg = chat.message
            messages.append(msg)
            calls = msg.get("tool_calls") or []
            if not calls:
                return done("completed", final_text=str(msg.get("content") or ""))
            for call in calls:
                fn = (call.get("function") or {}) if isinstance(call, dict) else {}
                name = str(fn.get("name") or "")
                if name not in self.tools:
                    return done("tool_denied", error_code=f"tool_not_allowed:{name}")
                if result.tool_calls >= self.max_tool_calls:
                    return done("budget_exhausted", error_code="max_tool_calls")
                try:
                    args = json.loads(fn.get("arguments") or "{}")
                except ValueError:
                    return done("tool_denied", error_code=f"tool_args_invalid:{name}")
                if not isinstance(args, dict):
                    return done("tool_denied", error_code=f"tool_args_invalid:{name}")
                result.tool_calls += 1
                output = self.tools[name](args)
                messages.append(
                    {"role": "tool", "tool_call_id": str(call.get("id") or ""), "content": output}
                )
        return done("budget_exhausted", error_code="max_turns")


def native_loop_from_env(
    tools: Mapping[str, ToolFn],
    *,
    grant: LiveGrant | None,
    env: Mapping[str, str] | None = None,
) -> tuple[BoundedNativeLoop | None, str]:
    """Build a live loop only with a router URL, a model and a usable LiveGrant."""
    e = os.environ if env is None else env
    base_url = e.get("SWARM_ROUTER_BASE_URL", "").strip()
    if not base_url:
        return None, "router_not_configured"
    model = e.get("SWARM_ROUTER_MODEL", "").strip()
    if not model:
        return None, "router_model_not_configured"
    pre = preflight_live_grant(grant, purpose="pursuit_native_loop", required_route=model)
    if not pre.ready:
        return None, pre.blocked_reason or "live_grant_not_ready"
    return BoundedNativeLoop(RouterClient(base_url), tools, model=model), "ready"
```

### Step 2 — `src/swarm/pursuit/native_dispatch.py` (replace the whole file, exactly)
Your base file must be the `dev @ 8e1c0fde` version. If `git diff 8e1c0fdec24c131e7612d88076220945230f4c3b -- src/swarm/pursuit/native_dispatch.py` prints anything before you start, someone else changed it: STOP (S4, section 10).
```python
"""Operational pursuit executor — durable native mission dispatch (R20-01).

Never synthesizes achievement. Admits a RUNNING mission under ``var/missions/``
and returns a pending outcome until protected verification accepts an artifact.
An optional bounded native loop (V20-E05) may run model/tool turns; its result is
recorded on the mission but never turns the outcome into success.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from swarm.contracts.common import new_id, utc_now
from swarm.contracts.enums import MissionStatus
from swarm.contracts.fixtures import sample_task
from swarm.contracts.mission import Mission
from swarm.pursuit.models import ExecutionOutcome, MissionProposalDraft
from swarm.pursuit.native_loop import BoundedNativeLoop, LoopResult, native_loop_from_env
from swarm.pursuit.verification import (
    artifact_digest_for_refs,
    issue_criterion_receipt,
)

if TYPE_CHECKING:
    from swarm.api.store import ProductStore

PROVENANCE = "pursuit_native_dispatch"
SOURCE = "pursuit_native"


class NativeMissionDispatchExecutor:
    """Dispatch real durable missions for operational pursuit.

    ``RecordingExecutor`` remains available only for explicit fixture/mock demos.
    """

    def __init__(
        self,
        store: ProductStore,
        *,
        enqueue_worker_task: bool = True,
        native_loop: BoundedNativeLoop | None = None,
    ) -> None:
        self.store = store
        self.enqueue_worker_task = enqueue_worker_task
        self.native_loop = native_loop
        self.loop_blocker: str | None = None
        if native_loop is None:
            # No LiveGrant is ever invented here, so this reports the honest blocker.
            _, self.loop_blocker = native_loop_from_env({}, grant=None)

    def execute(self, proposal: MissionProposalDraft) -> ExecutionOutcome:
        mission_id = proposal.mission_id or new_id("msn_")
        project_id = self._project_id(proposal.goal_id)
        mission = Mission(
            id=mission_id,
            project_id=project_id,
            objective=proposal.objective,
            acceptance_criteria=list(proposal.addresses_criteria),
            allowed_capabilities=list(proposal.admitted_tools) or ["workspace.read"],
            data_scope_ids=[f"scope_{project_id}"],
            resource_policy_id="policy_pursuit_native",
            max_wall_time_seconds=3600,
            max_graph_nodes=50,
            max_active_sessions=4,
            max_model_calls=50,
            status=MissionStatus.RUNNING,
        )
        self.store.controller.missions[mission.id] = mission
        self.store._persist_mission_record(mission, source=SOURCE)
        record = self.store.mission_store().load(mission.id)
        plan = dict(record.plan or {})
        plan.update(
            {
                "project_id": project_id,
                "goal_id": proposal.goal_id,
                "proposal_id": proposal.proposal_id,
                "dedupe_key": proposal.dedupe_key,
                "runtime": "native",
                "addresses_criteria": list(proposal.addresses_criteria),
                "admitted_tools": list(proposal.admitted_tools),
                "admitted_providers": list(proposal.admitted_providers),
                "provenance": PROVENANCE,
                "task_family": "extract",
            }
        )
        record.plan = plan
        record.source = SOURCE
        record.status = MissionStatus.RUNNING.value
        self.store.mission_store().append_timeline(
            record,
            "mission.created",
            {"source": SOURCE, "provenance": PROVENANCE, "goal_id": proposal.goal_id},
        )
        self.store.mission_store().save(record)

        try:
            self.store.goal_store().link_mission(proposal.goal_id, mission.id)
        except KeyError:
            pass

        if self.enqueue_worker_task:
            self._enqueue_task(mission_id=mission.id, project_id=project_id, proposal=proposal)

        loop_result = self._run_native_loop(mission.id, proposal)

        self.store.publish(
            project_id=project_id,
            type="mission.created",
            actor="pursuit",
            mission_id=mission.id,
            payload={"source": SOURCE, "provenance": PROVENANCE, "status": "running"},
            dedupe_key=f"mission.created:{mission.id}",
        )

        routes = [r.route_id for r in loop_result.receipts if r.route_id] if loop_result else []
        return ExecutionOutcome(
            mission_id=mission.id,
            success=False,
            failure_class="submitted_pending",
            notes="native_mission_dispatched_awaiting_worker_and_protected_verify",
            cost_usd=0.0,
            model_calls=loop_result.model_calls if loop_result else 0,
            tool_calls=loop_result.tool_calls if loop_result else 0,
            route_id=routes[0] if routes else None,
            runtime="native",
            usage_unknown=loop_result is not None
            and loop_result.model_calls > 0
            and not loop_result.usage_known,
        )

    def _run_native_loop(
        self, mission_id: str, proposal: MissionProposalDraft
    ) -> LoopResult | None:
        result: LoopResult | None = None
        if self.native_loop is None:
            summary: dict[str, Any] = {"status": "blocked", "reason": self.loop_blocker}
        else:
            result = self.native_loop.run(proposal.objective)
            summary = result.summary()
        record = self.store.mission_store().load(mission_id)
        plan = dict(record.plan or {})
        plan["native_loop"] = summary
        record.plan = plan
        self.store.mission_store().append_timeline(
            record, f"native_loop.{summary['status']}", dict(summary)
        )
        self.store.mission_store().save(record)
        return result

    def reconcile(self, mission_id: str) -> ExecutionOutcome | None:
        """Return terminal outcome when mission completed/failed; else None (still pending)."""
        path = self.store.mission_store()._path(mission_id)
        if not path.exists():
            return ExecutionOutcome(
                mission_id=mission_id,
                success=False,
                failure_class="mission_missing",
                runtime="native",
            )
        record = self.store.mission_store().load(mission_id)
        status = (record.status or "").lower()
        validation = dict(record.validation or {})
        protected = validation.get("protected_verify") or {}
        result = dict(record.result or {})
        receipt_id = result.get("acceptance_receipt_id")
        if not receipt_id:
            mission = self.store.controller.missions.get(mission_id)
            if mission is not None:
                receipt_id = mission.acceptance_receipt_id

        if status in {"failed", "cancelled"}:
            return ExecutionOutcome(
                mission_id=mission_id,
                success=False,
                failure_class=f"mission_{status}",
                notes=str((record.result or {}).get("summary") or status),
                runtime="native",
            )

        if (
            status == "completed"
            and receipt_id
            and isinstance(protected, dict)
            and protected.get("accepted") is True
        ):
            plan = dict(record.plan or {})
            criteria = list(plan.get("addresses_criteria") or [])
            goal_id = str(plan.get("goal_id") or "")
            content_hash = str(protected.get("content_hash") or "")
            artifact_id = str(protected.get("artifact_id") or "")
            evidence_refs = [f"art:{artifact_id}"] if artifact_id else [f"acr:{receipt_id}"]
            digest = content_hash or artifact_digest_for_refs(
                evidence_refs, mission_id=mission_id
            )
            receipts: list[dict[str, Any]] = []
            for criterion_id in criteria:
                if not goal_id:
                    break
                receipt = issue_criterion_receipt(
                    goal_id=goal_id,
                    criterion_id=criterion_id,
                    mission_id=mission_id,
                    artifact_digest=digest,
                    evidence_ref=evidence_refs[0],
                )
                receipts.append(receipt.model_dump(mode="json"))
            return ExecutionOutcome(
                mission_id=mission_id,
                success=True,
                evidence_refs=evidence_refs,
                satisfied_criteria=list(criteria),
                criterion_receipts=receipts,
                notes=f"protected_verify_accepted:{receipt_id}",
                cost_usd=0.0,
                model_calls=0,
                tool_calls=0,
                runtime="native",
            )

        # Still awaiting worker execution / protected verify.
        return None

    def _project_id(self, goal_id: str) -> str:
        try:
            return str(self.store.goal_store().get(goal_id).project_id)
        except KeyError:
            return "proj_unknown"

    def _enqueue_task(
        self,
        *,
        mission_id: str,
        project_id: str,
        proposal: MissionProposalDraft,
    ) -> None:
        task = sample_task(mission_id=mission_id).model_copy(
            update={
                "id": new_id("tsk_"),
                "project_id": project_id,
                "objective": proposal.objective,
                "task_family": "extract",
                "required_capabilities": ["extract"],
                "scopes": ["local"],
                "inputs": {
                    "goal_id": proposal.goal_id,
                    "proposal_id": proposal.proposal_id,
                    "addresses_criteria": list(proposal.addresses_criteria),
                    "dispatched_at": utc_now().isoformat(),
                },
            }
        )
        self.store.workers.enqueue(task)
        record = self.store.mission_store().load(mission_id)
        tasks = list(record.tasks or [])
        tasks.append(task.model_dump(mode="json"))
        record.tasks = tasks
        self.store.mission_store().append_timeline(
            record,
            "task.enqueued",
            {"task_id": task.id, "required_capabilities": list(task.required_capabilities)},
        )
        self.store.mission_store().save(record)


class BlockedMissingImplementationExecutor:
    """Honest blocker when no native dispatch is wired (no synthetic success).

    Used as ``PursuitEngine`` default when callers omit an executor. Operational
    ProductStore must prefer ``NativeMissionDispatchExecutor`` instead.
    """

    def execute(self, proposal: MissionProposalDraft) -> ExecutionOutcome:
        mission_id = proposal.mission_id or new_id("msn_")
        return ExecutionOutcome(
            mission_id=mission_id,
            success=False,
            failure_class="blocked_missing_implementation",
            notes="operational_pursuit_requires_native_dispatch",
            evidence_refs=[],
            satisfied_criteria=[],
            criterion_receipts=[],
            cost_usd=0.0,
            model_calls=0,
            tool_calls=0,
            runtime="blocked",
        )
```

### Step 3 — `tests/pursuit/test_v20_native_loop.py` (create, exactly)
It uses `tests/fixtures/router_http/fake_router.py` from SW-W1-S11, so no network is involved.
```python
"""SW-W2-S2 / V20-E05 + E07: bounded native loop over the fake router; honest live blocker."""

from __future__ import annotations

from pathlib import Path

from swarm.api.store import ProductStore
from swarm.providers.router_client import RouterClient
from swarm.pursuit.models import ContributionKind, MissionProposalDraft
from swarm.pursuit.native_dispatch import NativeMissionDispatchExecutor
from swarm.pursuit.native_loop import BoundedNativeLoop, native_loop_from_env
from tests.fixtures.router_http.fake_router import FakeRouter

BASE = "http://router.invalid"


def _loop(scenario: str, tools: dict | None = None, **kw: int) -> tuple[BoundedNativeLoop, list]:
    calls: list[dict] = []

    def read(args: dict) -> str:
        calls.append(args)
        return "readme contents"

    fake = FakeRouter(scenario)
    router = RouterClient(BASE, transport=fake.transport)
    tool_map = {"workspace.read": read} if tools is None else tools
    return BoundedNativeLoop(router, tool_map, model="fake-free", **kw), calls


def test_tool_roundtrip_completes_within_bounds() -> None:
    loop, calls = _loop("tools")
    res = loop.run("summarize README")
    assert res.status == "completed" and res.final_text == "done after tool"
    assert (res.model_calls, res.tool_calls, res.turns) == (2, 1, 2)
    assert calls == [{"path": "README.md"}]
    assert res.usage_known and res.transcript_digest


def test_disallowed_tool_is_never_executed() -> None:
    loop, calls = _loop("tools", tools={})
    res = loop.run("x")
    assert res.status == "tool_denied" and res.error_code == "tool_not_allowed:workspace.read"
    assert calls == []


def test_model_call_budget_is_hard() -> None:
    loop, _ = _loop("tools", max_model_calls=1)
    res = loop.run("x")
    assert res.status == "budget_exhausted" and res.model_calls == 1


def test_router_errors_stop_the_loop() -> None:
    loop, _ = _loop("rate_limited")
    res = loop.run("x")
    assert (res.status, res.error_class) == ("router_error", "rate_limit")
    paid, _ = _loop("paid")
    res = paid.run("x")
    assert (res.error_class, res.error_code) == ("policy_denied", "paid_route_forbidden")


def test_missing_usage_is_reported_unknown() -> None:
    loop, _ = _loop("missing_usage")
    res = loop.run("x")
    assert res.status == "completed" and res.usage_known is False


def test_live_loop_requires_grant() -> None:
    assert native_loop_from_env({}, grant=None, env={}) == (None, "router_not_configured")
    env = {"SWARM_ROUTER_BASE_URL": BASE, "SWARM_ROUTER_MODEL": "fake-free"}
    loop, reason = native_loop_from_env({}, grant=None, env=env)
    assert loop is None and reason == "missing_live_grant"


def _proposal(goal_id: str = "goal_nl") -> MissionProposalDraft:
    return MissionProposalDraft(
        goal_id=goal_id,
        title="t",
        objective="summarize README",
        kind=ContributionKind.ACT,
        dedupe_key=f"{goal_id}:act:1",
        addresses_criteria=["c1"],
    )


def test_executor_records_loop_but_never_invents_success(tmp_path: Path) -> None:
    store = ProductStore(repo_root=tmp_path, db_reachable=None)
    loop, _ = _loop("tools")
    executor = NativeMissionDispatchExecutor(store, enqueue_worker_task=False, native_loop=loop)
    out = executor.execute(_proposal())
    assert out.success is False and out.failure_class == "submitted_pending"
    assert (out.model_calls, out.tool_calls, out.route_id) == (2, 1, "fake-free")
    plan = store.mission_store().load(out.mission_id).plan
    assert plan["native_loop"]["status"] == "completed"
    assert "readme contents" not in str(plan)


def test_executor_without_loop_records_honest_blocker(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("SWARM_ROUTER_BASE_URL", raising=False)
    store = ProductStore(repo_root=tmp_path, db_reachable=None)
    out = NativeMissionDispatchExecutor(store, enqueue_worker_task=False).execute(_proposal())
    plan = store.mission_store().load(out.mission_id).plan
    assert plan["native_loop"] == {"status": "blocked", "reason": "router_not_configured"}
    assert out.model_calls == 0 and out.success is False
```

### Step 4 — run
```bash
uv run pytest tests/pursuit/test_v20_native_loop.py -q        # 8 passed
uv run pytest tests/pursuit tests/product tests/api -q        # all pass
```
If `RouterClient`, `ChatResult`, `RouterClientError` or `FakeRouter` are missing, SW-W1-S11 has not been merged into your base yet. STOP (S2, section 10) with reason `blocked_on SW-W1-S11`.

**Never** point the tests or a local run at a real inference_server or at any paid route. Live runs belong to SW-W4-S1, under an explicit owner grant.

## 6. Verify (run exactly; all must pass)
```bash
git clean -fdX -- var/            # F-15: stale runtime state breaks re-runs
# Private database for this session: concurrent sessions on one host must never share one.
sudo -u postgres psql -c "CREATE DATABASE swarm_sw_w2_s2 OWNER swarm;" || true
export SWARM_DATABASE_URL=postgresql+psycopg://swarm:swarm@127.0.0.1:5432/swarm_sw_w2_s2
uv run ruff check .
uv run mypy src/swarm
uv run alembic heads               # must print exactly ONE line ending in (head)
uv run pytest tests/pursuit -q
uv run pytest tests/contracts tests/spikes tests/api tests/broker tests/controller tests/chaos tests/deployment tests/evals tests/extensions tests/foundation tests/goals tests/pursuit tests/sdk tests/knowledge tests/load tests/memory tests/mission tests/objectives tests/onboarding tests/product tests/providers tests/recovery tests/regressions tests/release tests/runtime tests/selfdev tests/tools tests/ui tests/workers tests/workspace tests/e2e tests/acceptance tests/portability -q --ignore=tests/integration

# PostgreSQL integration (install steps in “PostgreSQL” below)
uv run pytest tests/integration -q -m integration

git checkout -- schemas/v1 docs/evidence/fix-004 var   # tests rewrite these tracked files
git status --porcelain            # every path listed must be one of YOUR files
```

### PostgreSQL (for the integration line)
```bash
pg_isready -h 127.0.0.1 || {
  sudo apt-get update && sudo apt-get install -y postgresql && sudo service postgresql start
  sudo -u postgres psql -c "CREATE USER swarm WITH PASSWORD 'swarm' SUPERUSER;" || true
}
```
Run this block before section 6. Section 6 creates your private database and exports `SWARM_DATABASE_URL` for **both** pytest lines; never unset it and never point it at the shared `swarm` database.
If `pg_isready -h 127.0.0.1` still fails after running this block twice, write `integration: SKIPPED (postgres unavailable: <last error line>)` in the handoff and continue. Never claim integration passed without running it.

## 7. Acceptance checklist (tick every box in the handoff)
- [ ] Every step in section 5 done; every acceptance box in section 5 ticked.
- [ ] `uv run ruff check .` and `uv run mypy src/swarm` pass.
- [ ] `uv run alembic heads` prints exactly one head.
- [ ] Full offline CI list passes (paste the final `N passed` line into the handoff).
- [ ] Integration run passed, or SKIPPED with reason in the handoff.
- [ ] `git status --porcelain` lists only files from section 3 + the handoff.
- [ ] No secrets, no network calls beyond section 5, no `accepted`/`complete` claims.
- [ ] The Codex review packet (section 11) is in the PR description and the handoff.

## 8. Commit, push, draft PR
```bash
git checkout -- schemas/v1 docs/evidence/fix-004 var
git add src/swarm/pursuit/native_loop.py src/swarm/pursuit/native_dispatch.py tests/pursuit/test_v20_native_loop.py docs/v2.3/sessions/SW-W2-S2.md
git status --porcelain            # nothing unexpected staged or left over
git commit -m "feat(v2.0): E05 bounded native model/tool loop over RouterClient (fake-router tested, live blocked)" -m "Session: SW-W2-S2. Plan: docs/plans/v2.3/PLAN.md."
git push -u origin cursor/v20-w2-s2-native-loop
gh pr create --draft --base cursor/sw-v23-integration-460c --head cursor/v20-w2-s2-native-loop --title "[SW-W2-S2] V20-E05 bounded native model/tool loop behind the fake router; honest E07 blocked path" --body-file docs/v2.3/sessions/SW-W2-S2.md
git ls-remote origin refs/heads/cursor/v20-w2-s2-native-loop   # must print the same SHA as: git rev-parse HEAD
```
If `gh pr create` is refused (read-only `gh`), the environment opens the PR: check that its base is `cursor/sw-v23-integration-460c` and that it is a draft, and put the PR URL (or the compare URL from section 10, step 4) into the handoff.
If push fails for network reasons, retry up to 4 times waiting 4 s, 8 s, 16 s, 32 s; then STOP (S8).
Docs to update: only your handoff file, plus any doc listed in section 3.

## 9. Handoff file (create before committing)
Create `docs/v2.3/sessions/SW-W2-S2.md` with exactly these headings:
```markdown
# SW-W2-S2 handoff
- Branch: <exact branch name>   Base SHA: <from setup>   Head SHA: <git rev-parse HEAD>
- PR: <url, or compare URL>
## Done
<bullet list of what you implemented>
## Verification
<each command from section 6 and its final result line; integration PASSED/SKIPPED(reason)>
## Acceptance
<copy the checkboxes from sections 5 and 7, ticked>
## Decisions
<choices you made under hard rule 8, or 'none'>
## Needs other owner
<files outside your scope that should change, with the exact change; or 'none'>
## Codex review packet
<the block from section 11, filled in>
## Status
implemented + tested (NOT accepted; needs Codex review)
```

## 10. STOP conditions (never wait for a human)
STOP immediately when any of these is true:
- **S1** `git status --porcelain` is not empty before Setup. (Do not commit, stash or discard anything; skip steps 1–4 below and only report.)
- **S2** a dependency check prints `MISSING`.
- **S3** a command in section 6, or a check in section 5, still fails after **2 attempts**. One attempt = one edit to *your own files* followed by re-running the failing command.
- **S4** a “currently reads” / before-block in section 5 does not match the file, or a function named in section 5 does not exist.
- **S5** finishing would require editing a file that is not in section 3.
- **S6** a required environment variable prints `MISSING`.
- **S7** an external gate check (inference_server sync point or approval line) in section 5 fails.
- **S8** `git push` still fails after 4 retries (waits 4 s, 8 s, 16 s, 32 s).

What to do on STOP, in this order:
1. Commit whatever is complete inside your own files: `git add <your files> docs/v2.3/sessions/SW-W2-S2.md` then `git commit -m "WIP(SW-W2-S2): <one-line reason>"`.
2. Write the handoff (section 9) with `## Status` = `BLOCKED: <condition id> <one-line reason>`, and under `## Needs other owner` the exact file, function and change you need. Commit it.
3. Push: `git push -u origin cursor/v20-w2-s2-native-loop` (plus your suffix).
4. Open the draft PR against `cursor/sw-v23-integration-460c` with the title prefix `[BLOCKED]`, or record the compare URL `https://github.com/pri8771/swarmai/compare/cursor/sw-v23-integration-460c...cursor/v20-w2-s2-native-loop?expand=1` in the handoff.
5. End the session with a final message: the condition id, the reason, the branch and the head SHA.
Never work around a STOP by editing other files, weakening tests, or adding `skip`/`xfail`.

If `tests/tools/test_v20_cancel_killbound.py` fails once in the full run and you did not touch `sandbox_runner.py` or that test, re-run the full list once. If it passes, record both result lines in the handoff under Verification and continue; if it fails twice, STOP (S3). (The known race was fixed by SW-FIX-FLAKE; a new failure is worth reporting.)

## 11. Codex review packet (put this in the PR description and in the handoff)
```markdown
### Codex review packet — SW-W2-S2
- PR: <PR URL — fill in after the PR exists>
- Branch: <exact branch name>  Base: origin/cursor/sw-v23-integration-460c @ <base SHA from Setup>
- Head SHA: <output of `git rev-parse HEAD`; must equal `git ls-remote origin refs/heads/<branch>`>
- Diff for review: `git diff <base SHA>...<head SHA>`
- Files to review: `src/swarm/pursuit/native_loop.py`, `src/swarm/pursuit/native_dispatch.py`, `tests/pursuit/test_v20_native_loop.py`, `docs/v2.3/sessions/SW-W2-S2.md`
- Review focus (AGENTS.md Code Review Rules): cross-tenant/project access; secret disclosure; financial accounting (unknown usage or cost is never zero); unbounded retries; silently changed model behaviour; recovery gaps after a crash/restart; unsupported release claims ("accepted", "complete"). Session-specific: loop bounds (turns/calls/tools); disallowed tool fails closed; no success invented.
- Checks run: <paste the final result line of every command in section 6>
- Verdict requested: `RECOMMEND_ACCEPT <head SHA>` or `REQUEST_CHANGES` with file:line findings.
```
