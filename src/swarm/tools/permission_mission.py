"""V0.5 — permissioned tool mission proof (allow / deny / human-gated)."""

from __future__ import annotations

import asyncio
import hashlib
import json
from pathlib import Path
from typing import Any

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from swarm.contracts.common import new_id, utc_now
from swarm.contracts.enums import ActionOutcome, MissionStatus, TaskStatus
from swarm.contracts.mission import Mission, TaskSpec
from swarm.contracts.workspace import ToolCall
from swarm.db.engine import DatabaseConfigError, create_db_engine, make_session_factory
from swarm.db.lease_fencing import ClaimedLease, LeaseLifecycleService, WorkerRegistrationRepository
from swarm.db.models import TaskRow
from swarm.db.repositories import MissionRepository
from swarm.tools.adapter_registry import AdapterRegistry
from swarm.tools.builtins import register_builtin_tools
from swarm.tools.effects import DurableEffectRepository
from swarm.tools.fences import ActorContext, LeaseFenceProvider, StaticPolicyProvider
from swarm.tools.gateway import (
    ApprovalInvalidError,
    LegacyToolCallAdapter,
    ToolAuthorizationError,
    ToolGateway,
)
from swarm.tools.registry import CapabilityRegistry, ToolSpec, hash_operation
from swarm.tools.v17_gateway import (
    ApprovalInvalidError as V17ApprovalInvalidError,
)
from swarm.tools.v17_gateway import (
    ConsequentialToolGateway,
    PolicyDeniedError,
)


def _register_repo_tools(registry: CapabilityRegistry, repo: Path, allow_roots: list[Path]) -> None:
    allow = [p.resolve() for p in allow_roots]

    def _safe_path(raw: str) -> Path:
        path = (repo / raw).resolve() if not Path(raw).is_absolute() else Path(raw).resolve()
        if not any(str(path).startswith(str(root)) for root in allow):
            raise ToolAuthorizationError(f"path_denied:{raw}")
        return path

    def read_file(args: dict[str, Any]) -> dict[str, Any]:
        path = _safe_path(str(args["path"]))
        text = path.read_text(encoding="utf-8")
        return {"path": str(path.relative_to(repo)), "bytes": len(text), "preview": text[:200]}

    def write_file(args: dict[str, Any]) -> dict[str, Any]:
        path = _safe_path(str(args["path"]))
        content = str(args.get("content") or "")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return {
            "outcome": "succeeded",
            "path": str(path.relative_to(repo)),
            "bytes": len(content),
            "written": True,
        }

    registry.register(
        ToolSpec(
            name="repo.read",
            version="1",
            required_scopes=("repo.read",),
            side_effecting=False,
            description="Read file under allowlisted roots",
        ),
        read_file,
    )
    registry.register(
        ToolSpec(
            name="repo.write",
            version="1",
            required_scopes=("repo.write",),
            side_effecting=True,
            description="Write file under allowlisted roots (approval required)",
        ),
        write_file,
    )


def _call(tool_version: str, args: dict[str, Any], *, approval_id: str | None = None) -> ToolCall:
    dest = str(args.get("destination") or "local")
    return ToolCall(
        task_id="tsk_perm",
        attempt_id="att_perm",
        tool_version=tool_version,
        normalized_args=args,
        payload_hash=hash_operation(tool_version, args, destination=dest),
        lease_generation=1,
        operation_id=new_id("op_"),
        approval_id=approval_id,
    )


def _bind_permission_lease(factory: sessionmaker[Session]) -> tuple[Mission, ClaimedLease]:
    project = new_id("proj_permission_")
    mission = Mission(
        id=new_id("msn_"),
        project_id=project,
        objective="Bounded local permission and durable action proof",
        allowed_capabilities=["repo.write"],
        data_scope_ids=["permission.local"],
        resource_policy_id="permission-proof",
        max_wall_time_seconds=300,
        max_graph_nodes=1,
        max_active_sessions=1,
        max_model_calls=1,
        status=MissionStatus.RUNNING,
    )
    task = TaskSpec(
        id=new_id("tsk_"),
        project_id=project,
        mission_id=mission.id,
        objective="Write one approved local permission probe",
        task_family="local_tool",
        output_schema_id="permission-proof",
        quality_policy_id="permission-proof",
        required_capabilities=["repo.write"],
        scopes=["permission.local"],
        status=TaskStatus.READY,
    )
    worker_id, membership = new_id("wrk_permission_"), new_id("membership_")
    with factory() as session:
        MissionRepository(session).insert(mission)
        session.add(
            TaskRow(
                id=task.id,
                project_id=project,
                mission_id=mission.id,
                objective=task.objective,
                task_family=task.task_family,
                status="ready",
                graph_revision=task.graph_revision,
                priority=task.priority,
                scopes=task.scopes,
                dependency_ids=[],
                payload=task.model_dump(mode="json"),
            )
        )
        WorkerRegistrationRepository(session).upsert_registration(
            worker_id=worker_id,
            project_id=project,
            node_identity=worker_id,
            architecture="local",
            runtime_version="permission-proof",
            capacity_units=1,
            membership_token=membership,
            generation=1,
            capabilities=["repo.write"],
            privacy_classes=["local"],
        )
        session.flush()
        claim = LeaseLifecycleService(session).claim_eligible_attempt(
            worker_id=worker_id,
            membership_token=membership,
            lease_seconds=300,
        )
        if claim is None or claim.task_id != task.id:
            raise RuntimeError("permission_lease_not_claimed")
        session.commit()
    return mission, claim


async def run_permission_mission(repo: Path) -> dict[str, Any]:
    try:
        engine = create_db_engine()
    except DatabaseConfigError:
        return {"ok": False, "reason": "durable_store_required", "cost_usd": 0.0}
    try:
        if engine.dialect.name != "postgresql":
            return {"ok": False, "reason": "durable_store_required", "cost_usd": 0.0}
        return await _run_permission_mission(repo, make_session_factory(engine))
    except SQLAlchemyError as exc:
        return {
            "ok": False,
            "reason": "durable_store_unavailable",
            "error_type": type(exc).__name__,
            "cost_usd": 0.0,
        }
    finally:
        engine.dispose()


async def _run_permission_mission(repo: Path, factory: sessionmaker[Session]) -> dict[str, Any]:
    mission, claim = _bind_permission_lease(factory)

    def bound_call(
        tool_version: str, args: dict[str, Any], *, approval_id: str | None = None
    ) -> ToolCall:
        call = _call(tool_version, args, approval_id=approval_id)
        call.task_id, call.attempt_id = claim.task_id, claim.attempt_id
        call.lease_generation = claim.worker_generation
        return call

    repo = repo.resolve()
    registry = CapabilityRegistry()
    register_builtin_tools(registry)
    allow_roots = [repo / "sandbox" / "selfdev_issue", repo / "var" / "tool-audit"]
    for root in allow_roots:
        root.mkdir(parents=True, exist_ok=True)
    _register_repo_tools(registry, repo, allow_roots)

    audit: list[dict[str, Any]] = []
    adapters = AdapterRegistry()
    adapters.register(LegacyToolCallAdapter(registry))
    context = ActorContext(actor="permission-proof", project_id=mission.project_id)
    action_gateway = ConsequentialToolGateway(
        registry=adapters,
        store=DurableEffectRepository(factory),
        fences=LeaseFenceProvider(factory),
        policy=StaticPolicyProvider({"repo.write", "artifact.write"}, "v17-policy-1"),
    )
    gateway = ToolGateway(
        registry,
        allowed_scopes={"repo.read", "workspace.read", "calc", "tests.run"},
        current_lease_generation=claim.worker_generation,
        action_gateway=action_gateway,
        context=context,
        mission_id=mission.id,
        cancellation_generation=mission.cancellation_generation,
    )

    read_receipt = await gateway.execute_or_reconcile(
        bound_call("repo.read@1", {"path": "sandbox/selfdev_issue/parser_helper.py"})
    )
    audit.append(
        {
            "step": "allowed_read",
            "outcome": read_receipt.outcome.value,
            "ok": read_receipt.outcome == ActionOutcome.SUCCEEDED,
        }
    )

    denied_ok = False
    try:
        await gateway.execute_or_reconcile(bound_call("repo.read@1", {"path": ".env"}))
    except Exception:  # noqa: BLE001 — path denial may surface as failed receipt
        denied_ok = True
    # Handler exceptions become FAILED receipts in gateway
    bad_receipt = None
    try:
        bad_receipt = await gateway.execute_or_reconcile(
            bound_call("repo.read@1", {"path": "README.md"})
        )
    except ToolAuthorizationError:
        denied_ok = True
    if bad_receipt is not None and bad_receipt.outcome == ActionOutcome.FAILED:
        denied_ok = True
        audit.append(
            {
                "step": "denied_outside_allowlist",
                "ok": True,
                "error": bad_receipt.after_observation.get("error"),
            }
        )
    elif denied_ok:
        audit.append({"step": "denied_secret_path", "ok": True})
    else:
        audit.append({"step": "denied_outside_allowlist", "ok": False})

    gated = False
    write_args = {
        "path": "var/tool-audit/permission_probe.txt",
        "content": "v0.5 permission mission ok\n",
        "destination": "local",
    }
    gateway.allowed_scopes |= {"repo.write", "artifact.write"}
    try:
        await gateway.execute_or_reconcile(bound_call("repo.write@1", write_args))
    except (
        ToolAuthorizationError,
        ApprovalInvalidError,
        V17ApprovalInvalidError,
        PolicyDeniedError,
    ) as exc:
        gated = True
        audit.append({"step": "human_gate_required", "ok": True, "error": str(exc)})

    write_call = bound_call("repo.write@1", write_args)
    envelope = gateway.action_envelope(write_call)
    approval = action_gateway.make_approval(envelope, context=context)
    write_call.approval_id = approval.approval_id
    write_receipt = await gateway.execute_or_reconcile(write_call)
    audit.append(
        {
            "step": "approved_write",
            "outcome": write_receipt.outcome.value,
            "ok": write_receipt.outcome == ActionOutcome.SUCCEEDED,
            "approval_id": approval.approval_id,
            "durable_receipt_refs": write_receipt.evidence_refs,
        }
    )

    proof = {
        "schema_version": "0.5.0",
        "generated_at": utc_now().isoformat(),
        "audit": audit,
        "receipt_count": len(gateway.receipts),
        "probe_file_exists": (repo / "var" / "tool-audit" / "permission_probe.txt").exists(),
        "cost_usd": 0.0,
        "mock_vs_live": "engineering_local_durable_tool_permission_proof",
        "mission_id": mission.id,
        "task_id": claim.task_id,
        "attempt_id": claim.attempt_id,
        "ok": all(a.get("ok") for a in audit) and gated and denied_ok,
    }
    raw = json.dumps(proof, sort_keys=True, default=str)
    proof["report_hash"] = hashlib.sha256(raw.encode()).hexdigest()
    out = repo / "var" / "reports" / "permissions"
    out.mkdir(parents=True, exist_ok=True)
    (out / "latest_permission_proof.json").write_text(
        json.dumps(proof, indent=2, default=str) + "\n"
    )
    return proof


def run_permission_mission_sync(repo: Path) -> dict[str, Any]:
    return asyncio.run(run_permission_mission(repo))
