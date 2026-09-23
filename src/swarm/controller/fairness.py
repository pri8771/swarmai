"""V2.3 durable fairness / project scheduling state."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ProjectFairnessState:
    project_id: str
    weight: float = 1.0
    fairness_debt: float = 0.0
    active_missions: int = 0


@dataclass
class DurableFairnessStore:
    """Process-local durable-shaped fairness store (DB row mirror)."""

    projects: dict[str, ProjectFairnessState] = field(default_factory=dict)

    def get(self, project_id: str) -> ProjectFairnessState:
        if project_id not in self.projects:
            self.projects[project_id] = ProjectFairnessState(project_id=project_id)
        return self.projects[project_id]

    def note_dispatch(self, project_id: str) -> ProjectFairnessState:
        state = self.get(project_id)
        state.fairness_debt += 1.0 / max(state.weight, 0.01)
        state.active_missions += 1
        return state

    def note_complete(self, project_id: str) -> ProjectFairnessState:
        state = self.get(project_id)
        state.active_missions = max(0, state.active_missions - 1)
        state.fairness_debt = max(0.0, state.fairness_debt - 0.5)
        return state

    def rank_projects(self, project_ids: list[str]) -> list[str]:
        scored = []
        for pid in project_ids:
            st = self.get(pid)
            # Lower debt / higher weight first.
            scored.append((st.fairness_debt / max(st.weight, 0.01), pid))
        scored.sort()
        return [pid for _, pid in scored]
