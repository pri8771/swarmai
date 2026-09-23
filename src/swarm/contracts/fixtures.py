"""Canonical deterministic fixtures for contract tests."""

from __future__ import annotations

from datetime import timedelta

from swarm.contracts.common import payload_hash, utc_now
from swarm.contracts.enums import (
    AccountStatus,
    ActionOutcome,
    AvailabilityStatus,
    BillingMode,
    FindingStatus,
    GraphOperation,
    MissionStatus,
    PurposeEligibility,
    QuotaDimension,
    ReservationPhase,
    RiskLevel,
    RoutingState,
    SettlementState,
    WindowType,
)
from swarm.contracts.mission import (
    AgentProfile,
    AgentSession,
    GraphProposal,
    Mission,
    SizeFeatures,
    TaskAttempt,
    TaskSpec,
)
from swarm.contracts.provider import (
    AttemptReceipt,
    BucketAmount,
    InferenceRequest,
    NormalizedUsage,
    ProviderAccount,
    QuotaBucket,
    Reservation,
    RouteSnapshot,
)
from swarm.contracts.workspace import (
    ActionReceipt,
    Approval,
    ArtifactRef,
    CapabilityProfile,
    ContextBundle,
    EvalResult,
    EventEnvelope,
    Finding,
    ToolCall,
    WorkerLease,
)


def sample_mission() -> Mission:
    return Mission(
        id="mission_demo_001",
        project_id="proj_demo",
        objective="Investigate failing parser and produce a verified patch",
        acceptance_criteria=["tests pass", "independent review accepted"],
        allowed_capabilities=["code.read", "code.write", "tests.run"],
        data_scope_ids=["scope_repo_demo"],
        resource_policy_id="policy_default",
        max_wall_time_seconds=3600,
        max_graph_nodes=50,
        max_active_sessions=8,
        max_model_calls=200,
        total_token_envelope=500_000,
        status=MissionStatus.DRAFT,
    )


def sample_task(mission_id: str = "mission_demo_001") -> TaskSpec:
    return TaskSpec(
        id="task_demo_001",
        project_id="proj_demo",
        mission_id=mission_id,
        objective="Extract failing cases from parser tests",
        task_family="extraction",
        size_features=SizeFeatures(entity_count=3, file_count=2, risk_level=RiskLevel.LOW),
        output_schema_id="schema.extraction.v1",
        acceptance_check_ids=["check.gold_match"],
        quality_policy_id="quality.default",
        required_capabilities=["code.read"],
        scopes=["scope_repo_demo"],
    )


def sample_provider_account() -> ProviderAccount:
    return ProviderAccount(
        id="pa_openrouter_demo",
        service_id="openrouter",
        account_alias="personal_unverified",
        secret_ref_names=["OPENROUTER_API_KEY"],
        owner="operator",
        account_status=AccountStatus.CATALOGED,
        purpose_eligibility=PurposeEligibility.UNKNOWN,
        billing_mode=BillingMode.UNKNOWN,
    )


def sample_route() -> RouteSnapshot:
    return RouteSnapshot(
        route_id="rt_fake_alpha",
        provider="fake",
        account_id="pa_openrouter_demo",
        model_id="fake-alpha-v1",
        resolved_model_revision="fake-alpha-v1.0",
        endpoint="fake://alpha",
        billing_origin="mock",
        capability_claims=["chat", "tools", "structured"],
        observed_capabilities=["chat", "tools", "structured"],
        availability_status=AvailabilityStatus.AVAILABLE,
        quota_bucket_ids=["qb_demo_requests"],
        status="mock_enabled",
    )


def sample_route_beta() -> RouteSnapshot:
    return RouteSnapshot(
        route_id="rt_fake_beta",
        provider="fake",
        account_id="pa_openrouter_demo",
        model_id="fake-beta-v1",
        resolved_model_revision="fake-beta-v1.0",
        endpoint="fake://beta",
        billing_origin="mock",
        capability_claims=["chat", "tools", "structured"],
        observed_capabilities=["chat", "tools", "structured"],
        availability_status=AvailabilityStatus.AVAILABLE,
        quota_bucket_ids=["qb_demo_requests"],
        status="mock_enabled",
    )


def sample_quota() -> QuotaBucket:
    return QuotaBucket(
        bucket_id="qb_demo_requests",
        scope_type="account",
        scope_id="pa_openrouter_demo",
        dimension=QuotaDimension.REQUESTS,
        limit=100,
        remaining=100,
        window_type=WindowType.FIXED,
        source="fixture",
        confidence="exact",
    )


def sample_unknown_quota() -> QuotaBucket:
    return QuotaBucket(
        bucket_id="qb_unknown",
        scope_type="account",
        scope_id="pa_unknown",
        dimension=QuotaDimension.CREDIT,
        limit=None,
        remaining=None,
        window_type=WindowType.UNKNOWN,
        source="unobserved",
        confidence="unknown",
    )


def sample_reservation(route_id: str = "rt_fake_alpha") -> Reservation:
    return Reservation(
        logical_call_id="lc_demo_001",
        attempt_id="att_demo_001",
        route_id=route_id,
        bucket_amounts=[
            BucketAmount(
                bucket_id="qb_demo_requests",
                dimension=QuotaDimension.REQUESTS,
                amount=1,
            )
        ],
        expires_at=utc_now() + timedelta(minutes=5),
    )


def sample_inference_request(route_id: str | None = "rt_fake_alpha") -> InferenceRequest:
    messages = [{"role": "user", "content": "summarize the failing parser cases"}]
    req = InferenceRequest(
        project_id="proj_demo",
        attempt_id="att_demo_001",
        route_id=route_id,
        purpose="mission",
        messages=messages,
        estimated_input_tokens=40,
        max_output_tokens=200,
        tools_requested=["echo_count"],
        secret_ref_names=["OPENROUTER_API_KEY"],
    )
    req.payload_hash = payload_hash({"messages": messages, "purpose": "mission"})
    return req


def sample_receipt(route_id: str = "rt_fake_alpha") -> AttemptReceipt:
    return AttemptReceipt(
        logical_call_id="lc_demo_001",
        send_phase=ReservationPhase.SETTLED,
        finished_at=utc_now(),
        normalized_usage=NormalizedUsage(input_tokens=40, output_tokens=12, total_tokens=52),
        actual_route=route_id,
        settlement_state=SettlementState.SETTLED,
    )


def all_required_type_instances() -> dict[str, object]:
    mission = sample_mission()
    task = sample_task()
    return {
        "Mission": mission,
        "TaskSpec": task,
        "TaskAttempt": TaskAttempt(task_id=task.id, agent_profile_id="ap_demo"),
        "SizeFeatures": task.size_features,
        "AgentProfile": AgentProfile(
            id="ap_demo",
            role="planner",
            instructions_version="v1",
            context_policy="scoped",
            delegation_policy="propose_only",
        ),
        "AgentSession": AgentSession(agent_profile_id="ap_demo", assigned_task_id=task.id),
        "GraphProposal": GraphProposal(
            project_id="proj_demo",
            mission_id=mission.id,
            based_on_revision=1,
            author_session_id="as_demo",
            operation=GraphOperation.SPAWN,
            rationale_summary="spawn extraction worker",
            task_specs=[task],
        ),
        "ProviderAccount": sample_provider_account(),
        "RouteSnapshot": sample_route(),
        "QuotaBucket": sample_quota(),
        "Reservation": sample_reservation(),
        "AttemptReceipt": sample_receipt(),
        "CapabilityProfile": CapabilityProfile(
            profile_key="rt_fake_alpha|extraction|S|harness1|prompt1|tools1|data1",
            route_fingerprint="rt_fake_alpha",
            task_family="extraction",
            size_features=task.size_features,
            harness_version="1",
            prompt_version="1",
            tool_protocol="tools1",
            dataset_version="data1",
            routing_state=RoutingState.UNASSESSED,
        ),
        "EvalResult": EvalResult(
            distinct_case_id="case_001",
            split="dev",
            route_fingerprint="rt_fake_alpha",
            model_fingerprint="fake-alpha-v1",
            exact_prompt_hash="abc",
            outcome="pass",
            grader_version="1",
            correctness=True,
        ),
        "Finding": Finding(
            project_id="proj_demo",
            content="parser fails on nested lists",
            author="as_demo",
            task_id=task.id,
            status=FindingStatus.HYPOTHESIS,
        ),
        "ArtifactRef": ArtifactRef(
            content_hash="deadbeef",
            uri="memory://artifact/demo",
            media_type="text/plain",
            byte_length=12,
            owner_scope="scope_repo_demo",
            retention_class="mission",
        ),
        "ContextBundle": ContextBundle(
            mission_id=mission.id,
            task_id=task.id,
            graph_revision=1,
            policy_version="v1",
        ),
        "WorkerLease": WorkerLease(
            node_identity="local-dev",
            architecture="arm64",
            runtime_version="0.1.0",
            capacity_units=1.0,
        ),
        "ToolCall": ToolCall(
            task_id=task.id,
            attempt_id="att_demo_001",
            tool_version="echo_count@1",
            normalized_args={"text": "hi"},
            payload_hash="hash",
            lease_generation=1,
        ),
        "Approval": Approval(
            payload_hash="hash",
            permitted_operation="publish",
            destination="local",
            grantor="operator",
            project_id="proj_demo",
            expires_at=utc_now() + timedelta(hours=1),
        ),
        "ActionReceipt": ActionReceipt(
            operation_id="op_demo",
            outcome=ActionOutcome.SUCCEEDED,
        ),
        "EventEnvelope": EventEnvelope(
            project_id="proj_demo",
            actor="controller",
            type="mission.created",
            mission_id=mission.id,
            payload={"status": "draft"},
        ),
        "InferenceRequest": sample_inference_request(),
    }
