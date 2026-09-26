"""Normalized operational event model (V2.3 observability).

Events are redacted recursively before they reach any sink. Sinks are pluggable:
``InMemoryOpsSink`` (default, tests) and ``SqlOpsSink`` (PostgreSQL ``v23_ops_events``).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from swarm.contracts.common import new_id, utc_now

SECRET_FRAGMENTS = ("secret", "api_key", "token", "password", "authorization", "credential")
REDACTED = "[redacted]"
MAX_LIST_LIMIT = 1000


@dataclass
class OpsEvent:
    """One event model for scheduler/fleet/effect/objective surfaces."""

    event_id: str
    kind: str
    component: str
    project_id: str | None = None
    tenant_id: str | None = None
    site_epoch: int | None = None
    correlation_id: str | None = None
    detail: dict[str, Any] = field(default_factory=dict)
    at: str = field(default_factory=lambda: utc_now().isoformat())
    trace_id: str | None = None
    parent_event_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "kind": self.kind,
            "component": self.component,
            "project_id": self.project_id,
            "tenant_id": self.tenant_id,
            "site_epoch": self.site_epoch,
            "correlation_id": self.correlation_id,
            "trace_id": self.trace_id,
            "parent_event_id": self.parent_event_id,
            "detail": dict(self.detail),
            "at": self.at,
        }


def _is_secret_key(key: str) -> bool:
    lk = key.lower()
    return any(s in lk for s in SECRET_FRAGMENTS)


def _redact_value(value: Any) -> Any:
    if isinstance(value, dict):
        return _redact(value)
    if isinstance(value, list | tuple):
        return [_redact_value(v) for v in value]
    return value


def _redact(detail: dict[str, Any]) -> dict[str, Any]:
    safe: dict[str, Any] = {}
    for key, value in detail.items():
        if _is_secret_key(str(key)):
            safe[key] = REDACTED
        else:
            safe[key] = _redact_value(value)
    return safe


class OpsEventSink(Protocol):
    def append(self, event: OpsEvent) -> None: ...

    def query(
        self,
        *,
        project_id: str | None = None,
        kind: str | None = None,
        trace_id: str | None = None,
        limit: int = 100,
    ) -> list[OpsEvent]: ...


def _matches(e: OpsEvent, project_id: str | None, kind: str | None, trace_id: str | None) -> bool:
    if project_id is not None and e.project_id != project_id:
        return False
    if kind is not None and e.kind != kind:
        return False
    return trace_id is None or e.trace_id == trace_id


class InMemoryOpsSink:
    def __init__(self) -> None:
        self._events: list[OpsEvent] = []

    def append(self, event: OpsEvent) -> None:
        self._events.append(event)

    def query(
        self,
        *,
        project_id: str | None = None,
        kind: str | None = None,
        trace_id: str | None = None,
        limit: int = 100,
    ) -> list[OpsEvent]:
        rows = [e for e in self._events if _matches(e, project_id, kind, trace_id)]
        return rows[-limit:] if limit > 0 else []


class SqlOpsSink:
    """PostgreSQL sink over ``v23_ops_events``; the full event lives in ``payload``."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._factory = session_factory

    def append(self, event: OpsEvent) -> None:
        from swarm.db.engine import session_scope
        from swarm.db.models import V23OpsEventRow

        with session_scope(self._factory) as s:
            s.add(
                V23OpsEventRow(
                    event_id=event.event_id,
                    kind=event.kind,
                    component=event.component,
                    project_id=event.project_id,
                    tenant_id=event.tenant_id,
                    trace_id=event.trace_id,
                    correlation_id=event.correlation_id,
                    site_epoch=event.site_epoch,
                    payload=event.to_dict(),
                    at=datetime.fromisoformat(event.at),
                )
            )

    def query(
        self,
        *,
        project_id: str | None = None,
        kind: str | None = None,
        trace_id: str | None = None,
        limit: int = 100,
    ) -> list[OpsEvent]:
        from swarm.db.engine import session_scope
        from swarm.db.models import V23OpsEventRow

        if limit <= 0:
            return []
        stmt = select(V23OpsEventRow)
        if project_id is not None:
            stmt = stmt.where(V23OpsEventRow.project_id == project_id)
        if kind is not None:
            stmt = stmt.where(V23OpsEventRow.kind == kind)
        if trace_id is not None:
            stmt = stmt.where(V23OpsEventRow.trace_id == trace_id)
        order = (V23OpsEventRow.at.desc(), V23OpsEventRow.event_id.desc())
        stmt = stmt.order_by(*order).limit(limit)
        with session_scope(self._factory) as s:
            rows = list(s.execute(stmt).scalars())
        rows.reverse()
        return [_from_payload(r.payload) for r in rows]


def _from_payload(p: dict[str, Any]) -> OpsEvent:
    return OpsEvent(
        event_id=str(p["event_id"]),
        kind=str(p["kind"]),
        component=str(p["component"]),
        project_id=p.get("project_id"),
        tenant_id=p.get("tenant_id"),
        site_epoch=p.get("site_epoch"),
        correlation_id=p.get("correlation_id"),
        detail=dict(p.get("detail") or {}),
        at=str(p["at"]),
        trace_id=p.get("trace_id"),
        parent_event_id=p.get("parent_event_id"),
    )


class OpsEventLog:
    """Read surface for operational events — mutations must use action boundary."""

    def __init__(self, sink: OpsEventSink | None = None) -> None:
        self._sink: OpsEventSink = sink if sink is not None else InMemoryOpsSink()

    @property
    def sink(self) -> OpsEventSink:
        return self._sink

    def emit(
        self,
        kind: str,
        component: str,
        *,
        project_id: str | None = None,
        tenant_id: str | None = None,
        site_epoch: int | None = None,
        correlation_id: str | None = None,
        detail: dict[str, Any] | None = None,
        trace_id: str | None = None,
        parent_event_id: str | None = None,
    ) -> OpsEvent:
        event = OpsEvent(
            event_id=new_id("oev_"),
            kind=kind,
            component=component,
            project_id=project_id,
            tenant_id=tenant_id,
            site_epoch=site_epoch,
            correlation_id=correlation_id,
            detail=_redact(detail or {}),
            trace_id=trace_id,
            parent_event_id=parent_event_id,
        )
        self._sink.append(event)
        return event

    def list_events(
        self,
        *,
        project_id: str | None = None,
        kind: str | None = None,
        trace_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        limit = max(0, min(limit, MAX_LIST_LIMIT))
        rows = self._sink.query(project_id=project_id, kind=kind, trace_id=trace_id, limit=limit)
        return [e.to_dict() for e in rows]


def assert_dashboard_mutation_via_action(*, surface: str, uses_action_boundary: bool) -> None:
    """Dashboard/UI mutations must go through the authenticated action/approval boundary."""
    if surface in {"dashboard", "console", "ui"} and not uses_action_boundary:
        raise PermissionError("dashboard_mutation_requires_action_boundary")
