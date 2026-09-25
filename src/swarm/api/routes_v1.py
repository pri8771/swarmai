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
    MissionArtifactPublishRequest,
    MissionCreateRequest,
    MissionReviewRequest,
    PageMeta,
    ProbeRequest,
    ProjectCreateRequest,
    ProjectUpdateRequest,
    WorkerEnrollRequest,
    WorkerHeartbeatRequest,
)
from swarm.api.store import ProductStore
from swarm.contracts.common import new_id, payload_hash
from swarm.evals.plan import build_plan
from swarm.providers.catalog import list_providers

router = APIRouter(prefix="/v1")


def get_store(request: Request) -> ProductStore:
    return request.app.state.store  # type: ignore[no-any-return]

def _history_project_id(store: ProductStore, mission_id: str) -> str | None:
    try:
        opened = store.history_index().reopen(mission_id)
    except (OSError, FileNotFoundError, TypeError, KeyError):
        return None
    mission = opened.get("mission") or {}
    if isinstance(mission, dict) and mission.get("project_id"):
        return str(mission["project_id"])
    # Fall back to index row
    for row in store.history_index().search(""):
        if row.get("mission_id") == mission_id and row.get("project_id"):
            return str(row["project_id"])
    return None




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
    auth.require_project(principal, body.mission.project_id)
    digest = payload_hash(body.mission.model_dump(mode="json"))
    cached = store.recall_idempotent(
        key,
        actor=principal.subject,
        project_id=body.mission.project_id,
        operation="missions.create",
        request_digest=digest,
    )
    if cached is not None:
        return cached
    mission = await store.create_mission(
        body.mission,
        actor=principal.subject,
        task_family=body.task_family,
        required_checks=body.required_checks,
    )
    result: dict[str, Any] = {"mission": mission.model_dump(mode="json")}
    if body.task_family:
        from swarm.mission.acceptance import classify_task_support

        result["task_family"] = body.task_family
        result["support"] = classify_task_support(body.task_family).to_dict()
    return store.store_idempotent(
        key,
        result,
        actor=principal.subject,
        project_id=body.mission.project_id,
        operation="missions.create",
        request_digest=digest,
    )


@router.get("/missions/{mission_id}")
async def get_mission(
    mission_id: str,
    principal: Principal = Depends(get_principal),
    auth: AuthRegistry = Depends(get_auth),
    store: ProductStore = Depends(get_store),
) -> dict[str, Any]:
    mission = store.get_mission(mission_id)
    auth.require_project(principal, mission.project_id)
    payload: dict[str, Any] = {"mission": mission.model_dump(mode="json")}
    try:
        record = store.mission_store().load(mission_id)
        if record.plan:
            payload["plan"] = record.plan
        if record.validation:
            payload["validation"] = record.validation
        if record.result:
            payload["result"] = record.result
    except (OSError, TypeError, KeyError, ValueError, FileNotFoundError):
        pass
    return payload


@router.post("/missions/{mission_id}/review")
async def review_mission(
    mission_id: str,
    body: MissionReviewRequest,
    principal: Principal = Depends(get_principal),
    auth: AuthRegistry = Depends(get_auth),
    store: ProductStore = Depends(get_store),
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> dict[str, Any]:
    key = body.idempotency_key or idempotency_key
    mission = store.get_mission(mission_id)
    auth.require_project(principal, mission.project_id)
    digest = payload_hash(
        {
            "mission_id": mission_id,
            "produced": body.produced,
            "required_checks": body.required_checks,
            "force_wrong": body.force_wrong,
            "operation": "missions.review",
        }
    )
    cached = store.recall_idempotent(
        key,
        actor=principal.subject,
        project_id=mission.project_id,
        operation="missions.review",
        request_digest=digest,
    )
    if cached is not None:
        return cached
    result = await store.review_mission_attempt(
        mission_id,
        actor=principal.subject,
        produced=body.produced,
        required_checks=body.required_checks,
        force_wrong=body.force_wrong,
    )
    return store.store_idempotent(
        key,
        result,
        actor=principal.subject,
        project_id=mission.project_id,
        operation="missions.review",
        request_digest=digest,
    )


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
    mission = store.get_mission(mission_id)
    auth.require_project(principal, mission.project_id)
    digest = payload_hash(
        {"mission_id": mission_id, "reason": body.reason, "operation": "missions.cancel"}
    )
    cached = store.recall_idempotent(
        key,
        actor=principal.subject,
        project_id=mission.project_id,
        operation="missions.cancel",
        request_digest=digest,
    )
    if cached is not None:
        return cached
    cancelled = await store.cancel_mission(mission_id, actor=principal.subject)
    result = {"mission": cancelled.model_dump(mode="json")}
    return store.store_idempotent(
        key,
        result,
        actor=principal.subject,
        project_id=mission.project_id,
        operation="missions.cancel",
        request_digest=digest,
    )


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
    mode = "mock" if store.fixture_mode else "catalog"
    return {
        "providers": list_providers(mode=mode),
        "accounts": store.public_accounts(),
        "mock_vs_live": (
            "fixture_catalog"
            if store.fixture_mode
            else "catalog_status_not_live_eligibility"
        ),
    }


@router.get("/routes")
async def routes(
    principal: Principal = Depends(get_principal),
    store: ProductStore = Depends(get_store),
) -> dict[str, Any]:
    _ = principal
    return {
        "routes": store.public_routes(),
        "mock_vs_live": (
            "fixtures_plus_retired_catalog"
            if store.fixture_mode
            else "configured_routes_plus_retired_catalog"
        ),
    }


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
    # Scope probes to an authorized project (first membership) before cache.
    if not principal.project_ids:
        raise ApiError(
            "policy_denied",
            "provider probe requires a project-scoped principal",
            status_code=403,
            details={"provider_id": provider_id},
        )
    project_id = sorted(principal.project_ids)[0]
    key = body.idempotency_key or idempotency_key
    digest = payload_hash(
        {
            "provider_id": provider_id,
            "purpose": body.purpose,
            "operation": "providers.probe",
        }
    )
    cached = store.recall_idempotent(
        key,
        actor=principal.subject,
        project_id=project_id,
        operation="providers.probe",
        request_digest=digest,
    )
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
    return store.store_idempotent(
        key,
        result,
        actor=principal.subject,
        project_id=project_id,
        operation="providers.probe",
        request_digest=digest,
    )


@router.get("/qualifications")
async def qualifications(
    principal: Principal = Depends(get_principal),
    store: ProductStore = Depends(get_store),
) -> dict[str, Any]:
    _ = principal
    profiles = [p.model_dump(mode="json") for p in store.profiles.profiles.values()]
    return {"profiles": profiles, "policy_version": store.profiles.policy.policy_version}


@router.get("/runtimes")
async def list_runtimes(
    principal: Principal = Depends(get_principal),
) -> dict[str, Any]:
    """Optional runtime adapter qualification status (Native / OpenCode / Hermes).

    Framework configuration alone does not enforce SwarmAI contracts. Only
    ``availability=available`` runtimes are mission-admissible.
    """
    _ = principal
    from swarm.runtime.adapters.qualify import qualification_report

    report = qualification_report()
    return report


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
    if not principal.project_ids:
        raise ApiError(
            "policy_denied",
            "evaluations require a project-scoped principal",
            status_code=403,
        )
    project_id = sorted(principal.project_ids)[0]
    key = body.idempotency_key or idempotency_key
    digest = payload_hash(
        {
            "suite": body.suite,
            "mode": body.mode,
            "max_cases": body.max_cases,
            "operation": "evaluations.create",
        }
    )
    cached = store.recall_idempotent(
        key,
        actor=principal.subject,
        project_id=project_id,
        operation="evaluations.create",
        request_digest=digest,
    )
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
    return store.store_idempotent(
        key,
        result,
        actor=principal.subject,
        project_id=project_id,
        operation="evaluations.create",
        request_digest=digest,
    )


@router.get("/workers")
async def list_workers(
    project_id: str | None = None,
    principal: Principal = Depends(get_principal),
    auth: AuthRegistry = Depends(get_auth),
    store: ProductStore = Depends(get_store),
) -> dict[str, Any]:
    if project_id:
        auth.require_project(principal, project_id)
        return store.workers.inspect(project_id=project_id)
    if "admin" in principal.roles:
        return store.workers.inspect()
    # Non-admin: union of project-scoped workers only (no cross-project leakage).
    workers: list[dict[str, Any]] = []
    quarantine: set[str] = set()
    total = 0.0
    for pid in sorted(principal.project_ids):
        view = store.workers.inspect(project_id=pid)
        workers.extend(view.get("workers") or [])
        quarantine.update(view.get("quarantine") or [])
        total += float(view.get("total_capacity") or 0.0)
    return {
        "workers": workers,
        "total_capacity": total,
        "quarantine": sorted(quarantine),
    }


@router.post("/workers/enroll")
async def enroll_worker(
    body: WorkerEnrollRequest,
    principal: Principal = Depends(get_principal),
    auth: AuthRegistry = Depends(get_auth),
    store: ProductStore = Depends(get_store),
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> dict[str, Any]:
    # Authorize project ownership before any idempotency cache access.
    auth.require_project(principal, body.project_id)
    key = body.idempotency_key or idempotency_key
    digest = payload_hash(
        {
            "project_id": body.project_id,
            "capabilities": body.capabilities,
            "capacity_units": body.capacity_units,
            "privacy_classes": body.privacy_classes,
            "named_inference_urls": body.named_inference_urls,
            "operation": "workers.enroll",
        }
    )
    cached = store.recall_idempotent(
        key,
        actor=principal.subject,
        project_id=body.project_id,
        operation="workers.enroll",
        request_digest=digest,
    )
    if cached is not None:
        return cached
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
        "worker": {**lease.model_dump(mode="json"), "project_id": body.project_id},
        "membership_token": token,
        "mock_vs_live": "membership_only_no_provider_secrets",
    }
    return store.store_idempotent(
        key,
        result,
        actor=principal.subject,
        project_id=body.project_id,
        operation="workers.enroll",
        request_digest=digest,
    )


@router.post("/workers/heartbeat")
async def worker_heartbeat(
    body: WorkerHeartbeatRequest,
    principal: Principal = Depends(get_principal),
    store: ProductStore = Depends(get_store),
) -> dict[str, Any]:
    rec = store.workers._workers.get(body.worker_id)
    if rec is None:
        raise ApiError("not_found", "worker not found", status_code=404)
    if (
        rec.project_id
        and rec.project_id not in principal.project_ids
        and "admin" not in principal.roles
    ):
        raise ApiError("forbidden_project", "worker not in project scope", status_code=403)
    lease = await store.workers.heartbeat(body.worker_id, body.generation, token=body.token)
    return {"worker": lease.model_dump(mode="json"), "project_id": rec.project_id}


@router.get("/approvals")
async def list_approvals(
    project_id: str | None = None,
    principal: Principal = Depends(get_principal),
    auth: AuthRegistry = Depends(get_auth),
    store: ProductStore = Depends(get_store),
) -> dict[str, Any]:
    if project_id:
        auth.require_project(principal, project_id)
        rows = [
            a.model_dump(mode="json")
            for a in store.approvals.values()
            if a.project_id == project_id
        ]
    elif "admin" in principal.roles:
        rows = [a.model_dump(mode="json") for a in store.approvals.values()]
    else:
        rows = [
            a.model_dump(mode="json")
            for a in store.approvals.values()
            if a.project_id in principal.project_ids
        ]
    return {"approvals": rows}


@router.post("/approvals/{approval_id}/resolve")
async def resolve_approval(
    approval_id: str,
    body: ApprovalResolveRequest,
    principal: Principal = Depends(get_principal),
    auth: AuthRegistry = Depends(get_auth),
    store: ProductStore = Depends(get_store),
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> dict[str, Any]:
    approval = store.approvals.get(approval_id)
    if approval is None:
        raise ApiError("not_found", "approval not found", status_code=404)
    # Authorize against durable approval ownership — not caller's first project.
    auth.require_project(principal, approval.project_id)
    project_id = approval.project_id
    key = body.idempotency_key or idempotency_key
    digest = payload_hash(
        {
            "approval_id": approval_id,
            "accept": body.accept,
            "payload": body.payload,
            "operation": "approvals.resolve",
        }
    )
    cached = store.recall_idempotent(
        key,
        actor=principal.subject,
        project_id=project_id,
        operation="approvals.resolve",
        request_digest=digest,
    )
    if cached is not None:
        return cached
    resolved = store.resolve_approval(
        approval_id,
        accept=body.accept,
        actor=principal.subject,
        payload=body.payload,
        project_id=project_id,
    )
    result = {"approval": resolved.model_dump(mode="json"), "accepted": body.accept}
    return store.store_idempotent(
        key,
        result,
        actor=principal.subject,
        project_id=project_id,
        operation="approvals.resolve",
        request_digest=digest,
    )


@router.post("/missions/{mission_id}/side-effects/demo")
async def demo_side_effect(
    mission_id: str,
    principal: Principal = Depends(get_principal),
    auth: AuthRegistry = Depends(get_auth),
    store: ProductStore = Depends(get_store),
) -> dict[str, Any]:
    """Fixture-only helper: attempt a side effect that cancel must block."""
    if not store.fixture_mode:
        raise ApiError(
            "fixture_only",
            "demo side-effect route is not available in operational mode",
            status_code=404,
        )
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
    try:
        mission = store.get_mission(mission_id)
        auth.require_project(principal, mission.project_id)
    except ApiError as exc:
        if getattr(exc, "code", None) == "forbidden_project":
            raise
        project_id = _history_project_id(store, mission_id)
        if project_id is None:
            raise ApiError("not_found", "mission report not found", status_code=404) from exc
        auth.require_project(principal, project_id)
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
    except ApiError as exc:
        if getattr(exc, "code", None) == "forbidden_project":
            raise
        project_id = _history_project_id(store, mission_id)
        if project_id is None:
            raise ApiError("not_found", "mission artifacts not found", status_code=404) from exc
        auth.require_project(principal, project_id)
    return {"artifacts": store.mission_artifacts(mission_id)}


@router.post("/missions/{mission_id}/artifacts")
async def publish_mission_artifact(
    mission_id: str,
    body: MissionArtifactPublishRequest,
    principal: Principal = Depends(get_principal),
    auth: AuthRegistry = Depends(get_auth),
    store: ProductStore = Depends(get_store),
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> dict[str, Any]:
    import base64

    mission = store.get_mission(mission_id)
    auth.require_project(principal, mission.project_id)
    if body.content_text is None and body.content_base64 is None:
        raise ApiError(
            "invalid_request",
            "content_text or content_base64 required",
            status_code=400,
        )
    if body.content_text is not None and body.content_base64 is not None:
        raise ApiError(
            "invalid_request",
            "provide only one of content_text or content_base64",
            status_code=400,
        )
    if body.content_base64 is not None:
        try:
            content = base64.b64decode(body.content_base64, validate=True)
        except Exception as exc:
            raise ApiError(
                "invalid_request", "content_base64 is not valid base64", status_code=400
            ) from exc
    else:
        content = (body.content_text or "").encode("utf-8")
    key = body.idempotency_key or idempotency_key
    digest = payload_hash(
        {
            "mission_id": mission_id,
            "kind": body.kind,
            "media_type": body.media_type,
            "content_sha256": payload_hash({"b": body.content_base64 or body.content_text}),
        }
    )
    cached = store.recall_idempotent(
        key,
        actor=principal.subject,
        project_id=mission.project_id,
        operation="missions.artifacts.publish",
        request_digest=digest,
    )
    if cached is not None:
        return cached
    owner_scope = body.owner_scope or mission.project_id
    published = store.publish_mission_artifact(
        mission_id,
        kind=body.kind,
        content=content,
        media_type=body.media_type,
        owner_scope=owner_scope,
        retention_class=body.retention_class,
        summary=body.summary,
        expected_hash=body.expected_hash,
        actor=principal.subject,
    )
    return store.store_idempotent(
        key,
        {"artifact": published, "mock_vs_live": "durable_cas_volume"},
        actor=principal.subject,
        project_id=mission.project_id,
        operation="missions.artifacts.publish",
        request_digest=digest,
    )


@router.get("/missions/{mission_id}/artifacts/{artifact_id}/content")
async def mission_artifact_content(
    mission_id: str,
    artifact_id: str,
    principal: Principal = Depends(get_principal),
    auth: AuthRegistry = Depends(get_auth),
    store: ProductStore = Depends(get_store),
) -> dict[str, Any]:
    import base64
    import hashlib

    mission = store.get_mission(mission_id)
    auth.require_project(principal, mission.project_id)
    try:
        data, meta = store.read_mission_artifact_bytes(mission_id, artifact_id)
    except FileNotFoundError as exc:
        raise ApiError("not_found", "artifact blob missing", status_code=404) from exc
    except KeyError as exc:
        raise ApiError("not_found", "artifact not found", status_code=404) from exc
    digest = hashlib.sha256(data).hexdigest()
    expected = str(meta.get("content_hash") or meta.get("sha256") or "")
    if expected and expected != digest:
        raise ApiError("checksum_mismatch", "artifact checksum failed", status_code=409)
    return {
        "artifact_id": artifact_id,
        "mission_id": mission_id,
        "content_hash": digest,
        "byte_length": len(data),
        "media_type": meta.get("media_type"),
        "content_base64": base64.b64encode(data).decode("ascii"),
        "mock_vs_live": "durable_cas_reopen",
    }


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
    digest = payload_hash(
        {
            "name": body.name,
            "repo_path": body.repo_path,
            "project_id": project_id,
            "overrides": overrides,
        }
    )
    cached = store.recall_idempotent(
        key,
        actor=principal.subject,
        project_id=project_id,
        operation="projects.create",
        request_digest=digest,
    )
    if cached is not None:
        return cached
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
    return store.store_idempotent(
        key,
        result,
        actor=principal.subject,
        project_id=cfg.project_id,
        operation="projects.create",
        request_digest=digest,
    )


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
    rows = store.history_index().search(q, status=status)
    if "admin" not in principal.roles:
        rows = [r for r in rows if r.get("project_id") in principal.project_ids]
    return {"entries": rows, "query": q, "status": status}


@router.get("/history/{mission_id}")
async def history_reopen(
    mission_id: str,
    principal: Principal = Depends(get_principal),
    auth: AuthRegistry = Depends(get_auth),
    store: ProductStore = Depends(get_store),
) -> dict[str, Any]:
    project_id = _history_project_id(store, mission_id)
    if project_id is None:
        raise ApiError("not_found", "history mission not found", status_code=404)
    auth.require_project(principal, project_id)
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


def _objective_repo(request: Request) -> Any:
    repo = getattr(request.app.state, "objective_repo", None)
    if repo is None:
        from swarm.objectives import ObjectiveRepository

        repo = ObjectiveRepository()
        request.app.state.objective_repo = repo
    return repo


def _learning_repo(request: Request) -> Any:
    repo = getattr(request.app.state, "learning_repo", None)
    if repo is None:
        from swarm.learning import LearningRepository

        repo = LearningRepository()
        request.app.state.learning_repo = repo
    return repo


@router.post("/objectives")
async def create_objective(
    request: Request,
    body: dict[str, Any],
    principal: Principal = Depends(get_principal),
    auth: AuthRegistry = Depends(get_auth),
) -> dict[str, Any]:
    from swarm.objectives import ObjectiveContract, ObjectiveError

    project_id = str(body.get("project_id") or "")
    auth.require_project(principal, project_id)
    repo = _objective_repo(request)
    try:
        templates = list(body.get("allowed_mission_templates") or ["generic"])
        obj = repo.create(
            ObjectiveContract(
                project_id=project_id,
                goal=str(body.get("goal") or ""),
                allowed_mission_templates=templates,
                spend_usd_ceiling=float(body.get("spend_usd_ceiling") or 0.0),
                tool_envelope=list(body.get("tool_envelope") or []),
                data_envelope=list(body.get("data_envelope") or []),
                provider_envelope=list(body.get("provider_envelope") or []),
            )
        )
    except ObjectiveError as exc:
        raise ApiError("objective_error", str(exc), status_code=400) from exc
    return {"objective": obj.model_dump(mode="json")}


@router.post("/objectives/{objective_id}/trigger")
async def trigger_objective(
    objective_id: str,
    request: Request,
    body: dict[str, Any],
    principal: Principal = Depends(get_principal),
    auth: AuthRegistry = Depends(get_auth),
) -> dict[str, Any]:
    from swarm.objectives import ObjectiveError

    repo = _objective_repo(request)
    try:
        obj = repo.get(objective_id)
        auth.require_project(principal, obj.project_id)
        proposal = repo.trigger(
            objective_id,
            dedupe_key=str(body.get("dedupe_key") or new_id("dk_")),
            trigger_kind=str(body.get("trigger_kind") or "manual"),
            template_id=body.get("template_id"),
        )
    except ObjectiveError as exc:
        raise ApiError("objective_error", str(exc), status_code=400) from exc
    return {"proposal": proposal.model_dump(mode="json")}


@router.post("/objectives/{objective_id}/admit")
async def admit_objective_proposal(
    objective_id: str,
    request: Request,
    body: dict[str, Any],
    principal: Principal = Depends(get_principal),
    auth: AuthRegistry = Depends(get_auth),
) -> dict[str, Any]:
    from swarm.objectives import ObjectiveError

    repo = _objective_repo(request)
    try:
        obj = repo.get(objective_id)
        auth.require_project(principal, obj.project_id)
        admitted = repo.admit_to_mission(str(body.get("proposal_id") or ""))
    except ObjectiveError as exc:
        raise ApiError("objective_error", str(exc), status_code=400) from exc
    return {"proposal": admitted.model_dump(mode="json")}


@router.post("/learning/proposals")
async def create_learning_proposal(
    request: Request,
    body: dict[str, Any],
    principal: Principal = Depends(get_principal),
    auth: AuthRegistry = Depends(get_auth),
) -> dict[str, Any]:
    from swarm.learning import LearningError, LearningProposal

    project_id = str(body.get("project_id") or "")
    auth.require_project(principal, project_id)
    repo = _learning_repo(request)
    try:
        prop = repo.create(
            LearningProposal(
                project_id=project_id,
                change_summary=str(body.get("change_summary") or ""),
                sealed_holdout_ref=body.get("sealed_holdout_ref"),
            )
        )
    except LearningError as exc:
        raise ApiError("learning_error", str(exc), status_code=400) from exc
    return {"proposal": prop.model_dump(mode="json")}


@router.get("/recovery/drill")
async def recovery_drill(
    principal: Principal = Depends(get_principal),
) -> dict[str, Any]:
    _ = principal
    from swarm.recovery import OutageDrillHarness

    return OutageDrillHarness().run_local(commit_sha="api-drill").to_dict()


@router.get("/install/clean-plan")
async def install_clean_plan(
    principal: Principal = Depends(get_principal),
) -> dict[str, Any]:
    _ = principal
    from swarm.deploy.install import InstallOrchestrator

    return InstallOrchestrator().clean_install_plan().to_dict()


@router.get("/ops/events")
async def list_ops_events(
    request: Request,
    project_id: str | None = None,
    principal: Principal = Depends(get_principal),
    auth: AuthRegistry = Depends(get_auth),
) -> dict[str, Any]:
    from swarm.observability import OpsEventLog

    log = getattr(request.app.state, "ops_events", None)
    if log is None:
        log = OpsEventLog()
        request.app.state.ops_events = log
    if project_id:
        auth.require_project(principal, project_id)
    return {"events": log.list_events(project_id=project_id)}


@router.post("/release/candidate-freeze")
async def freeze_candidate(
    principal: Principal = Depends(get_principal),
) -> dict[str, Any]:
    _ = principal
    import subprocess
    from pathlib import Path

    from swarm.release.candidate import CandidateFreezer

    root = Path(__file__).resolve().parents[3]
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    return CandidateFreezer(root).freeze(
        source_sha=sha, schema_revision="a18tov30schema0001"
    ).to_dict()
