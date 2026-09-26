"""SW-W1-S8: nested redaction, pluggable sink and trace graph."""

from __future__ import annotations

from swarm.observability import (
    TRACE_CHAIN,
    InMemoryOpsSink,
    OpsEventLog,
    build_trace,
)


def test_nested_secrets_are_redacted() -> None:
    log = OpsEventLog()
    log.emit(
        "tool.effect",
        "tools",
        project_id="p",
        detail={
            "api_key": "sk-1",
            "request": {"headers": {"Authorization": "Bearer x"}, "path": "/v1"},
            "items": [{"password": "hunter2", "ok": 1}],
        },
    )
    d = log.list_events(project_id="p")[0]["detail"]
    assert d["api_key"] == "[redacted]"
    assert d["request"]["headers"]["Authorization"] == "[redacted]"
    assert d["request"]["path"] == "/v1"
    assert d["items"][0] == {"password": "[redacted]", "ok": 1}


def test_secret_shaped_values_are_redacted_under_generic_keys() -> None:
    log = OpsEventLog()
    log.emit(
        "operator.action",
        "api",
        project_id="p",
        detail={
            "reason": "investigate ss_live_0123456789abcdef0123456789abcdef_abcdefghijklmnop",
            "destination": "postgresql://user:password@db.internal/private",
            "safe": "maintenance",
        },
    )
    detail = log.list_events(project_id="p")[0]["detail"]
    assert detail == {
        "reason": "[redacted]",
        "destination": "[redacted]",
        "safe": "maintenance",
    }


def test_custom_sink_receives_events_and_filters() -> None:
    sink = InMemoryOpsSink()
    log = OpsEventLog(sink)
    log.emit("a", "c", project_id="p1", trace_id="tr_1")
    log.emit("b", "c", project_id="p2", trace_id="tr_2")
    assert [e.kind for e in sink.query()] == ["a", "b"]
    assert [e["kind"] for e in log.list_events(trace_id="tr_2")] == ["b"]
    assert log.list_events(limit=0) == []
    assert len(log.list_events(limit=10**9)) == 2


def _full_chain(log: OpsEventLog, trace_id: str) -> None:
    parent: str | None = None
    for stage in TRACE_CHAIN:
        ev = log.emit(
            stage[0], "test", project_id="p", trace_id=trace_id, parent_event_id=parent
        )
        parent = ev.event_id


def test_complete_trace() -> None:
    log = OpsEventLog()
    _full_chain(log, "tr_ok")
    log.emit("mission.created", "test", project_id="p", trace_id="tr_other")
    graph = build_trace(log, "tr_ok")
    assert graph.complete is True
    assert [n.kind for n in graph.nodes] == [s[0] for s in TRACE_CHAIN]
    assert graph.to_dict()["projects"] == ["p"]


def test_gap_and_orphan_are_reported_not_invented() -> None:
    log = OpsEventLog()
    log.emit("operator.action", "api", project_id="p", trace_id="tr_gap")
    log.emit("tool.effect", "tools", project_id="p", trace_id="tr_gap", parent_event_id="oev_gone")
    graph = build_trace(log, "tr_gap")
    assert graph.complete is False
    assert "mission.created" in graph.missing
    assert "inference.call|tool.effect" not in graph.missing
    assert len(graph.orphans) == 1


def test_unknown_trace_is_empty_and_incomplete() -> None:
    graph = build_trace(OpsEventLog(), "tr_none")
    assert graph.nodes == []
    assert len(graph.missing) == len(TRACE_CHAIN)
