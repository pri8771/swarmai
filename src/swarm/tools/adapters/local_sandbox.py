"""Local/sandbox adapter — filesystem-bounded, no network."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from swarm.contracts.actions import ActionEnvelope, ActionReceiptV17, AdapterManifest
from swarm.contracts.common import utc_now


class LocalSandboxAdapter:
    def __init__(self, manifest: AdapterManifest, *, root: Path | None = None) -> None:
        if manifest.adapter_class != "local_sandbox":
            raise ValueError("adapter_class_mismatch")
        self.manifest = AdapterManifest.model_validate(manifest.model_dump())
        self.root = (root or Path("/tmp/swarm-sandbox")).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def normalize(self, request: dict[str, Any]) -> ActionEnvelope:
        dest = str(request.get("destination") or f"file://{self.root / 'out.txt'}")
        operation = str(request.get("operation", "write_text"))
        declaration = self.manifest.operations[operation]
        env = ActionEnvelope(
            project_id=str(request["project_id"]),
            actor=str(request.get("actor", "worker")),
            integration_id=self.manifest.integration_id,
            integration_version=self.manifest.integration_version,
            operation=operation,
            destination=dest,
            normalized_payload={
                "text": str(request.get("text", "")),
                "path": str(request.get("path", "out.txt")),
            },
            requested_scopes=list(declaration.scopes),
            side_effect_class=declaration.side_effect_class,
            risk_class=declaration.risk_class,
            lease_generation=request.get("lease_generation"),
            cancellation_generation=request.get("cancellation_generation"),
            policy_version=str(request.get("policy_version", "v17-policy-1")),
            mission_id=request.get("mission_id"),
            task_id=request.get("task_id"),
            attempt_id=request.get("attempt_id"),
            approval_id=request.get("approval_id"),
        )
        return env.ensure_hashes()

    def validate(self, envelope: ActionEnvelope) -> None:
        if envelope.integration_id != self.manifest.integration_id:
            raise ValueError("integration_mismatch")
        path = Path(str(envelope.normalized_payload.get("path", "out.txt")))
        if path.is_absolute() or ".." in path.parts:
            raise PermissionError("filesystem_path_escape_denied")

    def observe_pre_state(self, envelope: ActionEnvelope) -> dict[str, Any]:
        path = self.root / str(envelope.normalized_payload.get("path", "out.txt"))
        return {"exists": path.exists(), "path": str(path), "observed_at": utc_now().isoformat()}

    def execute(self, envelope: ActionEnvelope) -> dict[str, Any]:
        path = self.root / str(envelope.normalized_payload.get("path", "out.txt"))
        path.parent.mkdir(parents=True, exist_ok=True)
        text = str(envelope.normalized_payload.get("text", ""))
        path.write_text(text, encoding="utf-8")
        return {
            "outcome": "succeeded",
            "written": True,
            "bytes": len(text.encode("utf-8")),
            "path": str(path),
        }

    def observe_post_state(
        self, envelope: ActionEnvelope, execution_result: dict[str, Any]
    ) -> dict[str, Any]:
        path = Path(str(execution_result.get("path") or self.root / "out.txt"))
        return {
            "exists": path.exists(),
            "size": path.stat().st_size if path.exists() else 0,
            "result": execution_result,
        }

    def reconcile(
        self, envelope: ActionEnvelope, prior_receipts: list[ActionReceiptV17]
    ) -> dict[str, Any]:
        path = self.root / str(envelope.normalized_payload.get("path", "out.txt"))
        if path.exists():
            return {"state": "succeeded", "external_id": str(path)}
        return {"state": "failed", "reason": "file_missing"}
