"""SW-W1-S8: SqlOpsSink persists redacted events and survives a new log instance."""

from __future__ import annotations

import os

import pytest
from sqlalchemy import text

from swarm.db.engine import create_db_engine, make_session_factory, ping
from swarm.db.models import Base
from swarm.observability import OpsEventLog, SqlOpsSink, build_trace

pytestmark = pytest.mark.integration

DATABASE_URL = os.environ.get(
    "SWARM_DATABASE_URL", "postgresql+psycopg://swarm:swarm@127.0.0.1:5432/swarm"
)


@pytest.fixture(scope="module")
def factory():
    eng = create_db_engine(DATABASE_URL)
    try:
        ping(eng)
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"postgres_unavailable:{type(exc).__name__}")
    Base.metadata.create_all(eng)
    yield make_session_factory(eng)
    eng.dispose()


def test_sql_sink_roundtrip_and_redaction(factory) -> None:
    with factory() as s:
        s.execute(text("TRUNCATE v23_ops_events"))
        s.commit()
    log = OpsEventLog(SqlOpsSink(factory))
    first = log.emit(
        "operator.action", "api", project_id="p1", trace_id="tr_sql", detail={"token": "t"}
    )
    log.emit("mission.created", "api", project_id="p1", trace_id="tr_sql",
             parent_event_id=first.event_id)
    log.emit("mission.created", "api", project_id="p2", trace_id="tr_x")

    reopened = OpsEventLog(SqlOpsSink(factory))
    rows = reopened.list_events(project_id="p1")
    assert [r["kind"] for r in rows] == ["operator.action", "mission.created"]
    assert rows[0]["detail"]["token"] == "[redacted]"
    graph = build_trace(reopened, "tr_sql")
    assert [n.kind for n in graph.nodes] == ["operator.action", "mission.created"]
    assert graph.orphans == []
    with factory() as s:
        raw = s.execute(text("SELECT payload::text FROM v23_ops_events")).scalars().all()
    assert all('"t"' not in r for r in raw)
