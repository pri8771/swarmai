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
    GraphRevisionRow,
    MissionRow,
    OutboxRow,
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
