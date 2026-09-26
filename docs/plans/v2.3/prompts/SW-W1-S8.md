# SW-W1-S8 — Durable ops-event sink, trace graph, nested redaction

Copy this whole file into a fresh Cursor session opened on the **swarmai** repository. Follow it top to bottom. It is self-contained: do not read other plans to decide what to do.

| Field | Value |
|---|---|
| Session ID | `SW-W1-S8` |
| Repository | `pri8771/swarmai` (GitHub remote `origin`; **public** repo) |
| Base branch | `cursor/sw-v23-integration-460c` — always the **current** `origin/cursor/sw-v23-integration-460c` (plan baseline `dev` @ `8e1c0fde`) |
| Your branch | `cursor/v23-w1-s8-ops-trace` |
| Branch-suffix rule | If your environment forces a suffix (for example `-460c`), append it **once** to *your* branch and write the exact final name in the handoff. Never add a suffix to `cursor/sw-v23-integration-460c`: it already ends in `-460c`. |
| PR target | `cursor/sw-v23-integration-460c` — **draft** PR. Never `dev`, never `main`. |
| Wave | 1 |
| Depends on | SW-W0-S2 |
| Handoff file | `docs/v2.3/sessions/SW-W1-S8.md` |
| Independent reviewer | Codex (owner decision D2). You never accept your own work. |
| Plan | `docs/plans/v2.3/PLAN.md`; owner preflight `docs/plans/v2.3/OWNER_PREFLIGHT.md`; decisions `docs/swarm-mvp/DECISIONS.md` |

## 0. Hard rules (read twice)
1. Edit **only** the files listed in “Files you own” plus your handoff file. If another file must change, do not change it: write the exact change under “Needs other owner” in the handoff.
2. Never push to, or merge into, `main`, `dev` or `cursor/sw-v23-integration-460c`. Never merge any PR, never force-push, never rewrite history, never delete branches. Only the wave MERGE prompts (`SW-MERGE-*`) push to `cursor/sw-v23-integration-460c`.
3. Zero spend: no real model/provider calls, no paid APIs, no account creation, no deploys. `SWARM_ALLOW_PAID` stays `false`. Tests use fakes only.
4. Never commit or print secrets, tokens, `.env` files, customer data or raw logs. Test tokens are fake literals such as `atk_policy_demo`. Check environment variables only with `test -n "$NAME"`.
5. Passing tests are *not* acceptance. Never write “accepted”, “complete”, “released” or “V2.3 done”. Use “implemented” and “tested”.
6. `src/swarm/contracts/v23.py`, `src/swarm/db/models.py` and `migrations/` belong to SW-W0-S2. Import from them; never edit them (unless you *are* SW-W0-S2).
7. Do not edit `.github/workflows/`, `pyproject.toml`, `uv.lock`, `package.json` or lockfiles.
8. If a step can be read two ways, choose the reading that changes fewer lines inside your own files, and write the choice under “Decisions” in the handoff.

## 1. Setup
```bash
git status --porcelain            # must print nothing; otherwise STOP (S1)
git fetch origin cursor/sw-v23-integration-460c
git ls-remote --exit-code origin refs/heads/cursor/sw-v23-integration-460c >/dev/null && echo INTEG_OK || echo INTEG_MISSING
```
If it prints `INTEG_MISSING`, STOP (S2): SW-W0-S1 or the executor creates it.
```bash
git checkout -b cursor/v23-w1-s8-ops-trace origin/cursor/sw-v23-integration-460c
git log -1 --format='%H %s'       # record this SHA in the handoff as 'base'
command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh   # then: export PATH=$HOME/.local/bin:$PATH
uv sync
git clean -fdX -- var/
```

## 2. Dependency and environment check
Depends on: SW-W0-S2. Their PRs must already be merged into `cursor/sw-v23-integration-460c` (by the wave MERGE prompt).
Run every command below. Each must print `OK`. If any prints `MISSING`, STOP (condition S2 in section 10).

```bash
git fetch origin cursor/sw-v23-integration-460c
git cat-file -e origin/cursor/sw-v23-integration-460c:src/swarm/contracts/v23.py && echo "OK src/swarm/contracts/v23.py" || echo "MISSING src/swarm/contracts/v23.py"
git cat-file -e origin/cursor/sw-v23-integration-460c:migrations/versions/a23opsplatform0001_v23_ops_platform.py && echo "OK migrations/versions/a23opsplatform0001_v23_ops_platform.py" || echo "MISSING migrations/versions/a23opsplatform0001_v23_ops_platform.py"
```

This session needs **no** secrets or environment variables.

## 3. Files you own (the ONLY files you may create or modify)
- `src/swarm/observability/ops_events.py` — modify
- `src/swarm/observability/__init__.py` — modify
- `src/swarm/observability/trace_graph.py` — create
- `tests/controller/test_v23_ops_trace.py` — create
- `tests/integration/db/test_v23_ops_events_sql.py` — create
- `docs/v2.3/sessions/SW-W1-S8.md` — create (your handoff)

## 4. Do NOT touch
- Any file not listed in section 3 (in particular: `src/swarm/api/app.py`, `src/swarm/api/store.py`, `src/swarm/cli.py`, `src/swarm/db/models.py`, `migrations/`, `docs/agents/*`, `docs/plans/v2.3/*`, `CHANGELOG.md`, `README.md`, `.github/`, unless listed above).
- The `inference_server` repository: read-only, and only through the commands in section 5.
- The branches `main`, `dev`, `cursor/sw-v23-integration-460c`, `cursor/v23-plan-460c`, and any other session's branch.
- Generated files that tests rewrite: `schemas/v1/*`, `docs/evidence/fix-004/*`, `var/*` — always restore them before committing (section 6).

## 5. Steps
**Goal.** Complete ART-V23-OPS observability and the observability half of finding **F-04**.
- Ops events live only in a process-local list, redaction is one level deep (a secret nested inside `detail.request.headers` leaks), and there is no trace graph from operator action to acceptance.

**This session adds:**
- A pluggable sink: `InMemoryOpsSink`, the default, which behaves exactly like today, and `SqlOpsSink`, which writes to the `v23_ops_events` table created by SW-W0-S2.
- Recursive redaction of dicts and lists.
- `trace_id` / `parent_event_id` on events.
- `trace_graph.build_trace(log, trace_id)`, which reports missing stages and orphans instead of inventing links.
- A hard `MAX_LIST_LIMIT = 1000` cap on `list_events`.

**Compatibility.** Existing behaviour is kept:
- `OpsEventLog()` with no arguments.
- `emit(...)` with the old keywords.
- `list_events(project_id=, kind=, limit=)` returning dicts.
- `detail["api_key"] == "[redacted]"`.

`to_dict()` gains two keys, `trace_id` and `parent_event_id`. **Do not** wire `SqlOpsSink` into `app.py`; SW-W3-S1 owns that file.

The code below was compiled and run against `dev @ 8e1c0fde` plus SW-W0-S2. The offline tests give 17 passed with the existing gap tests, and the integration test gives 1 passed. Paste it **exactly**.

### Step 1 — `src/swarm/observability/ops_events.py` (replace the whole file, exactly)
```python
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
```

### Step 2 — `src/swarm/observability/trace_graph.py` (create, exactly)
```python
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
```

### Step 3 — `src/swarm/observability/__init__.py` (replace the whole file, exactly)
```python
"""Observability package."""

from swarm.observability.ops_events import (
    InMemoryOpsSink,
    OpsEvent,
    OpsEventLog,
    OpsEventSink,
    SqlOpsSink,
    assert_dashboard_mutation_via_action,
)
from swarm.observability.reliability import TraceRecorder, run_reliability_scenarios
from swarm.observability.trace_graph import TRACE_CHAIN, TraceGraph, build_trace

__all__ = [
    "TRACE_CHAIN",
    "InMemoryOpsSink",
    "OpsEvent",
    "OpsEventLog",
    "OpsEventSink",
    "SqlOpsSink",
    "TraceGraph",
    "TraceRecorder",
    "assert_dashboard_mutation_via_action",
    "build_trace",
    "run_reliability_scenarios",
]
```

### Step 4 — `tests/controller/test_v23_ops_trace.py` (create, exactly)
```python
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
```

### Step 5 — `tests/integration/db/test_v23_ops_events_sql.py` (create, exactly)
```python
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
```

### Step 6 — run
```bash
uv run pytest tests/controller/test_v23_ops_trace.py tests/controller/test_v18_v30_gaps.py -q   # all pass
uv run pytest tests/api -q                                                                     # unchanged
```

### Section-5 acceptance
- [ ] Nested secret keys at any depth, inside dicts and lists, are stored as `[redacted]`; the raw secret never reaches the SQL `payload`.
- [ ] `OpsEventLog()` with no arguments behaves as before, and the existing `test_ops_events_and_dashboard_boundary` passes unchanged.
- [ ] `SqlOpsSink` events survive a new `OpsEventLog` instance, and filters by project, kind and trace work.
- [ ] `build_trace` returns ordered nodes; `complete` is true only when every `TRACE_CHAIN` stage is present and there are no orphans; gaps are listed, never filled.
- [ ] `list_events(limit=…)` never returns more than 1000 rows.

## 6. Verify (run exactly; all must pass)
```bash
git clean -fdX -- var/            # F-15: stale runtime state breaks re-runs
# Private database for this session: concurrent sessions on one host must never share one.
sudo -u postgres psql -c "CREATE DATABASE swarm_sw_w1_s8 OWNER swarm;" || true
export SWARM_DATABASE_URL=postgresql+psycopg://swarm:swarm@127.0.0.1:5432/swarm_sw_w1_s8
uv run ruff check .
uv run mypy src/swarm
uv run alembic heads               # must print exactly ONE line ending in (head)
uv run pytest tests/controller/test_v23_ops_trace.py tests/controller/test_v18_v30_gaps.py -q
uv run pytest tests/contracts tests/spikes tests/api tests/broker tests/controller tests/chaos tests/deployment tests/evals tests/extensions tests/foundation tests/goals tests/pursuit tests/sdk tests/knowledge tests/load tests/memory tests/mission tests/objectives tests/onboarding tests/product tests/providers tests/recovery tests/regressions tests/release tests/runtime tests/selfdev tests/tools tests/ui tests/workers tests/workspace tests/e2e tests/acceptance tests/portability -q --ignore=tests/integration

# PostgreSQL integration (install steps in “PostgreSQL” below)
uv run pytest tests/integration -q -m integration

git checkout -- schemas/v1 docs/evidence/fix-004 var   # tests rewrite these tracked files
git status --porcelain            # every path listed must be one of YOUR files
```

### PostgreSQL (for the integration line)
```bash
pg_isready -h 127.0.0.1 || {
  sudo apt-get update && sudo apt-get install -y postgresql && sudo service postgresql start
  sudo -u postgres psql -c "CREATE USER swarm WITH PASSWORD 'swarm' SUPERUSER;" || true
}
```
Run this block before section 6. Section 6 creates your private database and exports `SWARM_DATABASE_URL` for **both** pytest lines; never unset it and never point it at the shared `swarm` database.
If `pg_isready -h 127.0.0.1` still fails after running this block twice, write `integration: SKIPPED (postgres unavailable: <last error line>)` in the handoff and continue. Never claim integration passed without running it.

## 7. Acceptance checklist (tick every box in the handoff)
- [ ] Every step in section 5 done; every acceptance box in section 5 ticked.
- [ ] `uv run ruff check .` and `uv run mypy src/swarm` pass.
- [ ] `uv run alembic heads` prints exactly one head.
- [ ] Full offline CI list passes (paste the final `N passed` line into the handoff).
- [ ] Integration run passed, or SKIPPED with reason in the handoff.
- [ ] `git status --porcelain` lists only files from section 3 + the handoff.
- [ ] No secrets, no network calls beyond section 5, no `accepted`/`complete` claims.
- [ ] The Codex review packet (section 11) is in the PR description and the handoff.

## 8. Commit, push, draft PR
```bash
git checkout -- schemas/v1 docs/evidence/fix-004 var
git add src/swarm/observability/ops_events.py src/swarm/observability/__init__.py src/swarm/observability/trace_graph.py tests/controller/test_v23_ops_trace.py tests/integration/db/test_v23_ops_events_sql.py docs/v2.3/sessions/SW-W1-S8.md
git status --porcelain            # nothing unexpected staged or left over
git commit -m "feat(v2.3): pluggable ops-event sinks (memory/PostgreSQL), recursive redaction, trace graph" -m "Session: SW-W1-S8. Plan: docs/plans/v2.3/PLAN.md."
git push -u origin cursor/v23-w1-s8-ops-trace
gh pr create --draft --base cursor/sw-v23-integration-460c --head cursor/v23-w1-s8-ops-trace --title "[SW-W1-S8] Durable ops-event sink, trace graph, nested redaction" --body-file docs/v2.3/sessions/SW-W1-S8.md
git ls-remote origin refs/heads/cursor/v23-w1-s8-ops-trace   # must print the same SHA as: git rev-parse HEAD
```
If `gh pr create` is refused (read-only `gh`), the environment opens the PR: check that its base is `cursor/sw-v23-integration-460c` and that it is a draft, and put the PR URL (or the compare URL from section 10, step 4) into the handoff.
If push fails for network reasons, retry up to 4 times waiting 4 s, 8 s, 16 s, 32 s; then STOP (S8).
Docs to update: only your handoff file, plus any doc listed in section 3.

## 9. Handoff file (create before committing)
Create `docs/v2.3/sessions/SW-W1-S8.md` with exactly these headings:
```markdown
# SW-W1-S8 handoff
- Branch: <exact branch name>   Base SHA: <from setup>   Head SHA: <git rev-parse HEAD>
- PR: <url, or compare URL>
## Done
<bullet list of what you implemented>
## Verification
<each command from section 6 and its final result line; integration PASSED/SKIPPED(reason)>
## Acceptance
<copy the checkboxes from sections 5 and 7, ticked>
## Decisions
<choices you made under hard rule 8, or 'none'>
## Needs other owner
<files outside your scope that should change, with the exact change; or 'none'>
## Codex review packet
<the block from section 11, filled in>
## Status
implemented + tested (NOT accepted; needs Codex review)
```

## 10. STOP conditions (never wait for a human)
STOP immediately when any of these is true:
- **S1** `git status --porcelain` is not empty before Setup. (Do not commit, stash or discard anything; skip steps 1–4 below and only report.)
- **S2** a dependency check prints `MISSING`.
- **S3** a command in section 6, or a check in section 5, still fails after **2 attempts**. One attempt = one edit to *your own files* followed by re-running the failing command.
- **S4** a “currently reads” / before-block in section 5 does not match the file, or a function named in section 5 does not exist.
- **S5** finishing would require editing a file that is not in section 3.
- **S6** a required environment variable prints `MISSING`.
- **S7** an external gate check (inference_server sync point or approval line) in section 5 fails.
- **S8** `git push` still fails after 4 retries (waits 4 s, 8 s, 16 s, 32 s).

What to do on STOP, in this order:
1. Commit whatever is complete inside your own files: `git add <your files> docs/v2.3/sessions/SW-W1-S8.md` then `git commit -m "WIP(SW-W1-S8): <one-line reason>"`.
2. Write the handoff (section 9) with `## Status` = `BLOCKED: <condition id> <one-line reason>`, and under `## Needs other owner` the exact file, function and change you need. Commit it.
3. Push: `git push -u origin cursor/v23-w1-s8-ops-trace` (plus your suffix).
4. Open the draft PR against `cursor/sw-v23-integration-460c` with the title prefix `[BLOCKED]`, or record the compare URL `https://github.com/pri8771/swarmai/compare/cursor/sw-v23-integration-460c...cursor/v23-w1-s8-ops-trace?expand=1` in the handoff.
5. End the session with a final message: the condition id, the reason, the branch and the head SHA.
Never work around a STOP by editing other files, weakening tests, or adding `skip`/`xfail`.

If `tests/tools/test_v20_cancel_killbound.py` fails once in the full run and you did not touch `sandbox_runner.py` or that test, re-run the full list once. If it passes, record both result lines in the handoff under Verification and continue; if it fails twice, STOP (S3). (The known race was fixed by SW-FIX-FLAKE; a new failure is worth reporting.)

## 11. Codex review packet (put this in the PR description and in the handoff)
```markdown
### Codex review packet — SW-W1-S8
- PR: <PR URL — fill in after the PR exists>
- Branch: <exact branch name>  Base: origin/cursor/sw-v23-integration-460c @ <base SHA from Setup>
- Head SHA: <output of `git rev-parse HEAD`; must equal `git ls-remote origin refs/heads/<branch>`>
- Diff for review: `git diff <base SHA>...<head SHA>`
- Files to review: `src/swarm/observability/ops_events.py`, `src/swarm/observability/__init__.py`, `src/swarm/observability/trace_graph.py`, `tests/controller/test_v23_ops_trace.py`, `tests/integration/db/test_v23_ops_events_sql.py`, `docs/v2.3/sessions/SW-W1-S8.md`
- Review focus (AGENTS.md Code Review Rules): cross-tenant/project access; secret disclosure; financial accounting (unknown usage or cost is never zero); unbounded retries; silently changed model behaviour; recovery gaps after a crash/restart; unsupported release claims ("accepted", "complete"). Session-specific: trace graph never crosses projects; a foreign trace is 404.
- Checks run: <paste the final result line of every command in section 6>
- Verdict requested: `RECOMMEND_ACCEPT <head SHA>` or `REQUEST_CHANGES` with file:line findings.
```
