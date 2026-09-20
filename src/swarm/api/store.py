"""In-memory product API store — wires controller, workers, events, approvals."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
from pathlib import Path
from typing import Any

from swarm.api.errors import ApiError
from swarm.api.events import EventLog
from swarm.broker.explain import build_mock_broker, explain_capacity
from swarm.contracts.common import new_id, payload_hash, utc_now
from swarm.contracts.enums import MissionStatus, TaskStatus
from swarm.contracts.fixtures import sample_provider_account, sample_route, sample_route_beta
from swarm.contracts.mission import Mission
from swarm.contracts.provider import ProviderAccount, RouteSnapshot
from swarm.contracts.workspace import Approval, EventEnvelope, WorkerLease
from swarm.controller.mission import MissionController
from swarm.evals.profiles import ProfileStore
from swarm.mission.store import MissionRecord, MissionStore
from swarm.product.contracts import mission_public_view, public_product_contract, strip_internal
from swarm.product.history import HistoryIndex
from swarm.product.projects import ProjectConfig, ProjectStore, scrub_config
from swarm.providers.catalog import list_providers
from swarm.workers.registry import WorkerRegistryService


def _scrub(obj: dict[str, Any]) -> dict[str, Any]:
    """Strip anything that looks like a secret value from API responses."""
    banned = ("api_key", "secret", "password", "authorization", "token_value")
    out: dict[str, Any] = {}
    for k, v in obj.items():
        lk = k.lower()
        if any(b in lk for b in banned) and lk not in {
            "token_id",
            "secret_ref_names",
            "idempotency_key",
        }:
            continue
        if isinstance(v, dict):
            out[k] = _scrub(v)
        elif isinstance(v, str) and (v.startswith("sk-") or "api_key=" in v.lower()):
            out[k] = "[redacted]"
        else:
            out[k] = v
    return out


@dataclass
class ProductStore:
    controller: MissionController = field(default_factory=lambda: MissionController())
    workers: WorkerRegistryService = field(default_factory=WorkerRegistryService)
    events: EventLog = field(default_factory=EventLog)
    profiles: ProfileStore = field(default_factory=ProfileStore)
    accounts: dict[str, ProviderAccount] = field(default_factory=dict)
    routes: dict[str, RouteSnapshot] = field(default_factory=dict)
    approvals: dict[str, Approval] = field(default_factory=dict)
    idempotency: dict[str, dict[str, Any]] = field(default_factory=dict)
    cancelled_missions: set[str] = field(default_factory=set)
    cancelled_tasks: set[str] = field(default_factory=set)
    side_effects: list[str] = field(default_factory=list)
    db_reachable: bool | None = None  # None = not probed; False = down; True = up
    execution_mode: str = "mock"
    allow_paid: bool = False
    providers_network: bool = False
    repo_root: Path | None = None
    _project_store: ProjectStore | None = field(default=None, repr=False)
    _mission_store: MissionStore | None = field(default=None, repr=False)

    def project_store(self) -> ProjectStore:
        if self._project_store is None:
            root = (self.repo_root or Path.cwd()) / "var" / "projects"
            self._project_store = ProjectStore(root)
        return self._project_store

    def mission_store(self) -> MissionStore:
        """Durable mission identity shared by API / CLI / console reopen paths."""
        if self._mission_store is None:
            root = (self.repo_root or Path.cwd()) / "var" / "missions"
            self._mission_store = MissionStore(root)
        return self._mission_store

    def history_index(self) -> HistoryIndex:
        return HistoryIndex(self.repo_root or Path.cwd())

    def _persist_mission_record(
        self, mission: Mission, *, source: str = "api"
    ) -> MissionRecord:
        store = self.mission_store()
        existing: MissionRecord | None = None
        path = store._path(mission.id)
        if path.exists():
            try:
                existing = store.load(mission.id)
            except (OSError, TypeError, KeyError, ValueError):
                existing = None
        now = utc_now().isoformat()
        record = MissionRecord(
            mission_id=mission.id,
            goal=mission.objective,
            status=mission.status.value,
            created_at=existing.created_at if existing else now,
            updated_at=now,
            revision=mission.revision,
            project_id=mission.project_id,
            source=source,
            contract=mission.model_dump(mode="json"),
            plan=existing.plan if existing else {"project_id": mission.project_id},
            tasks=existing.tasks if existing else [],
            timeline=existing.timeline if existing else [],
            agents=existing.agents if existing else [],
            artifacts=existing.artifacts if existing else {},
            validation=existing.validation if existing else {},
            retries=existing.retries if existing else [],
            model_assignments=existing.model_assignments if existing else [],
            cost=existing.cost if existing else {},
            result=existing.result if existing else {},
        )
        if existing is None:
            store.append_timeline(
                record,
                "mission.created",
                {"source": source, "status": mission.status.value},
            )
        store.save(record)
        return record

    def _hydrate_mission_from_store(self, mission_id: str) -> Mission | None:
        path = self.mission_store()._path(mission_id)
        if not path.exists():
            return None
        try:
            record = self.mission_store().load(mission_id)
        except (OSError, TypeError, KeyError, ValueError):
            return None
        if record.contract:
            try:
                mission = Mission.model_validate(record.contract)
            except (TypeError, ValueError, KeyError):
                return None
            self.controller.missions[mission.id] = mission
            return mission
        return None

    def list_public_missions(self, *, project_id: str | None = None) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        seen: set[str] = set()
        for mission in self.controller.missions.values():
            if project_id and mission.project_id != project_id:
                continue
            seen.add(mission.id)
            rows.append(
                strip_internal(
                    scrub_config(
                        {
                            "mission_id": mission.id,
                            "project_id": mission.project_id,
                            "status": mission.status.value,
                            "objective": mission.objective,
                            "revision": mission.revision,
                            "source": "api_controller",
                        }
                    )
                )
            )
        # Durable MissionStore is the shared identity across API/CLI/console.
        try:
            for entry in self.mission_store().list_missions():
                mid = str(entry.get("mission_id") or "")
                if not mid or mid in seen:
                    continue
                try:
                    record = self.mission_store().load(mid)
                except (OSError, TypeError, KeyError, ValueError):
                    continue
                rec_project = record.project_id or (record.plan or {}).get("project_id")
                if project_id and rec_project != project_id:
                    continue
                seen.add(mid)
                rows.append(
                    strip_internal(
                        scrub_config(
                            {
                                "mission_id": mid,
                                "project_id": rec_project,
                                "status": record.status,
                                "objective": record.goal,
                                "revision": record.revision,
                                "source": record.source or "mission_store",
                            }
                        )
                    )
                )
        except OSError:
            pass
        # Merge history index for reopenable missions not already listed.
        try:
            for entry in self.history_index().load_index():
                if project_id and entry.get("project_id") != project_id:
                    continue
                mid = str(entry.get("mission_id") or "")
                if not mid or mid in seen:
                    continue
                seen.add(mid)
                rows.append(strip_internal(scrub_config(entry)))
        except OSError:
            pass
        return rows

    def create_project(self, **kwargs: Any) -> ProjectConfig:
        return self.project_store().create(**kwargs)

    def get_project(self, project_id: str) -> ProjectConfig:
        try:
            return self.project_store().get(project_id)
        except KeyError as exc:
            raise ApiError("not_found", "project not found", status_code=404) from exc

    def list_projects(self) -> list[dict[str, Any]]:
        return self.project_store().list_projects()

    def public_contract(self) -> dict[str, Any]:
        return public_product_contract()

    def mission_report(self, mission_id: str) -> dict[str, Any]:
        # Prefer live controller mission; hydrate durable store; then history.
        if mission_id not in self.controller.missions:
            self._hydrate_mission_from_store(mission_id)
        if mission_id in self.controller.missions:
            mission = self.controller.missions[mission_id]
            graph = self.graph_view(mission_id)
            payload = strip_internal(
                scrub_config(
                    {
                        "mission": mission.model_dump(mode="json"),
                        "graph": graph,
                        "source": "api_controller",
                    }
                )
            )
            assert isinstance(payload, dict)
            return payload
        try:
            return self.history_index().reopen(mission_id)
        except (OSError, KeyError, TypeError, FileNotFoundError) as exc:
            raise ApiError("not_found", "mission report not found", status_code=404) from exc

    def mission_artifacts(self, mission_id: str) -> list[dict[str, Any]]:
        try:
            return self.history_index().list_artifacts(mission_id)
        except (OSError, FileNotFoundError, TypeError, KeyError):
            return []

    def public_mission_view(self, mission_id: str) -> dict[str, Any]:
        mission = self.get_mission(mission_id)
        graph = self.graph_view(mission_id)
        return mission_public_view(
            {
                **mission.model_dump(mode="json"),
                "mission_id": mission.id,
                "goal": mission.objective,
                "tasks": graph.get("tasks") or [],
            }
        )

    def seed_catalog(self) -> None:
        acct = sample_provider_account()
        self.accounts[acct.id] = acct
        for route in (sample_route(), sample_route_beta()):
            self.routes[route.route_id] = route
        # Explicit unknown route so APIs never invent readiness.
        from swarm.contracts.enums import AvailabilityStatus

        unknown = sample_route().model_copy(
            update={
                "route_id": "rt_fake_unknown",
                "model_id": "fake-unknown-v0",
                "availability_status": AvailabilityStatus.UNKNOWN,
                "status": "cataloged",
                "observed_capabilities": [],
            }
        )
        self.routes[unknown.route_id] = unknown

    def publish(
        self,
        *,
        project_id: str,
        type: str,
        actor: str,
        mission_id: str | None = None,
        task_id: str | None = None,
        payload: dict[str, Any] | None = None,
        dedupe_key: str | None = None,
        correlation_id: str | None = None,
    ) -> EventEnvelope:
        event = EventEnvelope(
            project_id=project_id,
            type=type,
            actor=actor,
            mission_id=mission_id,
            task_id=task_id,
            payload=_scrub(payload or {}),
            dedupe_key=dedupe_key,
            correlation_id=correlation_id,
        )
        return self.events.append(event)

    def _idem_key(
        self,
        *,
        actor: str,
        project_id: str,
        operation: str,
        key: str,
    ) -> str:
        return f"{actor}|{project_id}|{operation}|{key}"

    def recall_idempotent(
        self,
        key: str | None,
        *,
        actor: str | None = None,
        project_id: str | None = None,
        operation: str | None = None,
        request_digest: str | None = None,
    ) -> dict[str, Any] | None:
        if not key:
            return None
        # Backward-compatible bare-key lookup only when scope omitted (legacy callers).
        if actor is None or project_id is None or operation is None:
            return self.idempotency.get(key)
        scoped = self._idem_key(
            actor=actor, project_id=project_id, operation=operation, key=key
        )
        entry = self.idempotency.get(scoped)
        if entry is None:
            return None
        if request_digest is not None and entry.get("request_digest") != request_digest:
            raise ApiError(
                "idempotency_payload_mismatch",
                "idempotency key reused with a different request body",
                status_code=409,
            )
        return entry.get("body")

    def store_idempotent(
        self,
        key: str | None,
        body: dict[str, Any],
        *,
        actor: str | None = None,
        project_id: str | None = None,
        operation: str | None = None,
        request_digest: str | None = None,
    ) -> dict[str, Any]:
        if not key:
            return body
        if actor is None or project_id is None or operation is None:
            self.idempotency[key] = body
            return body
        scoped = self._idem_key(
            actor=actor, project_id=project_id, operation=operation, key=key
        )
        self.idempotency[scoped] = {
            "request_digest": request_digest,
            "body": body,
        }
        return body

    async def create_mission(self, mission: Mission, *, actor: str) -> Mission:
        created = await self.controller.submit_mission(mission)
        self._persist_mission_record(created, source="api")
        self.publish(
            project_id=created.project_id,
            type="mission.created",
            actor=actor,
            mission_id=created.id,
            payload={"revision": created.revision, "status": created.status.value},
            dedupe_key=f"mission.created:{created.id}",
        )
        return created

    def get_mission(self, mission_id: str) -> Mission:
        mission = self.controller.missions.get(mission_id)
        if mission is None:
            mission = self._hydrate_mission_from_store(mission_id)
        if mission is None:
            raise ApiError("not_found", "mission not found", status_code=404)
        return mission

    async def cancel_mission(self, mission_id: str, *, actor: str) -> Mission:
        mission = self.get_mission(mission_id)
        if mission_id in self.cancelled_missions:
            return mission
        updated = mission.model_copy(
            update={
                "status": MissionStatus.CANCELLED,
                "cancellation_generation": mission.cancellation_generation + 1,
            }
        )
        self.controller.missions[mission_id] = updated
        self.cancelled_missions.add(mission_id)
        # Mark all tasks cancelled so no new side effects.
        for tid, task in list(self.controller.tasks.get(mission_id, {}).items()):
            self.cancelled_tasks.add(tid)
            self.controller.tasks[mission_id][tid] = task.model_copy(
                update={"status": TaskStatus.CANCELLED}
            )
        self._persist_mission_record(updated, source="api")
        cancelled_record = self.mission_store().load(mission_id)
        self.mission_store().append_timeline(
            cancelled_record,
            "mission.cancelled",
            {"actor": actor, "cancellation_generation": updated.cancellation_generation},
        )
        self.mission_store().save(cancelled_record)
        self.publish(
            project_id=updated.project_id,
            type="mission.cancelled",
            actor=actor,
            mission_id=mission_id,
            payload={"cancellation_generation": updated.cancellation_generation},
            dedupe_key=f"mission.cancelled:{mission_id}:{updated.cancellation_generation}",
        )
        return updated

    def assert_not_cancelled(
        self, mission_id: str | None = None, task_id: str | None = None
    ) -> None:
        if mission_id and mission_id in self.cancelled_missions:
            raise ApiError(
                "mission_cancelled",
                "mission cancelled; new side effects blocked",
                status_code=409,
            )
        if task_id and task_id in self.cancelled_tasks:
            raise ApiError(
                "task_cancelled",
                "task cancelled; new side effects blocked",
                status_code=409,
            )

    def record_side_effect(
        self, label: str, *, mission_id: str | None = None, task_id: str | None = None
    ) -> None:
        self.assert_not_cancelled(mission_id=mission_id, task_id=task_id)
        self.side_effects.append(label)

    def graph_view(self, mission_id: str) -> dict[str, Any]:
        mission = self.get_mission(mission_id)
        tasks = list(self.controller.tasks.get(mission_id, {}).values())
        return {
            "mission_id": mission_id,
            "revision": mission.revision,
            "status": mission.status.value,
            "tasks": [t.model_dump(mode="json") for t in tasks],
            "explanations": list(self.controller.graph_explanations),
        }

    def public_accounts(self) -> list[dict[str, Any]]:
        rows = []
        for acct in self.accounts.values():
            data = acct.model_dump(mode="json")
            # secret_ref_names stay; never invent secret values.
            rows.append(_scrub(data))
        return rows

    def public_routes(self) -> list[dict[str, Any]]:
        rows = []
        for route in self.routes.values():
            data = route.model_dump(mode="json")
            # Accurate unknown/retired statuses from catalog + route.
            if route.availability_status.value == "unknown":
                data["availability_status"] = "unknown"
            rows.append(_scrub(data))
        # Merge retired catalog entries so UI never invents "available".
        for row in list_providers(mode="mock"):
            if row.get("retired"):
                rows.append(
                    {
                        "route_id": f"retired_{row['id']}",
                        "provider": row["id"],
                        "account_id": None,
                        "model_id": None,
                        "availability_status": "retired",
                        "status": "retired",
                        "capability_claims": [],
                    }
                )
        return rows

    async def capacity(self, *, purpose: str = "mission") -> dict[str, Any]:
        # Offline mock broker explain — not live spend.
        _ = build_mock_broker()
        return await explain_capacity(mode="mock", purpose=purpose)

    def create_approval(
        self,
        *,
        permitted_operation: str,
        destination: str,
        grantor: str,
        payload: dict[str, Any],
        ttl_seconds: int = 600,
    ) -> Approval:
        approval = Approval(
            payload_hash=payload_hash(payload),
            permitted_operation=permitted_operation,
            destination=destination,
            grantor=grantor,
            expires_at=utc_now() + timedelta(seconds=ttl_seconds),
        )
        self.approvals[approval.id] = approval
        self.publish(
            project_id=payload.get("project_id", "proj_unknown"),
            type="approval.requested",
            actor=grantor,
            payload={"approval_id": approval.id, "operation": permitted_operation},
            dedupe_key=f"approval.requested:{approval.id}",
        )
        return approval

    def resolve_approval(
        self,
        approval_id: str,
        *,
        accept: bool,
        actor: str,
        payload: dict[str, Any] | None = None,
    ) -> Approval:
        approval = self.approvals.get(approval_id)
        if approval is None:
            raise ApiError("not_found", "approval not found", status_code=404)
        if approval.revoked_at is not None:
            raise ApiError("approval_revoked", "approval already revoked", status_code=409)
        if approval.expires_at <= utc_now():
            raise ApiError("approval_expired", "approval expired", status_code=409)
        if payload is not None and payload_hash(payload) != approval.payload_hash:
            raise ApiError(
                "approval_payload_mismatch",
                "payload changed since approval",
                status_code=409,
            )
        if not accept:
            approval = approval.model_copy(update={"revoked_at": utc_now()})
            self.approvals[approval_id] = approval
        self.publish(
            project_id="proj_system",
            type="approval.resolved",
            actor=actor,
            payload={"approval_id": approval_id, "accepted": accept},
            dedupe_key=f"approval.resolved:{approval_id}:{accept}",
        )
        return approval

    async def enroll_worker(
        self,
        *,
        capabilities: list[str],
        capacity_units: float,
        privacy_classes: list[str],
        named_inference_urls: list[str] | None = None,
        project_id: str,
        actor: str,
    ) -> tuple[WorkerLease, str]:
        token = new_id("wt_")
        lease = WorkerLease(
            worker_id=new_id("wk_"),
            node_identity=f"api-{new_id('node_')[:8]}",
            architecture="api",
            runtime_version="0.1.0",
            capacity_units=capacity_units,
            capabilities=capabilities,
            labels=["api"],
        )
        registered = await self.workers.register(lease, token=token)
        rec = self.workers._workers[registered.worker_id]
        rec.privacy_classes = set(privacy_classes)
        rec.named_inference_urls = list(named_inference_urls or [])
        self.publish(
            project_id=project_id,
            type="worker.joined",
            actor=actor,
            payload={
                "worker_id": registered.worker_id,
                "capacity": capacity_units,
                "privacy": privacy_classes,
            },
            dedupe_key=f"worker.joined:{registered.worker_id}",
        )
        return registered, token

    def health_ready(self) -> dict[str, Any]:
        runtime_ok = self.controller is not None and self.workers is not None
        db_status: str
        if self.db_reachable is True:
            db_status = "up"
        elif self.db_reachable is False:
            db_status = "down"
        else:
            db_status = "unprobed"
        ready = runtime_ok and self.db_reachable is not False
        return {
            "status": "ready" if ready else "not_ready",
            "execution_mode": self.execution_mode,
            "providers_network": self.providers_network,
            "allow_paid": self.allow_paid,
            "database": db_status,
            "runtime": "ok" if runtime_ok else "down",
            "mock_vs_live": "api_store_in_memory_not_live_providers",
        }
