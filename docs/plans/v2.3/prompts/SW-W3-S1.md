# SW-W3-S1 — API routes_v23 (scheduler/ops/trace/packs/portability/fleet/worker drain+revoke) + app wiring

Copy this whole file into a fresh Cursor session opened on the **swarmai** repository. Follow it top to bottom. It is self-contained: do not read other plans to decide what to do.

| Field | Value |
|---|---|
| Session ID | `SW-W3-S1` |
| Repository | `pri8771/swarmai` (GitHub remote `origin`; **public** repo) |
| Base branch | `cursor/sw-v23-integration-460c` — always the **current** `origin/cursor/sw-v23-integration-460c` (plan baseline `dev` @ `8e1c0fde`) |
| Your branch | `cursor/v23-w3-s1-api-routes` |
| Branch-suffix rule | If your environment forces a suffix (for example `-460c`), append it **once** to *your* branch and write the exact final name in the handoff. Never add a suffix to `cursor/sw-v23-integration-460c`: it already ends in `-460c`. |
| PR target | `cursor/sw-v23-integration-460c` — **draft** PR. Never `dev`, never `main`. |
| Wave | 3 |
| Depends on | SW-W2-S1, SW-W1-S5, SW-W1-S6, SW-W1-S7, SW-W1-S8, SW-W0-S3 |
| Handoff file | `docs/v2.3/sessions/SW-W3-S1.md` |
| Independent reviewer | Codex (owner decision D2). You never accept your own work. |
| Plan | `docs/plans/v2.3/PLAN.md`; owner preflight `docs/plans/v2.3/OWNER_PREFLIGHT.md`; decisions `docs/swarm-mvp/DECISIONS.md` |

## 0. Hard rules (read twice)
1. Edit **only** the files listed in “Files you own” plus your handoff file. If another file must change, do not change it: write the exact change under “Needs other owner” in the handoff.
2. Never push to, or merge into, `main`, `dev` or `cursor/sw-v23-integration-460c`. Never merge any PR, never force-push, never rewrite history, never delete branches. Only the wave MERGE prompts (`SW-MERGE-*`) push to `cursor/sw-v23-integration-460c`.
3. Zero spend: no real model/provider calls, no paid APIs, no account creation, no deploys. `SWARM_ALLOW_PAID` stays `false`. Tests use fakes only.
4. Never commit or print secrets, tokens, `.env` files, customer data or raw logs. Test tokens are fake literals such as `atk_policy_demo`. Check environment variables only with `test -n "$NAME"`.
5. Passing tests are *not* acceptance. Never write “accepted”, “complete”, “released” or “V2.3 done”. Use “implemented” and “tested”.
6. `src/swarm/contracts/v23.py`, `src/swarm/db/models.py` and `migrations/` belong to SW-W0-S2. Import from them; never edit them (unless you *are* SW-W0-S2).
7. Do not edit `.github/workflows/`, `pyproject.toml`, `uv.lock`, `package.json` or lockfiles.
8. If a step can be read two ways, choose the reading that changes fewer lines inside your own files, and write the choice under “Decisions” in the handoff.

## 1. Setup
```bash
git status --porcelain            # must print nothing; otherwise STOP (S1)
git fetch origin cursor/sw-v23-integration-460c
git ls-remote --exit-code origin refs/heads/cursor/sw-v23-integration-460c >/dev/null && echo INTEG_OK || echo INTEG_MISSING
```
If it prints `INTEG_MISSING`, STOP (S2): SW-W0-S1 or the executor creates it.
```bash
git checkout -b cursor/v23-w3-s1-api-routes origin/cursor/sw-v23-integration-460c
git log -1 --format='%H %s'       # record this SHA in the handoff as 'base'
command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh   # then: export PATH=$HOME/.local/bin:$PATH
uv sync
git clean -fdX -- var/
```

## 2. Dependency and environment check
Depends on: SW-W2-S1, SW-W1-S5, SW-W1-S6, SW-W1-S7, SW-W1-S8, SW-W0-S3. Their PRs must already be merged into `cursor/sw-v23-integration-460c` (by the wave MERGE prompt).
Run every command below. Each must print `OK`. If any prints `MISSING`, STOP (condition S2 in section 10).

```bash
git fetch origin cursor/sw-v23-integration-460c
git cat-file -e origin/cursor/sw-v23-integration-460c:src/swarm/scheduling/service.py && echo "OK src/swarm/scheduling/service.py" || echo "MISSING src/swarm/scheduling/service.py"
git cat-file -e origin/cursor/sw-v23-integration-460c:src/swarm/capabilities/lifecycle.py && echo "OK src/swarm/capabilities/lifecycle.py" || echo "MISSING src/swarm/capabilities/lifecycle.py"
git cat-file -e origin/cursor/sw-v23-integration-460c:src/swarm/capabilities/signing.py && echo "OK src/swarm/capabilities/signing.py" || echo "MISSING src/swarm/capabilities/signing.py"
git cat-file -e origin/cursor/sw-v23-integration-460c:src/swarm/observability/trace_graph.py && echo "OK src/swarm/observability/trace_graph.py" || echo "MISSING src/swarm/observability/trace_graph.py"
git cat-file -e origin/cursor/sw-v23-integration-460c:tests/api/test_v23_ops_events_scope.py && echo "OK tests/api/test_v23_ops_events_scope.py" || echo "MISSING tests/api/test_v23_ops_events_scope.py"
```

This session needs **no** secrets or environment variables.

## 3. Files you own (the ONLY files you may create or modify)
- `src/swarm/api/routes_v23.py` — create
- `src/swarm/api/app.py` — modify
- `tests/api/test_v23_routes.py` — create
- `tests/integration/db/test_v23_routes_durable_sql.py` — create
- `docs/v2.3/sessions/SW-W3-S1.md` — create (your handoff)

## 4. Do NOT touch
- Any file not listed in section 3 (in particular: `src/swarm/api/app.py`, `src/swarm/api/store.py`, `src/swarm/cli.py`, `src/swarm/db/models.py`, `migrations/`, `docs/agents/*`, `docs/plans/v2.3/*`, `CHANGELOG.md`, `README.md`, `.github/`, unless listed above).
- The `inference_server` repository: read-only, and only through the commands in section 5.
- The branches `main`, `dev`, `cursor/sw-v23-integration-460c`, `cursor/v23-plan-460c`, and any other session's branch.
- Generated files that tests rewrite: `schemas/v1/*`, `docs/evidence/fix-004/*`, `var/*` — always restore them before committing (section 6).

## 5. Steps
**Goal.** Expose the Wave-1/Wave-2 V2.3 services over HTTP in one new router module, `src/swarm/api/routes_v23.py`, and wire it into `create_app`.

**Security rules** (tests enforce each one):
- Every route resolves a `Principal` through `get_principal`.
- Project-level routes call `auth.require_project(principal, project_id)` **before** reading or writing.
- Admin-only: pack install, drain, disable, uninstall, revoke and history; fleet audit; scheduler receipts without a `project_id`.
- `GET /v1/scheduler/queues` shows a non-admin only their own projects.
- `GET /v1/ops/trace/{id}` returns **404, not 403**, when any node belongs to a foreign project, so a foreign trace's existence is never confirmed.
- Portability import checks the **target** and **source** projects, and rejects any `bundle_id` that does not match `^port_[A-Za-z0-9_-]{1,64}$`. This blocks path traversal.
- Worker drain/revoke: a worker with no `project_id` (fleet-level) is admin-only. This is stricter than the legacy `/v1/workers/drain`, which stays unchanged.
- The pack registry is built with `require_signature=True, trusted_keys=trusted_keys_from_env()`, so unsigned or untrusted packs are refused.
- The API runtime **never dispatches**. Its scheduler's reserve function raises `api_runtime_has_no_broker`, so a stray `schedule_once` defers and reserves nothing.
- Every mutation emits an `operator.action` ops event containing the actor subject; the sink redacts secrets.
- Durable state (`SqlSchedulingStore`, `SqlSchedulerEpochService`, `SqlPackInstallStore`, `SqlOpsSink`) is used **only** when `SWARM_V23_DURABLE=1` **and** the database is reachable. Otherwise everything is in memory, as today.

**API shapes** (the SW-W1-S12 console codes against these; do not change them):

| Method and path | Response |
|---|---|
| `GET /v1/scheduler/queues` | `{"projects":[{project_id, tenant_id, weight, credit, running, max_concurrency, paused, version}]}` |
| `GET /v1/scheduler/receipts?project_id=&limit=` | `{"receipts":[...]}` |
| `POST /v1/scheduler/projects/{pid}` body `{weight?, max_concurrency?}` | project state |
| `POST /v1/scheduler/projects/{pid}/weight` body `{weight>0}` | project state |
| `POST /v1/scheduler/projects/{pid}/pause` or `/resume` | project state |
| `GET /v1/ops/trace/{trace_id}` | `TraceGraph.to_dict()` |
| `POST /v1/packs/install` body `{manifest}` | install record (admin) |
| `POST /v1/projects/{pid}/packs/{pack}/{ver}/enable` body `{capabilities:[...]}` | project install record |
| `POST /v1/packs/{pack}/{ver}/drain` (or `disable`, `uninstall`, `revoke`) | install record (admin) |
| `GET /v1/packs/{pack}/{ver}/history` | `{"history":[...]}` (admin) |
| `POST /v1/projects/{pid}/export` | `{bundle_id, project_id, integrity_digest, schema_version}` |
| `POST /v1/projects/{pid}/import` body `{bundle_id}` | `{bundle_id, project_id, imported:true}` |
| `POST /v1/fleet/place` body `{project_id, preferred_locality?, min_trust?}` | placement decision |
| `GET /v1/fleet/audit` | `{"events":[...]}` (admin) |
| `POST /v1/workers/{worker_id}/drain` or `/revoke` body `{reason}` | `{"worker_id","drain_state"}` |

The code below was compiled and run against `dev @ 8e1c0fde` plus every Wave-1/Wave-2 change. `tests/api/test_v23_routes.py` gives 7 passed, the durable integration test gives 1 passed, `tests/api tests/product` all pass, and ruff and mypy are clean. Paste it **exactly**.

### Step 1 — `src/swarm/api/routes_v23.py` (create, exactly)
```python
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
```

### Step 2 — `src/swarm/api/app.py` (replace the whole file, exactly)
First run `git diff 8e1c0fdec24c131e7612d88076220945230f4c3b -- src/swarm/api/app.py`; it must print nothing. The change against that baseline is only:
- two new import lines for `routes_v23`;
- `OpsEventLog, SqlOpsSink` in the local import;
- the `v23_factory` / `app.state.v23` block right after the `ops_events` line;
- `app.include_router(v23_router)` after `app.include_router(v1_router)`.

If `app.py` on your base differs from what this file implies, apply just those four edits by hand instead; if any of the four anchor lines is missing, STOP (S4, section 10).
```python
"""FastAPI application — health, auth, /v1 product API."""

from __future__ import annotations

import json
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from swarm import __version__
from swarm.api.auth import AuthRegistry
from swarm.api.errors import ApiError, api_error_handler
from swarm.api.routes_v1 import router as v1_router
from swarm.api.routes_v23 import build_v23_runtime, v23_session_factory
from swarm.api.routes_v23 import router as v23_router
from swarm.api.store import ProductStore
from swarm.contracts.common import new_id


def _install_identity_path(repo_root: Path) -> Path:
    return repo_root / "var" / "install" / "identity.json"


def resolve_install_project_id(repo_root: Path) -> str:
    """Per-install project id — never hard-codes proj_demo/proj_other.

    Order:
    1. SWARM_INSTALL_PROJECT_ID env (explicit operator mapping)
    2. Persisted var/install/identity.json
    3. Generate and persist a new install-local id
    """
    env_id = (os.environ.get("SWARM_INSTALL_PROJECT_ID") or "").strip()
    if env_id:
        if env_id in {"proj_demo", "proj_other"}:
            raise ApiError(
                "invalid_install_project",
                "SWARM_INSTALL_PROJECT_ID must not use demo project ids",
                status_code=500,
            )
        return env_id

    path = _install_identity_path(repo_root)
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            pid = str(data.get("project_id") or "").strip()
            if pid and pid not in {"proj_demo", "proj_other"}:
                return pid
        except (OSError, json.JSONDecodeError, TypeError):
            pass

    project_id = new_id("proj_install_")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "project_id": project_id,
                "subject": "install-operator",
                "note": "install-local identity — not demo fixture membership",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return project_id


def create_app(
    *,
    require_auth: bool = True,
    seed_loopback_token: str | None = None,
    seed_fixtures: bool = False,
    db_reachable: bool | None = None,
    repo_root: Path | None = None,
    install_project_id: str | None = None,
) -> FastAPI:
    app = FastAPI(title="SwarmAI", version=__version__)
    app.add_exception_handler(ApiError, api_error_handler)  # type: ignore[arg-type]
    # Private console on loopback only — not a public deployment surface.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1:43127",
            "http://localhost:43127",
            "http://127.0.0.1:4177",
            "http://localhost:4177",
            # Product-compose console publishes host 43127 → container 8080;
            # Vite preview / alternate local binds may use 8080 directly.
            "http://127.0.0.1:8080",
            "http://localhost:8080",
        ],
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Idempotency-Key", "Accept"],
    )

    root = repo_root
    if root is None:
        env_root = (os.environ.get("SWARM_REPO_ROOT") or "").strip()
        if env_root:
            root = Path(env_root)
        else:
            # Prefer package-adjacent repo root (…/swarm-ai) for editable checkouts.
            root = Path(__file__).resolve().parents[3]

    if db_reachable is None and (os.environ.get("SWARM_DATABASE_URL") or "").strip():
        # Probe only when an explicit DSN is configured (secret-drop / .env).
        try:
            from swarm.db.engine import create_db_engine, ping

            db_reachable = ping(create_db_engine())
        except Exception:
            db_reachable = False

    store = ProductStore(db_reachable=db_reachable, repo_root=root)
    store.bootstrap_durable()
    if seed_fixtures:
        store.seed_catalog()
        store.fixture_mode = True
        store.execution_mode = "mock"
    auth = AuthRegistry(require_auth=require_auth)
    if seed_loopback_token:
        if seed_fixtures:
            # Fixture/test bootstrap may use known demo project membership.
            auth.issue(
                subject="loopback-operator",
                project_ids={"proj_demo", "proj_other"},
                roles={"operator"},
                allow_canary=False,
                allow_eval=False,
                token=seed_loopback_token,
            )
        else:
            # Operational bootstrap: install-local project only — no demo IDs.
            project_id = install_project_id or resolve_install_project_id(root)
            auth.issue(
                subject="install-operator",
                project_ids={project_id},
                roles={"operator"},
                allow_canary=False,
                allow_eval=False,
                token=seed_loopback_token,
            )
            app.state.install_project_id = project_id
        auth.loopback_mock_token = seed_loopback_token
    if seed_fixtures:
        # Explicit test/fixture seeding — separate from operational bootstrap.
        auth.issue(
            subject="policy-operator",
            project_ids={"proj_demo"},
            roles={"operator"},
            allow_canary=True,
            allow_eval=True,
            token="atk_policy_demo",
        )
        auth.issue(
            subject="other-project-user",
            project_ids={"proj_other"},
            roles={"operator"},
            token="atk_other_project",
        )
        if seed_loopback_token is None:
            # Tests that only set seed_fixtures still need a demo loopback principal.
            auth.issue(
                subject="loopback-operator",
                project_ids={"proj_demo", "proj_other"},
                roles={"operator"},
                allow_canary=False,
                allow_eval=False,
                token="atk_loopback_demo",
            )
            auth.loopback_mock_token = "atk_loopback_demo"

    app.state.store = store
    app.state.auth = auth
    app.state.repo_root = root
    from swarm.learning import LearningRepository
    from swarm.objectives import ObjectiveRepository
    from swarm.observability import OpsEventLog, SqlOpsSink

    app.state.objective_repo = ObjectiveRepository()
    app.state.learning_repo = LearningRepository()
    v23_factory = v23_session_factory(bool(db_reachable))
    app.state.ops_events = OpsEventLog(sink=SqlOpsSink(v23_factory) if v23_factory else None)
    app.state.v23 = build_v23_runtime(
        workers=store.workers, ops=app.state.ops_events, session_factory=v23_factory
    )
    if not hasattr(app.state, "install_project_id"):
        app.state.install_project_id = None

    @app.get("/health/live")
    async def live() -> dict[str, str]:
        return {"status": "ok", "service": "swarm", "version": __version__}

    @app.get("/health/ready")
    async def ready() -> dict[str, object]:
        return store.health_ready()

    app.include_router(v1_router)
    app.include_router(v23_router)
    return app


def _env_loopback_token() -> str | None:
    """Optional private install bootstrap. Empty/unset = no seeded identities."""
    raw = (os.environ.get("SWARM_SEED_LOOPBACK_TOKEN") or "").strip()
    return raw or None


app = create_app(seed_loopback_token=_env_loopback_token(), seed_fixtures=False)
```

### Step 3 — `tests/api/test_v23_routes.py` (create, exactly)
```python
"""SW-W3-S1: V2.3 routes are project-scoped and admin-gated."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from swarm.api.app import create_app
from swarm.capabilities import CapabilityPackManifest
from swarm.capabilities.signing import sign_manifest

DEMO = "atk_policy_demo"
OTHER = "atk_other_project"
ADMIN = "atk_admin_v23"
PACK_KEY = b"test-only-pack-key"


def _h(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("SWARM_V23_DURABLE", raising=False)
    monkeypatch.setenv("SWARM_PACK_TRUSTED_PUBLISHERS", "acme")
    monkeypatch.setenv("SWARM_PACK_KEY_ACME", PACK_KEY.decode())
    app = create_app(require_auth=True, db_reachable=False, seed_fixtures=True, repo_root=tmp_path)
    app.state.auth.issue(subject="site-admin", project_ids=set(), roles={"admin"}, token=ADMIN)
    with TestClient(app) as c:
        yield c


def _manifest(signed: bool) -> dict:
    m = CapabilityPackManifest(
        pack_id="pack_demo",
        version="1.0.0",
        content_digest="sha256:abc",
        capability_declarations=["read_docs"],
        publisher="acme",
    )
    return (sign_manifest(m, key=PACK_KEY) if signed else m).model_dump(mode="json")


def test_queues_are_project_scoped(client: TestClient) -> None:
    assert client.post("/v1/scheduler/projects/proj_demo", json={}, headers=_h(DEMO)).status_code == 200
    assert client.post("/v1/scheduler/projects/proj_other", json={}, headers=_h(OTHER)).status_code == 200
    rows = client.get("/v1/scheduler/queues", headers=_h(DEMO)).json()["projects"]
    assert [r["project_id"] for r in rows] == ["proj_demo"]
    assert {"weight", "credit", "running", "max_concurrency", "paused"} <= set(rows[0])
    admin_rows = client.get("/v1/scheduler/queues", headers=_h(ADMIN)).json()["projects"]
    assert {r["project_id"] for r in admin_rows} == {"proj_demo", "proj_other"}


def test_scheduler_mutations_require_project(client: TestClient) -> None:
    res = client.post("/v1/scheduler/projects/proj_other", json={}, headers=_h(DEMO))
    assert res.status_code == 403
    client.post("/v1/scheduler/projects/proj_demo", json={}, headers=_h(DEMO))
    res = client.post("/v1/scheduler/projects/proj_demo/weight", json={"weight": 3}, headers=_h(DEMO))
    assert res.status_code == 200 and res.json()["weight"] == 3.0
    assert client.post("/v1/scheduler/projects/proj_demo/pause", headers=_h(DEMO)).json()["paused"]
    assert client.post("/v1/scheduler/projects/proj_demo/bogus", headers=_h(DEMO)).status_code == 404
    unknown = client.post("/v1/scheduler/projects/proj_demo/weight", json={"weight": 0}, headers=_h(DEMO))
    assert unknown.status_code == 422
    assert client.get("/v1/scheduler/receipts", headers=_h(DEMO)).status_code == 403
    own = client.get("/v1/scheduler/receipts", params={"project_id": "proj_demo"}, headers=_h(DEMO))
    assert own.status_code == 200 and own.json() == {"receipts": []}


def test_trace_never_leaks_foreign_projects(client: TestClient) -> None:
    log = client.app.state.ops_events  # type: ignore[attr-defined]
    log.emit("operator.action", "api", project_id="proj_other", trace_id="tr_x")
    log.emit("operator.action", "api", project_id="proj_demo", trace_id="tr_mine")
    assert client.get("/v1/ops/trace/tr_x", headers=_h(DEMO)).status_code == 404
    assert client.get("/v1/ops/trace/tr_x", headers=_h(ADMIN)).status_code == 200
    mine = client.get("/v1/ops/trace/tr_mine", headers=_h(DEMO))
    assert mine.status_code == 200 and mine.json()["projects"] == ["proj_demo"]
    assert client.get("/v1/ops/trace/tr_none", headers=_h(ADMIN)).status_code == 404


def test_pack_install_requires_admin_and_signature(client: TestClient) -> None:
    signed = {"manifest": _manifest(signed=True)}
    assert client.post("/v1/packs/install", json=signed, headers=_h(DEMO)).status_code == 403
    unsigned = client.post("/v1/packs/install", json={"manifest": _manifest(False)}, headers=_h(ADMIN))
    assert unsigned.status_code == 403 and unsigned.json()["code"] == "pack_rejected"
    assert client.post("/v1/packs/install", json=signed, headers=_h(ADMIN)).status_code == 200
    body = {"capabilities": ["read_docs"]}
    url = "/v1/projects/{p}/packs/pack_demo/1.0.0/enable"
    assert client.post(url.format(p="proj_demo"), json=body, headers=_h(DEMO)).status_code == 200
    assert client.post(url.format(p="proj_other"), json=body, headers=_h(DEMO)).status_code == 403
    assert client.post("/v1/packs/pack_demo/1.0.0/revoke", headers=_h(DEMO)).status_code == 403
    assert client.post("/v1/packs/pack_demo/1.0.0/revoke", headers=_h(ADMIN)).status_code == 200
    hist = client.get("/v1/packs/pack_demo/1.0.0/history", headers=_h(ADMIN)).json()["history"]
    assert [h["action"] for h in hist] == ["install", "revoke"]


def test_portability_export_import_scoped(client: TestClient) -> None:
    res = client.post("/v1/projects/proj_demo/export", headers=_h(DEMO))
    assert res.status_code == 200
    bundle_id = res.json()["bundle_id"]
    ok = client.post("/v1/projects/proj_demo/import", json={"bundle_id": bundle_id}, headers=_h(DEMO))
    assert ok.status_code == 200 and ok.json()["imported"] is True
    stolen = client.post(
        "/v1/projects/proj_other/import", json={"bundle_id": bundle_id}, headers=_h(OTHER)
    )
    assert stolen.status_code == 403
    bad = client.post("/v1/projects/proj_demo/import", json={"bundle_id": "../x"}, headers=_h(DEMO))
    assert bad.status_code == 422
    assert client.post("/v1/projects/proj_other/export", headers=_h(DEMO)).status_code == 403


def test_worker_drain_and_revoke_are_scoped(client: TestClient) -> None:
    enrolled = client.post("/v1/workers/enroll", json={"project_id": "proj_demo"}, headers=_h(DEMO))
    assert enrolled.status_code == 200
    wid = enrolled.json()["worker"]["worker_id"]
    body = {"reason": "maintenance"}
    assert client.post(f"/v1/workers/{wid}/drain", json=body, headers=_h(OTHER)).status_code == 403
    drained = client.post(f"/v1/workers/{wid}/drain", json=body, headers=_h(DEMO))
    assert drained.json() == {"worker_id": wid, "drain_state": "draining"}
    revoked = client.post(f"/v1/workers/{wid}/revoke", json=body, headers=_h(DEMO))
    assert revoked.json() == {"worker_id": wid, "drain_state": "revoked"}
    assert client.post(f"/v1/workers/{wid}/drain", json=body, headers=_h(DEMO)).status_code == 409
    assert client.post("/v1/workers/wk_nope/drain", json=body, headers=_h(DEMO)).status_code == 404
    kinds = [e["detail"]["action"] for e in client.get("/v1/ops/events", headers=_h(DEMO)).json()["events"]]
    assert kinds == ["worker.drain", "worker.revoke"]


def test_fleet_audit_is_admin_only(client: TestClient) -> None:
    assert client.get("/v1/fleet/audit", headers=_h(DEMO)).status_code == 403
    assert client.get("/v1/fleet/audit", headers=_h(ADMIN)).status_code == 200
```

### Step 4 — `tests/integration/db/test_v23_routes_durable_sql.py` (create, exactly)
```python
"""SW-W3-S1: with SWARM_V23_DURABLE=1 scheduler, pack and ops state survive an app restart."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from swarm.api.app import create_app
from swarm.db.engine import create_db_engine, ping
from swarm.db.models import Base

pytestmark = pytest.mark.integration

DATABASE_URL = os.environ.get(
    "SWARM_DATABASE_URL", "postgresql+psycopg://swarm:swarm@127.0.0.1:5432/swarm"
)
TABLES = (
    "v23_project_queue_state",
    "v23_mission_queue_state",
    "v23_scheduler_receipts",
    "v23_dispatch_intents",
    "v23_scheduler_epochs",
    "v23_pack_installs",
    "v23_ops_events",
)
DEMO = {"Authorization": "Bearer atk_policy_demo"}


@pytest.fixture()
def durable_env(monkeypatch: pytest.MonkeyPatch):
    eng = create_db_engine(DATABASE_URL)
    try:
        ping(eng)
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"postgres_unavailable:{type(exc).__name__}")
    Base.metadata.create_all(eng)
    with eng.begin() as conn:
        conn.execute(text("TRUNCATE " + ", ".join(TABLES)))
    monkeypatch.setenv("SWARM_DATABASE_URL", DATABASE_URL)
    monkeypatch.setenv("SWARM_V23_DURABLE", "1")
    yield
    eng.dispose()


def _app(root: Path):
    return create_app(require_auth=True, db_reachable=True, seed_fixtures=True, repo_root=root)


def test_scheduler_and_ops_state_survive_restart(durable_env, tmp_path: Path) -> None:
    first = _app(tmp_path)
    assert first.state.v23.durable is True
    with TestClient(first) as c:
        c.post("/v1/scheduler/projects/proj_demo", json={}, headers=DEMO)
        c.post("/v1/scheduler/projects/proj_demo/weight", json={"weight": 2.5}, headers=DEMO)
    second = _app(tmp_path)
    with TestClient(second) as c:
        rows = c.get("/v1/scheduler/queues", headers=DEMO).json()["projects"]
        events = c.get("/v1/ops/events", params={"project_id": "proj_demo"}, headers=DEMO)
    assert [(r["project_id"], r["weight"]) for r in rows] == [("proj_demo", 2.5)]
    actions = [e["detail"]["action"] for e in events.json()["events"]]
    assert actions == ["scheduler.register", "scheduler.weight"]
```

### Step 5 — run
```bash
git clean -fdX -- var/
uv run pytest tests/api/test_v23_routes.py -q                               # 7 passed
uv run pytest tests/integration/db/test_v23_routes_durable_sql.py -q        # 1 passed (skips if no Postgres)
uv run pytest tests/api tests/product -q
```
If an import fails (for example `swarm.scheduling.service`, `swarm.capabilities.lifecycle` or `swarm.observability.build_trace`), a dependency session has not been merged. STOP (S2, section 10); do **not** write stand-in modules.

## 6. Verify (run exactly; all must pass)
```bash
git clean -fdX -- var/            # F-15: stale runtime state breaks re-runs
# Private database for this session: concurrent sessions on one host must never share one.
sudo -u postgres psql -c "CREATE DATABASE swarm_sw_w3_s1 OWNER swarm;" || true
export SWARM_DATABASE_URL=postgresql+psycopg://swarm:swarm@127.0.0.1:5432/swarm_sw_w3_s1
uv run ruff check .
uv run mypy src/swarm
uv run alembic heads               # must print exactly ONE line ending in (head)
uv run pytest tests/api tests/product -q
uv run pytest tests/contracts tests/spikes tests/api tests/broker tests/controller tests/chaos tests/deployment tests/evals tests/extensions tests/foundation tests/goals tests/pursuit tests/sdk tests/knowledge tests/load tests/memory tests/mission tests/objectives tests/onboarding tests/product tests/providers tests/recovery tests/regressions tests/release tests/runtime tests/selfdev tests/tools tests/ui tests/workers tests/workspace tests/e2e tests/acceptance tests/portability -q --ignore=tests/integration

# PostgreSQL integration (install steps in “PostgreSQL” below)
uv run pytest tests/integration -q -m integration

git checkout -- schemas/v1 docs/evidence/fix-004 var   # tests rewrite these tracked files
git status --porcelain            # every path listed must be one of YOUR files
```

### PostgreSQL (for the integration line)
```bash
pg_isready -h 127.0.0.1 || {
  sudo apt-get update && sudo apt-get install -y postgresql && sudo service postgresql start
  sudo -u postgres psql -c "CREATE USER swarm WITH PASSWORD 'swarm' SUPERUSER;" || true
}
```
Run this block before section 6. Section 6 creates your private database and exports `SWARM_DATABASE_URL` for **both** pytest lines; never unset it and never point it at the shared `swarm` database.
If `pg_isready -h 127.0.0.1` still fails after running this block twice, write `integration: SKIPPED (postgres unavailable: <last error line>)` in the handoff and continue. Never claim integration passed without running it.

## 7. Acceptance checklist (tick every box in the handoff)
- [ ] Every step in section 5 done; every acceptance box in section 5 ticked.
- [ ] `uv run ruff check .` and `uv run mypy src/swarm` pass.
- [ ] `uv run alembic heads` prints exactly one head.
- [ ] Full offline CI list passes (paste the final `N passed` line into the handoff).
- [ ] Integration run passed, or SKIPPED with reason in the handoff.
- [ ] `git status --porcelain` lists only files from section 3 + the handoff.
- [ ] No secrets, no network calls beyond section 5, no `accepted`/`complete` claims.
- [ ] The Codex review packet (section 11) is in the PR description and the handoff.

## 8. Commit, push, draft PR
```bash
git checkout -- schemas/v1 docs/evidence/fix-004 var
git add src/swarm/api/routes_v23.py src/swarm/api/app.py tests/api/test_v23_routes.py tests/integration/db/test_v23_routes_durable_sql.py docs/v2.3/sessions/SW-W3-S1.md
git status --porcelain            # nothing unexpected staged or left over
git commit -m "feat(v2.3): /v1 scheduler, ops trace, packs, portability, fleet and worker drain/revoke routes" -m "Session: SW-W3-S1. Plan: docs/plans/v2.3/PLAN.md."
git push -u origin cursor/v23-w3-s1-api-routes
gh pr create --draft --base cursor/sw-v23-integration-460c --head cursor/v23-w3-s1-api-routes --title "[SW-W3-S1] API routes_v23 (scheduler/ops/trace/packs/portability/fleet/worker drain+revoke) + app wiring" --body-file docs/v2.3/sessions/SW-W3-S1.md
git ls-remote origin refs/heads/cursor/v23-w3-s1-api-routes   # must print the same SHA as: git rev-parse HEAD
```
If `gh pr create` is refused (read-only `gh`), the environment opens the PR: check that its base is `cursor/sw-v23-integration-460c` and that it is a draft, and put the PR URL (or the compare URL from section 10, step 4) into the handoff.
If push fails for network reasons, retry up to 4 times waiting 4 s, 8 s, 16 s, 32 s; then STOP (S8).
Docs to update: only your handoff file, plus any doc listed in section 3.

## 9. Handoff file (create before committing)
Create `docs/v2.3/sessions/SW-W3-S1.md` with exactly these headings:
```markdown
# SW-W3-S1 handoff
- Branch: <exact branch name>   Base SHA: <from setup>   Head SHA: <git rev-parse HEAD>
- PR: <url, or compare URL>
## Done
<bullet list of what you implemented>
## Verification
<each command from section 6 and its final result line; integration PASSED/SKIPPED(reason)>
## Acceptance
<copy the checkboxes from sections 5 and 7, ticked>
## Decisions
<choices you made under hard rule 8, or 'none'>
## Needs other owner
<files outside your scope that should change, with the exact change; or 'none'>
## Codex review packet
<the block from section 11, filled in>
## Status
implemented + tested (NOT accepted; needs Codex review)
```

## 10. STOP conditions (never wait for a human)
STOP immediately when any of these is true:
- **S1** `git status --porcelain` is not empty before Setup. (Do not commit, stash or discard anything; skip steps 1–4 below and only report.)
- **S2** a dependency check prints `MISSING`.
- **S3** a command in section 6, or a check in section 5, still fails after **2 attempts**. One attempt = one edit to *your own files* followed by re-running the failing command.
- **S4** a “currently reads” / before-block in section 5 does not match the file, or a function named in section 5 does not exist.
- **S5** finishing would require editing a file that is not in section 3.
- **S6** a required environment variable prints `MISSING`.
- **S7** an external gate check (inference_server sync point or approval line) in section 5 fails.
- **S8** `git push` still fails after 4 retries (waits 4 s, 8 s, 16 s, 32 s).

What to do on STOP, in this order:
1. Commit whatever is complete inside your own files: `git add <your files> docs/v2.3/sessions/SW-W3-S1.md` then `git commit -m "WIP(SW-W3-S1): <one-line reason>"`.
2. Write the handoff (section 9) with `## Status` = `BLOCKED: <condition id> <one-line reason>`, and under `## Needs other owner` the exact file, function and change you need. Commit it.
3. Push: `git push -u origin cursor/v23-w3-s1-api-routes` (plus your suffix).
4. Open the draft PR against `cursor/sw-v23-integration-460c` with the title prefix `[BLOCKED]`, or record the compare URL `https://github.com/pri8771/swarmai/compare/cursor/sw-v23-integration-460c...cursor/v23-w3-s1-api-routes?expand=1` in the handoff.
5. End the session with a final message: the condition id, the reason, the branch and the head SHA.
Never work around a STOP by editing other files, weakening tests, or adding `skip`/`xfail`.

If `tests/tools/test_v20_cancel_killbound.py` fails once in the full run and you did not touch `sandbox_runner.py` or that test, re-run the full list once. If it passes, record both result lines in the handoff under Verification and continue; if it fails twice, STOP (S3). (The known race was fixed by SW-FIX-FLAKE; a new failure is worth reporting.)

## 11. Codex review packet (put this in the PR description and in the handoff)
```markdown
### Codex review packet — SW-W3-S1
- PR: <PR URL — fill in after the PR exists>
- Branch: <exact branch name>  Base: origin/cursor/sw-v23-integration-460c @ <base SHA from Setup>
- Head SHA: <output of `git rev-parse HEAD`; must equal `git ls-remote origin refs/heads/<branch>`>
- Diff for review: `git diff <base SHA>...<head SHA>`
- Files to review: `src/swarm/api/routes_v23.py`, `src/swarm/api/app.py`, `tests/api/test_v23_routes.py`, `tests/integration/db/test_v23_routes_durable_sql.py`, `docs/v2.3/sessions/SW-W3-S1.md`
- Review focus (AGENTS.md Code Review Rules): cross-tenant/project access; secret disclosure; financial accounting (unknown usage or cost is never zero); unbounded retries; silently changed model behaviour; recovery gaps after a crash/restart; unsupported release claims ("accepted", "complete"). Session-specific: every route checks project scope; admin-only routes; drain/revoke audited.
- Checks run: <paste the final result line of every command in section 6>
- Verdict requested: `RECOMMEND_ACCEPT <head SHA>` or `REQUEST_CHANGES` with file:line findings.
```
