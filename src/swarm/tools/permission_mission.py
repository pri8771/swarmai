"""V0.5 — permissioned tool mission proof (allow / deny / human-gated)."""

from __future__ import annotations

import asyncio
import hashlib
import json
from pathlib import Path
from typing import Any

from swarm.contracts.common import new_id, utc_now
from swarm.contracts.enums import ActionOutcome
from swarm.contracts.workspace import ToolCall
from swarm.tools.builtins import register_builtin_tools
from swarm.tools.gateway import (
    ApprovalInvalidError,
    ToolAuthorizationError,
    ToolGateway,
    make_approval,
)
from swarm.tools.registry import CapabilityRegistry, ToolSpec, hash_operation


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
        return {"path": str(path.relative_to(repo)), "bytes": len(content), "written": True}

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


async def run_permission_mission(repo: Path) -> dict[str, Any]:
    repo = repo.resolve()
    registry = CapabilityRegistry()
    register_builtin_tools(registry)
    allow_roots = [repo / "sandbox" / "selfdev_issue", repo / "var" / "tool-audit"]
    for root in allow_roots:
        root.mkdir(parents=True, exist_ok=True)
    _register_repo_tools(registry, repo, allow_roots)

    audit: list[dict[str, Any]] = []
    gateway = ToolGateway(
        registry,
        allowed_scopes={"repo.read", "workspace.read", "calc", "tests.run"},
        current_lease_generation=1,
    )

    read_receipt = await gateway.execute_or_reconcile(
        _call("repo.read@1", {"path": "sandbox/selfdev_issue/parser_helper.py"})
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
        await gateway.execute_or_reconcile(_call("repo.read@1", {"path": ".env"}))
    except Exception:  # noqa: BLE001 — path denial may surface as failed receipt
        denied_ok = True
    # Handler exceptions become FAILED receipts in gateway
    bad_receipt = None
    try:
        bad_receipt = await gateway.execute_or_reconcile(
            _call("repo.read@1", {"path": "README.md"})
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
    try:
        await gateway.execute_or_reconcile(_call("repo.write@1", write_args))
    except (ToolAuthorizationError, ApprovalInvalidError) as exc:
        gated = True
        audit.append({"step": "human_gate_required", "ok": True, "error": str(exc)})

    gateway.allowed_scopes = set(gateway.allowed_scopes) | {"repo.write", "artifact.write"}
    approval = make_approval(tool_version="repo.write@1", args=write_args, destination="local")
    gateway.approvals[approval.id] = approval
    write_receipt = await gateway.execute_or_reconcile(
        _call("repo.write@1", write_args, approval_id=approval.id)
    )
    audit.append(
        {
            "step": "approved_write",
            "outcome": write_receipt.outcome.value,
            "ok": write_receipt.outcome == ActionOutcome.SUCCEEDED,
            "approval_id": approval.id,
        }
    )

    proof = {
        "schema_version": "0.5.0",
        "generated_at": utc_now().isoformat(),
        "audit": audit,
        "receipt_count": len(gateway.receipts),
        "probe_file_exists": (repo / "var" / "tool-audit" / "permission_probe.txt").exists(),
        "cost_usd": 0.0,
        "mock_vs_live": "live_local_tool_permission_proof",
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
