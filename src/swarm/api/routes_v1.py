"""Authenticated /v1 product routes."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, Query, Request
from fastapi.responses import StreamingResponse

from swarm.api.auth import AuthRegistry, Principal, get_auth, get_principal
from swarm.api.errors import ApiError
from swarm.api.schemas import (
    ApprovalResolveRequest,
    CancelRequest,
    EvaluationCreateRequest,
    MissionCreateRequest,
    PageMeta,
    ProbeRequest,
    ProjectCreateRequest,
    ProjectUpdateRequest,
    WorkerEnrollRequest,
    WorkerHeartbeatRequest,
)
from swarm.api.store import ProductStore
from swarm.contracts.common import new_id
from swarm.evals.plan import build_plan
from swarm.providers.catalog import list_providers

router = APIRouter(prefix="/v1")


def get_store(request: Request) -> ProductStore:
    return request.app.state.store  # type: ignore[no-any-return]


def _page(items: list[Any], *, limit: int, cursor: str | None) -> dict[str, Any]:
    return {
        "items": items,
        "page": PageMeta(limit=limit, cursor=cursor, has_more=len(items) >= limit).model_dump(),
    }


@router.post("/missions")
async def create_mission(
    body: MissionCreateRequest,
    principal: Principal = Depends(get_principal),
    auth: AuthRegistry = Depends(get_auth),
    store: ProductStore = Depends(get_store),
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> dict[str, Any]:
    key = body.idempotency_key or idempotency_key
    cached = store.recall_idempotent(key)
    if cached is not None:
        return cached
    auth.require_project(principal, body.mission.project_id)
    mission = await store.create_mission(body.mission, actor=principal.subject)
    result = {"mission": mission.model_dump(mode="json")}
    return store.store_idempotent(key, result)


@router.get("/missions/{mission_id}")
async def get_mission(
    mission_id: str,
    principal: Principal = Depends(get_principal),
    auth: AuthRegistry = Depends(get_auth),
    store: ProductStore = Depends(get_store),
) -> dict[str, Any]:
    mission = store.get_mission(mission_id)
    auth.require_project(principal, mission.project_id)
    return {"mission": mission.model_dump(mode="json")}


@router.post("/missions/{mission_id}/cancel")
async def cancel_mission(
    mission_id: str,
    body: CancelRequest | None = None,
    principal: Principal = Depends(get_principal),
    auth: AuthRegistry = Depends(get_auth),
    store: ProductStore = Depends(get_store),
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> dict[str, Any]:
    body = body or CancelRequest()
    key = body.idempotency_key or idempotency_key
    cached = store.recall_idempotent(key)
    if cached is not None:
        return cached
    mission = store.get_mission(mission_id)
    auth.require_project(principal, mission.project_id)
    cancelled = await store.cancel_mission(mission_id, actor=principal.subject)
    result = {"mission": cancelled.model_dump(mode="json")}
    return store.store_idempotent(key, result)


@router.get("/missions/{mission_id}/graph")
async def mission_graph(
    mission_id: str,
    principal: Principal = Depends(get_principal),
    auth: AuthRegistry = Depends(get_auth),
    store: ProductStore = Depends(get_store),
) -> dict[str, Any]:
    mission = store.get_mission(mission_id)
    auth.require_project(principal, mission.project_id)
    return store.graph_view(mission_id)


@router.get("/events")
async def list_events(
    after: str | None = None,
    project_id: str | None = None,
    mission_id: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    principal: Principal = Depends(get_principal),
    auth: AuthRegistry = Depends(get_auth),
    store: ProductStore = Depends(get_store),
) -> dict[str, Any]:
    if project_id:
        auth.require_project(principal, project_id)
    # Without project filter, only return events for principal's projects.
    events, cursor = store.events.list_after(
        project_id=project_id,
        mission_id=mission_id,
        after=after,
        limit=limit,
    )
    if project_id is None:
        allowed = principal.project_ids
        is_admin = "admin" in principal.roles
        events = [e for e in events if e.project_id in allowed or is_admin]
    return _page([e.model_dump(mode="json") for e in events], limit=limit, cursor=cursor)


@router.get("/events/stream")
async def stream_events(
    after: str | None = None,
    project_id: str | None = None,
    principal: Principal = Depends(get_principal),
    auth: AuthRegistry = Depends(get_auth),
    store: ProductStore = Depends(get_store),
) -> StreamingResponse:
    """SSE snapshot + continuation cursor (not a long-lived live broker)."""
    if project_id:
        auth.require_project(principal, project_id)

    async def gen() -> Any:
        events, cursor = store.events.list_after(project_id=project_id, after=after, limit=100)
        if project_id is None:
            allowed = principal.project_ids
            is_admin = "admin" in principal.roles
            events = [e for e in events if e.project_id in allowed or is_admin]
        for ev in events:
            yield f"id: {ev.id}\nevent: {ev.type}\ndata: {ev.model_dump_json()}\n\n"
        yield f"event: cursor\ndata: {{\"cursor\": \"{cursor or ''}\"}}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")


@router.get("/providers")
async def providers(
    principal: Principal = Depends(get_principal),
    store: ProductStore = Depends(get_store),
) -> dict[str, Any]:
    _ = principal
    return {
        "providers": list_providers(mode="mock"),
        "accounts": store.public_accounts(),
        "mock_vs_live": "catalog_and_fixtures_only",
    }


@router.get("/routes")
async def routes(
    principal: Principal = Depends(get_principal),
    store: ProductStore = Depends(get_store),
) -> dict[str, Any]:
    _ = principal
    return {"routes": store.public_routes(), "mock_vs_live": "fixtures_plus_retired_catalog"}


@router.get("/capacity")
async def capacity(
    purpose: str = "mission",
    principal: Principal = Depends(get_principal),
    store: ProductStore = Depends(get_store),
) -> dict[str, Any]:
    _ = principal
    return await store.capacity(purpose=purpose)


@router.post("/providers/{provider_id}/probe")
async def probe_provider(
    provider_id: str,
    body: ProbeRequest | None = None,
    principal: Principal = Depends(get_principal),
    store: ProductStore = Depends(get_store),
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> dict[str, Any]:
    body = body or ProbeRequest()
    if not principal.allow_canary:
        raise ApiError(
            "policy_denied",
            "provider probe requires explicit canary admission",
            status_code=403,
            details={"provider_id": provider_id},
        )
    key = body.idempotency_key or idempotency_key
    cached = store.recall_idempotent(key)
    if cached is not None:
        return cached
    # Offline: never call network; return blocked/unknown honestly.
    result = {
        "provider_id": provider_id,
        "status": "blocked",
        "reason": "offline_mock_no_network",
        "mock_vs_live": "probe_not_live",
        "purpose": body.purpose,
    }
    return store.store_idempotent(key, result)


@router.get("/qualifications")
async def qualifications(
    principal: Principal = Depends(get_principal),
    store: ProductStore = Depends(get_store),
) -> dict[str, Any]:
    _ = principal
    profiles = [p.model_dump(mode="json") for p in store.profiles.profiles.values()]
    return {"profiles": profiles, "policy_version": store.profiles.policy.policy_version}


@router.post("/evaluations")
async def create_evaluation(
    body: EvaluationCreateRequest,
    principal: Principal = Depends(get_principal),
    store: ProductStore = Depends(get_store),
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> dict[str, Any]:
    if not principal.allow_eval:
        raise ApiError(
            "policy_denied",
            "evaluations require explicit policy admission",
            status_code=403,
        )
    key = body.idempotency_key or idempotency_key
    cached = store.recall_idempotent(key)
    if cached is not None:
        return cached
    from pathlib import Path

    dataset = Path(__file__).resolve().parents[3] / "benchmarks" / "starter.jsonl"
    plan = build_plan(dataset, suite=body.suite, mode=body.mode, max_cases=body.max_cases)
    result = {
        "evaluation_id": new_id("eval_"),
        "plan": plan.to_dict(),
        "status": "planned",
        "mock_vs_live": "plan_only_not_executed_live",
    }
    return store.store_idempotent(key, result)


@router.get("/workers")
async def list_workers(
    principal: Principal = Depends(get_principal),
    store: ProductStore = Depends(get_store),
) -> dict[str, Any]:
    _ = principal
    return store.workers.inspect()


@router.post("/workers/enroll")
async def enroll_worker(
    body: WorkerEnrollRequest,
    principal: Principal = Depends(get_principal),
    auth: AuthRegistry = Depends(get_auth),
    store: ProductStore = Depends(get_store),
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> dict[str, Any]:
    key = body.idempotency_key or idempotency_key
    cached = store.recall_idempotent(key)
    if cached is not None:
        return cached
    auth.require_project(principal, body.project_id)
    lease, token = await store.enroll_worker(
        capabilities=body.capabilities,
        capacity_units=body.capacity_units,
        privacy_classes=body.privacy_classes,
        named_inference_urls=body.named_inference_urls,
        project_id=body.project_id,
        actor=principal.subject,
    )
    # Return membership token once; not a provider secret.
    result = {
        "worker": lease.model_dump(mode="json"),
        "membership_token": token,
        "mock_vs_live": "membership_only_no_provider_secrets",
    }
    return store.store_idempotent(key, result)


@router.post("/workers/heartbeat")
async def worker_heartbeat(
    body: WorkerHeartbeatRequest,
    principal: Principal = Depends(get_principal),
    store: ProductStore = Depends(get_store),
) -> dict[str, Any]:
    _ = principal
    lease = await store.workers.heartbeat(body.worker_id, body.generation, token=body.token)
    return {"worker": lease.model_dump(mode="json")}


@router.get("/approvals")
async def list_approvals(
    principal: Principal = Depends(get_principal),
    store: ProductStore = Depends(get_store),
) -> dict[str, Any]:
    _ = principal
    return {
        "approvals": [a.model_dump(mode="json") for a in store.approvals.values()],
    }


@router.post("/approvals/{approval_id}/resolve")
async def resolve_approval(
    approval_id: str,
    body: ApprovalResolveRequest,
    principal: Principal = Depends(get_principal),
    store: ProductStore = Depends(get_store),
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> dict[str, Any]:
    key = body.idempotency_key or idempotency_key
    cached = store.recall_idempotent(key)
    if cached is not None:
        return cached
    approval = store.resolve_approval(
        approval_id,
        accept=body.accept,
        actor=principal.subject,
        payload=body.payload,
    )
    result = {"approval": approval.model_dump(mode="json"), "accepted": body.accept}
    return store.store_idempotent(key, result)


@router.post("/missions/{mission_id}/side-effects/demo")
async def demo_side_effect(
    mission_id: str,
    principal: Principal = Depends(get_principal),
    auth: AuthRegistry = Depends(get_auth),
    store: ProductStore = Depends(get_store),
) -> dict[str, Any]:
    """Test helper: attempt a side effect that cancel must block."""
    mission = store.get_mission(mission_id)
    auth.require_project(principal, mission.project_id)
    store.record_side_effect(f"demo:{mission_id}", mission_id=mission_id)
    return {"ok": True, "side_effects": list(store.side_effects)}


@router.get("/missions")
async def list_missions(
    project_id: str | None = None,
    principal: Principal = Depends(get_principal),
    auth: AuthRegistry = Depends(get_auth),
    store: ProductStore = Depends(get_store),
) -> dict[str, Any]:
    if project_id:
        auth.require_project(principal, project_id)
    rows = store.list_public_missions(project_id=project_id)
    if project_id is None and "admin" not in principal.roles:
        rows = [r for r in rows if r.get("project_id") in principal.project_ids]
    return {"missions": rows, "mock_vs_live": "controller_plus_file_history"}


@router.get("/missions/{mission_id}/report")
async def mission_report(
    mission_id: str,
    principal: Principal = Depends(get_principal),
    auth: AuthRegistry = Depends(get_auth),
    store: ProductStore = Depends(get_store),
) -> dict[str, Any]:
    # Auth: if live mission, check project; history reopen uses proj_demo default.
    try:
        mission = store.get_mission(mission_id)
        auth.require_project(principal, mission.project_id)
    except ApiError:
        # History-backed missions: allow if principal has any project (operator).
        if not principal.project_ids and "admin" not in principal.roles:
            raise
    return store.mission_report(mission_id)


@router.get("/missions/{mission_id}/artifacts")
async def mission_artifacts(
    mission_id: str,
    principal: Principal = Depends(get_principal),
    auth: AuthRegistry = Depends(get_auth),
    store: ProductStore = Depends(get_store),
) -> dict[str, Any]:
    try:
        mission = store.get_mission(mission_id)
        auth.require_project(principal, mission.project_id)
    except ApiError:
        if not principal.project_ids and "admin" not in principal.roles:
            raise
    return {"artifacts": store.mission_artifacts(mission_id)}


@router.get("/projects")
async def list_projects(
    principal: Principal = Depends(get_principal),
    store: ProductStore = Depends(get_store),
) -> dict[str, Any]:
    rows = store.list_projects()
    if "admin" not in principal.roles:
        rows = [r for r in rows if r.get("project_id") in principal.project_ids]
    return {"projects": rows}


@router.post("/projects")
async def create_project(
    body: ProjectCreateRequest,
    principal: Principal = Depends(get_principal),
    auth: AuthRegistry = Depends(get_auth),
    store: ProductStore = Depends(get_store),
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> dict[str, Any]:
    key = body.idempotency_key or idempotency_key
    cached = store.recall_idempotent(key)
    if cached is not None:
        return cached
    overrides: dict[str, Any] = {}
    for field in (
        "allowed_tools",
        "provider_policy",
        "budgets",
        "defaults",
        "env_refs",
        "safety",
    ):
        val = getattr(body, field)
        if val is not None:
            overrides[field] = val
    project_id = body.project_id
    if project_id:
        auth.require_project(principal, project_id)
    else:
        project_id = (
            sorted(principal.project_ids)[0]
            if principal.project_ids
            else new_id("proj_")
        )
    cfg = store.create_project(
        name=body.name,
        repo_path=body.repo_path,
        project_id=project_id,
        **overrides,
    )
    result = {"project": cfg.to_dict()}
    store.publish(
        project_id=cfg.project_id,
        type="project.created",
        actor=principal.subject,
        payload={"name": cfg.name},
        dedupe_key=f"project.created:{cfg.project_id}",
    )
    return store.store_idempotent(key, result)


@router.get("/projects/{project_id}")
async def get_project(
    project_id: str,
    principal: Principal = Depends(get_principal),
    auth: AuthRegistry = Depends(get_auth),
    store: ProductStore = Depends(get_store),
) -> dict[str, Any]:
    auth.require_project(principal, project_id)
    return {"project": store.get_project(project_id).to_dict()}


@router.patch("/projects/{project_id}")
async def update_project(
    project_id: str,
    body: ProjectUpdateRequest,
    principal: Principal = Depends(get_principal),
    auth: AuthRegistry = Depends(get_auth),
    store: ProductStore = Depends(get_store),
) -> dict[str, Any]:
    auth.require_project(principal, project_id)
    patch = {k: v for k, v in body.model_dump().items() if v is not None and k != "idempotency_key"}
    cfg = store.project_store().update(project_id, **patch)
    return {"project": cfg.to_dict()}


@router.get("/history")
async def history_search(
    q: str = "",
    status: str | None = None,
    principal: Principal = Depends(get_principal),
    store: ProductStore = Depends(get_store),
) -> dict[str, Any]:
    _ = principal
    rows = store.history_index().search(q, status=status)
    return {"entries": rows, "query": q, "status": status}


@router.get("/history/{mission_id}")
async def history_reopen(
    mission_id: str,
    principal: Principal = Depends(get_principal),
    store: ProductStore = Depends(get_store),
) -> dict[str, Any]:
    _ = principal
    try:
        return store.history_index().reopen(mission_id)
    except (OSError, FileNotFoundError, TypeError, KeyError) as exc:
        raise ApiError("not_found", "history mission not found", status_code=404) from exc


@router.get("/product/contract")
async def product_contract(
    principal: Principal = Depends(get_principal),
    store: ProductStore = Depends(get_store),
) -> dict[str, Any]:
    _ = principal
    return store.public_contract()
