"""V3.0 objective repository + trigger admission."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from swarm.contracts.common import new_id, utc_now
from swarm.objectives.contracts import MissionProposal, ObjectiveContract

__all__ = [
    "MissionProposal",
    "ObjectiveContract",
    "ObjectiveError",
    "ObjectiveRepository",
]


class ObjectiveError(RuntimeError):
    pass


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    raw = value.replace("Z", "+00:00")
    dt = datetime.fromisoformat(raw)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt


class ObjectiveRepository:
    def __init__(self) -> None:
        self._objectives: dict[str, ObjectiveContract] = {}
        self._versions: dict[str, list[ObjectiveContract]] = {}
        self._triggers: dict[tuple[str, str], dict[str, Any]] = {}
        self._trigger_times: dict[str, list[datetime]] = {}
        self._proposals: dict[str, MissionProposal] = {}
        self._active_by_objective: dict[str, int] = {}
        self._stop_hits: dict[str, set[str]] = {}

    def create(self, objective: ObjectiveContract) -> ObjectiveContract:
        if objective.spend_usd_ceiling < 0:
            raise ObjectiveError("invalid_spend_ceiling")
        # Persistent objectives are not permanent permissions to spend.
        if objective.spend_usd_ceiling > 0:
            raise ObjectiveError("paid_spend_requires_operator_auth")
        # Versions are immutable: same objective_id + version cannot be rewritten.
        existing_versions = self._versions.get(objective.objective_id, [])
        for prior in existing_versions:
            if prior.version == objective.version:
                raise ObjectiveError("objective_version_immutable")
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

    def mark_stop(self, objective_id: str, condition: str) -> ObjectiveContract:
        obj = self.get(objective_id)
        hits = self._stop_hits.setdefault(objective_id, set())
        hits.add(condition)
        if condition in obj.stop_conditions or "*" in obj.stop_conditions:
            obj.state = "revoked"
        return obj

    def intersect_authority(
        self,
        objective_id: str,
        *,
        tools: set[str] | None = None,
        data: set[str] | None = None,
        providers: set[str] | None = None,
    ) -> dict[str, set[str]]:
        """Authority intersection: requested scopes ∩ objective envelopes."""
        obj = self.get(objective_id)
        tool_env = set(obj.tool_envelope)
        data_env = set(obj.data_envelope)
        prov_env = set(obj.provider_envelope)
        req_tools = tools if tools is not None else tool_env
        req_data = data if data is not None else data_env
        req_prov = providers if providers is not None else prov_env
        if tool_env and not (req_tools & tool_env):
            raise ObjectiveError("authority_intersection_empty:tools")
        if data_env and not (req_data & data_env):
            raise ObjectiveError("authority_intersection_empty:data")
        if prov_env and not (req_prov & prov_env):
            raise ObjectiveError("authority_intersection_empty:providers")
        return {
            "tools": req_tools & tool_env if tool_env else req_tools,
            "data": req_data & data_env if data_env else req_data,
            "providers": req_prov & prov_env if prov_env else req_prov,
        }

    def _enforce_active(self, obj: ObjectiveContract) -> None:
        if obj.state != "active":
            raise ObjectiveError(f"objective_not_active:{obj.state}")
        expires = _parse_iso(obj.expires_at)
        if expires is not None and utc_now() >= expires:
            obj.state = "expired"
            raise ObjectiveError("objective_expired")
        stop_hits = self._stop_hits.get(obj.objective_id, set())
        if stop_hits & set(obj.stop_conditions):
            obj.state = "revoked"
            raise ObjectiveError("stop_condition_met")

    def _enforce_rate(self, objective_id: str, limit: int) -> None:
        now = utc_now()
        window = self._trigger_times.setdefault(objective_id, [])
        cutoff = now.timestamp() - 3600
        kept = [t for t in window if t.timestamp() >= cutoff]
        self._trigger_times[objective_id] = kept
        if len(kept) >= limit:
            raise ObjectiveError("rate_limit_per_hour")

    def trigger(
        self,
        objective_id: str,
        *,
        dedupe_key: str,
        trigger_kind: str,
        template_id: str | None = None,
    ) -> MissionProposal:
        obj = self.get(objective_id)
        self._enforce_active(obj)
        if obj.trigger_policy == "schedule" and trigger_kind != "schedule":
            raise ObjectiveError("trigger_policy_denied")
        if obj.trigger_policy == "event" and trigger_kind != "event":
            raise ObjectiveError("trigger_policy_denied")
        if obj.trigger_policy == "schedule" and not obj.schedule_cron:
            raise ObjectiveError("schedule_cron_required")
        if obj.trigger_policy == "event" and not obj.event_types:
            raise ObjectiveError("event_types_required")
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
        self._enforce_rate(objective_id, obj.rate_limit_per_hour)
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
        self._trigger_times.setdefault(objective_id, []).append(utc_now())
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
        obj = self.get(proposal.objective_id)
        self._enforce_active(obj)
        mid = mission_id or new_id("mis_")
        proposal.mission_id = mid
        proposal.state = "admitted"
        self._active_by_objective[proposal.objective_id] = (
            self._active_by_objective.get(proposal.objective_id, 0) + 1
        )
        return proposal
