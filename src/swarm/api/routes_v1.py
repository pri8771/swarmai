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
    GoalCreateRequest,
    GoalLifecycleRequest,
    GoalLinkMissionRequest,
    GoalMissionOutcomeRequest,
    GoalProgressRequest,
    GoalTransitionRequest,
    GoalTriggerRequest,
    MissionArtifactPublishRequest,
    MissionCreateRequest,
    MissionReviewRequest,
    PageMeta,
    ProbeRequest,
    ProjectCreateRequest,
    ProjectUpdateRequest,
    PursuitLessonEvaluateRequest,
    PursuitLessonProposeRequest,
    PursuitTickRequest,
    WorkerCancelLeaseRequest,
    WorkerClaimRequest,
    WorkerDrainRequest,
    WorkerEnqueueTaskRequest,
    WorkerEnrollRequest,
    WorkerHeartbeatRequest,
    WorkerReconnectRequest,
    WorkerRenewRequest,
    WorkerRevokeRequest,
    WorkerRotateTokenRequest,
    WorkerSubmitResultRequest,
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
        yield f'event: cursor\ndata: {{"cursor": "{cursor or ""}"}}\n\n'

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
            "fixture_catalog" if store.fixture_mode else "catalog_status_not_live_eligibility"
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
        host_alias=body.host_alias,
        architecture=body.architecture,
        runtime_version=body.runtime_version,
        labels=body.labels,
        platform=body.platform,
        runtimes=body.runtimes,
        resource_limits=body.resource_limits,
        data_locality=body.data_locality,
        workspace_grant_ids=body.workspace_grant_ids,
        role=body.role,
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
    try:
        lease = await store.workers.heartbeat(body.worker_id, body.generation, token=body.token)
    except Exception as exc:  # noqa: BLE001 — map auth/fence errors
        from swarm.workers.registry import StaleGenerationError, WorkerAuthError

        if isinstance(exc, WorkerAuthError):
            raise ApiError("forbidden", str(exc), status_code=403) from exc
        if isinstance(exc, StaleGenerationError):
            raise ApiError("stale_generation", str(exc), status_code=409) from exc
        raise
    store._persist_durable_workers()
    return {
        "worker": lease.model_dump(mode="json"),
        "project_id": rec.project_id,
        "cancel_notices": store.workers.cancel_notices_for(body.worker_id),
        "active_lease_ids": list(rec.active_lease_ids),
    }


@router.post("/workers/claim")
async def worker_claim(
    body: WorkerClaimRequest,
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
    if body.generation != rec.lease.lease_generation:
        raise ApiError("stale_generation", "worker generation mismatch", status_code=409)
    try:
        claimed = await store.workers.claim_work(body.worker_id, token=body.token)
    except Exception as exc:  # noqa: BLE001
        from swarm.workers.registry import StaleGenerationError, WorkerAuthError

        if isinstance(exc, WorkerAuthError):
            raise ApiError("forbidden", str(exc), status_code=403) from exc
        if isinstance(exc, StaleGenerationError):
            raise ApiError("stale_generation", str(exc), status_code=409) from exc
        raise
    store._persist_durable_workers()
    if not claimed.claimed or claimed.lease is None:
        return {
            "claimed": False,
            "cancel_notices": claimed.cancel_notices,
            "agent_profile_id": body.agent_profile_id,
        }
    lease = claimed.lease
    return {
        "claimed": True,
        "lease_id": lease.lease_id,
        "task_id": lease.task.id,
        "mission_id": lease.task.mission_id,
        "project_id": rec.project_id,
        "worker_generation": lease.worker_generation,
        "expires_at": lease.expires_at.isoformat(),
        "state": lease.state,
        "task": lease.task.model_dump(mode="json"),
        "cancel_notices": claimed.cancel_notices,
        "agent_profile_id": body.agent_profile_id,
    }


@router.post("/workers/renew")
async def worker_renew(
    body: WorkerRenewRequest,
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
    try:
        lease = store.workers.renew_lease(
            lease_id=body.lease_id,
            worker_id=body.worker_id,
            generation=body.generation,
            token=body.token,
            extend_seconds=body.extend_seconds,
        )
    except Exception as exc:  # noqa: BLE001
        from swarm.workers.registry import (
            LeaseStateError,
            StaleGenerationError,
            WorkerAuthError,
        )

        if isinstance(exc, WorkerAuthError):
            raise ApiError("forbidden", str(exc), status_code=403) from exc
        if isinstance(exc, StaleGenerationError):
            raise ApiError("stale_generation", str(exc), status_code=409) from exc
        if isinstance(exc, LeaseStateError):
            raise ApiError("lease_state", str(exc), status_code=409) from exc
        raise
    store._persist_durable_workers()
    return {
        "lease_id": lease.lease_id,
        "state": lease.state,
        "expires_at": lease.expires_at.isoformat(),
        "progress_class": body.progress_class,
        "cancel_notices": store.workers.cancel_notices_for(body.worker_id),
    }


@router.post("/workers/submit-result")
async def worker_submit_result(
    body: WorkerSubmitResultRequest,
    principal: Principal = Depends(get_principal),
    store: ProductStore = Depends(get_store),
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
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
    key = body.idempotency_key or idempotency_key
    digest = payload_hash(
        {
            "lease_id": body.lease_id,
            "worker_id": body.worker_id,
            "status": body.status,
            "checks": body.checks,
            "artifact_manifest": body.artifact_manifest,
            "result_id": body.result_id,
            "operation": "workers.submit_result",
        }
    )
    cached = store.recall_idempotent(
        key,
        actor=principal.subject,
        project_id=rec.project_id or "",
        operation="workers.submit_result",
        request_digest=digest,
    )
    if cached is not None:
        return cached
    try:
        payload = store.workers.submit_result(
            lease_id=body.lease_id,
            worker_id=body.worker_id,
            generation=body.generation,
            token=body.token,
            status=body.status,
            checks=body.checks,
            artifact_manifest=body.artifact_manifest,
            usage=body.usage,
            summary=body.summary,
            result_id=body.result_id,
        )
    except Exception as exc:  # noqa: BLE001
        from swarm.workers.registry import (
            LeaseStateError,
            StaleGenerationError,
            WorkerAuthError,
        )

        if isinstance(exc, WorkerAuthError):
            raise ApiError("forbidden", str(exc), status_code=403) from exc
        if isinstance(exc, StaleGenerationError):
            raise ApiError("stale_generation", str(exc), status_code=409) from exc
        if isinstance(exc, LeaseStateError):
            raise ApiError("lease_state", str(exc), status_code=409) from exc
        raise
    store._persist_durable_workers()
    # Explicit: worker submit never self-accepts.
    result = {
        **payload,
        "self_accepted": False,
        "acceptance_requires": "control_plane",
    }
    return store.store_idempotent(
        key,
        result,
        actor=principal.subject,
        project_id=rec.project_id or "",
        operation="workers.submit_result",
        request_digest=digest,
    )


@router.post("/workers/cancel-lease")
async def worker_cancel_lease(
    body: WorkerCancelLeaseRequest,
    principal: Principal = Depends(get_principal),
    store: ProductStore = Depends(get_store),
) -> dict[str, Any]:
    lease = store.workers._leases.get(body.lease_id)
    if lease is None:
        raise ApiError("not_found", "lease not found", status_code=404)
    rec = store.workers._workers.get(lease.worker_id)
    if rec is not None and rec.project_id:
        if rec.project_id not in principal.project_ids and "admin" not in principal.roles:
            raise ApiError("forbidden_project", "lease not in project scope", status_code=403)
    try:
        cancelled = store.workers.cancel_lease(lease_id=body.lease_id, reason=body.reason)
    except Exception as exc:  # noqa: BLE001
        from swarm.workers.registry import LeaseStateError

        if isinstance(exc, LeaseStateError):
            raise ApiError("lease_state", str(exc), status_code=409) from exc
        raise
    store._persist_durable_workers()
    return {
        "lease_id": cancelled.lease_id,
        "state": cancelled.state,
        "reason": cancelled.cancel_reason,
    }


@router.post("/workers/reconnect")
async def worker_reconnect(
    body: WorkerReconnectRequest,
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
    try:
        payload = store.workers.reconnect(
            body.worker_id, generation=body.generation, token=body.token
        )
    except Exception as exc:  # noqa: BLE001
        from swarm.workers.registry import StaleGenerationError, WorkerAuthError

        if isinstance(exc, WorkerAuthError):
            raise ApiError("forbidden", str(exc), status_code=403) from exc
        if isinstance(exc, StaleGenerationError):
            raise ApiError("stale_generation", str(exc), status_code=409) from exc
        raise
    store._persist_durable_workers()
    return payload


@router.get("/workers")
async def workers_inspect(
    project_id: str | None = None,
    principal: Principal = Depends(get_principal),
    auth: AuthRegistry = Depends(get_auth),
    store: ProductStore = Depends(get_store),
) -> dict[str, Any]:
    if project_id:
        auth.require_project(principal, project_id)
    elif "admin" not in principal.roles:
        # Non-admin must scope to a project they own.
        raise ApiError("project_required", "project_id required", status_code=400)
    return store.workers.inspect(project_id=project_id)


@router.post("/workers/drain")
async def worker_drain(
    body: WorkerDrainRequest,
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
    try:
        if body.token:
            if body.generation is None:
                raise ApiError(
                    "invalid_request",
                    "generation required for self-drain",
                    status_code=400,
                )
            if int(body.generation) != int(rec.lease.lease_generation):
                raise ApiError("stale_generation", "worker generation mismatch", status_code=409)
            lease = await store.workers.drain(body.worker_id, token=body.token)
        else:
            lease = store.workers.operator_drain(body.worker_id)
    except Exception as exc:  # noqa: BLE001
        from swarm.workers.registry import StaleGenerationError, WorkerAuthError

        if isinstance(exc, WorkerAuthError):
            raise ApiError("forbidden", str(exc), status_code=403) from exc
        if isinstance(exc, StaleGenerationError):
            raise ApiError("stale_generation", str(exc), status_code=409) from exc
        raise
    store._persist_durable_workers()
    return {
        "worker_id": lease.worker_id,
        "status": lease.status.value,
        "active_lease_ids": list(rec.active_lease_ids),
        "generation": lease.lease_generation,
    }


@router.post("/workers/revoke")
async def worker_revoke(
    body: WorkerRevokeRequest,
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
    new_gen = await store.workers.revoke_generation(body.worker_id)
    store._persist_durable_workers()
    store.publish(
        project_id=rec.project_id or "",
        type="worker.revoked",
        actor=principal.subject,
        payload={
            "worker_id": body.worker_id,
            "generation": new_gen,
            "reason": body.reason,
        },
        dedupe_key=f"worker.revoked:{body.worker_id}:{new_gen}",
    )
    return {
        "worker_id": body.worker_id,
        "generation": new_gen,
        "status": "quarantined",
        "revoked": True,
        "reason": body.reason,
    }


@router.post("/workers/rotate-token")
async def worker_rotate_token(
    body: WorkerRotateTokenRequest,
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
    if int(body.generation) != int(rec.lease.lease_generation):
        raise ApiError("stale_generation", "worker generation mismatch", status_code=409)
    try:
        lease, new_token = store.workers.rotate_membership_token(
            body.worker_id, current_token=body.token
        )
    except Exception as exc:  # noqa: BLE001
        from swarm.workers.registry import WorkerAuthError

        if isinstance(exc, WorkerAuthError):
            raise ApiError("forbidden", str(exc), status_code=403) from exc
        raise
    store._persist_durable_workers()
    return {
        "worker_id": lease.worker_id,
        "generation": lease.lease_generation,
        "membership_token": new_token,
        "status": lease.status.value,
    }


@router.post("/workers/enqueue")
async def worker_enqueue_task(
    body: WorkerEnqueueTaskRequest,
    principal: Principal = Depends(get_principal),
    auth: AuthRegistry = Depends(get_auth),
    store: ProductStore = Depends(get_store),
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> dict[str, Any]:
    from swarm.contracts.mission import TaskSpec

    try:
        task = TaskSpec.model_validate(body.task)
    except Exception as exc:  # noqa: BLE001
        raise ApiError("invalid_request", f"invalid task: {exc}", status_code=400) from exc
    auth.require_project(principal, task.project_id)
    key = body.idempotency_key or idempotency_key
    digest = payload_hash(
        {"task_id": task.id, "mission_id": task.mission_id, "operation": "enqueue"}
    )
    cached = store.recall_idempotent(
        key,
        actor=principal.subject,
        project_id=task.project_id,
        operation="workers.enqueue",
        request_digest=digest,
    )
    if cached is not None:
        return cached
    store.workers.enqueue(task)
    store._persist_durable_workers()
    result = {
        "enqueued": True,
        "task_id": task.id,
        "mission_id": task.mission_id,
        "queue_depth": len(store.workers._dispatch_queue),
    }
    return store.store_idempotent(
        key,
        result,
        actor=principal.subject,
        project_id=task.project_id,
        operation="workers.enqueue",
        request_digest=digest,
    )


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


@router.get("/goals")
async def list_goals(
    project_id: str | None = None,
    principal: Principal = Depends(get_principal),
    auth: AuthRegistry = Depends(get_auth),
    store: ProductStore = Depends(get_store),
) -> dict[str, Any]:
    if project_id:
        auth.require_project(principal, project_id)
    goals = store.goal_store().list_goals(project_id=project_id)
    if "admin" not in principal.roles:
        goals = [g for g in goals if g.project_id in principal.project_ids]
    return {"goals": [g.model_dump(mode="json") for g in goals]}


@router.post("/goals")
async def create_goal(
    body: GoalCreateRequest,
    principal: Principal = Depends(get_principal),
    auth: AuthRegistry = Depends(get_auth),
    store: ProductStore = Depends(get_store),
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> dict[str, Any]:
    from swarm.goals.models import Goal, GoalError, GoalKind

    auth.require_project(principal, body.project_id)
    store.require_durable_writes()
    key = body.idempotency_key or idempotency_key
    digest = payload_hash(
        body.model_dump(mode="json", exclude={"idempotency_key"})
    )
    cached = store.recall_idempotent(
        key,
        actor=principal.subject,
        project_id=body.project_id,
        operation="goals.create",
        request_digest=digest,
    )
    if cached is not None:
        return cached
    try:
        kind = GoalKind(body.kind)
    except ValueError as exc:
        raise ApiError("invalid_goal_kind", str(exc), status_code=400) from exc
    goal = Goal(
        project_id=body.project_id,
        desired_outcome=body.desired_outcome,
        verification_criteria=list(body.verification_criteria),
        kind=kind,
        scope=dict(body.scope),
        constraints=dict(body.constraints),
        resource_envelope=dict(body.resource_envelope),
        authority_envelope=dict(body.authority_envelope),
        owner=body.owner or principal.subject,
        permitted_agents=list(body.permitted_agents),
        strategy=body.strategy,
        stop_conditions=list(body.stop_conditions),
        dependencies=list(body.dependencies),
        open_questions=list(body.open_questions),
        blockers=list(body.blockers),
        review_cadence=body.review_cadence,
        expires_at=body.expires_at,
    )
    try:
        created = store.goal_store().create(goal)
    except GoalError as exc:
        raise ApiError("goal_create_error", str(exc), status_code=409) from exc
    result = {"goal": created.model_dump(mode="json")}
    return store.store_idempotent(
        key,
        result,
        actor=principal.subject,
        project_id=body.project_id,
        operation="goals.create",
        request_digest=digest,
    )


@router.get("/goals/{goal_id}")
async def get_goal(
    goal_id: str,
    principal: Principal = Depends(get_principal),
    auth: AuthRegistry = Depends(get_auth),
    store: ProductStore = Depends(get_store),
) -> dict[str, Any]:
    try:
        goal = store.goal_store().get(goal_id)
        store.goal_store().evaluate_expiry(goal_id)
        goal = store.goal_store().get(goal_id)
    except KeyError as exc:
        raise ApiError("not_found", "goal not found", status_code=404) from exc
    auth.require_project(principal, goal.project_id)
    return {"goal": goal.model_dump(mode="json")}


@router.post("/goals/{goal_id}/transition")
async def transition_goal(
    goal_id: str,
    body: GoalTransitionRequest,
    principal: Principal = Depends(get_principal),
    auth: AuthRegistry = Depends(get_auth),
    store: ProductStore = Depends(get_store),
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> dict[str, Any]:
    from swarm.goals.models import GoalError, GoalStatus

    try:
        goal = store.goal_store().get(goal_id)
    except KeyError as exc:
        raise ApiError("not_found", "goal not found", status_code=404) from exc
    auth.require_project(principal, goal.project_id)
    key = body.idempotency_key or idempotency_key
    digest = payload_hash(body.model_dump(mode="json", exclude={"idempotency_key"}))
    cached = store.recall_idempotent(
        key,
        actor=principal.subject,
        project_id=goal.project_id,
        operation=f"goals.transition:{goal_id}",
        request_digest=digest,
    )
    if cached is not None:
        return cached
    try:
        status = GoalStatus(body.status)
        updated = store.goal_store().transition(
            goal_id, status, reason=body.reason or "operator", actor=principal.subject
        )
    except (ValueError, GoalError) as exc:
        raise ApiError("illegal_transition", str(exc), status_code=409) from exc
    result = {"goal": updated.model_dump(mode="json")}
    return store.store_idempotent(
        key,
        result,
        actor=principal.subject,
        project_id=goal.project_id,
        operation=f"goals.transition:{goal_id}",
        request_digest=digest,
    )


def _goal_lifecycle(
    *,
    goal_id: str,
    action: str,
    body: GoalLifecycleRequest,
    principal: Principal,
    auth: AuthRegistry,
    store: ProductStore,
    idempotency_key: str | None,
) -> dict[str, Any]:
    from swarm.goals.models import GoalError

    try:
        goal = store.goal_store().get(goal_id)
    except KeyError as exc:
        raise ApiError("not_found", "goal not found", status_code=404) from exc
    auth.require_project(principal, goal.project_id)
    key = body.idempotency_key or idempotency_key
    digest = payload_hash(
        {"action": action, **body.model_dump(mode="json", exclude={"idempotency_key"})}
    )
    cached = store.recall_idempotent(
        key,
        actor=principal.subject,
        project_id=goal.project_id,
        operation=f"goals.{action}:{goal_id}",
        request_digest=digest,
    )
    if cached is not None:
        return cached
    reason = body.reason or action
    gs = store.goal_store()
    try:
        if action == "pause":
            updated = gs.pause(goal_id, reason=reason, actor=principal.subject)
        elif action == "resume":
            updated = gs.resume(goal_id, reason=reason, actor=principal.subject)
        elif action == "cancel":
            updated = gs.cancel(goal_id, reason=reason, actor=principal.subject)
        elif action == "restart":
            updated = gs.restart(goal_id, reason=reason, actor=principal.subject)
        else:
            raise ApiError("invalid_action", f"unknown lifecycle action:{action}", status_code=400)
    except GoalError as exc:
        raise ApiError("illegal_transition", str(exc), status_code=409) from exc
    result = {"goal": updated.model_dump(mode="json")}
    return store.store_idempotent(
        key,
        result,
        actor=principal.subject,
        project_id=goal.project_id,
        operation=f"goals.{action}:{goal_id}",
        request_digest=digest,
    )


@router.post("/goals/{goal_id}/pause")
async def pause_goal(
    goal_id: str,
    body: GoalLifecycleRequest | None = None,
    principal: Principal = Depends(get_principal),
    auth: AuthRegistry = Depends(get_auth),
    store: ProductStore = Depends(get_store),
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> dict[str, Any]:
    return _goal_lifecycle(
        goal_id=goal_id,
        action="pause",
        body=body or GoalLifecycleRequest(),
        principal=principal,
        auth=auth,
        store=store,
        idempotency_key=idempotency_key,
    )


@router.post("/goals/{goal_id}/resume")
async def resume_goal(
    goal_id: str,
    body: GoalLifecycleRequest | None = None,
    principal: Principal = Depends(get_principal),
    auth: AuthRegistry = Depends(get_auth),
    store: ProductStore = Depends(get_store),
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> dict[str, Any]:
    return _goal_lifecycle(
        goal_id=goal_id,
        action="resume",
        body=body or GoalLifecycleRequest(),
        principal=principal,
        auth=auth,
        store=store,
        idempotency_key=idempotency_key,
    )


@router.post("/goals/{goal_id}/cancel")
async def cancel_goal(
    goal_id: str,
    body: GoalLifecycleRequest | None = None,
    principal: Principal = Depends(get_principal),
    auth: AuthRegistry = Depends(get_auth),
    store: ProductStore = Depends(get_store),
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> dict[str, Any]:
    return _goal_lifecycle(
        goal_id=goal_id,
        action="cancel",
        body=body or GoalLifecycleRequest(),
        principal=principal,
        auth=auth,
        store=store,
        idempotency_key=idempotency_key,
    )


@router.post("/goals/{goal_id}/restart")
async def restart_goal(
    goal_id: str,
    body: GoalLifecycleRequest | None = None,
    principal: Principal = Depends(get_principal),
    auth: AuthRegistry = Depends(get_auth),
    store: ProductStore = Depends(get_store),
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> dict[str, Any]:
    return _goal_lifecycle(
        goal_id=goal_id,
        action="restart",
        body=body or GoalLifecycleRequest(),
        principal=principal,
        auth=auth,
        store=store,
        idempotency_key=idempotency_key,
    )


@router.post("/goals/{goal_id}/triggers")
async def trigger_goal(
    goal_id: str,
    body: GoalTriggerRequest,
    principal: Principal = Depends(get_principal),
    auth: AuthRegistry = Depends(get_auth),
    store: ProductStore = Depends(get_store),
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> dict[str, Any]:
    from swarm.goals.models import GoalError

    try:
        goal = store.goal_store().get(goal_id)
    except KeyError as exc:
        raise ApiError("not_found", "goal not found", status_code=404) from exc
    auth.require_project(principal, goal.project_id)
    key = body.idempotency_key or idempotency_key
    digest = payload_hash(body.model_dump(mode="json", exclude={"idempotency_key"}))
    cached = store.recall_idempotent(
        key,
        actor=principal.subject,
        project_id=goal.project_id,
        operation=f"goals.trigger:{goal_id}",
        request_digest=digest,
    )
    if cached is not None:
        return cached
    try:
        updated, receipt = store.goal_store().accept_trigger(
            goal_id,
            dedupe_key=body.dedupe_key,
            trigger_kind=body.trigger_kind,
            actor=principal.subject,
            payload=dict(body.payload),
        )
    except GoalError as exc:
        raise ApiError("goal_trigger_error", str(exc), status_code=409) from exc
    result = {"goal": updated.model_dump(mode="json"), "receipt": receipt}
    return store.store_idempotent(
        key,
        result,
        actor=principal.subject,
        project_id=goal.project_id,
        operation=f"goals.trigger:{goal_id}",
        request_digest=digest,
    )


@router.post("/goals/{goal_id}/progress")
async def record_goal_progress(
    goal_id: str,
    body: GoalProgressRequest,
    principal: Principal = Depends(get_principal),
    auth: AuthRegistry = Depends(get_auth),
    store: ProductStore = Depends(get_store),
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> dict[str, Any]:
    from swarm.goals.models import GoalError

    try:
        goal = store.goal_store().get(goal_id)
    except KeyError as exc:
        raise ApiError("not_found", "goal not found", status_code=404) from exc
    auth.require_project(principal, goal.project_id)
    key = body.idempotency_key or idempotency_key
    digest = payload_hash(body.model_dump(mode="json", exclude={"idempotency_key"}))
    cached = store.recall_idempotent(
        key,
        actor=principal.subject,
        project_id=goal.project_id,
        operation=f"goals.progress:{goal_id}",
        request_digest=digest,
    )
    if cached is not None:
        return cached
    try:
        updated = store.goal_store().record_progress(
            goal_id,
            summary=body.summary,
            actor=principal.subject,
            metrics=dict(body.metrics),
        )
    except GoalError as exc:
        raise ApiError("goal_progress_error", str(exc), status_code=409) from exc
    result = {"goal": updated.model_dump(mode="json")}
    return store.store_idempotent(
        key,
        result,
        actor=principal.subject,
        project_id=goal.project_id,
        operation=f"goals.progress:{goal_id}",
        request_digest=digest,
    )


@router.post("/goals/{goal_id}/mission-outcomes")
async def record_goal_mission_outcome(
    goal_id: str,
    body: GoalMissionOutcomeRequest,
    principal: Principal = Depends(get_principal),
    auth: AuthRegistry = Depends(get_auth),
    store: ProductStore = Depends(get_store),
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> dict[str, Any]:
    from swarm.goals.models import GoalError

    try:
        goal = store.goal_store().get(goal_id)
    except KeyError as exc:
        raise ApiError("not_found", "goal not found", status_code=404) from exc
    auth.require_project(principal, goal.project_id)
    key = body.idempotency_key or idempotency_key
    digest = payload_hash(body.model_dump(mode="json", exclude={"idempotency_key"}))
    cached = store.recall_idempotent(
        key,
        actor=principal.subject,
        project_id=goal.project_id,
        operation=f"goals.mission_outcome:{goal_id}",
        request_digest=digest,
    )
    if cached is not None:
        return cached
    try:
        updated = store.goal_store().record_mission_outcome(
            goal_id,
            mission_id=body.mission_id,
            outcome=body.outcome,
            actor=principal.subject,
            notes=body.notes,
            evidence_refs=list(body.evidence_refs),
        )
    except GoalError as exc:
        raise ApiError("goal_outcome_error", str(exc), status_code=409) from exc
    result = {
        "goal": updated.model_dump(mode="json"),
        "mission_completion_implies_goal_achievement": False,
    }
    return store.store_idempotent(
        key,
        result,
        actor=principal.subject,
        project_id=goal.project_id,
        operation=f"goals.mission_outcome:{goal_id}",
        request_digest=digest,
    )


@router.post("/goals/{goal_id}/missions")
async def link_goal_mission(
    goal_id: str,
    body: GoalLinkMissionRequest,
    principal: Principal = Depends(get_principal),
    auth: AuthRegistry = Depends(get_auth),
    store: ProductStore = Depends(get_store),
) -> dict[str, Any]:
    try:
        goal = store.goal_store().get(goal_id)
    except KeyError as exc:
        raise ApiError("not_found", "goal not found", status_code=404) from exc
    auth.require_project(principal, goal.project_id)
    mission = store.get_mission(body.mission_id)
    auth.require_project(principal, mission.project_id)
    updated = store.goal_store().link_mission(goal_id, body.mission_id)
    return {"goal": updated.model_dump(mode="json")}


@router.post("/goals/{goal_id}/pursuit/tick")
async def pursuit_tick(
    goal_id: str,
    body: PursuitTickRequest,
    principal: Principal = Depends(get_principal),
    auth: AuthRegistry = Depends(get_auth),
    store: ProductStore = Depends(get_store),
) -> dict[str, Any]:
    """Advance one V1.9 autonomous pursuit cycle.

    Operational mode dispatches a durable native mission and returns pending
    until worker execution + protected verification succeed (R20-01). Fixture/mock
    mode may still use RecordingExecutor for explicit demos.
    """
    store.require_durable_writes()
    try:
        goal = store.goal_store().get(goal_id)
    except KeyError as exc:
        raise ApiError("not_found", "goal not found", status_code=404) from exc
    auth.require_project(principal, goal.project_id)
    engine = store.pursuit_engine()
    cycle = engine.tick(goal_id, force=body.force)
    refreshed = store.goal_store().get(goal_id)
    return {
        "cycle": cycle.model_dump(mode="json"),
        "goal": refreshed.model_dump(mode="json"),
    }


@router.get("/goals/{goal_id}/pursuit")
async def pursuit_status(
    goal_id: str,
    principal: Principal = Depends(get_principal),
    auth: AuthRegistry = Depends(get_auth),
    store: ProductStore = Depends(get_store),
) -> dict[str, Any]:
    try:
        goal = store.goal_store().get(goal_id)
    except KeyError as exc:
        raise ApiError("not_found", "goal not found", status_code=404) from exc
    auth.require_project(principal, goal.project_id)
    engine = store.pursuit_engine()
    schedule = engine.scheduler.get(goal_id)
    return {
        "goal_id": goal_id,
        "schedule": schedule.model_dump(mode="json"),
        "history": [c.model_dump(mode="json") for c in engine.history(goal_id)],
        "commitments": engine.commitments(goal_id),
        "adopted_lessons": [
            lesson.model_dump(mode="json") for lesson in engine.lessons.adopted_for_goal(goal_id)
        ],
    }


@router.post("/goals/{goal_id}/pursuit/lessons")
async def propose_pursuit_lesson(
    goal_id: str,
    body: PursuitLessonProposeRequest,
    principal: Principal = Depends(get_principal),
    auth: AuthRegistry = Depends(get_auth),
    store: ProductStore = Depends(get_store),
) -> dict[str, Any]:
    try:
        goal = store.goal_store().get(goal_id)
    except KeyError as exc:
        raise ApiError("not_found", "goal not found", status_code=404) from exc
    auth.require_project(principal, goal.project_id)
    from swarm.pursuit.models import PursuitLesson

    engine = store.pursuit_engine()
    lesson = engine.lessons.propose(
        PursuitLesson(
            goal_id=goal_id,
            summary=body.summary,
            scope=list(body.scope),
            evidence_refs=list(body.evidence_refs),
            strategy_delta=body.strategy_delta,
        )
    )
    return {"lesson": lesson.model_dump(mode="json")}


@router.post("/goals/{goal_id}/pursuit/lessons/{lesson_id}/evaluate")
async def evaluate_pursuit_lesson(
    goal_id: str,
    lesson_id: str,
    body: PursuitLessonEvaluateRequest,
    principal: Principal = Depends(get_principal),
    auth: AuthRegistry = Depends(get_auth),
    store: ProductStore = Depends(get_store),
) -> dict[str, Any]:
    try:
        goal = store.goal_store().get(goal_id)
    except KeyError as exc:
        raise ApiError("not_found", "goal not found", status_code=404) from exc
    auth.require_project(principal, goal.project_id)
    from swarm.pursuit.learning import PursuitLearningError

    engine = store.pursuit_engine()
    try:
        lesson = engine.lessons.evaluate(
            lesson_id,
            holdout_check_id=body.holdout_check_id,
            holdout_passed=body.holdout_passed,
        )
    except PursuitLearningError as exc:
        raise ApiError("lesson_error", str(exc), status_code=409) from exc
    return {"lesson": lesson.model_dump(mode="json")}


@router.post("/goals/{goal_id}/pursuit/lessons/{lesson_id}/adopt")
async def adopt_pursuit_lesson(
    goal_id: str,
    lesson_id: str,
    principal: Principal = Depends(get_principal),
    auth: AuthRegistry = Depends(get_auth),
    store: ProductStore = Depends(get_store),
) -> dict[str, Any]:
    try:
        goal = store.goal_store().get(goal_id)
    except KeyError as exc:
        raise ApiError("not_found", "goal not found", status_code=404) from exc
    auth.require_project(principal, goal.project_id)
    from swarm.pursuit.learning import PursuitLearningError

    engine = store.pursuit_engine()
    try:
        lesson = engine.lessons.adopt(lesson_id, current_strategy=goal.strategy)
        new_strategy = engine.lessons.applied_strategy(goal_id, goal.strategy)
        store.goal_store().apply_strategy(
            goal_id,
            strategy=new_strategy,
            actor=principal.subject,
            reason=f"lesson_adopted:{lesson_id}",
        )
    except PursuitLearningError as exc:
        raise ApiError("lesson_error", str(exc), status_code=409) from exc
    return {"lesson": lesson.model_dump(mode="json"), "strategy": new_strategy}


@router.post("/goals/{goal_id}/pursuit/lessons/{lesson_id}/rollback")
async def rollback_pursuit_lesson(
    goal_id: str,
    lesson_id: str,
    principal: Principal = Depends(get_principal),
    auth: AuthRegistry = Depends(get_auth),
    store: ProductStore = Depends(get_store),
) -> dict[str, Any]:
    try:
        goal = store.goal_store().get(goal_id)
    except KeyError as exc:
        raise ApiError("not_found", "goal not found", status_code=404) from exc
    auth.require_project(principal, goal.project_id)
    from swarm.pursuit.learning import PursuitLearningError

    engine = store.pursuit_engine()
    try:
        lesson = engine.lessons.rollback(lesson_id)
        restored = engine.lessons.applied_strategy(goal_id, lesson.prior_strategy or "")
        store.goal_store().apply_strategy(
            goal_id,
            strategy=restored,
            actor=principal.subject,
            reason=f"lesson_rolled_back:{lesson_id}",
        )
    except PursuitLearningError as exc:
        raise ApiError("lesson_error", str(exc), status_code=409) from exc
    return {"lesson": lesson.model_dump(mode="json"), "strategy": restored}


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
        project_id = sorted(principal.project_ids)[0] if principal.project_ids else new_id("proj_")
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
    if "admin" in principal.roles:
        return {"events": log.list_events()}
    # Non-admin without project_id: only the principal's projects; never unscoped events.
    events: list[dict[str, Any]] = []
    for pid in sorted(principal.project_ids):
        events.extend(log.list_events(project_id=pid))
    events.sort(key=lambda e: (str(e.get("at")), str(e.get("event_id"))))
    return {"events": events[-100:]}


@router.post("/release/candidate-freeze")
async def freeze_candidate(
    principal: Principal = Depends(get_principal),
) -> dict[str, Any]:
    if "admin" not in principal.roles:
        raise ApiError("forbidden_admin", "admin role required", status_code=403)
    import subprocess
    from pathlib import Path

    from swarm.release.candidate import CURRENT_SCHEMA_REVISION, CandidateFreezer

    root = Path(__file__).resolve().parents[3]
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    return (
        CandidateFreezer(root)
        .freeze(source_sha=sha, schema_revision=CURRENT_SCHEMA_REVISION)
        .to_dict()
    )
