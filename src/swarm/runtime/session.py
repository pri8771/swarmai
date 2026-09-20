"""Agent session runtime — brokered model calls, tools, checkpoints."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from swarm.broker.broker import SharedInferenceBroker
from swarm.broker.errors import AmbiguousSendError, BrokerBypassError, PolicyDeniedError
from swarm.contracts.common import utc_now
from swarm.contracts.enums import (
    AttemptStatus,
    FindingStatus,
    GraphOperation,
    TaskStatus,
)
from swarm.contracts.mission import (
    AgentProfile,
    GraphProposal,
    TaskAttempt,
    TaskSpec,
)
from swarm.contracts.provider import InferenceRequest, RouteSnapshot
from swarm.contracts.workspace import (
    ActionReceipt,
    ContextBundle,
    Finding,
    ToolCall,
    WorkerLease,
)
from swarm.runtime.capacity import CapacityPool, ResourceLimits
from swarm.runtime.checkpoint import CheckpointStore, SessionCheckpoint
from swarm.runtime.registry import SessionRegistry
from swarm.tools.gateway import ToolGateway


class CancelledError(RuntimeError):
    pass


class UnsupportedFeatureError(RuntimeError):
    pass


class HiddenCallDeniedError(BrokerBypassError):
    """Summarization/judge/embedding outside broker is denied."""


@dataclass
class SessionDeps:
    """Runtime-only holders — never persisted in checkpoints."""

    runtime_client: object = field(default_factory=object)
    secret_ref_name: str = "FAKE_API_KEY"


@dataclass
class RunResult:
    attempt: TaskAttempt
    checkpoint_id: str | None
    findings: list[Finding]
    proposals: list[GraphProposal]
    receipts: list[ActionReceipt]
    decision_trace: list[dict[str, Any]]


class AgentSessionRuntime:
    """Implements Runtime protocol against broker + workspace + tools."""

    def __init__(
        self,
        broker: SharedInferenceBroker,
        *,
        tool_gateway: ToolGateway | None = None,
        workspace: Any | None = None,
        limits: ResourceLimits | None = None,
        checkpoint_store: CheckpointStore | None = None,
    ) -> None:
        self.broker = broker
        self.tools = tool_gateway
        self.workspace = workspace
        self.limits = limits or ResourceLimits()
        self.checkpoints = checkpoint_store or CheckpointStore()
        self.registry = SessionRegistry()
        self.capacity = CapacityPool(limits=self.limits)
        self._attempts: dict[str, TaskAttempt] = {}
        self._cancel: set[str] = set()
        self._interrupted: set[str] = set()
        self._sessions_by_attempt: dict[str, str] = {}
        self._deps: dict[str, SessionDeps] = {}
        self._traces: dict[str, list[dict[str, Any]]] = {}

    def _trace(self, attempt_id: str, event: str, **payload: Any) -> None:
        row = {"event": event, **payload, "at": utc_now().isoformat()}
        self._traces.setdefault(attempt_id, []).append(row)

    async def run_task(
        self,
        task: TaskSpec,
        context: ContextBundle,
        lease: WorkerLease,
        *,
        profile: AgentProfile,
        route: RouteSnapshot | None = None,
        deterministic: bool = False,
        allow_hidden_summary: bool = False,
    ) -> TaskAttempt:
        if allow_hidden_summary:
            raise HiddenCallDeniedError("hidden_summarization_denied")

        session = self.registry.open_session(profile, task_id=task.id)
        self.capacity.acquire(session.id)
        attempt = TaskAttempt(
            task_id=task.id,
            agent_profile_id=profile.id,
            selected_route_id=route.route_id if route else None,
            worker_id=lease.worker_id,
            lease_generation=lease.lease_generation,
            status=AttemptStatus.RUNNING,
        )
        self._attempts[attempt.attempt_id] = attempt
        self._sessions_by_attempt[attempt.attempt_id] = session.id
        self._deps[attempt.attempt_id] = SessionDeps()
        self._trace(
            attempt.attempt_id,
            "started",
            role=profile.role,
            route_id=attempt.selected_route_id,
            task_family=task.task_family,
        )

        try:
            if task.status == TaskStatus.WAITING_CHILDREN or task.dependency_ids:
                # Parent waiting for children releases runnable capacity.
                unfinished = list(task.dependency_ids)
                if unfinished:
                    self.capacity.mark_waiting_children(session.id)
                    attempt.status = AttemptStatus.PENDING
                    attempt.blocked_reason = "waiting_for_children"
                    self._trace(attempt.attempt_id, "waiting_children", children=unfinished)
                    cp = self._checkpoint(
                        session.id,
                        profile,
                        task,
                        attempt,
                        waiting=unfinished,
                    )
                    session.checkpoint_ref = cp
                    return attempt

            if attempt.attempt_id in self._cancel:
                raise CancelledError(attempt.attempt_id)

            findings: list[Finding] = []
            proposals: list[GraphProposal] = []
            receipts: list[ActionReceipt] = []
            model_calls = 0

            if deterministic or route is None:
                finding = Finding(
                    project_id=task.project_id,
                    content=f"deterministic:{task.objective}",
                    author=session.id,
                    task_id=task.id,
                    status=FindingStatus.HYPOTHESIS,
                    acl=list(task.scopes),
                )
                if self.workspace is not None:
                    finding = await self.workspace.append_finding(finding)
                findings.append(finding)
                self._trace(attempt.attempt_id, "deterministic_result", finding_id=finding.id)
            else:
                # Capability gate: unsupported features fail explicitly.
                required = set(task.required_capabilities)
                claimed = set(route.capability_claims) | set(route.observed_capabilities)
                missing = required - claimed
                if missing:
                    raise UnsupportedFeatureError(f"unsupported:{sorted(missing)}")

                model_calls = await self._brokered_model_turn(
                    task, context, attempt, route, session.id
                )
                finding = Finding(
                    project_id=task.project_id,
                    content=f"model_result:{route.route_id}:{task.objective[:80]}",
                    author=session.id,
                    task_id=task.id,
                    status=FindingStatus.HYPOTHESIS,
                    acl=list(task.scopes),
                    source_ids=[route.route_id],
                )
                if self.workspace is not None:
                    finding = await self.workspace.append_finding(finding)
                findings.append(finding)

                if self.tools is not None and "tools" in claimed:
                    call = ToolCall(
                        task_id=task.id,
                        attempt_id=attempt.attempt_id,
                        tool_version="calc.add@1",
                        normalized_args={"a": 1, "b": 2},
                        payload_hash="pending",
                        scopes=list(task.scopes),
                        lease_generation=lease.lease_generation,
                    )
                    call = await self.tools.validate(call)
                    call = await self.tools.authorize(call)
                    receipt = await self.tools.execute_or_reconcile(call)
                    receipts.append(receipt)
                    self._trace(
                        attempt.attempt_id,
                        "tool_receipt",
                        operation_id=receipt.operation_id,
                        outcome=receipt.outcome.value,
                    )

                if profile.delegation_policy == "propose_spawn":
                    proposals.append(
                        GraphProposal(
                            project_id=task.project_id,
                            mission_id=task.mission_id,
                            based_on_revision=task.graph_revision,
                            author_session_id=session.id,
                            operation=GraphOperation.SPAWN,
                            rationale_summary="spawn child for verification",
                            task_specs=[],
                        )
                    )

            if attempt.attempt_id in self._interrupted:
                attempt.status = AttemptStatus.UNKNOWN
                attempt.blocked_reason = "interrupted_model_response"
                self._trace(attempt.attempt_id, "interrupted")
            elif attempt.attempt_id in self._cancel:
                raise CancelledError(attempt.attempt_id)
            else:
                attempt.status = AttemptStatus.SUCCEEDED
                attempt.completed_at = utc_now()

            cp = self._checkpoint(
                session.id,
                profile,
                task,
                attempt,
                model_calls=model_calls,
                finding_ids=[f.id for f in findings],
                tool_ops=[r.operation_id for r in receipts],
            )
            session.checkpoint_ref = cp
            session.status = "completed" if attempt.status == AttemptStatus.SUCCEEDED else "blocked"
            if route is not None:
                session.route_history.append(route.route_id)
            self.capacity.clear_waiting(session.id)
            return attempt
        except CancelledError:
            attempt.status = AttemptStatus.CANCELLED
            attempt.completed_at = utc_now()
            attempt.blocked_reason = "cancelled"
            self._trace(attempt.attempt_id, "cancelled")
            self._checkpoint(session.id, profile, task, attempt, cancel=True)
            return attempt
        except AmbiguousSendError as exc:
            attempt.status = AttemptStatus.UNKNOWN
            attempt.blocked_reason = f"ambiguous_send:{exc}"
            self._trace(attempt.attempt_id, "ambiguous_send")
            self._checkpoint(session.id, profile, task, attempt)
            return attempt
        except (UnsupportedFeatureError, PolicyDeniedError) as exc:
            attempt.status = AttemptStatus.FAILED
            attempt.completed_at = utc_now()
            attempt.blocked_reason = str(exc)
            self._trace(attempt.attempt_id, "failed", reason=str(exc))
            self._checkpoint(session.id, profile, task, attempt)
            return attempt
        finally:
            if attempt.status in {
                AttemptStatus.SUCCEEDED,
                AttemptStatus.FAILED,
                AttemptStatus.CANCELLED,
            }:
                self.capacity.release(session.id)

    async def _brokered_model_turn(
        self,
        task: TaskSpec,
        context: ContextBundle,
        attempt: TaskAttempt,
        route: RouteSnapshot,
        session_id: str,
    ) -> int:
        if attempt.attempt_id in self._cancel:
            raise CancelledError(attempt.attempt_id)
        prior_calls = len(
            [t for t in self._traces.get(attempt.attempt_id, []) if t.get("event") == "model_call"]
        )
        if prior_calls >= self.limits.max_model_calls:
            raise RuntimeError("max_model_calls")

        messages = [
            {"role": "system", "content": f"task={task.id} excerpts={len(context.excerpts)}"},
            {"role": "user", "content": task.objective},
        ]
        req = InferenceRequest(
            project_id=task.project_id,
            attempt_id=attempt.attempt_id,
            route_id=route.route_id,
            purpose="mission",
            messages=messages,
            estimated_input_tokens=context.token_estimate or 40,
            max_output_tokens=128,
            secret_ref_names=[self._deps[attempt.attempt_id].secret_ref_name],
        )
        eligible = await self.broker.assess(req)
        if not eligible:
            raise PolicyDeniedError("no_eligible_route")
        selected = next((r for r in eligible if r.route_id == route.route_id), eligible[0])
        # Resume must keep same route for same attempt; mismatch is a bug.
        if attempt.selected_route_id and selected.route_id != attempt.selected_route_id:
            raise RuntimeError("route_mismatch_on_attempt")
        ticket = await self.broker.reserve(req, selected)
        if attempt.attempt_id in self._interrupted:
            # Simulate interrupt after reserve / during send.
            raise AmbiguousSendError("interrupted_mid_send")
        receipt = await self.broker.invoke(ticket)
        self.broker.assert_all_calls_accounted()
        self._trace(
            attempt.attempt_id,
            "model_call",
            route_id=selected.route_id,
            reservation_id=ticket.reservation_id,
            settlement=receipt.settlement_state.value,
            session_id=session_id,
        )
        return prior_calls + 1

    def _checkpoint(
        self,
        session_id: str,
        profile: AgentProfile,
        task: TaskSpec,
        attempt: TaskAttempt,
        *,
        waiting: list[str] | None = None,
        model_calls: int = 0,
        finding_ids: list[str] | None = None,
        tool_ops: list[str] | None = None,
        cancel: bool = False,
    ) -> str:
        cp = SessionCheckpoint(
            session_id=session_id,
            agent_profile_id=profile.id,
            task_id=task.id,
            attempt_id=attempt.attempt_id,
            route_id=attempt.selected_route_id,
            task_status=task.status,
            attempt_status=attempt.status,
            model_calls=model_calls,
            tool_operation_ids=list(tool_ops or []),
            finding_ids=list(finding_ids or []),
            waiting_for_children=list(waiting or []),
            cancel_requested=cancel or attempt.attempt_id in self._cancel,
            decision_trace=list(self._traces.get(attempt.attempt_id, [])),
            resource_usage={"model_calls": model_calls},
        )
        # Ensure deps/runtime_client never appear.
        serial = cp.to_serializable()
        if "runtime_client" in serial:
            raise RuntimeError("runtime_client_leaked")
        return self.checkpoints.save(cp)

    async def resume(self, checkpoint: str) -> TaskAttempt:
        cp = self.checkpoints.load(checkpoint)
        attempt = self._attempts.get(cp.attempt_id)
        if attempt is None:
            attempt = TaskAttempt(
                attempt_id=cp.attempt_id,
                task_id=cp.task_id,
                agent_profile_id=cp.agent_profile_id,
                selected_route_id=cp.route_id,
                status=cp.attempt_status,
            )
            self._attempts[attempt.attempt_id] = attempt
        # Same attempt resumes same route — no silent reroute.
        if cp.route_id and attempt.selected_route_id and cp.route_id != attempt.selected_route_id:
            raise RuntimeError("resume_route_mismatch")
        attempt.selected_route_id = cp.route_id
        self._trace(attempt.attempt_id, "resumed", checkpoint_id=checkpoint, route_id=cp.route_id)
        # Tool state recovery: receipts already on gateway by operation id.
        if self.tools is not None:
            for op in cp.tool_operation_ids:
                try:
                    await self.tools.receipt(op)
                except KeyError:
                    self._trace(attempt.attempt_id, "tool_receipt_missing", operation_id=op)
        return attempt

    async def request_cancel(self, attempt_id: str) -> None:
        self._cancel.add(attempt_id)
        self._trace(attempt_id, "cancel_requested")

    def interrupt_model_response(self, attempt_id: str) -> None:
        """Test/helper: mark in-flight model response as interrupted."""
        self._interrupted.add(attempt_id)

    def safe_reroute_new_attempt(
        self, task: TaskSpec, profile: AgentProfile, new_route: RouteSnapshot
    ) -> TaskAttempt:
        """Explicit new attempt for authorized route change — never mutate old attempt route."""
        attempt = TaskAttempt(
            task_id=task.id,
            agent_profile_id=profile.id,
            selected_route_id=new_route.route_id,
            status=AttemptStatus.PENDING,
        )
        self._attempts[attempt.attempt_id] = attempt
        self._trace(
            attempt.attempt_id,
            "authorized_reroute",
            route_id=new_route.route_id,
            prior_task=task.id,
        )
        return attempt

    def decision_trace(self, attempt_id: str) -> list[dict[str, Any]]:
        return list(self._traces.get(attempt_id, []))
