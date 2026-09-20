"""Mission report writers — machine JSON + human markdown."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from swarm.mission.store import MissionRecord


def write_reports(record: MissionRecord, out_dir: Path) -> dict[str, str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    machine = out_dir / "mission-report.json"
    human = out_dir / "MISSION_REPORT.md"
    machine.write_text(
        __import__("json").dumps(record.to_dict(), indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    cost = record.cost or {}
    lines = [
        f"# Mission report — `{record.mission_id}`",
        "",
        f"- **Status:** {record.status}",
        f"- **Goal:** {record.goal}",
        f"- **Created:** {record.created_at}",
        f"- **Updated:** {record.updated_at}",
        f"- **Cost USD:** {cost.get('total_usd', 0.0)}",
        f"- **Provider spend policy:** {cost.get('spend_policy', 'zero')}",
        "",
        "## Tasks",
    ]
    for task in record.tasks:
        lines.append(
            f"- `{task.get('id')}` [{task.get('task_family')}] "
            f"status={task.get('status')} ok={task.get('ok')}"
        )
    lines.extend(["", "## Timeline"])
    for event in record.timeline[-30:]:
        lines.append(f"- {event.get('at')}: **{event.get('event')}**")
    lines.extend(["", "## Result", ""])
    result = record.result or {}
    lines.append(f"- accepted: {result.get('accepted')}")
    lines.append(f"- summary: {result.get('summary')}")
    if result.get("changed_files"):
        lines.append(f"- changed_files: {', '.join(result['changed_files'])}")
    lines.append("")
    human.write_text("\n".join(lines), encoding="utf-8")
    return {"machine": str(machine), "human": str(human)}


def live_state_view(record: MissionRecord) -> dict[str, Any]:
    return {
        "mission_id": record.mission_id,
        "status": record.status,
        "revision": record.revision,
        "tasks": [
            {
                "id": t.get("id"),
                "family": t.get("task_family"),
                "status": t.get("status"),
                "ok": t.get("ok"),
            }
            for t in record.tasks
        ],
        "cost_usd": (record.cost or {}).get("total_usd", 0.0),
        "last_event": record.timeline[-1] if record.timeline else None,
        "updated_at": record.updated_at,
    }
