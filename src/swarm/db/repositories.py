"""Domain repositories with optimistic graph versioning."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Select, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from swarm.contracts.common import new_id
from swarm.contracts.mission import GraphProposal, Mission, TaskSpec
from swarm.contracts.provider import AttemptReceipt, Reservation
from swarm.contracts.workspace import ArtifactRef, EventEnvelope, Finding
from swarm.db.models import (
    ArtifactMetaRow,
    AttemptReceiptRow,
    EventRow,
    FindingRow,
    GoalCriterionVerdictRow,
    GoalRow,
    GraphRevisionRow,
    MissionRow,
    OutboxRow,
    PursuitCycleRow,
    PursuitDedupeRow,
    PursuitScheduleRow,
    ReservationRow,
    TaskRow,
)


class GraphRevisionConflict(RuntimeError):
    pass


class MissionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def insert(self, mission: Mission) -> MissionRow:
        row = MissionRow(
            id=mission.id,
            project_id=mission.project_id,
            schema_version=mission.schema_version,
            objective=mission.objective,
            status=mission.status.value,
            revision=mission.revision,
            cancellation_generation=mission.cancellation_generation,
            resource_policy_id=mission.resource_policy_id,
            max_wall_time_seconds=mission.max_wall_time_seconds,
            max_graph_nodes=mission.max_graph_nodes,
            max_active_sessions=mission.max_active_sessions,
            max_model_calls=mission.max_model_calls,
            total_token_envelope=mission.total_token_envelope,
            acceptance_receipt_id=mission.acceptance_receipt_id,
            payload=mission.model_dump(mode="json"),
        )
        self.session.add(row)
        return row

    def get(self, mission_id: str) -> MissionRow | None:
        return self.session.get(MissionRow, mission_id)

    def commit_graph_revision(self, proposal: GraphProposal) -> GraphRevisionRow:
        mission = self.get(proposal.mission_id)
        if mission is None:
            raise KeyError(proposal.mission_id)
        if mission.revision != proposal.based_on_revision:
            raise GraphRevisionConflict(
                f"expected revision {proposal.based_on_revision}, found {mission.revision}"
            )
        new_revision = mission.revision + 1
        mission.revision = new_revision
        rev = GraphRevisionRow(
            id=new_id("gr_"),
            mission_id=proposal.mission_id,
            revision=new_revision,
            based_on_revision=proposal.based_on_revision,
            author_session_id=proposal.author_session_id,
            operation=proposal.operation.value,
            rationale_summary=proposal.rationale_summary,
            payload=proposal.model_dump(mode="json"),
        )
        self.session.add(rev)
        for task in proposal.task_specs:
            self._upsert_task(task, graph_revision=new_revision)
        return rev

    def _upsert_task(self, task: TaskSpec, *, graph_revision: int) -> TaskRow:
        existing = self.session.get(TaskRow, task.id)
        if existing is None:
            row = TaskRow(
                id=task.id,
                project_id=task.project_id,
                mission_id=task.mission_id,
                parent_task_id=task.parent_task_id,
                objective=task.objective,
                task_family=task.task_family,
                status=task.status.value,
                graph_revision=graph_revision,
                priority=task.priority,
                scopes=list(task.scopes),
                dependency_ids=list(task.dependency_ids),
                payload=task.model_dump(mode="json"),
            )
            self.session.add(row)
            return row
        existing.objective = task.objective
        existing.status = task.status.value
        existing.graph_revision = graph_revision
        existing.priority = task.priority
        existing.scopes = list(task.scopes)
        existing.dependency_ids = list(task.dependency_ids)
        existing.payload = task.model_dump(mode="json")
        return existing


class FindingRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def append(self, finding: Finding, *, scopes: list[str] | None = None) -> FindingRow:
        row = FindingRow(
            id=finding.id,
            project_id=finding.project_id,
            task_id=finding.task_id,
            author=finding.author,
            status=finding.status.value,
            content=finding.content,
            artifact_ref=finding.artifact_ref,
            acl=list(finding.acl),
            scopes=scopes or list(finding.acl),
            payload=finding.model_dump(mode="json"),
        )
        self.session.add(row)
        return row

    def query_scoped(self, project_id: str, allowed_scopes: set[str]) -> list[FindingRow]:
        stmt: Select[tuple[FindingRow]] = select(FindingRow).where(
            FindingRow.project_id == project_id
        )
        rows = list(self.session.scalars(stmt))
        return [r for r in rows if allowed_scopes.intersection(set(r.scopes or []))]


class ArtifactRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def put_metadata(self, artifact: ArtifactRef) -> ArtifactMetaRow:
        row = ArtifactMetaRow(
            id=artifact.id,
            content_hash=artifact.content_hash,
            uri=artifact.uri,
            media_type=artifact.media_type,
            byte_length=artifact.byte_length,
            owner_scope=artifact.owner_scope,
            retention_class=artifact.retention_class,
        )
        self.session.add(row)
        return row


class LedgerRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def insert_reservation(self, reservation: Reservation) -> ReservationRow:
        row = ReservationRow(
            reservation_id=reservation.reservation_id,
            logical_call_id=reservation.logical_call_id,
            attempt_id=reservation.attempt_id,
            route_id=reservation.route_id,
            state=reservation.state.value,
            phase=reservation.phase.value,
            fence_token=reservation.fence_token,
            expires_at=reservation.expires_at,
            payload=reservation.model_dump(mode="json"),
        )
        self.session.add(row)
        return row

    def insert_receipt(self, receipt: AttemptReceipt) -> AttemptReceiptRow:
        row = AttemptReceiptRow(
            network_attempt_id=receipt.network_attempt_id,
            logical_call_id=receipt.logical_call_id,
            idempotency_key=receipt.idempotency_key,
            provider_request_id=receipt.provider_request_id,
            actual_route=receipt.actual_route,
            send_phase=receipt.send_phase.value,
            settlement_state=receipt.settlement_state.value,
            error_class=receipt.error_class.value if receipt.error_class else None,
            started_at=receipt.started_at,
            finished_at=receipt.finished_at,
            payload=receipt.model_dump(mode="json"),
        )
        self.session.add(row)
        try:
            self.session.flush()
        except IntegrityError:
            raise
        return row


class EventRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def append(self, event: EventEnvelope) -> EventRow:
        row = EventRow(
            id=event.id,
            project_id=event.project_id,
            type=event.type,
            actor=event.actor,
            mission_id=event.mission_id,
            task_id=event.task_id,
            attempt_id=event.attempt_id,
            payload=event.payload,
            causation_id=event.causation_id,
            correlation_id=event.correlation_id,
            dedupe_key=event.dedupe_key,
            occurred_at=event.occurred_at,
        )
        self.session.add(row)
        return row

    def list_after(
        self, project_id: str, *, after_id: str | None = None, limit: int = 100
    ) -> list[EventRow]:
        stmt = (
            select(EventRow)
            .where(EventRow.project_id == project_id)
            .order_by(EventRow.occurred_at)
        )
        if after_id:
            anchor = self.session.get(EventRow, after_id)
            if anchor is not None:
                stmt = stmt.where(EventRow.occurred_at > anchor.occurred_at)
        stmt = stmt.limit(limit)
        return list(self.session.scalars(stmt))


class OutboxRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def enqueue(
        self,
        *,
        stable_workflow_id: str,
        aggregate_type: str,
        aggregate_id: str,
        event_type: str,
        payload: dict[str, Any],
    ) -> OutboxRow:
        row = OutboxRow(
            id=new_id("ob_"),
            stable_workflow_id=stable_workflow_id,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            event_type=event_type,
            payload=payload,
            status="pending",
        )
        self.session.add(row)
        return row

    def claim_pending(self, limit: int = 50) -> list[OutboxRow]:
        stmt = (
            select(OutboxRow)
            .where(OutboxRow.status == "pending")
            .order_by(OutboxRow.created_at)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        return list(self.session.scalars(stmt))

    def mark_published(self, row: OutboxRow) -> None:
        row.status = "published"
        row.published_at = datetime.now(UTC)

    def mark_failed(self, row: OutboxRow, error: str) -> None:
        row.status = "pending"
        row.attempts += 1
        row.last_error = error


class GoalAuthorityRepository:
    """PostgreSQL goal authority — optimistic revision, synthetic achievement flags."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert_goal(
        self,
        *,
        goal_id: str,
        project_id: str,
        status: str,
        kind: str,
        revision: int,
        achievement_authority: str | None,
        payload: dict[str, Any],
    ) -> GoalRow:
        existing = self.session.get(GoalRow, goal_id)
        if existing is None:
            row = GoalRow(
                id=goal_id,
                project_id=project_id,
                status=status,
                kind=kind,
                revision=revision,
                achievement_authority=achievement_authority,
                payload=payload,
            )
            self.session.add(row)
            return row
        if existing.revision > revision:
            raise GraphRevisionConflict(
                f"goal {goal_id}: stale write revision {revision} < {existing.revision}"
            )
        existing.status = status
        existing.kind = kind
        existing.revision = revision
        existing.achievement_authority = achievement_authority
        existing.payload = payload
        return existing

    def get(self, goal_id: str) -> GoalRow | None:
        return self.session.get(GoalRow, goal_id)

    def record_criterion_verdict(
        self,
        *,
        goal_id: str,
        criterion_key: str,
        goal_revision: int,
        state: str,
        authority: str,
        evidence_digest: str | None = None,
        verifier_receipt_id: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> GoalCriterionVerdictRow:
        row = GoalCriterionVerdictRow(
            verdict_id=new_id("gcv_"),
            goal_id=goal_id,
            criterion_key=criterion_key,
            goal_revision=goal_revision,
            state=state,
            authority=authority,
            evidence_digest=evidence_digest,
            verifier_receipt_id=verifier_receipt_id,
            payload=payload or {},
        )
        self.session.add(row)
        try:
            self.session.flush()
        except IntegrityError:
            raise
        return row


class PursuitStateRepository:
    """Persist pursuit cycles, schedules and dedupe keys transactionally."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def append_cycle(
        self,
        *,
        cycle_id: str,
        goal_id: str,
        phase: str,
        decided_kind: str | None,
        payload: dict[str, Any],
    ) -> PursuitCycleRow:
        row = PursuitCycleRow(
            cycle_id=cycle_id,
            goal_id=goal_id,
            phase=phase,
            decided_kind=decided_kind,
            payload=payload,
        )
        self.session.add(row)
        return row

    def list_cycles(self, goal_id: str, *, limit: int = 200) -> list[PursuitCycleRow]:
        stmt = (
            select(PursuitCycleRow)
            .where(PursuitCycleRow.goal_id == goal_id)
            .order_by(PursuitCycleRow.created_at)
            .limit(limit)
        )
        return list(self.session.scalars(stmt))

    def upsert_schedule(
        self,
        *,
        goal_id: str,
        next_due_at: float,
        backoff_seconds: float = 0.0,
        consecutive_failures: int = 0,
        consecutive_no_progress: int = 0,
        last_cycle_at: float | None = None,
        wait_reason: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> PursuitScheduleRow:
        existing = self.session.get(PursuitScheduleRow, goal_id)
        if existing is None:
            row = PursuitScheduleRow(
                goal_id=goal_id,
                next_due_at=next_due_at,
                backoff_seconds=backoff_seconds,
                consecutive_failures=consecutive_failures,
                consecutive_no_progress=consecutive_no_progress,
                last_cycle_at=last_cycle_at,
                wait_reason=wait_reason,
                payload=payload or {},
            )
            self.session.add(row)
            return row
        existing.next_due_at = next_due_at
        existing.backoff_seconds = backoff_seconds
        existing.consecutive_failures = consecutive_failures
        existing.consecutive_no_progress = consecutive_no_progress
        existing.last_cycle_at = last_cycle_at
        existing.wait_reason = wait_reason
        existing.payload = payload or {}
        return existing

    def put_dedupe(
        self,
        *,
        goal_id: str,
        dedupe_key: str,
        proposal_id: str,
        payload: dict[str, Any] | None = None,
    ) -> PursuitDedupeRow:
        existing = self.session.scalar(
            select(PursuitDedupeRow).where(PursuitDedupeRow.dedupe_key == dedupe_key)
        )
        if existing is not None:
            if existing.proposal_id != proposal_id:
                raise GraphRevisionConflict(
                    f"pursuit_dedupe_conflict:{dedupe_key}"
                )
            return existing
        row = PursuitDedupeRow(
            dedupe_id=new_id("pdd_"),
            goal_id=goal_id,
            dedupe_key=dedupe_key,
            proposal_id=proposal_id,
            payload=payload or {},
        )
        self.session.add(row)
        try:
            self.session.flush()
        except IntegrityError:
            raise
        return row

