"""V2.3 /v1 routes: scheduler, ops trace, packs, portability, fleet, worker drain/revoke.

Every route resolves a principal and scopes by project. Fleet-wide and pack-wide
mutations are admin-only. This module never dispatches work: the API runtime's
scheduler has no resource broker, so ``schedule_once`` through it always defers.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, Request
from pydantic import Field
from sqlalchemy.orm import Session, sessionmaker

from swarm.api.auth import AuthRegistry, Principal, get_auth, get_principal
from swarm.api.errors import ApiError
from swarm.api.store import ProductStore
from swarm.capabilities import CapabilityPackManifest, CapabilityPackRegistry
from swarm.capabilities.lifecycle import (
    PackInstallStore,
    PackLifecycleService,
    SqlPackInstallStore,
)
from swarm.capabilities.signing import trusted_keys_from_env
from swarm.contracts.common import StrictModel
from swarm.contracts.v23 import DispatchIntent, DispatchIntentComponent, WorkerDrainState
from swarm.extensions.registry import ExtensionAuthzError
from swarm.observability import OpsEventLog, build_trace
from swarm.product.portability import PortabilityService
from swarm.scheduling.epoch import InMemorySchedulerEpochService, SqlSchedulerEpochService
from swarm.scheduling.memory_store import InMemorySchedulingStore
from swarm.scheduling.service import SchedulerService, SchedulerServiceError
from swarm.scheduling.store import SqlSchedulingStore
from swarm.workers.fleet import FleetError, FleetPlacementService
from swarm.workers.registry import WorkerRegistryService

router = APIRouter(prefix="/v1")

PACK_ACTIONS = ("drain", "disable", "uninstall", "revoke")
_BUNDLE_ID = re.compile(r"^port_[A-Za-z0-9_-]{1,64}$")


@dataclass
class V23Runtime:
    scheduler: SchedulerService
    packs: PackLifecycleService
    fleet: FleetPlacementService
    portability: PortabilityService
    durable: bool


def _no_broker_reserve(intent: DispatchIntent, comp: DispatchIntentComponent) -> str | None:
    raise SchedulerServiceError("api_runtime_has_no_broker")


def _no_broker_release(intent: DispatchIntent, comp: DispatchIntentComponent) -> None:
    return None


def v23_session_factory(db_reachable: bool) -> sessionmaker[Session] | None:
    if not db_reachable or os.environ.get("SWARM_V23_DURABLE", "") != "1":
        return None
    from swarm.db.engine import create_db_engine, make_session_factory

    return make_session_factory(create_db_engine())


def build_v23_runtime(
    *,
    workers: WorkerRegistryService,
    ops: OpsEventLog,
    session_factory: sessionmaker[Session] | None = None,
) -> V23Runtime:
    registry = CapabilityPackRegistry(require_signature=True, trusted_keys=trusted_keys_from_env())
    pack_store: PackInstallStore | None = None
    if session_factory is not None:
        store: Any = SqlSchedulingStore(session_factory)
        epochs: Any = SqlSchedulerEpochService(session_factory)
        pack_store = SqlPackInstallStore(session_factory)
    else:
        store = InMemorySchedulingStore()
        epochs = InMemorySchedulerEpochService()
    scheduler = SchedulerService(
        store,
        epochs=epochs,
        holder_id="api",
        reserve=_no_broker_reserve,
        release=_no_broker_release,
        ops=ops,
    )
    return V23Runtime(
        scheduler=scheduler,
        packs=PackLifecycleService(registry, pack_store),
        fleet=FleetPlacementService(workers),
        portability=PortabilityService(),
        durable=session_factory is not None,
    )


def get_v23(request: Request) -> V23Runtime:
    return request.app.state.v23  # type: ignore[no-any-return]


def _ops(request: Request) -> OpsEventLog:
    return request.app.state.ops_events  # type: ignore[no-any-return]


def _require_admin(principal: Principal) -> None:
    if "admin" not in principal.roles:
        raise ApiError("forbidden_admin", "admin role required", status_code=403)


def _audit(
    request: Request, principal: Principal, action: str, project_id: str | None, **detail: Any
) -> None:
    _ops(request).emit(
        "operator.action",
        "api",
        project_id=project_id,
        detail={"action": action, "actor": principal.subject, **detail},
    )


# ------------------------------------------------------------------ scheduler
class RegisterProjectRequest(StrictModel):
    weight: float = Field(default=1.0, gt=0)
    max_concurrency: int = Field(default=4, ge=1, le=1024)


class WeightRequest(StrictModel):
    weight: float = Field(gt=0)


@router.get("/scheduler/queues")
async def scheduler_queues(
    principal: Principal = Depends(get_principal),
    rt: V23Runtime = Depends(get_v23),
) -> dict[str, Any]:
    rows = rt.scheduler.queues()
    if "admin" not in principal.roles:
        rows = [r for r in rows if r["project_id"] in principal.project_ids]
    return {"projects": rows}


@router.get("/scheduler/receipts")
async def scheduler_receipts(
    project_id: str | None = None,
    limit: int = 100,
    principal: Principal = Depends(get_principal),
    auth: AuthRegistry = Depends(get_auth),
    rt: V23Runtime = Depends(get_v23),
) -> dict[str, Any]:
    if project_id is None:
        _require_admin(principal)
    else:
        auth.require_project(principal, project_id)
    limit = max(1, min(int(limit), 1000))
    rows = rt.scheduler.store.list_receipts(project_id=project_id, limit=limit)
    return {"receipts": [r.model_dump(mode="json") for r in rows]}


@router.post("/scheduler/projects/{project_id}")
async def scheduler_register_project(
    project_id: str,
    body: RegisterProjectRequest,
    request: Request,
    principal: Principal = Depends(get_principal),
    auth: AuthRegistry = Depends(get_auth),
    rt: V23Runtime = Depends(get_v23),
) -> dict[str, Any]:
    auth.require_project(principal, project_id)
    state = rt.scheduler.register_project(
        project_id, weight=body.weight, max_concurrency=body.max_concurrency
    )
    _audit(request, principal, "scheduler.register", project_id)
    return state.model_dump(mode="json")


def _mutate_project(rt: V23Runtime, project_id: str, action: str, weight: float = 0.0) -> Any:
    try:
        if action == "weight":
            return rt.scheduler.set_weight(project_id, weight)
        if action == "pause":
            return rt.scheduler.pause_project(project_id)
        return rt.scheduler.resume_project(project_id)
    except SchedulerServiceError as exc:
        raise ApiError("scheduler_rejected", str(exc), status_code=404) from exc


@router.post("/scheduler/projects/{project_id}/weight")
async def scheduler_set_weight(
    project_id: str,
    body: WeightRequest,
    request: Request,
    principal: Principal = Depends(get_principal),
    auth: AuthRegistry = Depends(get_auth),
    rt: V23Runtime = Depends(get_v23),
) -> dict[str, Any]:
    auth.require_project(principal, project_id)
    state = _mutate_project(rt, project_id, "weight", body.weight)
    _audit(request, principal, "scheduler.weight", project_id, weight=body.weight)
    return state.model_dump(mode="json")  # type: ignore[no-any-return]


@router.post("/scheduler/projects/{project_id}/{action}")
async def scheduler_pause_resume(
    project_id: str,
    action: str,
    request: Request,
    principal: Principal = Depends(get_principal),
    auth: AuthRegistry = Depends(get_auth),
    rt: V23Runtime = Depends(get_v23),
) -> dict[str, Any]:
    if action not in {"pause", "resume"}:
        raise ApiError("not_found", "unknown scheduler action", status_code=404)
    auth.require_project(principal, project_id)
    state = _mutate_project(rt, project_id, action)
    _audit(request, principal, f"scheduler.{action}", project_id)
    return state.model_dump(mode="json")  # type: ignore[no-any-return]


# ------------------------------------------------------------------ ops trace
@router.get("/ops/trace/{trace_id}")
async def ops_trace(
    trace_id: str,
    request: Request,
    principal: Principal = Depends(get_principal),
) -> dict[str, Any]:
    graph = build_trace(_ops(request), trace_id)
    if not graph.nodes:
        raise ApiError("trace_not_found", "trace not found", status_code=404)
    if "admin" not in principal.roles:
        projects = set(graph.projects)
        if not projects or not projects <= set(principal.project_ids):
            # 404, not 403: never confirm that a foreign trace exists.
            raise ApiError("trace_not_found", "trace not found", status_code=404)
    return graph.to_dict()


# ------------------------------------------------------------------ packs
class PackInstallRequest(StrictModel):
    manifest: dict[str, Any]


class PackEnableRequest(StrictModel):
    capabilities: list[str] = Field(min_length=1)


def _pack_error(exc: Exception) -> ApiError:
    return ApiError(
        "pack_rejected", "pack operation rejected", status_code=403, details={"reason": str(exc)}
    )


@router.post("/packs/install")
async def pack_install(
    body: PackInstallRequest,
    request: Request,
    principal: Principal = Depends(get_principal),
    rt: V23Runtime = Depends(get_v23),
) -> dict[str, Any]:
    _require_admin(principal)
    try:
        manifest = CapabilityPackManifest.model_validate(body.manifest)
        rec = rt.packs.install(manifest)
    except ValueError as exc:
        raise ApiError("invalid_manifest", "manifest failed validation", status_code=422) from exc
    except ExtensionAuthzError as exc:
        raise _pack_error(exc) from exc
    _audit(request, principal, "pack.install", None, pack_id=rec.pack_id)
    return rec.model_dump(mode="json")


@router.post("/projects/{project_id}/packs/{pack_id}/{version}/enable")
async def pack_enable(
    project_id: str,
    pack_id: str,
    version: str,
    body: PackEnableRequest,
    request: Request,
    principal: Principal = Depends(get_principal),
    auth: AuthRegistry = Depends(get_auth),
    rt: V23Runtime = Depends(get_v23),
) -> dict[str, Any]:
    auth.require_project(principal, project_id)
    try:
        rec = rt.packs.enable_for_project(pack_id, version, project_id, body.capabilities)
    except ExtensionAuthzError as exc:
        raise _pack_error(exc) from exc
    _audit(request, principal, "pack.enable", project_id, pack_id=pack_id)
    return rec.model_dump(mode="json")


@router.post("/packs/{pack_id}/{version}/{action}")
async def pack_transition(
    pack_id: str,
    version: str,
    action: str,
    request: Request,
    principal: Principal = Depends(get_principal),
    rt: V23Runtime = Depends(get_v23),
) -> dict[str, Any]:
    if action not in PACK_ACTIONS:
        raise ApiError("not_found", "unknown pack action", status_code=404)
    _require_admin(principal)
    fn = {
        "drain": rt.packs.begin_drain,
        "disable": rt.packs.disable,
        "uninstall": rt.packs.uninstall,
        "revoke": rt.packs.revoke,
    }[action]
    try:
        rec = fn(pack_id, version)
    except ExtensionAuthzError as exc:
        raise _pack_error(exc) from exc
    _audit(request, principal, f"pack.{action}", None, pack_id=pack_id)
    return rec.model_dump(mode="json")


@router.get("/packs/{pack_id}/{version}/history")
async def pack_history(
    pack_id: str,
    version: str,
    principal: Principal = Depends(get_principal),
    rt: V23Runtime = Depends(get_v23),
) -> dict[str, Any]:
    _require_admin(principal)
    try:
        return {"history": rt.packs.history(pack_id, version)}
    except ExtensionAuthzError as exc:
        raise _pack_error(exc) from exc


# ------------------------------------------------------------------ portability
class ImportRequest(StrictModel):
    bundle_id: str


def _bundle_dir(request: Request) -> Path:
    return Path(request.app.state.repo_root) / "var" / "portability"


@router.post("/projects/{project_id}/export")
async def project_export(
    project_id: str,
    request: Request,
    principal: Principal = Depends(get_principal),
    auth: AuthRegistry = Depends(get_auth),
    rt: V23Runtime = Depends(get_v23),
) -> dict[str, Any]:
    auth.require_project(principal, project_id)
    queue = [q for q in rt.scheduler.queues() if q["project_id"] == project_id]
    receipts = rt.scheduler.store.list_receipts(project_id=project_id, limit=1000)
    try:
        bundle = rt.portability.export_project(
            project_id=project_id,
            project_config={"project_id": project_id, "scheduler": queue[0] if queue else {}},
            receipts=[r.model_dump(mode="json") for r in receipts],
            out_dir=_bundle_dir(request),
        )
    except ValueError as exc:
        raise ApiError("export_rejected", str(exc), status_code=422) from exc
    _audit(request, principal, "portability.export", project_id, bundle_id=bundle.bundle_id)
    return {
        "bundle_id": bundle.bundle_id,
        "project_id": bundle.project_id,
        "integrity_digest": bundle.integrity_digest,
        "schema_version": bundle.schema_version,
    }


@router.post("/projects/{project_id}/import")
async def project_import(
    project_id: str,
    body: ImportRequest,
    request: Request,
    principal: Principal = Depends(get_principal),
    auth: AuthRegistry = Depends(get_auth),
    rt: V23Runtime = Depends(get_v23),
) -> dict[str, Any]:
    auth.require_project(principal, project_id)
    if not _BUNDLE_ID.match(body.bundle_id):
        raise ApiError("invalid_bundle_id", "bundle id has an invalid shape", status_code=422)
    path = _bundle_dir(request) / f"{body.bundle_id}.json"
    if not path.is_file():
        raise ApiError("not_found", "bundle not found", status_code=404)
    try:
        source = str(json.loads(path.read_text(encoding="utf-8")).get("project_id") or "")
    except (OSError, json.JSONDecodeError) as exc:
        raise ApiError("bundle_rejected", "bundle unreadable", status_code=422) from exc
    auth.require_project(principal, source)
    try:
        bundle = rt.portability.import_bundle(path, target_project_id=project_id)
    except ValueError as exc:
        raise ApiError("bundle_rejected", str(exc), status_code=422) from exc
    _audit(request, principal, "portability.import", project_id, bundle_id=body.bundle_id)
    return {"bundle_id": bundle.bundle_id, "project_id": bundle.project_id, "imported": True}


# ------------------------------------------------------------------ fleet
class PlaceRequest(StrictModel):
    project_id: str
    preferred_locality: str | None = None
    min_trust: str = "compute_only"


@router.post("/fleet/place")
async def fleet_place(
    body: PlaceRequest,
    principal: Principal = Depends(get_principal),
    auth: AuthRegistry = Depends(get_auth),
    rt: V23Runtime = Depends(get_v23),
) -> dict[str, Any]:
    auth.require_project(principal, body.project_id)
    try:
        decision = rt.fleet.place(
            project_id=body.project_id,
            preferred_locality=body.preferred_locality,
            min_trust=body.min_trust,
        )
    except FleetError as exc:
        raise ApiError("placement_rejected", str(exc), status_code=409) from exc
    return decision.to_dict()


@router.get("/fleet/audit")
async def fleet_audit(
    principal: Principal = Depends(get_principal),
    rt: V23Runtime = Depends(get_v23),
) -> dict[str, Any]:
    _require_admin(principal)
    return {"events": rt.fleet.audit_log()}


# ------------------------------------------------------------------ worker control
class WorkerControlRequest(StrictModel):
    reason: str = Field(min_length=1, max_length=500)


def _get_store(request: Request) -> ProductStore:
    return request.app.state.store  # type: ignore[no-any-return]


def _worker_in_scope(store: ProductStore, principal: Principal, worker_id: str) -> str | None:
    rec = store.workers._workers.get(worker_id)  # noqa: SLF001 — shared registry
    if rec is None:
        raise ApiError("not_found", "worker not found", status_code=404)
    if "admin" in principal.roles:
        return rec.project_id
    # Unscoped (fleet-level) workers are admin-only.
    if not rec.project_id or rec.project_id not in principal.project_ids:
        raise ApiError("forbidden_project", "worker not in project scope", status_code=403)
    return rec.project_id


@router.post("/workers/{worker_id}/drain")
async def worker_drain_v23(
    worker_id: str,
    body: WorkerControlRequest,
    request: Request,
    principal: Principal = Depends(get_principal),
    rt: V23Runtime = Depends(get_v23),
) -> dict[str, Any]:
    store = _get_store(request)
    project_id = _worker_in_scope(store, principal, worker_id)
    try:
        state = rt.fleet.set_drain_state(worker_id, WorkerDrainState.DRAINING)
    except FleetError as exc:
        raise ApiError("drain_rejected", str(exc), status_code=409) from exc
    store.workers.operator_drain(worker_id)
    store._persist_durable_workers()  # noqa: SLF001
    _audit(request, principal, "worker.drain", project_id, worker_id=worker_id, reason=body.reason)
    return {"worker_id": worker_id, "drain_state": state.value}


@router.post("/workers/{worker_id}/revoke")
async def worker_revoke_v23(
    worker_id: str,
    body: WorkerControlRequest,
    request: Request,
    principal: Principal = Depends(get_principal),
    rt: V23Runtime = Depends(get_v23),
) -> dict[str, Any]:
    store = _get_store(request)
    project_id = _worker_in_scope(store, principal, worker_id)
    try:
        state = rt.fleet.set_drain_state(worker_id, WorkerDrainState.REVOKED)
    except FleetError as exc:
        raise ApiError("revoke_rejected", str(exc), status_code=409) from exc
    await store.workers.revoke_generation(worker_id)
    store._persist_durable_workers()  # noqa: SLF001
    _audit(request, principal, "worker.revoke", project_id, worker_id=worker_id, reason=body.reason)
    return {"worker_id": worker_id, "drain_state": state.value}
