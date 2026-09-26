"""Durable pursuit runtime state — survives ProductStore / process reopen.

Closes R20-04: criteria progress, cycle history, dedupe, commitments, active
missions, failed approaches and schedules must not live only in process memory.
File-backed under ``var/pursuit/`` for local volume durability. When a
``mirror`` (V20-E03 PostgreSQL write-through) is given, the database is written
first and read first; mirror failures raise ``PursuitMirrorError`` (fail closed).
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from swarm.pursuit.models import CycleRecord, ScheduleState
from swarm.pursuit.pg_mirror import PursuitMirror


def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True, default=str)
            handle.write("\n")
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


class DurablePursuitStateStore:
    """Per-goal pursuit runtime snapshot under ``root/<goal_id>.json``."""

    schema_version = "2.0-pursuit-state"

    def __init__(self, root: Path, *, mirror: PursuitMirror | None = None) -> None:
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.mirror = mirror

    def _path(self, goal_id: str) -> Path:
        safe = goal_id.replace("/", "_").replace("..", "_")
        return self.root / f"{safe}.json"

    def _load_file(self, goal_id: str) -> dict[str, Any] | None:
        path = self._path(goal_id)
        if not path.is_file():
            return None
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, TypeError):
            return None
        if not isinstance(raw, dict):
            return None
        return raw

    def load(self, goal_id: str) -> dict[str, Any] | None:
        if self.mirror is not None:
            snap = self.mirror.load_snapshot(goal_id)
            if snap is not None:
                return snap
        return self._load_file(goal_id)

    def save(
        self,
        goal_id: str,
        *,
        satisfied: set[str],
        history: list[CycleRecord],
        dedupe: dict[str, str],
        failed_approaches: set[str],
        active_missions: set[str],
        commitments: list[str],
        schedule: ScheduleState | None,
    ) -> None:
        payload: dict[str, Any] = {
            "schema_version": self.schema_version,
            "goal_id": goal_id,
            "satisfied_criteria": sorted(satisfied),
            "history": [c.model_dump(mode="json") for c in history],
            "dedupe": dict(dedupe),
            "failed_approaches": sorted(failed_approaches),
            "active_missions": sorted(active_missions),
            "commitments": list(commitments),
            "schedule": schedule.model_dump(mode="json") if schedule else None,
        }
        if self.mirror is not None:
            self.mirror.write_snapshot(goal_id, payload)
        _atomic_write(self._path(goal_id), payload)

    def parse_history(self, raw: dict[str, Any]) -> list[CycleRecord]:
        out: list[CycleRecord] = []
        for row in raw.get("history") or []:
            try:
                out.append(CycleRecord.model_validate(row))
            except (TypeError, ValueError):
                continue
        return out

    def parse_schedule(self, raw: dict[str, Any]) -> ScheduleState | None:
        row = raw.get("schedule")
        if not row:
            return None
        try:
            return ScheduleState.model_validate(row)
        except (TypeError, ValueError):
            return None
