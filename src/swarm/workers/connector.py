"""Generic worker connector entry — reuses P1 continuous connector semantics.

P1 owns ``continuous_connector`` (modes, permitted runtimes, no echo-success).
This module exposes a portable ``ContinuousWorkerConnector`` alias and a
``python -m swarm.workers.connector`` entrypoint for the generic worker compose
profile (bounded workspace, no whole-repo mount).
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from swarm.workers.continuous_connector import (
    ConnectorMode,
    ContinuousMacConnector,
    PermittedRuntime,
    RuntimeExecutorRegistry,
    default_mac_executor,
    default_operational_registry,
    execute_assigned_work,
    fixture_demo_executor,
    resolve_connector_mode,
)
from swarm.workers.continuous_connector import (
    run_from_env as continuous_run_from_env,
)

# Alias: portable name for the same P1 connector implementation.
ContinuousWorkerConnector = ContinuousMacConnector


def unsupported_result(
    task: dict[str, Any], *, reason: str = "no_registered_executor"
) -> dict[str, Any]:
    return {
        "status": "unsupported",
        "checks": {
            "unsupported": True,
            "blocked": True,
            "reason": reason,
            "task_id": task.get("id"),
        },
        "artifact_manifest": {"kind": "unsupported", "task_id": task.get("id")},
        "usage": {"spend_usd": 0.0, "model_calls": 0},
        "summary": f"unsupported:{reason}",
    }


def default_worker_executor(claim: dict[str, Any], workspace_dir: Path) -> dict[str, Any]:
    """Operational default — delegates to P1 execute_assigned_work (no echo)."""
    return execute_assigned_work(
        claim,
        workspace_dir,
        mode="operational",
        registry=default_operational_registry(),
    )


def run_from_env(*, max_iterations: int | None = None) -> dict[str, Any]:
    """Worker-profile entry: bounded workspace + operational mode."""
    os.environ.setdefault("SWARM_CONNECTOR_MODE", "operational")
    os.environ.setdefault("SWARM_PROCESS_ROLE", "worker")
    return continuous_run_from_env(max_iterations=max_iterations)


def main() -> int:
    from swarm.product.portable_config import PublicEndpointConfig
    from swarm.workers.mac_connector import DEFAULT_SERVER_URL, load_bearer_token

    server = (os.environ.get("SWARM_SERVER_URL") or DEFAULT_SERVER_URL).rstrip("/")
    root = Path(os.environ.get("SWARM_REPO_ROOT") or Path.cwd())
    workspace = Path(
        os.environ.get("SWARM_WORKER_WORKSPACE")
        or (root / "var" / "worker" / "workspaces")
    )
    workspace.mkdir(parents=True, exist_ok=True)
    stop_after = os.environ.get("SWARM_CONNECTOR_MAX_ITERATIONS")
    max_iterations = int(stop_after) if stop_after else None
    public_hostname = (os.environ.get("SWARM_PUBLIC_HOSTNAME") or "").strip() or None
    endpoint = None
    if public_hostname:
        try:
            endpoint = PublicEndpointConfig(
                public_hostname=public_hostname,
                api_base_url=server,
            )
        except Exception:
            endpoint = None
    connector = ContinuousWorkerConnector(
        server_url=server,
        bearer_token=load_bearer_token(root=root),
        project_id=(os.environ.get("SWARM_PROJECT_ID") or "").strip() or None,
        poll_interval_seconds=float(os.environ.get("SWARM_CONNECTOR_POLL") or "1.0"),
        fixture_dir=workspace,
        evidence_dir=root / "docs" / "evidence" / "v2" / "worker-connector",
        mode=resolve_connector_mode(),
        public_hostname=public_hostname,
        endpoint=endpoint,
        max_iterations=max_iterations,
    )
    evidence = connector.run()
    print(
        json.dumps(
            {
                "ok": True,
                "submitted": evidence.get("submitted"),
                "path": evidence.get("evidence_path"),
                "mode": evidence.get("connector_mode"),
            }
        )
    )
    return 0


__all__ = [
    "ContinuousWorkerConnector",
    "ContinuousMacConnector",
    "ConnectorMode",
    "PermittedRuntime",
    "RuntimeExecutorRegistry",
    "default_mac_executor",
    "default_operational_registry",
    "default_worker_executor",
    "execute_assigned_work",
    "fixture_demo_executor",
    "resolve_connector_mode",
    "run_from_env",
    "unsupported_result",
]


if __name__ == "__main__":
    raise SystemExit(main())
