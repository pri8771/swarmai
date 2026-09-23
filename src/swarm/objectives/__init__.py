"""V3.0 objective repository + trigger admission."""

from __future__ import annotations

from typing import Any

from swarm.contracts.common import new_id, utc_now
from swarm.objectives.contracts import MissionProposal, ObjectiveContract


class ObjectiveError(RuntimeError):
    pass


class ObjectiveRepository:
    def __init__(self) -> None:
        self._objectives: dict[str, ObjectiveContract] = {}
        self._versions: dict[str, list[ObjectiveContract]] = {}
        self._triggers: dict[tuple[str, str], dict[str, Any]] = {}
        self._proposals: dict[str, MissionProposal] = {}
        self._active_by_objective: dict[str, int] = {}

    def create(self, objective: ObjectiveContract) -> ObjectiveContract:
        if objective.spend_usd_ceiling < 0:
            raise ObjectiveError("invalid_spend_ceiling")
        # Persistent objectives are not permanent permissions to spend.
        if objective.spend_usd_ceiling > 0:
            raise ObjectiveError("paid_spend_requires_operator_auth")
        self._objectives[objective.objective_id] = objective
        self._versions.setdefault(objective.objective_id, []).append(objective)
        return objective

    def get(self, objective_id: str) -> ObjectiveContract:
        obj = self._objectives.get(objective_id)
        if obj is None:
            raise ObjectiveError("objective_missing")
        return obj

    def pause(self, objective_id: str) -> ObjectiveContract:
        obj = self.get(objective_id)
        obj.state = "paused"
        return obj

    def revoke(self, objective_id: str) -> ObjectiveContract:
        obj = self.get(objective_id)
        obj.state = "revoked"
        return obj

    def trigger(
        self,
        objective_id: str,
        *,
        dedupe_key: str,
        trigger_kind: str,
        template_id: str | None = None,
    ) -> MissionProposal:
        obj = self.get(objective_id)
        if obj.state != "active":
            raise ObjectiveError(f"objective_not_active:{obj.state}")
        key = (objective_id, dedupe_key)
        if key in self._triggers:
            existing = self._proposals.get(str(self._triggers[key].get("proposal_id")))
            if existing is not None:
                return MissionProposal(
                    objective_id=existing.objective_id,
                    objective_version=existing.objective_version,
                    project_id=existing.project_id,
                    goal=existing.goal,
                    template_id=existing.template_id,
                    state="duplicate",
                    mission_id=existing.mission_id,
                    dedupe_key=dedupe_key,
                )
            raise ObjectiveError("duplicate_trigger")
        active = self._active_by_objective.get(objective_id, 0)
        if active >= obj.max_active_missions:
            raise ObjectiveError("max_active_missions")
        if template_id:
            tmpl = template_id
        elif obj.allowed_mission_templates:
            tmpl = obj.allowed_mission_templates[0]
        else:
            tmpl = "generic"
        if obj.allowed_mission_templates and tmpl not in obj.allowed_mission_templates:
            raise ObjectiveError("template_not_allowed")
        proposal = MissionProposal(
            objective_id=obj.objective_id,
            objective_version=obj.version,
            project_id=obj.project_id,
            goal=obj.goal,
            template_id=tmpl,
            dedupe_key=dedupe_key,
        )
        self._proposals[proposal.proposal_id] = proposal
        self._triggers[key] = {
            "proposal_id": proposal.proposal_id,
            "trigger_kind": trigger_kind,
            "at": utc_now().isoformat(),
        }
        return proposal

    def admit_to_mission(
        self, proposal_id: str, *, mission_id: str | None = None
    ) -> MissionProposal:
        """Bridge into normal mission admission — no side door."""
        proposal = self._proposals.get(proposal_id)
        if proposal is None:
            raise ObjectiveError("proposal_missing")
        if proposal.state not in {"proposed", "duplicate"}:
            raise ObjectiveError(f"proposal_state:{proposal.state}")
        if proposal.state == "duplicate":
            raise ObjectiveError("duplicate_cannot_admit")
        mid = mission_id or new_id("mis_")
        proposal.mission_id = mid
        proposal.state = "admitted"
        self._active_by_objective[proposal.objective_id] = (
            self._active_by_objective.get(proposal.objective_id, 0) + 1
        )
        return proposal
