"""Lesson provenance ledger — adoption/reversion evidence without replacing evaluator.

Reuse PursuitLessonStore for state transitions; this module records durable
source/event/artifact provenance and adoption receipts.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from swarm.contracts.common import new_id, utc_now
from swarm.pursuit.learning import PursuitLessonStore
from swarm.pursuit.models import PursuitLesson

ProvenanceEventKind = Literal[
    "proposed",
    "evaluated",
    "adopted",
    "rejected",
    "rolled_back",
]


@dataclass
class LessonProvenanceEvent:
    event_id: str
    lesson_id: str
    goal_id: str
    kind: ProvenanceEventKind
    source_refs: list[str]
    artifact_refs: list[str]
    event_refs: list[str]
    actor_id: str
    detail: str = ""
    created_at: str = field(default_factory=lambda: utc_now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "lesson_id": self.lesson_id,
            "goal_id": self.goal_id,
            "kind": self.kind,
            "source_refs": list(self.source_refs),
            "artifact_refs": list(self.artifact_refs),
            "event_refs": list(self.event_refs),
            "actor_id": self.actor_id,
            "detail": self.detail,
            "created_at": self.created_at,
        }


class LessonProvenanceLedger:
    """Append-only provenance alongside an existing PursuitLessonStore."""

    def __init__(
        self,
        lessons: PursuitLessonStore | None = None,
        *,
        root: Path | None = None,
    ) -> None:
        self.lessons = lessons or PursuitLessonStore()
        self.root = root
        self._events: list[LessonProvenanceEvent] = []
        if self.root is not None:
            self.root.mkdir(parents=True, exist_ok=True)
            self._load()

    def _path(self) -> Path | None:
        return None if self.root is None else self.root / "lesson_provenance.jsonl"

    def record(
        self,
        *,
        lesson: PursuitLesson,
        kind: ProvenanceEventKind,
        actor_id: str,
        source_refs: list[str] | None = None,
        artifact_refs: list[str] | None = None,
        event_refs: list[str] | None = None,
        detail: str = "",
    ) -> LessonProvenanceEvent:
        ev = LessonProvenanceEvent(
            event_id=new_id("lpe_"),
            lesson_id=lesson.lesson_id,
            goal_id=lesson.goal_id,
            kind=kind,
            source_refs=list(source_refs or lesson.evidence_refs),
            artifact_refs=list(artifact_refs or []),
            event_refs=list(event_refs or []),
            actor_id=actor_id,
            detail=detail,
        )
        self._events.append(ev)
        self._append(ev)
        return ev

    def propose_with_provenance(
        self,
        lesson: PursuitLesson,
        *,
        actor_id: str,
        source_refs: list[str] | None = None,
        artifact_refs: list[str] | None = None,
    ) -> tuple[PursuitLesson, LessonProvenanceEvent]:
        stored = self.lessons.propose(lesson)
        ev = self.record(
            lesson=stored,
            kind="proposed",
            actor_id=actor_id,
            source_refs=source_refs,
            artifact_refs=artifact_refs,
        )
        return stored, ev

    def adopt_with_provenance(
        self,
        lesson_id: str,
        *,
        current_strategy: str,
        actor_id: str,
        event_refs: list[str] | None = None,
    ) -> tuple[PursuitLesson, LessonProvenanceEvent]:
        adopted = self.lessons.adopt(lesson_id, current_strategy=current_strategy)
        ev = self.record(
            lesson=adopted,
            kind="adopted",
            actor_id=actor_id,
            event_refs=event_refs,
            detail=f"prior_strategy={adopted.prior_strategy}",
        )
        return adopted, ev

    def rollback_with_provenance(
        self,
        lesson_id: str,
        *,
        actor_id: str,
        event_refs: list[str] | None = None,
    ) -> tuple[PursuitLesson, LessonProvenanceEvent]:
        rolled = self.lessons.rollback(lesson_id)
        ev = self.record(
            lesson=rolled,
            kind="rolled_back",
            actor_id=actor_id,
            event_refs=event_refs,
            detail="strategy_restored",
        )
        return rolled, ev

    def history_for(self, lesson_id: str) -> list[LessonProvenanceEvent]:
        return [e for e in self._events if e.lesson_id == lesson_id]

    def evidence(self) -> dict[str, Any]:
        return {
            "event_count": len(self._events),
            "events": [e.to_dict() for e in self._events],
        }

    def _append(self, ev: LessonProvenanceEvent) -> None:
        path = self._path()
        if path is None:
            return
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(ev.to_dict(), default=str) + "\n")

    def _load(self) -> None:
        path = self._path()
        if path is None or not path.exists():
            return
        rows: list[LessonProvenanceEvent] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            data = json.loads(line)
            rows.append(
                LessonProvenanceEvent(
                    event_id=data["event_id"],
                    lesson_id=data["lesson_id"],
                    goal_id=data["goal_id"],
                    kind=data["kind"],
                    source_refs=list(data.get("source_refs") or []),
                    artifact_refs=list(data.get("artifact_refs") or []),
                    event_refs=list(data.get("event_refs") or []),
                    actor_id=data["actor_id"],
                    detail=data.get("detail") or "",
                    created_at=data.get("created_at") or utc_now().isoformat(),
                )
            )
        self._events = rows
