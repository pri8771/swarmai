"""Trace graph: operator action → … → acceptance, rebuilt from ops events.

``build_trace`` never invents links. A missing stage is reported in ``missing``
so a UI or probe can show an honest gap instead of a fabricated chain.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from swarm.observability.ops_events import OpsEventLog

TRACE_CHAIN: tuple[tuple[str, ...], ...] = (
    ("operator.action",),
    ("mission.created",),
    ("scheduler.decision",),
    ("attempt.started",),
    ("inference.call", "tool.effect"),
    ("artifact.stored",),
    ("acceptance.recorded",),
)


@dataclass
class TraceNode:
    event_id: str
    kind: str
    component: str
    parent_event_id: str | None
    at: str
    project_id: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "kind": self.kind,
            "component": self.component,
            "parent_event_id": self.parent_event_id,
            "at": self.at,
            "project_id": self.project_id,
        }


@dataclass
class TraceGraph:
    trace_id: str
    nodes: list[TraceNode] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    orphans: list[str] = field(default_factory=list)
    projects: list[str] = field(default_factory=list)

    @property
    def complete(self) -> bool:
        return not self.missing and not self.orphans

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "complete": self.complete,
            "nodes": [n.to_dict() for n in self.nodes],
            "missing": list(self.missing),
            "orphans": list(self.orphans),
            "projects": list(self.projects),
        }


def build_trace(log: OpsEventLog, trace_id: str, *, limit: int = 1000) -> TraceGraph:
    events = log.list_events(trace_id=trace_id, limit=limit)
    events.sort(key=lambda e: (str(e["at"]), str(e["event_id"])))
    nodes = [
        TraceNode(
            event_id=str(e["event_id"]),
            kind=str(e["kind"]),
            component=str(e["component"]),
            parent_event_id=e.get("parent_event_id"),
            at=str(e["at"]),
            project_id=e.get("project_id"),
        )
        for e in events
    ]
    ids = {n.event_id for n in nodes}
    kinds = {n.kind for n in nodes}
    missing = ["|".join(stage) for stage in TRACE_CHAIN if not kinds.intersection(stage)]
    orphans = [
        n.event_id for n in nodes if n.parent_event_id is not None and n.parent_event_id not in ids
    ]
    projects = sorted({n.project_id for n in nodes if n.project_id is not None})
    return TraceGraph(
        trace_id=trace_id, nodes=nodes, missing=missing, orphans=orphans, projects=projects
    )
