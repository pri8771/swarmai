"""Normalized operational event model (V2.3 observability)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from swarm.contracts.common import new_id, utc_now

SECRET_FRAGMENTS = ("secret", "api_key", "token", "password", "authorization", "credential")


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

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "kind": self.kind,
            "component": self.component,
            "project_id": self.project_id,
            "tenant_id": self.tenant_id,
            "site_epoch": self.site_epoch,
            "correlation_id": self.correlation_id,
            "detail": dict(self.detail),
            "at": self.at,
        }


def _redact(detail: dict[str, Any]) -> dict[str, Any]:
    safe: dict[str, Any] = {}
    for key, value in detail.items():
        lk = key.lower()
        if any(s in lk for s in SECRET_FRAGMENTS):
            safe[key] = "[redacted]"
        else:
            safe[key] = value
    return safe


class OpsEventLog:
    """Read surface for operational events — mutations must use action boundary."""

    def __init__(self) -> None:
        self._events: list[OpsEvent] = []

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
        )
        self._events.append(event)
        return event

    def list_events(
        self,
        *,
        project_id: str | None = None,
        kind: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        rows = self._events
        if project_id is not None:
            rows = [e for e in rows if e.project_id == project_id]
        if kind is not None:
            rows = [e for e in rows if e.kind == kind]
        return [e.to_dict() for e in rows[-limit:]]


def assert_dashboard_mutation_via_action(*, surface: str, uses_action_boundary: bool) -> None:
    """Dashboard/UI mutations must go through the authenticated action/approval boundary."""
    if surface in {"dashboard", "console", "ui"} and not uses_action_boundary:
        raise PermissionError("dashboard_mutation_requires_action_boundary")
