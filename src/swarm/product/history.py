"""Searchable mission history + artifact UX."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from swarm.contracts.common import utc_now
from swarm.mission.store import MissionStore
from swarm.product.contracts import mission_public_view, strip_internal
from swarm.product.projects import scrub_config


@dataclass
class HistoryEntry:
    mission_id: str
    project_id: str | None
    goal: str
    status: str
    updated_at: str
    cost_usd: float = 0.0
    artifact_count: int = 0
    tags: list[str] = field(default_factory=list)
    path: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "mission_id": self.mission_id,
            "project_id": self.project_id,
            "goal": self.goal,
            "status": self.status,
            "updated_at": self.updated_at,
            "cost_usd": self.cost_usd,
            "artifact_count": self.artifact_count,
            "tags": self.tags,
            "path": self.path,
        }


class HistoryIndex:
    """Index completed missions for reopen/search/compare."""

    def __init__(self, repo: Path) -> None:
        self.repo = repo.resolve()
        self.missions = MissionStore(self.repo / "var" / "missions")
        self.index_path = self.repo / "var" / "history" / "index.json"
        self.index_path.parent.mkdir(parents=True, exist_ok=True)

    def rebuild(self) -> list[HistoryEntry]:
        entries: list[HistoryEntry] = []
        for row in self.missions.list_missions():
            mid = str(row["mission_id"])
            try:
                record = self.missions.load(mid)
            except (OSError, json.JSONDecodeError, TypeError, KeyError):
                continue
            data = record.to_dict()
            arts = data.get("artifacts") or {}
            if isinstance(arts, dict):
                art_count = len(arts)
            else:
                art_count = len(arts) if isinstance(arts, list) else 0
            cost = data.get("cost") or {}
            tags = []
            if data.get("status") == "completed":
                tags.append("completed")
            if (cost.get("total_usd") or 0) == 0:
                tags.append("zero_spend")
            if data.get("model_assignments"):
                tags.append("heterogeneous")
            entries.append(
                HistoryEntry(
                    mission_id=mid,
                    project_id=data.get("project_id") or data.get("plan", {}).get("project_id"),
                    goal=str(data.get("goal") or ""),
                    status=str(data.get("status") or "unknown"),
                    updated_at=str(data.get("updated_at") or ""),
                    cost_usd=float(cost.get("total_usd") or 0.0),
                    artifact_count=art_count,
                    tags=tags,
                    path=str(self.missions._path(mid)),
                )
            )
        payload = {
            "schema_version": "0.8.0",
            "generated_at": utc_now().isoformat(),
            "count": len(entries),
            "entries": [e.to_dict() for e in entries],
        }
        self.index_path.write_text(
            json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8"
        )
        return entries

    def load_index(self) -> list[dict[str, Any]]:
        if not self.index_path.exists():
            return [e.to_dict() for e in self.rebuild()]
        data = json.loads(self.index_path.read_text(encoding="utf-8"))
        return list(data.get("entries") or [])

    def search(self, query: str = "", *, status: str | None = None) -> list[dict[str, Any]]:
        q = query.strip().lower()
        rows = self.load_index()
        out: list[dict[str, Any]] = []
        for row in rows:
            if status and str(row.get("status")) != status:
                continue
            hay = " ".join(
                [
                    str(row.get("mission_id") or ""),
                    str(row.get("goal") or ""),
                    str(row.get("project_id") or ""),
                    " ".join(row.get("tags") or []),
                ]
            ).lower()
            if q and q not in hay:
                continue
            out.append(row)
        return out

    def reopen(self, mission_id: str) -> dict[str, Any]:
        record = self.missions.load(mission_id)
        view = mission_public_view(record.to_dict())
        artifacts = self.list_artifacts(mission_id)
        return {
            "mission": view,
            "artifacts": artifacts,
            "timeline": view.get("timeline") or [],
            "comparable": {
                "status": view.get("status"),
                "cost_usd": (view.get("cost") or {}).get("total_usd", 0.0),
                "task_count": len(view.get("tasks") or []),
                "validation": view.get("validation") or {},
                "model_decisions": view.get("model_assignments") or [],
            },
            "mock_vs_live": "file_backed_history_reopen",
        }

    def list_artifacts(self, mission_id: str) -> list[dict[str, Any]]:
        record = self.missions.load(mission_id)
        arts = record.artifacts or {}
        rows: list[dict[str, Any]] = []
        if isinstance(arts, dict):
            for key, val in arts.items():
                if isinstance(val, dict):
                    rows.append(
                        strip_internal(
                            scrub_config(
                                {
                                    "artifact_id": val.get("id") or key,
                                    "kind": val.get("kind") or key,
                                    "uri": val.get("uri") or val.get("path"),
                                    "media_type": val.get("media_type"),
                                    "summary": val.get("summary") or val.get("preview"),
                                }
                            )
                        )
                    )
                else:
                    rows.append({"artifact_id": key, "summary": str(val)[:200]})
        report_dir = self.repo / "var" / "reports" / "missions" / mission_id
        if report_dir.exists():
            for path in sorted(report_dir.glob("*")):
                if path.is_file():
                    rows.append(
                        {
                            "artifact_id": f"report:{path.name}",
                            "kind": "report",
                            "uri": str(path),
                            "media_type": "application/json"
                            if path.suffix == ".json"
                            else "text/markdown",
                        }
                    )
        return rows

    def compare(self, mission_a: str, mission_b: str) -> dict[str, Any]:
        a = self.reopen(mission_a)["comparable"]
        b = self.reopen(mission_b)["comparable"]
        return {
            "a": {"mission_id": mission_a, **a},
            "b": {"mission_id": mission_b, **b},
            "same_status": a.get("status") == b.get("status"),
            "cost_delta_usd": float(b.get("cost_usd") or 0) - float(a.get("cost_usd") or 0),
        }
