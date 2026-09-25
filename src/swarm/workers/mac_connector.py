"""Mac connector — outbound worker client for Mac-local scoped tasks.

Runs on the Mac (or mac-connector container). Talks only to the SwarmAI server
HTTP API. Never hosts Postgres. Mac disconnect must not take the server down.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import httpx

DEFAULT_SERVER_URL = "http://127.0.0.1:18766"
MAC_CAPABILITIES = ("mac.local.extract", "extract", "chat", "code.read")
MAC_PRIVACY = ("mac_local", "local")


@dataclass(frozen=True)
class MacLocalWork:
    """Result of Mac-only local work (file must not live on the server)."""

    path: str
    email_count: int
    artifact_sha256: str
    emails: tuple[str, ...]
    placement: str = "mac_local"
    host_role: str = "mac_connector"
    runtime: str = "mac_connector_native"
    spend_usd: float = 0.0

    def required_checks(self) -> dict[str, Any]:
        return {
            "email_count": self.email_count,
            "artifact_sha256": self.artifact_sha256,
            "placement": self.placement,
            "host_role": self.host_role,
            "runtime": self.runtime,
        }

    def produced(self, *, worker_id: str, run_id: str) -> dict[str, Any]:
        return {
            "checks": self.required_checks(),
            "worker_id": worker_id,
            "mac_local_path": self.path,
            "emails": list(self.emails),
            "fixture_run_id": run_id,
            "spend_usd": self.spend_usd,
        }


def load_bearer_token(*, root: Path | None = None) -> str:
    """Resolve connector auth token without printing secrets."""
    env_token = (os.environ.get("SWARM_API_AUTH_TOKEN") or "").strip()
    if env_token:
        return env_token
    env_token = (os.environ.get("SWARM_SEED_LOOPBACK_TOKEN") or "").strip()
    if env_token:
        return env_token
    base = root or Path.cwd()
    for rel in (
        "deploy/env/mac-connector.env",
        "deploy/env/server.env",
    ):
        path = base / rel
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("SWARM_API_AUTH_TOKEN=") or line.startswith(
                "SWARM_SEED_LOOPBACK_TOKEN="
            ):
                token = line.split("=", 1)[1].strip()
                if token and "replace-with" not in token:
                    return token
    raise RuntimeError("connector_auth_token_missing")


def perform_mac_local_extract(path: Path) -> MacLocalWork:
    """Read a Mac-local fixture and produce protected checks. No model calls."""
    payload = path.read_text(encoding="utf-8")
    emails = tuple(
        sorted(set(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", payload)))
    )
    digest = hashlib.sha256(
        (path.resolve().as_posix() + "\n" + "|".join(emails) + "\n" + payload).encode("utf-8")
    ).hexdigest()
    return MacLocalWork(
        path=str(path.resolve()),
        email_count=len(emails),
        artifact_sha256=digest,
        emails=emails,
    )


def write_mac_local_fixture(directory: Path, *, run_id: str) -> Path:
    """Create a fixture that exists on the Mac connector host only."""
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"th03-mac-local-{run_id}.txt"
    path.write_text(
        "TH-03 Mac-local fixture for swarm.splitsignal.ai connector.\n"
        "Contact mac-agent@splitsignal.ai and ops@example.com.\n"
        f"run_id={run_id}\n"
        "placement=mac_local\n",
        encoding="utf-8",
    )
    return path


class MacConnectorClient:
    """Outbound authenticated connector to the SwarmAI server."""

    def __init__(
        self,
        *,
        server_url: str,
        bearer_token: str,
        timeout: float = 30.0,
    ) -> None:
        self.server_url = server_url.rstrip("/")
        self._headers = {
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        self._client = httpx.Client(
            base_url=self.server_url, headers=self._headers, timeout=timeout
        )
        self.worker_id: str | None = None
        self.generation: int | None = None
        self.membership_token: str | None = None
        self.project_id: str | None = None

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> MacConnectorClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def health_ready(self) -> dict[str, Any]:
        response = self._client.get("/health/ready")
        response.raise_for_status()
        body = response.json()
        if body.get("database") != "up":
            raise RuntimeError(f"server_database_not_up:{body.get('database')}")
        return cast(dict[str, Any], body)

    def ensure_project(self, *, run_id: str) -> str:
        response = self._client.post(
            "/v1/projects",
            headers={**self._headers, "Idempotency-Key": f"th03-proj-{run_id}"},
            json={
                "name": "TH-03 Mac connector",
                "repo_path": "/app",
                "allowed_tools": ["mac.local.extract", "extract"],
                "provider_policy": {"allow_paid": False, "prefer_local": True},
                "budgets": {"max_cost_usd": 0.0, "max_requests": 20},
                "safety": {
                    "require_approval_for_writes": True,
                    "mac_local_only_tools": ["mac.local.extract"],
                },
            },
        )
        if response.status_code >= 400:
            raise RuntimeError(f"create_project:{response.status_code}:{response.text}")
        project_id = response.json()["project"]["project_id"]
        self.project_id = project_id
        return cast(str, project_id)

    def enroll(self, *, project_id: str, run_id: str) -> dict[str, Any]:
        response = self._client.post(
            "/v1/workers/enroll",
            headers={**self._headers, "Idempotency-Key": f"th03-wrk-{run_id}"},
            json={
                "project_id": project_id,
                "capabilities": list(MAC_CAPABILITIES),
                "capacity_units": 1.0,
                "privacy_classes": list(MAC_PRIVACY),
            },
        )
        if response.status_code >= 400:
            raise RuntimeError(f"enroll:{response.status_code}:{response.text}")
        body = response.json()
        worker = body["worker"]
        self.worker_id = worker.get("worker_id") or worker.get("id")
        self.generation = int(worker.get("lease_generation") or worker.get("generation") or 1)
        self.membership_token = body["membership_token"]
        self.project_id = project_id
        return cast(dict[str, Any], body)

    def heartbeat(self) -> dict[str, Any]:
        if not self.worker_id or self.generation is None or not self.membership_token:
            raise RuntimeError("connector_not_enrolled")
        response = self._client.post(
            "/v1/workers/heartbeat",
            json={
                "worker_id": self.worker_id,
                "generation": self.generation,
                "token": self.membership_token,
            },
        )
        if response.status_code >= 400:
            raise RuntimeError(f"heartbeat:{response.status_code}:{response.text}")
        return cast(dict[str, Any], response.json())

    def claim(self, *, agent_profile_id: str = "ap_default") -> dict[str, Any]:
        if not self.worker_id or self.generation is None or not self.membership_token:
            raise RuntimeError("connector_not_enrolled")
        response = self._client.post(
            "/v1/workers/claim",
            json={
                "worker_id": self.worker_id,
                "generation": self.generation,
                "token": self.membership_token,
                "agent_profile_id": agent_profile_id,
            },
        )
        if response.status_code >= 400:
            raise RuntimeError(f"claim:{response.status_code}:{response.text}")
        return cast(dict[str, Any], response.json())

    def renew(
        self,
        *,
        lease_id: str,
        progress_class: str = "running",
        extend_seconds: int | None = None,
    ) -> dict[str, Any]:
        if not self.worker_id or self.generation is None or not self.membership_token:
            raise RuntimeError("connector_not_enrolled")
        payload: dict[str, Any] = {
            "lease_id": lease_id,
            "worker_id": self.worker_id,
            "generation": self.generation,
            "token": self.membership_token,
            "progress_class": progress_class,
        }
        if extend_seconds is not None:
            payload["extend_seconds"] = extend_seconds
        response = self._client.post("/v1/workers/renew", json=payload)
        if response.status_code >= 400:
            raise RuntimeError(f"renew:{response.status_code}:{response.text}")
        return cast(dict[str, Any], response.json())

    def submit_result(
        self,
        *,
        lease_id: str,
        status: str,
        checks: dict[str, Any] | None = None,
        artifact_manifest: dict[str, Any] | None = None,
        usage: dict[str, Any] | None = None,
        summary: str | None = None,
        result_id: str | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Submit evidence only — never self-accepts."""
        if not self.worker_id or self.generation is None or not self.membership_token:
            raise RuntimeError("connector_not_enrolled")
        headers = dict(self._headers)
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        response = self._client.post(
            "/v1/workers/submit-result",
            headers=headers,
            json={
                "lease_id": lease_id,
                "worker_id": self.worker_id,
                "generation": self.generation,
                "token": self.membership_token,
                "status": status,
                "checks": dict(checks or {}),
                "artifact_manifest": dict(artifact_manifest or {}),
                "usage": dict(usage or {}),
                "summary": summary,
                "result_id": result_id,
            },
        )
        if response.status_code >= 400:
            raise RuntimeError(f"submit_result:{response.status_code}:{response.text}")
        body = cast(dict[str, Any], response.json())
        if body.get("self_accepted") is True or body.get("acceptance_state") == "accepted":
            raise RuntimeError("connector_must_not_self_accept")
        return body

    def reconnect(self) -> dict[str, Any]:
        if not self.worker_id or self.generation is None or not self.membership_token:
            raise RuntimeError("connector_not_enrolled")
        response = self._client.post(
            "/v1/workers/reconnect",
            json={
                "worker_id": self.worker_id,
                "generation": self.generation,
                "token": self.membership_token,
            },
        )
        if response.status_code >= 400:
            raise RuntimeError(f"reconnect:{response.status_code}:{response.text}")
        return cast(dict[str, Any], response.json())

    def reconcile(self) -> dict[str, Any]:
        """Recover ownership from server after disconnect — drop cancelled leases."""
        recon = self.reconnect()
        active = []
        cancelled = list(recon.get("cancel_notices") or [])
        for row in recon.get("active_leases") or []:
            lease_id = str(row.get("lease_id") or "")
            if not lease_id:
                continue
            if lease_id in cancelled or row.get("cancel_requested") or row.get("state") == "cancelled":
                cancelled.append(lease_id)
                continue
            active.append(row)
        return {
            "worker_id": recon.get("worker_id"),
            "generation": recon.get("generation"),
            "status": recon.get("status"),
            "active_leases": active,
            "cancelled_leases": sorted(set(cancelled)),
            "reconciled": True,
        }

    def enqueue_task(self, task: dict[str, Any], *, idempotency_key: str | None = None) -> dict[str, Any]:
        headers = dict(self._headers)
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        response = self._client.post(
            "/v1/workers/enqueue",
            headers=headers,
            json={"task": task},
        )
        if response.status_code >= 400:
            raise RuntimeError(f"enqueue:{response.status_code}:{response.text}")
        return cast(dict[str, Any], response.json())

    def create_mac_scoped_mission(
        self,
        *,
        project_id: str,
        run_id: str,
        required_checks: dict[str, Any],
    ) -> dict[str, Any]:
        response = self._client.post(
            "/v1/missions",
            headers={**self._headers, "Idempotency-Key": f"th03-msn-{run_id}"},
            json={
                "mission": {
                    "project_id": project_id,
                    "objective": "TH-03 Mac connector scoped mac_local extract",
                    "acceptance_criteria": [
                        "mac connector enrolled outbound",
                        "work uses Mac-local fixture only",
                        "server accepts via authoritative review",
                    ],
                    "allowed_capabilities": list(MAC_CAPABILITIES),
                    "data_scope_ids": ["scope_mac_local", "local_only", "mac_local"],
                    "resource_policy_id": "policy_mac_local",
                    "max_wall_time_seconds": 600,
                    "max_graph_nodes": 20,
                    "max_active_sessions": 2,
                    "max_model_calls": 5,
                },
                "task_family": "extract",
                "required_checks": required_checks,
            },
        )
        if response.status_code >= 400:
            raise RuntimeError(f"create_mission:{response.status_code}:{response.text}")
        return cast(dict[str, Any], response.json())

    def review(
        self,
        *,
        mission_id: str,
        run_id: str,
        produced: dict[str, Any],
        idempotency_suffix: str,
    ) -> dict[str, Any]:
        response = self._client.post(
            f"/v1/missions/{mission_id}/review",
            headers={
                **self._headers,
                "Idempotency-Key": f"th03-{idempotency_suffix}-{run_id}",
            },
            json={"produced": produced},
        )
        if response.status_code >= 400:
            raise RuntimeError(f"review:{response.status_code}:{response.text}")
        return cast(dict[str, Any], response.json())

    def get_mission(self, mission_id: str) -> dict[str, Any]:
        response = self._client.get(f"/v1/missions/{mission_id}")
        response.raise_for_status()
        return cast(dict[str, Any], response.json())

    def list_workers(self, project_id: str) -> dict[str, Any]:
        response = self._client.get("/v1/workers", params={"project_id": project_id})
        response.raise_for_status()
        return cast(dict[str, Any], response.json())


def dump_evidence(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
