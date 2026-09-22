"""In-memory product API store — wires controller, workers, events, approvals."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
from pathlib import Path
from typing import Any

from swarm.api.errors import ApiError
from swarm.api.events import EventLog
from swarm.broker.explain import explain_capacity
from swarm.contracts.common import new_id, payload_hash, utc_now
from swarm.contracts.enums import MissionStatus, TaskStatus
from swarm.contracts.fixtures import sample_provider_account, sample_route, sample_route_beta
from swarm.contracts.mission import Mission
from swarm.contracts.provider import ProviderAccount, RouteSnapshot
from swarm.contracts.workspace import Approval, EventEnvelope, WorkerLease
from swarm.controller.mission import MissionController
from swarm.evals.profiles import ProfileStore
from swarm.mission.action_boundary import local_worktree_gateway
from swarm.mission.store import MissionRecord, MissionStore
from swarm.product.contracts import mission_public_view, public_product_contract, strip_internal
from swarm.product.history import HistoryIndex
from swarm.product.projects import ProjectConfig, ProjectStore, scrub_config
from swarm.providers.catalog import list_providers
from swarm.tools.fences import ActorContext
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
    # Operational default is not mock — fixtures require explicit fixture_mode.
    execution_mode: str = "operational"
    fixture_mode: bool = False
    allow_paid: bool = False
    providers_network: bool = False
    repo_root: Path | None = None
    _project_store: ProjectStore | None = field(default=None, repr=False)
    _mission_store: MissionStore | None = field(default=None, repr=False)
    # Governed local zero-spend broker for operational generic execute path.
    _mission_broker: Any | None = field(default=None, repr=False)

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

    def operational_mission_broker(self, *, models: list[str] | None = None) -> Any:
        """Reuse the existing governed local mission broker (no second broker)."""
        from swarm.mission.brokered_inference import build_local_mission_broker

        wanted = tuple(models) if models is not None else ("gemma3:4b", "qwen3.5:4b")
        cached_key = getattr(self, "_mission_broker_models", None)
        if self._mission_broker is None or cached_key != wanted:
            self._mission_broker = build_local_mission_broker(
                repo_root=self.repo_root or Path.cwd(),
                models=list(wanted),
            )
            self._mission_broker_models = wanted
        return self._mission_broker

    def history_index(self) -> HistoryIndex:
        return HistoryIndex(self.repo_root or Path.cwd())

    def _persist_mission_record(self, mission: Mission, *, source: str = "api") -> MissionRecord:
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

    def _refresh_mission_from_store(self, mission_id: str) -> Mission | None:
        """Prefer durable MissionStore when CLI/console mutated the same ID."""
        path = self.mission_store()._path(mission_id)
        if not path.exists():
            return self.controller.missions.get(mission_id)
        try:
            record = self.mission_store().load(mission_id)
        except (OSError, TypeError, KeyError, ValueError):
            return self.controller.missions.get(mission_id)
        if not record.contract:
            return self.controller.missions.get(mission_id)
        try:
            durable = Mission.model_validate(record.contract)
        except (TypeError, ValueError, KeyError):
            return self.controller.missions.get(mission_id)
        cached = self.controller.missions.get(mission_id)
        if cached is None or durable.revision >= cached.revision or durable.status != cached.status:
            self.controller.missions[mission_id] = durable
            return durable
        return cached

    def list_public_missions(self, *, project_id: str | None = None) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        seen: set[str] = set()
        # Durable store first — CLI/console/API share IDs; controller may be stale.
        try:
            for entry in self.mission_store().list_missions():
                mid = str(entry.get("mission_id") or "")
                if not mid:
                    continue
                mission = self._refresh_mission_from_store(mid)
                if mission is None:
                    continue
                if project_id and mission.project_id != project_id:
                    continue
                seen.add(mid)
                rows.append(
                    strip_internal(
                        scrub_config(
                            {
                                "mission_id": mission.id,
                                "project_id": mission.project_id,
                                "status": mission.status.value,
                                "objective": mission.objective,
                                "revision": mission.revision,
                                "source": "mission_store",
                            }
                        )
                    )
                )
        except (OSError, TypeError, KeyError, ValueError):
            pass
        for mission in self.controller.missions.values():
            if mission.id in seen:
                continue
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
        """Fixture-only catalog seed — marks store as fixture_mode."""
        self.fixture_mode = True
        self.execution_mode = "mock"
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
        scoped = self._idem_key(actor=actor, project_id=project_id, operation=operation, key=key)
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
        scoped = self._idem_key(actor=actor, project_id=project_id, operation=operation, key=key)
        self.idempotency[scoped] = {
            "request_digest": request_digest,
            "body": body,
        }
        return body

    async def create_mission(
        self,
        mission: Mission,
        *,
        actor: str,
        task_family: str | None = None,
        required_checks: dict[str, Any] | None = None,
        hidden_acceptance: dict[str, Any] | None = None,
    ) -> Mission:
        from swarm.mission.acceptance import classify_task_support

        created = await self.controller.submit_mission(mission)
        support = classify_task_support(task_family or "")
        if task_family and not support.supported:
            # Honest unsupported outcome: durable ID exists, status failed.
            created = created.model_copy(update={"status": MissionStatus.FAILED})
            self.controller.missions[created.id] = created
        self._persist_mission_record(created, source="api")
        record = self.mission_store().load(created.id)
        plan = dict(record.plan or {})
        plan["project_id"] = created.project_id
        if task_family:
            plan["task_family"] = task_family
            plan["support"] = support.to_dict()
        if required_checks:
            plan["required_checks"] = dict(required_checks)
        if hidden_acceptance:
            # Stored for independent review only — never returned to worker prompts.
            plan["hidden_acceptance"] = dict(hidden_acceptance)
        record.plan = plan
        if task_family and not support.supported:
            record.result = {
                "ok": False,
                "unsupported": True,
                "support": support.to_dict(),
                "summary": support.reason,
            }
            record.validation = {
                "supported": False,
                "reasons": [support.reason],
            }
            self.mission_store().append_timeline(
                record,
                "mission.unsupported",
                {"task_family": task_family, "reason": support.reason},
            )
        self.mission_store().save(record)
        self.publish(
            project_id=created.project_id,
            type="mission.created",
            actor=actor,
            mission_id=created.id,
            payload={
                "revision": created.revision,
                "status": created.status.value,
                "task_family": task_family,
                "supported": support.supported if task_family else None,
            },
            dedupe_key=f"mission.created:{created.id}",
        )
        return created

    async def review_mission_attempt(
        self,
        mission_id: str,
        *,
        actor: str,
        produced: dict[str, Any],
        required_checks: dict[str, Any] | None = None,
        force_wrong: bool = False,
    ) -> dict[str, Any]:
        from swarm.mission.acceptance import review_attempt

        mission = self.get_mission(mission_id)
        record = self.mission_store().load(mission_id)
        plan_checks = (record.plan or {}).get("required_checks")
        checks = required_checks if required_checks is not None else plan_checks
        hidden = (record.plan or {}).get("hidden_acceptance")
        decision = review_attempt(
            produced=produced,
            required_checks=checks if isinstance(checks, dict) else None,
            force_wrong=force_wrong,
            hidden_acceptance=hidden if isinstance(hidden, dict) else None,
        )
        record.validation = {
            **(record.validation or {}),
            "review": decision.to_dict(),
            "reviewed_at": utc_now().isoformat(),
            "reviewed_by": actor,
        }
        if decision.accepted:
            receipt_id = new_id("acr_")
            updated = mission.model_copy(
                update={
                    "status": MissionStatus.COMPLETED,
                    "acceptance_receipt_id": receipt_id,
                    "revision": mission.revision + 1,
                }
            )
            self.controller.missions[mission_id] = updated
            record.status = updated.status.value
            record.revision = updated.revision
            record.result = {
                **(record.result or {}),
                "ok": True,
                "accepted": True,
                "acceptance_receipt_id": receipt_id,
            }
            self._persist_mission_record(updated, source="api")
            record = self.mission_store().load(mission_id)
            record.validation = {
                **(record.validation or {}),
                "review": decision.to_dict(),
                "reviewed_at": utc_now().isoformat(),
                "reviewed_by": actor,
            }
            self.mission_store().append_timeline(
                record,
                "mission.accepted",
                {"acceptance_receipt_id": receipt_id, "reasons": decision.reasons},
            )
            self.mission_store().save(record)
            self.publish(
                project_id=updated.project_id,
                type="mission.accepted",
                actor=actor,
                mission_id=mission_id,
                payload={"acceptance_receipt_id": receipt_id},
                dedupe_key=f"mission.accepted:{mission_id}:{receipt_id}",
            )
            return {
                "mission_id": mission_id,
                "accepted": True,
                "acceptance_receipt_id": receipt_id,
                "review": decision.to_dict(),
                "mission": updated.model_dump(mode="json"),
            }

        updated = mission.model_copy(
            update={
                "status": MissionStatus.FAILED,
                "acceptance_receipt_id": None,
                "revision": mission.revision + 1,
            }
        )
        self.controller.missions[mission_id] = updated
        record.status = updated.status.value
        record.revision = updated.revision
        record.result = {
            **(record.result or {}),
            "ok": False,
            "accepted": False,
            "rejected_reasons": list(decision.reasons),
        }
        self._persist_mission_record(updated, source="api")
        record = self.mission_store().load(mission_id)
        record.validation = {
            **(record.validation or {}),
            "review": decision.to_dict(),
            "reviewed_at": utc_now().isoformat(),
            "reviewed_by": actor,
        }
        self.mission_store().append_timeline(
            record,
            "mission.rejected",
            {"reasons": decision.reasons, "checks": decision.checks},
        )
        self.mission_store().save(record)
        self.publish(
            project_id=updated.project_id,
            type="mission.rejected",
            actor=actor,
            mission_id=mission_id,
            payload={"reasons": decision.reasons},
            dedupe_key=f"mission.rejected:{mission_id}:{updated.revision}",
        )
        return {
            "mission_id": mission_id,
            "accepted": False,
            "acceptance_receipt_id": None,
            "review": decision.to_dict(),
            "mission": updated.model_dump(mode="json"),
        }

    async def execute_mission(
        self,
        mission_id: str,
        *,
        actor: str,
        model: str = "gemma3:4b",
    ) -> dict[str, Any]:
        """Execute the declared task_family for a durable mission via RepoWorker ($0 local)."""
        from swarm.contracts.mission import SizeFeatures, TaskSpec
        from swarm.cost.ledger import CostEntry, CostLedger
        from swarm.mission.acceptance import review_attempt
        from swarm.mission.worker import RepoWorker

        mission = self.get_mission(mission_id)
        if mission_id in self.cancelled_missions or mission.status == MissionStatus.CANCELLED:
            raise ApiError("mission_cancelled", "mission cancelled", status_code=409)
        record = self.mission_store().load(mission_id)
        family = str((record.plan or {}).get("task_family") or "").strip().lower()
        if not family:
            raise ApiError(
                "invalid_request",
                "mission has no task_family to execute",
                status_code=400,
            )
        support = (record.plan or {}).get("support") or {}
        if support.get("supported") is False:
            raise ApiError(
                "unsupported_task",
                str(support.get("reason") or "unsupported"),
                status_code=400,
            )

        task = TaskSpec(
            mission_id=mission_id,
            project_id=mission.project_id,
            objective=mission.objective,
            task_family=family,
            size_features=SizeFeatures(),
            inputs={"goal": mission.objective},
            output_schema_id="generic_json",
            quality_policy_id="policy_default",
            status=TaskStatus.READY,
        )
        # ART-V12 / V2A-001: operational generic execution must use the governed
        # project-scoped broker — never construct RepoWorker without one.
        broker = self.operational_mission_broker(models=[model])
        worker = RepoWorker(
            self.repo_root or Path.cwd(),
            model=model,
            broker=broker,
            project_id=mission.project_id,
            action_gateway=local_worktree_gateway(self.repo_root or Path.cwd()),
            actor_context=ActorContext(actor="product_store", project_id=mission.project_id),
            action_gateway_factory=local_worktree_gateway,
            require_broker=True,
        )
        result, _wt = worker.run_task(task, mission_id=mission_id, prior={})
        ledger = CostLedger()
        inf = result.inference or {}
        if inf:
            try:
                ledger.add(
                    CostEntry(
                        source=task.id,
                        route_id=str(inf.get("route_id") or f"rt_ollama_{model}"),
                        model=str(inf.get("model") or model),
                        requests=1,
                        prompt_tokens=int(inf.get("prompt_tokens") or 0),
                        completion_tokens=int(inf.get("completion_tokens") or 0),
                        cost_usd=float(inf.get("cost_usd") or 0.0),
                    )
                )
            except PermissionError:
                # Paid attempt blocked — record zero and continue with honest failure.
                pass

        checks = (result.artifacts or {}).get("checks") or {}
        required = (record.plan or {}).get("required_checks")
        hidden = (record.plan or {}).get("hidden_acceptance")
        review = review_attempt(
            produced={
                "checks": checks,
                "unsupported": bool((result.artifacts or {}).get("unsupported")),
                "output_excerpt": (result.artifacts or {}).get("output_excerpt") or "",
            },
            required_checks=required if isinstance(required, dict) else None,
            hidden_acceptance=hidden if isinstance(hidden, dict) else None,
        )

        record.tasks = [
            {
                "id": task.id,
                "task_family": family,
                "objective": mission.objective,
                "status": "completed" if result.ok else "failed",
                "ok": result.ok,
                "summary": result.summary,
            }
        ]
        record.cost = {
            **ledger.to_dict(),
            "requests": len(ledger.entries),
            "spend_policy": "zero",
            "allow_paid": False,
            "total_usd": float(ledger.to_dict().get("total_usd") or 0.0),
        }
        record.artifacts = {
            **(record.artifacts or {}),
            "worker_result": result.to_dict(),
            "broker_contract": {
                "governed": True,
                "project_id": mission.project_id,
                "route_id": (inf.get("route_id") if inf else None),
                "broker_error": (inf.get("error") if inf else None),
                "require_broker": True,
            },
        }
        record.validation = {
            **(record.validation or {}),
            "execution_review": review.to_dict(),
            "executed_at": utc_now().isoformat(),
            "executed_by": actor,
        }
        if review.accepted and result.ok:
            receipt_id = new_id("acr_")
            updated = mission.model_copy(
                update={
                    "status": MissionStatus.COMPLETED,
                    "acceptance_receipt_id": receipt_id,
                    "revision": mission.revision + 1,
                }
            )
            record.status = updated.status.value
            record.revision = updated.revision
            record.result = {
                "ok": True,
                "accepted": True,
                "acceptance_receipt_id": receipt_id,
                "summary": result.summary,
            }
            self.controller.missions[mission_id] = updated
            self.mission_store().append_timeline(
                record,
                "mission.executed_accepted",
                {"acceptance_receipt_id": receipt_id, "family": family},
            )
        else:
            updated = mission.model_copy(
                update={
                    "status": MissionStatus.FAILED,
                    "acceptance_receipt_id": None,
                    "revision": mission.revision + 1,
                }
            )
            record.status = updated.status.value
            record.revision = updated.revision
            record.result = {
                "ok": False,
                "accepted": False,
                "summary": result.summary,
                "review_reasons": list(review.reasons),
            }
            self.controller.missions[mission_id] = updated
            self.mission_store().append_timeline(
                record,
                "mission.executed_failed",
                {"family": family, "summary": result.summary, "reasons": review.reasons},
            )
        self._persist_mission_record(updated, source="api")
        # Re-apply execution fields after persist (persist may overwrite from contract).
        saved = self.mission_store().load(mission_id)
        saved.tasks = record.tasks
        saved.cost = record.cost
        saved.artifacts = record.artifacts
        saved.validation = record.validation
        saved.result = record.result
        saved.status = record.status
        self.mission_store().save(saved)
        self.publish(
            project_id=updated.project_id,
            type="mission.executed",
            actor=actor,
            mission_id=mission_id,
            payload={
                "status": saved.status,
                "family": family,
                "ok": bool(result.ok and review.accepted),
                "total_usd": saved.cost.get("total_usd"),
            },
            dedupe_key=f"mission.executed:{mission_id}:{saved.revision}",
        )
        return {
            "mission_id": mission_id,
            "task_family": family,
            "worker_ok": result.ok,
            "accepted": bool(result.ok and review.accepted),
            "status": saved.status,
            "summary": result.summary,
            "cost": saved.cost,
            "review": review.to_dict(),
            "result": saved.result,
            "broker": {
                "governed": True,
                "project_id": mission.project_id,
                "route_id": (inf.get("route_id") if inf else None),
                "error": (inf.get("error") if inf else None),
                "prompt_tokens": (inf.get("prompt_tokens") if inf else None),
                "completion_tokens": (inf.get("completion_tokens") if inf else None),
                "cost_usd": (inf.get("cost_usd") if inf else None),
            },
            "mock_vs_live": "local_ollama_worker_execution_zero_spend",
        }

    def get_mission(self, mission_id: str) -> Mission:
        mission = self._refresh_mission_from_store(mission_id)
        if mission is None:
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
        # Catalog retired markers only — not mock eligibility fabrication.
        for row in list_providers(mode="catalog"):
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
        # Operational path: honest empty/unknown. Mock broker only in fixture_mode.
        mode = "mock" if self.fixture_mode or self.execution_mode == "mock" else self.execution_mode
        return await explain_capacity(mode=mode, purpose=purpose)

    def create_approval(
        self,
        *,
        permitted_operation: str,
        destination: str,
        grantor: str,
        payload: dict[str, Any],
        project_id: str | None = None,
        ttl_seconds: int = 600,
    ) -> Approval:
        owned_project = project_id or str(payload.get("project_id") or "")
        if not owned_project:
            raise ApiError(
                "invalid_request",
                "approval requires project_id ownership",
                status_code=400,
            )
        approval = Approval(
            payload_hash=payload_hash(payload),
            permitted_operation=permitted_operation,
            destination=destination,
            grantor=grantor,
            project_id=owned_project,
            expires_at=utc_now() + timedelta(seconds=ttl_seconds),
        )
        self.approvals[approval.id] = approval
        self.publish(
            project_id=owned_project,
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
        project_id: str | None = None,
    ) -> Approval:
        approval = self.approvals.get(approval_id)
        if approval is None:
            raise ApiError("not_found", "approval not found", status_code=404)
        if project_id is not None and approval.project_id != project_id:
            raise ApiError("forbidden_project", "approval not in project scope", status_code=403)
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
            project_id=approval.project_id,
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
        registered = await self.workers.register(lease, token=token, project_id=project_id)
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
            "fixture_mode": self.fixture_mode,
            "providers_network": self.providers_network,
            "allow_paid": self.allow_paid,
            "database": db_status,
            "runtime": "ok" if runtime_ok else "down",
            "configured_accounts": len(self.accounts),
            "configured_routes": len(self.routes),
            "mock_vs_live": (
                "fixture_mode_seeded"
                if self.fixture_mode
                else "operational_empty_or_observed_not_mock_broker"
            ),
        }
