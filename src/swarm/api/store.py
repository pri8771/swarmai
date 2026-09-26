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
from swarm.mission.store import MissionRecord, MissionStore
from swarm.product.contracts import mission_public_view, public_product_contract, strip_internal
from swarm.product.history import HistoryIndex
from swarm.product.portable_config import WorkerIdentitySpec, default_support_matrix
from swarm.product.projects import ProjectConfig, ProjectStore, scrub_config
from swarm.providers.catalog import list_providers
from swarm.workers.capability_authority import CapabilityAuthority
from swarm.workers.identity import (
    detect_platform_arch,
    identity_from_authorization,
    normalize_architecture,
    normalize_platform,
    primary_locality,
)
from swarm.workers.registry import WorkerRegistryService
from swarm.workspace.grants import WorkspaceGrantRegistry


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
    capability_authority: CapabilityAuthority = field(default_factory=CapabilityAuthority)
    workspace_grants: WorkspaceGrantRegistry = field(default_factory=WorkspaceGrantRegistry)
    _project_store: ProjectStore | None = field(default=None, repr=False)
    _mission_store: MissionStore | None = field(default=None, repr=False)
    _goal_store: Any = field(default=None, repr=False)
    _pursuit_engine: Any = field(default=None, repr=False)
    _pg_factory: Any = field(default=None, repr=False)
    _pursuit_ticker: Any = field(default=None, repr=False)
    _durable_bootstrapped: bool = field(default=False, repr=False)

    def bootstrap_durable(self) -> None:
        """Load durable worker + idempotency mirrors from repo_root (R2/R3)."""
        if self._durable_bootstrapped or self.repo_root is None:
            return
        from swarm.api.durable_authority import load_idempotency, load_worker_registry

        load_worker_registry(self.repo_root, self.workers)
        loaded = load_idempotency(self.repo_root)
        if loaded:
            self.idempotency.update(loaded)
        self._durable_bootstrapped = True

    def require_durable_writes(self) -> None:
        """Refuse simulated writable authority when operational DB is down (PC-02).

        ``db_reachable is False`` means the database was probed and unavailable.
        File-backed local durability remains allowed when no DB was configured
        (``db_reachable is None``) or when fixture/mock mode is explicit.
        """
        if self.fixture_mode or self.execution_mode != "operational":
            return
        if self.db_reachable is False:
            raise ApiError(
                "durable_authority_unavailable",
                "operational writes require a reachable durable database; "
                "refusing writable fallback to simulated in-memory/file authority",
                status_code=503,
            )

    def _persist_durable_workers(self) -> None:
        if self.repo_root is None:
            return
        from swarm.api.durable_authority import save_worker_registry

        save_worker_registry(self.repo_root, self.workers)

    def _persist_durable_idempotency(self) -> None:
        if self.repo_root is None:
            return
        from swarm.api.durable_authority import save_idempotency

        save_idempotency(self.repo_root, self.idempotency)

    def project_store(self) -> ProjectStore:
        if self._project_store is None:
            root = (self.repo_root or Path.cwd()) / "var" / "projects"
            self._project_store = ProjectStore(root)
        return self._project_store

    def goal_store(self) -> Any:
        if self._goal_store is None:
            from swarm.goals.models import GoalStore

            root = (self.repo_root or Path.cwd()) / "var" / "goals"
            self._goal_store = GoalStore(root)
        return self._goal_store

    def pursuit_engine(self) -> Any:
        """V1.9 autonomous pursuit loop.

        Operational / non-fixture composition uses ``NativeMissionDispatchExecutor``
        (R20-01) plus durable cycle/schedule state (R20-04). ``RecordingExecutor``
        is reserved for explicit fixture/mock demos.
        """
        if self._pursuit_engine is None:
            import time

            from swarm.pursuit import PursuitEngine, RecordingExecutor
            from swarm.pursuit.native_dispatch import NativeMissionDispatchExecutor
            from swarm.pursuit.schedule import PursuitScheduler
            from swarm.pursuit.state_store import DurablePursuitStateStore

            root = (self.repo_root or Path.cwd()) / "var" / "pursuit"
            if self.fixture_mode or self.execution_mode == "mock":
                executor: Any = RecordingExecutor(default_success=True)
            else:
                executor = NativeMissionDispatchExecutor(self)
            factory = self.pg_session_factory()
            mirror: Any = None
            lessons: Any = None
            hold_store: Any = None
            if factory is not None:
                from swarm.pursuit.durable_accounting import SqlHoldStore, SqlLessonPersistence
                from swarm.pursuit.learning import PursuitLessonStore
                from swarm.pursuit.pg_mirror import PursuitPgMirror

                mirror = PursuitPgMirror(factory)
                lessons = PursuitLessonStore(persistence=SqlLessonPersistence(factory))
                hold_store = SqlHoldStore(factory)
            self._pursuit_engine = PursuitEngine(
                self.goal_store(),
                executor=executor,
                lessons=lessons,
                scheduler=PursuitScheduler(clock=time.time),
                clock=time.time,
                state_store=DurablePursuitStateStore(root, mirror=mirror),
                hold_store=hold_store,
            )
        return self._pursuit_engine

    def pg_session_factory(self) -> Any:
        """PostgreSQL session factory for durable pursuit state, or ``None``.

        Only when ``SWARM_V23_DURABLE=1`` and the database was probed reachable;
        otherwise file-backed state under ``var/`` stays authoritative, as before.
        """
        if self._pg_factory is None and self.db_reachable is True:
            import os

            if os.environ.get("SWARM_V23_DURABLE", "") == "1":
                from swarm.db.engine import create_db_engine, make_session_factory

                self._pg_factory = make_session_factory(create_db_engine())
        return self._pg_factory

    def pursuit_ticker(self) -> Any:
        """Site-wide singleton ticker; the epoch row ``pursuit-ticker`` fences other processes."""
        if self._pursuit_ticker is None:
            from swarm.contracts.common import new_id
            from swarm.scheduling.epoch import (
                InMemorySchedulerEpochService,
                SqlSchedulerEpochService,
            )
            from swarm.scheduling.singleton import SingletonTicker

            factory = self.pg_session_factory()
            epochs: Any = (
                SqlSchedulerEpochService(factory, site_id="pursuit-ticker")
                if factory is not None
                else InMemorySchedulerEpochService(site_id="pursuit-ticker")
            )
            self._pursuit_ticker = SingletonTicker(epochs, holder_id=new_id("pursuit_"))
        return self._pursuit_ticker

    def run_pursuit_tick(self) -> Any:
        """Tick all due goals once, only if this process holds the pursuit epoch."""
        return self.pursuit_engine().singleton_tick(self.pursuit_ticker())

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

    def artifact_store(self) -> Any:
        """Content-addressed blob store under durable ``var/artifacts/cas``."""
        from swarm.workspace.artifacts import ArtifactStore

        root = (self.repo_root or Path.cwd()) / "var" / "artifacts" / "cas"
        return ArtifactStore(root)

    def publish_mission_artifact(
        self,
        mission_id: str,
        *,
        kind: str,
        content: bytes,
        media_type: str,
        owner_scope: str,
        retention_class: str = "mission",
        summary: str | None = None,
        expected_hash: str | None = None,
        actor: str = "api",
    ) -> dict[str, Any]:
        """Write blob to durable CAS, attach ref on mission record, best-effort PG meta."""
        mission = self.get_mission(mission_id)
        store = self.artifact_store()
        ref = store.put(
            content,
            media_type=media_type,
            owner_scope=owner_scope,
            retention_class=retention_class,
            expected_hash=expected_hash,
        )
        record = self.mission_store().load(mission_id)
        arts = dict(record.artifacts or {})
        # Preserve history: kind may have many revisions; keep list under kind_history.
        history = list(arts.get(f"{kind}__history") or [])
        entry = {
            "id": ref.id,
            "kind": kind,
            "uri": ref.uri,
            "media_type": ref.media_type,
            "content_hash": ref.content_hash,
            "byte_length": ref.byte_length,
            "owner_scope": ref.owner_scope,
            "retention_class": ref.retention_class,
            "summary": summary or f"{kind} artifact",
        }
        if isinstance(arts.get(kind), dict) and arts[kind].get("id"):
            history.append(arts[kind])
        history.append(entry)
        arts[f"{kind}__history"] = history
        arts[kind] = entry
        record.artifacts = arts
        self.mission_store().append_timeline(
            record,
            "artifact.published",
            {
                "artifact_id": ref.id,
                "kind": kind,
                "content_hash": ref.content_hash,
                "byte_length": ref.byte_length,
                "actor": actor,
            },
        )
        self.mission_store().save(record)
        self._persist_artifact_metadata(ref)
        self.publish(
            project_id=mission.project_id,
            type="artifact.published",
            actor=actor,
            mission_id=mission_id,
            payload={
                "artifact_id": ref.id,
                "kind": kind,
                "content_hash": ref.content_hash,
            },
            dedupe_key=f"artifact.published:{mission_id}:{ref.content_hash}",
        )
        return {
            "artifact_id": ref.id,
            "kind": kind,
            "uri": ref.uri,
            "media_type": ref.media_type,
            "content_hash": ref.content_hash,
            "byte_length": ref.byte_length,
            "owner_scope": ref.owner_scope,
            "retention_class": ref.retention_class,
            "summary": summary or f"{kind} artifact",
            "mission_id": mission_id,
            "project_id": mission.project_id,
        }

    def read_mission_artifact_bytes(
        self, mission_id: str, artifact_id: str
    ) -> tuple[bytes, dict[str, Any]]:
        """Reopen artifact bytes; enforce tombstone/scope via ArtifactStore.resolve (R4)."""
        mission = self.get_mission(mission_id)
        record = self.mission_store().load(mission_id)
        arts = record.artifacts or {}
        meta: dict[str, Any] | None = None
        if isinstance(arts, dict):
            for key, val in arts.items():
                if key.endswith("__history"):
                    if isinstance(val, list):
                        for item in val:
                            if isinstance(item, dict) and str(item.get("id") or "") == artifact_id:
                                meta = dict(item)
                                meta.setdefault("kind", key.replace("__history", ""))
                                break
                    if meta is not None:
                        break
                    continue
                if not isinstance(val, dict):
                    continue
                if str(val.get("id") or key) == artifact_id:
                    meta = dict(val)
                    meta.setdefault("kind", key)
                    break
        if meta is None:
            raise ApiError("not_found", "artifact not found on mission", status_code=404)
        store = self.artifact_store()
        try:
            # Authoritative deletion/scope check — never bypass via bare hash read.
            ref = store.resolve(
                artifact_id,
                allowed_scopes={
                    str(meta.get("owner_scope") or mission.project_id),
                    "*",
                    mission.project_id,
                },
            )
        except FileNotFoundError as exc:
            raise ApiError("not_found", str(exc), status_code=404) from exc
        except KeyError as exc:
            raise ApiError("not_found", "artifact metadata missing", status_code=404) from exc
        except PermissionError as exc:
            raise ApiError("forbidden", str(exc), status_code=403) from exc
        data = store.get_bytes_by_hash(ref.content_hash)
        meta = {
            **meta,
            "content_hash": ref.content_hash,
            "byte_length": ref.byte_length,
            "media_type": ref.media_type,
        }
        return data, meta

    def _persist_artifact_metadata(self, ref: Any) -> None:
        """Best-effort Postgres metadata row — blob remains authoritative on volume."""
        import os

        from swarm.contracts.workspace import ArtifactRef

        if not isinstance(ref, ArtifactRef):
            return
        url = (os.environ.get("SWARM_DATABASE_URL") or "").strip()
        if not url:
            return
        try:
            from swarm.db.engine import create_db_engine, make_session_factory
            from swarm.db.repositories import ArtifactRepository

            engine = create_db_engine(url)
            session = make_session_factory(engine)()
            try:
                ArtifactRepository(session).put_metadata(ref)
                session.commit()
            except Exception:
                session.rollback()
            finally:
                session.close()
        except Exception:
            # Volume-backed CAS + mission JSON already durable; PG meta is secondary.
            return

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
            self._persist_durable_idempotency()
            return body
        scoped = self._idem_key(
            actor=actor, project_id=project_id, operation=operation, key=key
        )
        self.idempotency[scoped] = {
            "request_digest": request_digest,
            "body": body,
        }
        self._persist_durable_idempotency()
        return body

    async def create_mission(
        self,
        mission: Mission,
        *,
        actor: str,
        task_family: str | None = None,
        required_checks: dict[str, Any] | None = None,
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
        mission = self.get_mission(mission_id)
        record = self.mission_store().load(mission_id)
        plan_checks = (record.plan or {}).get("required_checks")
        # R1: worker/caller cannot replace frozen verifier specs.
        if required_checks is not None:
            if plan_checks is None or dict(required_checks) != dict(plan_checks):
                raise ApiError(
                    "verifier_override_forbidden",
                    "caller-supplied required_checks cannot override frozen plan checks",
                    status_code=403,
                )
        checks = plan_checks if isinstance(plan_checks, dict) else None
        # R1: acceptance requires an actual mission artifact binding.
        arts = record.artifacts or {}
        artifact_meta: dict[str, Any] | None = None
        if isinstance(arts, dict):
            for key, val in arts.items():
                if key.endswith("__history"):
                    continue
                if isinstance(val, dict) and val.get("content_hash"):
                    artifact_meta = dict(val)
                    artifact_meta.setdefault("kind", key)
                    break
        if artifact_meta is None:
            raise ApiError(
                "artifact_required",
                "mission acceptance requires a published artifact under protected verification",
                status_code=409,
            )
        task_family = str((record.plan or {}).get("task_family") or "")
        art_id = str(artifact_meta.get("id") or "")
        content_hash = str(artifact_meta.get("content_hash") or "")
        try:
            artifact_bytes, _meta = self.read_mission_artifact_bytes(mission_id, art_id)
        except ApiError:
            raise
        from swarm.mission.acceptance import ReviewDecision
        from swarm.mission.protected_verify import protected_review

        if force_wrong or produced.get("intentionally_wrong") is True:
            decision = ReviewDecision(
                accepted=False,
                reasons=["wrong_result_rejected"],
                checks={"wrong_result": False},
            )
            protected = None
        else:
            protected = protected_review(
                task_family=task_family,
                required_checks=checks if isinstance(checks, dict) else None,
                artifact_id=art_id,
                artifact_bytes=artifact_bytes,
                content_hash=content_hash,
                worker_produced=produced,
            )
            decision = ReviewDecision(
                accepted=protected.accepted,
                reasons=list(protected.reasons),
                checks=dict(protected.checks),
            )
        record.validation = {
            **(record.validation or {}),
            "review": decision.to_dict(),
            "protected_verify": protected.to_dict() if protected is not None else None,
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
            accepted_result = {
                **(record.result or {}),
                "ok": True,
                "accepted": True,
                "acceptance_receipt_id": receipt_id,
            }
            record.result = accepted_result
            self._persist_mission_record(updated, source="api")
            record = self.mission_store().load(mission_id)
            record.validation = {
                **(record.validation or {}),
                "review": decision.to_dict(),
                "protected_verify": protected.to_dict() if protected is not None else None,
                "reviewed_at": utc_now().isoformat(),
                "reviewed_by": actor,
            }
            # _persist_mission_record preserves prior disk result; re-bind acceptance.
            record.result = {**(record.result or {}), **accepted_result}
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
        rejected_result = {
            **(record.result or {}),
            "ok": False,
            "accepted": False,
            "rejected_reasons": list(decision.reasons),
        }
        record.result = rejected_result
        self._persist_mission_record(updated, source="api")
        record = self.mission_store().load(mission_id)
        record.validation = {
            **(record.validation or {}),
            "review": decision.to_dict(),
            "reviewed_at": utc_now().isoformat(),
            "reviewed_by": actor,
        }
        record.result = {**(record.result or {}), **rejected_result}
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
        host_alias: str | None = None,
        architecture: str | None = None,
        runtime_version: str | None = None,
        labels: list[str] | None = None,
        platform: dict[str, Any] | str | None = None,
        runtimes: list[dict[str, Any]] | list[str] | None = None,
        resource_limits: dict[str, Any] | None = None,
        data_locality: dict[str, Any] | str | None = None,
        workspace_grant_ids: list[str] | None = None,
        role: str = "worker",
    ) -> tuple[WorkerLease, str]:
        token = new_id("wt_")
        authz = self.capability_authority.authorize(
            project_id=project_id,
            requested=capabilities,
            labels=labels or [],
        )
        # Platform may arrive as P4 string or legacy dict {os_family, arch}.
        if isinstance(platform, dict):
            plat_name = str(
                platform.get("os_family") or platform.get("platform") or "unknown"
            )
            arch_from_plat = platform.get("arch") or platform.get("architecture")
        elif isinstance(platform, str) and platform.strip():
            plat_name = platform
            arch_from_plat = None
        else:
            plat_name = "unknown"
            arch_from_plat = None
        arch = normalize_architecture(
            str(architecture or arch_from_plat or "unknown")
        )
        plat_name = normalize_platform(plat_name)
        # Omitted platform/arch → detect host; explicit unsupported stays unqualified.
        if plat_name == "unknown" or arch == "unknown":
            detected_plat, detected_arch = detect_platform_arch()
            if plat_name == "unknown":
                plat_name = detected_plat
            if arch == "unknown":
                arch = detected_arch
        matrix = default_support_matrix()
        platform_supported = matrix.is_supported(plat_name, arch)
        runtime_names: list[str] = []
        for item in runtimes or []:
            if isinstance(item, str):
                runtime_names.append(item)
            elif isinstance(item, dict):
                kind = str(item.get("kind") or "runtime")
                ver = str(item.get("version") or "")
                runtime_names.append(f"{kind}:{ver}" if ver else kind)
        primary_runtime = runtime_version or (
            runtime_names[0] if runtime_names else "unknown"
        )
        if isinstance(data_locality, dict):
            classes_raw = [str(c) for c in (data_locality.get("classes") or []) if c]
            primary_raw = data_locality.get("primary")
            locality_str = primary_locality(
                privacy_classes,
                str(primary_raw) if primary_raw else (classes_raw[0] if classes_raw else None),
            )
            loc_classes = sorted(set(privacy_classes) | set(classes_raw) | {locality_str})
        else:
            locality_str = primary_locality(
                privacy_classes,
                data_locality if isinstance(data_locality, str) else None,
            )
            loc_classes = sorted(set(privacy_classes) | {locality_str})
        node = host_alias or f"worker-{new_id('node_')[:8]}"
        worker_id = new_id("wk_")
        identity: WorkerIdentitySpec = identity_from_authorization(
            worker_id=worker_id,
            node_identity=node,
            platform_name=plat_name,
            architecture=arch,
            authz=authz,
            runtime_version=primary_runtime,
            runtimes=runtime_names,
            resource_limits=resource_limits,
            workspace_grants=list(workspace_grant_ids or []),
            privacy_classes=loc_classes,
            data_locality=locality_str,
            role=role,
            support_matrix=matrix,
        )
        # Scheduling: supported host may use authorized grants; unsupported → empty.
        # Verified flag tracks explicit project policy only (never nonempty-list coercion).
        if platform_supported:
            scheduling = sorted(set(authz.granted))
        else:
            scheduling = []
        capabilities_verified = bool(
            authz.verified and platform_supported and identity.verified_capabilities
        )
        lease = WorkerLease(
            worker_id=identity.worker_id,
            node_identity=identity.node_identity,
            architecture=identity.architecture,
            runtime_version=identity.runtime_version,
            capacity_units=capacity_units,
            capabilities=scheduling,
            labels=list(labels or []),
            claimed_capabilities=list(identity.capabilities),
            capabilities_verified=capabilities_verified,
            platform={
                "platform": identity.platform,
                "architecture": identity.architecture,
            },
            runtimes=[{"name": r} for r in identity.runtimes],
            data_locality={
                "primary": identity.data_locality,
                "classes": loc_classes,
            },
            resource_limits=dict(identity.resource_limits),
            workspace_grant_ids=list(identity.workspace_grants),
        )
        registered = await self.workers.register(
            lease, token=token, project_id=project_id
        )
        rec = self.workers._workers[registered.worker_id]
        rec.privacy_classes = set(loc_classes)
        rec.named_inference_urls = list(named_inference_urls or [])
        rec.claimed_capabilities = set(identity.capabilities)
        rec.capabilities_verified = capabilities_verified
        rec.host_alias = node
        rec.workspace_grant_ids = list(identity.workspace_grants)
        self._persist_durable_workers()
        self.publish(
            project_id=project_id,
            type="worker.joined",
            actor=actor,
            payload={
                "worker_id": registered.worker_id,
                "capacity": capacity_units,
                "privacy": loc_classes,
                "capabilities_granted": scheduling,
                "capabilities_claimed": list(identity.capabilities),
                "capabilities_verified": capabilities_verified,
                "platform_supported": platform_supported,
                "architecture": identity.architecture,
                "platform": identity.platform,
                "role": identity.role,
                "data_locality": identity.data_locality,
                "identity": identity.model_dump(mode="json"),
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
        writable = True
        if (
            self.execution_mode == "operational"
            and not self.fixture_mode
            and self.db_reachable is False
        ):
            writable = False
        return {
            "status": "ready" if ready else "not_ready",
            "execution_mode": self.execution_mode,
            "fixture_mode": self.fixture_mode,
            "providers_network": self.providers_network,
            "allow_paid": self.allow_paid,
            "database": db_status,
            "durable_writes": "allowed" if writable else "blocked_db_down",
            "runtime": "ok" if runtime_ok else "down",
            "configured_accounts": len(self.accounts),
            "configured_routes": len(self.routes),
            "mock_vs_live": (
                "fixture_mode_seeded"
                if self.fixture_mode
                else "operational_empty_or_observed_not_mock_broker"
            ),
        }
