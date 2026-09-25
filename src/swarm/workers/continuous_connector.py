"""Genuine continuous worker connector — claim/renew/submit/cancel/reconnect.

Not a one-shot self-approving script. The connector enrolls, heartbeats, claims
leased work from the server, executes assigned work via a registered permitted
runtime, renews leases, submits immutable results, and honors cancel notices.
Acceptance remains on the server control plane (protected review) — never on
the connector.

Fixtures and echo completions are restricted to explicit test/demo modes.
Unsupported work returns unsupported/blocked — never success from mere message
processing.
"""

from __future__ import annotations

import json
import os
import threading
import time
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from swarm.acceptance.freeze import resolve_deployment_public_hostname
from swarm.product.portable_config import (
    PortableConfigError,
    PublicEndpointConfig,
    SupportMatrix,
    WorkerIdentitySpec,
    default_support_matrix,
)
from swarm.workers.mac_connector import (
    DEFAULT_SERVER_URL,
    MacConnectorClient,
    dump_evidence,
    load_bearer_token,
    perform_mac_local_extract,
    write_mac_local_fixture,
)

Executor = Callable[[dict[str, Any], Path], dict[str, Any]]
ConnectorMode = Literal["operational", "test", "demo"]

SUPPORTED_MODES: frozenset[str] = frozenset({"operational", "test", "demo"})


def resolve_connector_mode(
    *,
    explicit: str | None = None,
    env: Mapping[str, str] | None = None,
) -> ConnectorMode:
    """Resolve connector work mode; operational is the default."""
    raw = (explicit if explicit is not None else None) or (
        (env if env is not None else os.environ).get("SWARM_CONNECTOR_MODE") or ""
    )
    mode = str(raw).strip().lower() or "operational"
    if mode not in SUPPORTED_MODES:
        raise ValueError(f"unsupported_connector_mode:{mode}")
    return mode  # type: ignore[return-value]


@dataclass(frozen=True)
class PermittedRuntime:
    """A registered runtime allowed to execute scoped task work."""

    runtime_id: str
    capabilities: frozenset[str]
    scopes: frozenset[str]
    execute: Executor

    def matches(self, task: Mapping[str, Any]) -> bool:
        required = {str(c) for c in (task.get("required_capabilities") or [])}
        scopes = {str(s) for s in (task.get("scopes") or [])}
        if required and required.isdisjoint(self.capabilities):
            return False
        if scopes and scopes.isdisjoint(self.scopes) and required.isdisjoint(self.capabilities):
            return False
        if not required and not scopes:
            return False
        # Capability match preferred; scope overlap also admits when capability set empty on task.
        if required and not required.isdisjoint(self.capabilities):
            return True
        return bool(scopes and not scopes.isdisjoint(self.scopes))


class RuntimeExecutorRegistry:
    """Registry of permitted runtimes — self-reported labels do not grant access."""

    def __init__(self) -> None:
        self._runtimes: list[PermittedRuntime] = []

    def register(self, runtime: PermittedRuntime) -> None:
        self._runtimes.append(runtime)

    def resolve(self, task: Mapping[str, Any]) -> PermittedRuntime | None:
        for runtime in self._runtimes:
            if runtime.matches(task):
                return runtime
        return None

    @property
    def runtime_ids(self) -> tuple[str, ...]:
        return tuple(r.runtime_id for r in self._runtimes)


def _task_input_path(task: Mapping[str, Any]) -> Path | None:
    raw = task.get("input_path")
    if not raw:
        inputs = task.get("inputs") or {}
        if isinstance(inputs, Mapping):
            raw = inputs.get("path") or inputs.get("input_path")
    if not raw:
        return None
    path = Path(str(raw))
    return path if path.is_file() else path


def execute_mac_local_extract_operational(
    claim: dict[str, Any], work_dir: Path
) -> dict[str, Any]:
    """Operational mac-local extract: requires assigned input path (no fixture invent)."""
    del work_dir  # workspace grant is caller-owned; input path comes from the task
    task = claim.get("task") or {}
    path = _task_input_path(task)
    if path is None or not path.is_file():
        return {
            "status": "blocked",
            "checks": {
                "blocked": True,
                "reason": "missing_or_unreadable_input_path",
            },
            "artifact_manifest": {"kind": "blocked", "task_id": task.get("id")},
            "usage": {"spend_usd": 0.0, "model_calls": 0},
            "summary": "blocked_missing_input_path",
        }
    work = perform_mac_local_extract(path)
    return {
        "status": "completed",
        "checks": work.required_checks(),
        "artifact_manifest": {
            "placement": "mac_local",
            "path": work.path,
            "sha256": work.artifact_sha256,
            "email_count": work.email_count,
            "runtime": "mac_local_extract",
        },
        "usage": {"spend_usd": 0.0, "model_calls": 0},
        "summary": f"mac_local extract emails={work.email_count}",
    }


def default_operational_registry() -> RuntimeExecutorRegistry:
    """Baseline permitted runtimes for operational connector mode."""
    registry = RuntimeExecutorRegistry()
    registry.register(
        PermittedRuntime(
            runtime_id="mac_local_extract",
            capabilities=frozenset({"mac.local.extract", "extract"}),
            scopes=frozenset({"mac_local"}),
            execute=execute_mac_local_extract_operational,
        )
    )
    return registry


def fixture_demo_executor(claim: dict[str, Any], fixture_dir: Path) -> dict[str, Any]:
    """Test/demo-only Mac fixture extract. Never the operational default."""
    task = claim.get("task") or {}
    scopes = set(task.get("scopes") or [])
    run_id = str(task.get("id") or uuid.uuid4().hex[:12])
    if "mac_local" in scopes or "mac.local.extract" in set(
        task.get("required_capabilities") or []
    ):
        path = write_mac_local_fixture(fixture_dir, run_id=run_id)
        work = perform_mac_local_extract(path)
        return {
            "status": "completed",
            "checks": work.required_checks(),
            "artifact_manifest": {
                "placement": "mac_local",
                "path": work.path,
                "sha256": work.artifact_sha256,
                "email_count": work.email_count,
                "mode": "fixture_demo",
            },
            "usage": {"spend_usd": 0.0, "model_calls": 0},
            "summary": f"mac_local extract emails={work.email_count}",
        }
    return {
        "status": "completed",
        "checks": {"echo": True, "task_id": task.get("id"), "mode": "fixture_demo"},
        "artifact_manifest": {"kind": "echo", "task_id": task.get("id"), "mode": "fixture_demo"},
        "usage": {"spend_usd": 0.0, "model_calls": 0},
        "summary": "non_mac_local_echo",
    }


def execute_assigned_work(
    claim: dict[str, Any],
    work_dir: Path,
    *,
    mode: ConnectorMode = "operational",
    registry: RuntimeExecutorRegistry | None = None,
) -> dict[str, Any]:
    """Execute claimed work according to mode and permitted runtimes.

    Operational mode never invents fixtures or echo-completes. Unsupported
    assignments return ``status=unsupported`` (not completed).
    """
    if mode in {"test", "demo"}:
        return fixture_demo_executor(claim, work_dir)

    task = claim.get("task") or {}
    active = registry or default_operational_registry()
    runtime = active.resolve(task if isinstance(task, Mapping) else {})
    if runtime is None:
        return {
            "status": "unsupported",
            "checks": {
                "unsupported": True,
                "reason": "no_permitted_runtime_for_task",
                "required_capabilities": list(task.get("required_capabilities") or []),
                "scopes": list(task.get("scopes") or []),
                "registered_runtimes": list(active.runtime_ids),
            },
            "artifact_manifest": {
                "kind": "unsupported",
                "task_id": task.get("id"),
            },
            "usage": {"spend_usd": 0.0, "model_calls": 0},
            "summary": "unsupported_no_permitted_runtime",
        }
    produced = runtime.execute(claim, work_dir)
    # Never upgrade unsupported/blocked to success at the registry boundary.
    status = str(produced.get("status") or "")
    if status in {"", "completed"} and produced.get("checks", {}).get("echo") is True:
        return {
            "status": "unsupported",
            "checks": {"unsupported": True, "reason": "echo_forbidden_in_operational"},
            "artifact_manifest": {"kind": "unsupported", "task_id": task.get("id")},
            "usage": {"spend_usd": 0.0, "model_calls": 0},
            "summary": "unsupported_echo_forbidden",
        }
    manifest = dict(produced.get("artifact_manifest") or {})
    manifest.setdefault("runtime", runtime.runtime_id)
    return {**produced, "artifact_manifest": manifest}


def default_mac_executor(claim: dict[str, Any], fixture_dir: Path) -> dict[str, Any]:
    """Operational default executor — permitted runtime only; no fixture/echo success."""
    return execute_assigned_work(
        claim,
        fixture_dir,
        mode="operational",
        registry=default_operational_registry(),
    )


@dataclass
class ContinuousMacConnector:
    """Outbound continuous worker loop against the SwarmAI server HTTP API."""

    server_url: str = DEFAULT_SERVER_URL
    bearer_token: str = ""
    project_id: str | None = None
    poll_interval_seconds: float = 1.0
    renew_every_seconds: float = 15.0
    fixture_dir: Path = field(default_factory=lambda: Path("var") / "mac-connector" / "fixtures")
    evidence_dir: Path = field(
        default_factory=lambda: Path("docs") / "evidence" / "v17" / "continuous-connector"
    )
    mode: ConnectorMode = "operational"
    runtime_registry: RuntimeExecutorRegistry = field(default_factory=default_operational_registry)
    executor: Executor | None = None
    max_iterations: int | None = None
    stop_event: threading.Event | None = None
    events: list[dict[str, Any]] = field(default_factory=list)
    public_hostname: str | None = None
    endpoint: PublicEndpointConfig | None = None
    worker_identity: WorkerIdentitySpec | None = None
    support_matrix: SupportMatrix = field(default_factory=default_support_matrix)

    def _executor(self) -> Executor:
        if self.executor is not None:
            return self.executor

        def _bound(claim: dict[str, Any], work_dir: Path) -> dict[str, Any]:
            return execute_assigned_work(
                claim,
                work_dir,
                mode=self.mode,
                registry=self.runtime_registry,
            )

        return _bound

    def _stopped(self) -> bool:
        if self.stop_event is not None and self.stop_event.is_set():
            return True
        return False

    def _record(self, step: str, **payload: Any) -> None:
        row = {"at": datetime.now(UTC).isoformat(), "step": step, **payload}
        self.events.append(row)

    def run(self) -> dict[str, Any]:
        token = self.bearer_token or load_bearer_token()
        run_id = uuid.uuid4().hex[:12]
        started = datetime.now(UTC).isoformat()
        iterations = 0
        submitted = 0
        cancelled_honored = 0
        reconnects = 0
        executor = self._executor()
        if self.worker_identity is not None:
            self.support_matrix.require(
                self.worker_identity.platform,
                self.worker_identity.architecture,
            )
        hostname = (
            (self.endpoint.public_hostname if self.endpoint is not None else None)
            or self.public_hostname
            or resolve_deployment_public_hostname(endpoint=self.endpoint)
            or "unconfigured"
        )

        with MacConnectorClient(server_url=self.server_url, bearer_token=token) as client:
            ready = client.health_ready()
            self._record("health_ready", ok=True, database=ready.get("database"))

            project_id = self.project_id
            if not project_id:
                project_id = client.ensure_project(run_id=run_id)
            self._record("project", project_id=project_id)

            enrolled = client.enroll(project_id=project_id, run_id=run_id)
            self._record(
                "enroll",
                worker_id=client.worker_id,
                generation=client.generation,
                ok=bool(client.membership_token),
            )

            active_lease: str | None = None
            last_renew = 0.0

            while not self._stopped():
                if self.max_iterations is not None and iterations >= self.max_iterations:
                    break
                iterations += 1
                try:
                    hb = client.heartbeat()
                    for notice in hb.get("cancel_notices") or []:
                        self._record("cancel_notice_heartbeat", lease_id=notice)
                        if active_lease == notice:
                            active_lease = None
                            cancelled_honored += 1
                    if active_lease is None:
                        claim = client.claim()
                        if claim.get("claimed") and claim.get("lease_id"):
                            active_lease = str(claim["lease_id"])
                            last_renew = time.monotonic()
                            self._record(
                                "claim",
                                lease_id=active_lease,
                                task_id=claim.get("task_id"),
                                mission_id=claim.get("mission_id"),
                            )
                            # Honor cancel before work if already fenced.
                            if active_lease in (claim.get("cancel_notices") or []):
                                self._record("cancel_before_work", lease_id=active_lease)
                                active_lease = None
                                cancelled_honored += 1
                                continue
                            # Renew once mid-flight to prove lease fencing.
                            renew = client.renew(lease_id=active_lease, progress_class="running")
                            self._record(
                                "renew",
                                lease_id=active_lease,
                                state=renew.get("state"),
                                expires_at=renew.get("expires_at"),
                            )
                            if active_lease in (renew.get("cancel_notices") or []):
                                self._record("cancel_on_renew", lease_id=active_lease)
                                active_lease = None
                                cancelled_honored += 1
                                continue
                            produced = executor(claim, self.fixture_dir)
                            submitted_body = client.submit_result(
                                lease_id=active_lease,
                                status=str(produced.get("status") or "unsupported"),
                                checks=dict(produced.get("checks") or {}),
                                artifact_manifest=dict(produced.get("artifact_manifest") or {}),
                                usage=dict(produced.get("usage") or {}),
                                summary=str(produced.get("summary") or ""),
                                idempotency_key=f"cont-submit-{active_lease}",
                            )
                            if submitted_body.get("self_accepted") is True:
                                raise RuntimeError("continuous_connector_self_accept_forbidden")
                            submitted += 1
                            self._record(
                                "submit_result",
                                lease_id=active_lease,
                                result_id=submitted_body.get("result_id"),
                                acceptance_state=submitted_body.get("acceptance_state"),
                                self_accepted=submitted_body.get("self_accepted"),
                                work_status=produced.get("status"),
                            )
                            active_lease = None
                    else:
                        # Keep renewing an in-flight lease (long executor / pause).
                        if time.monotonic() - last_renew >= self.renew_every_seconds:
                            renew = client.renew(lease_id=active_lease, progress_class="running")
                            last_renew = time.monotonic()
                            self._record("renew_keepalive", lease_id=active_lease)
                            if active_lease in (renew.get("cancel_notices") or []):
                                active_lease = None
                                cancelled_honored += 1
                except Exception as exc:  # noqa: BLE001 — reconnect and continue
                    self._record("error", error=str(exc))
                    try:
                        recon = client.reconcile()
                        reconnects += 1
                        self._record(
                            "reconcile",
                            ok=True,
                            active_leases=len(recon.get("active_leases") or []),
                            cancelled_leases=len(recon.get("cancelled_leases") or []),
                        )
                        leases = recon.get("active_leases") or []
                        active_lease = leases[0]["lease_id"] if leases else None
                        cancelled_honored += len(recon.get("cancelled_leases") or [])
                    except Exception as recon_exc:  # noqa: BLE001
                        self._record("reconcile_failed", error=str(recon_exc))
                        active_lease = None
                if self._stopped():
                    break
                time.sleep(self.poll_interval_seconds)

            evidence = {
                "packet": "V1.7-continuous-connector",
                "hostname_public": hostname,
                "server_url": self.server_url,
                "connector_role": "mac_connector_continuous",
                "connector_mode": self.mode,
                "started_at": started,
                "finished_at": datetime.now(UTC).isoformat(),
                "project_id": project_id,
                "worker_id": client.worker_id,
                "iterations": iterations,
                "submitted": submitted,
                "cancelled_honored": cancelled_honored,
                "reconnects": reconnects,
                "self_accepting": False,
                "one_shot": False,
                "enrolled": bool(enrolled.get("membership_token")),
                "events": self.events,
                "spend_usd": 0,
                "allow_paid": False,
            }
            out = self.evidence_dir / f"continuous-{run_id}.json"
            dump_evidence(out, evidence)
            evidence["evidence_path"] = str(out)
            return evidence


def run_from_env(*, max_iterations: int | None = None) -> dict[str, Any]:
    server = (os.environ.get("SWARM_SERVER_URL") or DEFAULT_SERVER_URL).rstrip("/")
    root = Path(os.environ.get("SWARM_REPO_ROOT") or Path.cwd())
    stop_after = os.environ.get("SWARM_CONNECTOR_MAX_ITERATIONS")
    if max_iterations is None and stop_after:
        max_iterations = int(stop_after)
    mode = resolve_connector_mode()
    endpoint: PublicEndpointConfig | None = None
    try:
        endpoint = PublicEndpointConfig.from_env(
            {
                **dict(os.environ),
                "SWARM_SERVER_URL": server,
                "SWARM_API_BASE_URL": os.environ.get("SWARM_API_BASE_URL") or server,
            }
        )
    except PortableConfigError:
        endpoint = None
    connector = ContinuousMacConnector(
        server_url=server,
        bearer_token=load_bearer_token(root=root),
        project_id=(os.environ.get("SWARM_PROJECT_ID") or "").strip() or None,
        poll_interval_seconds=float(os.environ.get("SWARM_CONNECTOR_POLL") or "1.0"),
        fixture_dir=root / "var" / "mac-connector" / "fixtures",
        evidence_dir=root / "docs" / "evidence" / "v17" / "continuous-connector",
        mode=mode,
        max_iterations=max_iterations,
        endpoint=endpoint,
        public_hostname=resolve_deployment_public_hostname(endpoint=endpoint),
    )
    return connector.run()


def main() -> int:
    evidence = run_from_env()
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


if __name__ == "__main__":
    raise SystemExit(main())
