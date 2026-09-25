"""Python SDK client for SwarmAI goal-pursuit and mission APIs.

Mirrors product HTTP contracts under ``/v1``:
- Goals lifecycle: create/transition/pause/resume/cancel/restart/…
- Pursuit: ``/v1/goals/{id}/pursuit/*``
- Missions, artifacts, events
- Workers inspect + cancel-lease (operator control)
- Approvals list + resolve
Does not launch a separate engine.
"""

from __future__ import annotations

from typing import Any

import httpx

from swarm.goals.models import Goal, GoalStatus


class SwarmClientError(RuntimeError):
    """Raised when the product API returns a non-success response."""

    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(f"{code}: {message} (HTTP {status_code})")
        self.status_code = status_code
        self.code = code
        self.message = message


class SwarmClient:
    """Sync HTTP client for goal create → pursue → interrupt/resume → inspect."""

    def __init__(
        self,
        base_url: str,
        *,
        token: str | None = None,
        timeout: float = 30.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        headers: dict[str, str] = {"Accept": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self._client = httpx.Client(
            base_url=base_url.rstrip("/"),
            headers=headers,
            timeout=timeout,
            transport=transport,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> SwarmClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _raise_for_error(self, response: httpx.Response) -> None:
        if response.is_success:
            return
        code = "api_error"
        message = response.text[:500]
        try:
            body = response.json()
            if isinstance(body, dict):
                err = body.get("error") if isinstance(body.get("error"), dict) else body
                if isinstance(err, dict):
                    code = str(err.get("code") or err.get("type") or code)
                    message = str(err.get("message") or err.get("detail") or message)
        except (ValueError, TypeError):
            pass
        raise SwarmClientError(response.status_code, code, message)

    def _json(self, response: httpx.Response) -> dict[str, Any]:
        self._raise_for_error(response)
        payload = response.json()
        if not isinstance(payload, dict):
            raise SwarmClientError(response.status_code, "invalid_payload", "expected object")
        return payload

    def _goal_from(self, data: dict[str, Any]) -> Goal:
        return Goal.model_validate(data["goal"])

    # --- Goals (Lane C / V1.8) ---

    def list_goals(self, *, project_id: str | None = None) -> list[Goal]:
        params = {"project_id": project_id} if project_id else None
        data = self._json(self._client.get("/v1/goals", params=params))
        return [Goal.model_validate(row) for row in data.get("goals") or []]

    def get_goal(self, goal_id: str) -> Goal:
        data = self._json(self._client.get(f"/v1/goals/{goal_id}"))
        return self._goal_from(data)

    def create_goal(
        self,
        *,
        project_id: str,
        desired_outcome: str,
        verification_criteria: list[str] | None = None,
        kind: str = "finite",
        permitted_agents: list[str] | None = None,
        resource_envelope: dict[str, Any] | None = None,
        authority_envelope: dict[str, Any] | None = None,
        scope: dict[str, Any] | None = None,
        constraints: dict[str, Any] | None = None,
        strategy: str = "",
        stop_conditions: list[str] | None = None,
        dependencies: list[str] | None = None,
        open_questions: list[str] | None = None,
        blockers: list[str] | None = None,
        review_cadence: str | None = None,
        expires_at: str | None = None,
        owner: str = "operator",
        idempotency_key: str | None = None,
    ) -> Goal:
        body: dict[str, Any] = {
            "project_id": project_id,
            "desired_outcome": desired_outcome,
            "verification_criteria": verification_criteria or [],
            "kind": kind,
            "permitted_agents": permitted_agents or [],
            "resource_envelope": resource_envelope or {},
            "authority_envelope": authority_envelope or {},
            "scope": scope or {},
            "constraints": constraints or {},
            "strategy": strategy,
            "stop_conditions": stop_conditions or [],
            "dependencies": dependencies or [],
            "open_questions": open_questions or [],
            "blockers": blockers or [],
            "owner": owner,
        }
        if review_cadence is not None:
            body["review_cadence"] = review_cadence
        if expires_at is not None:
            body["expires_at"] = expires_at
        if idempotency_key:
            body["idempotency_key"] = idempotency_key
        return self._goal_from(self._json(self._client.post("/v1/goals", json=body)))

    def transition_goal(
        self,
        goal_id: str,
        status: GoalStatus | str,
        *,
        reason: str = "",
        idempotency_key: str | None = None,
    ) -> Goal:
        body: dict[str, Any] = {
            "status": status.value if isinstance(status, GoalStatus) else str(status),
            "reason": reason,
        }
        if idempotency_key:
            body["idempotency_key"] = idempotency_key
        return self._goal_from(
            self._json(self._client.post(f"/v1/goals/{goal_id}/transition", json=body))
        )

    def _lifecycle(self, goal_id: str, action: str, *, reason: str = "") -> Goal:
        return self._goal_from(
            self._json(
                self._client.post(
                    f"/v1/goals/{goal_id}/{action}",
                    json={"reason": reason},
                )
            )
        )

    def interrupt_goal(self, goal_id: str, *, reason: str = "operator interrupt") -> Goal:
        """Pause via Lane C ``POST /goals/{id}/pause``."""
        return self._lifecycle(goal_id, "pause", reason=reason)

    def resume_goal(self, goal_id: str, *, reason: str = "operator resume") -> Goal:
        return self._lifecycle(goal_id, "resume", reason=reason)

    def cancel_goal(self, goal_id: str, *, reason: str = "operator cancel") -> Goal:
        return self._lifecycle(goal_id, "cancel", reason=reason)

    def restart_goal(self, goal_id: str, *, reason: str = "operator restart") -> Goal:
        return self._lifecycle(goal_id, "restart", reason=reason)

    def link_mission(self, goal_id: str, mission_id: str) -> Goal:
        return self._goal_from(
            self._json(
                self._client.post(
                    f"/v1/goals/{goal_id}/missions",
                    json={"mission_id": mission_id},
                )
            )
        )

    def record_progress(
        self,
        goal_id: str,
        *,
        summary: str,
        metrics: dict[str, Any] | None = None,
    ) -> Goal:
        return self._goal_from(
            self._json(
                self._client.post(
                    f"/v1/goals/{goal_id}/progress",
                    json={"summary": summary, "metrics": metrics or {}},
                )
            )
        )

    def record_mission_outcome(
        self,
        goal_id: str,
        *,
        mission_id: str,
        outcome: str,
        notes: str = "",
        evidence_refs: list[str] | None = None,
    ) -> Goal:
        return self._goal_from(
            self._json(
                self._client.post(
                    f"/v1/goals/{goal_id}/mission-outcomes",
                    json={
                        "mission_id": mission_id,
                        "outcome": outcome,
                        "notes": notes,
                        "evidence_refs": evidence_refs or [],
                    },
                )
            )
        )

    def redirect_goal(
        self,
        goal_id: str,
        *,
        reason: str,
        force_tick: bool = True,
    ) -> dict[str, Any]:
        """Interrupt, resume with redirect reason, then tick pursuit once."""
        goal = self.get_goal(goal_id)
        if goal.status == GoalStatus.ACTIVE:
            goal = self.interrupt_goal(goal_id, reason=f"redirect:{reason}")
        if goal.status == GoalStatus.PAUSED:
            goal = self.resume_goal(goal_id, reason=f"redirect_resume:{reason}")
        elif goal.status in {GoalStatus.CANCELLED, GoalStatus.EXPIRED, GoalStatus.ACHIEVED}:
            goal = self.restart_goal(goal_id, reason=f"redirect_restart:{reason}")
        cycle_payload = self.pursuit_tick(goal_id, force=force_tick)
        return {"goal": cycle_payload["goal"], "cycle": cycle_payload.get("cycle")}

    # --- Pursuit (Lane D / V1.9) ---

    def start_pursuit(self, goal_id: str, *, force: bool = True) -> dict[str, Any]:
        """Start/advance pursuit via ``POST /v1/goals/{id}/pursuit/tick``."""
        goal = self.get_goal(goal_id)
        if goal.status == GoalStatus.PAUSED:
            self.resume_goal(goal_id, reason="start_pursuit")
        elif goal.status in {GoalStatus.CANCELLED, GoalStatus.EXPIRED}:
            self.restart_goal(goal_id, reason="start_pursuit")
        return self.pursuit_tick(goal_id, force=force)

    def pursuit_tick(self, goal_id: str, *, force: bool = False) -> dict[str, Any]:
        data = self._json(
            self._client.post(
                f"/v1/goals/{goal_id}/pursuit/tick",
                json={"force": force},
            )
        )
        goal = Goal.model_validate(data["goal"])
        return {"goal": goal, "cycle": data.get("cycle")}

    def pursuit_status(self, goal_id: str) -> dict[str, Any]:
        return self._json(self._client.get(f"/v1/goals/{goal_id}/pursuit"))

    def why_next(self, goal_id: str) -> dict[str, Any]:
        """Inspect pursuit status + decision history explaining the next action."""
        goal = self.get_goal(goal_id)
        status = self.pursuit_status(goal_id)
        history = list(status.get("history") or [])
        latest_cycle = history[-1] if history else None
        decisions = list(goal.decision_history)
        latest_decision = decisions[-1] if decisions else None
        why = None
        if isinstance(latest_cycle, dict):
            why = (
                latest_cycle.get("notes")
                or (latest_cycle.get("decided_kind") and f"decided:{latest_cycle['decided_kind']}")
                or None
            )
        if not why and isinstance(latest_decision, dict):
            why = latest_decision.get("reason") or latest_decision.get("action")
        if not why:
            why = goal.strategy or "no_decision_recorded"
        return {
            "goal_id": goal.id,
            "status": goal.status.value,
            "strategy": goal.strategy,
            "blockers": list(goal.blockers),
            "open_questions": list(goal.open_questions),
            "progress": list(goal.progress),
            "mission_outcomes": list(goal.mission_outcomes),
            "evidence_refs": list(goal.evidence_refs),
            "mission_ids": list(goal.mission_ids),
            "decision_history": decisions,
            "pursuit": status,
            "latest_cycle": latest_cycle,
            "latest_decision": latest_decision,
            "why_next": why,
        }

    # --- Missions ---

    def create_mission(
        self,
        *,
        project_id: str,
        objective: str,
        acceptance_criteria: list[str] | None = None,
        allowed_capabilities: list[str] | None = None,
        data_scope_ids: list[str] | None = None,
        resource_policy_id: str = "policy_default",
        max_wall_time_seconds: int = 3600,
        max_graph_nodes: int = 50,
        max_active_sessions: int = 4,
        max_model_calls: int = 50,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "mission": {
                "project_id": project_id,
                "objective": objective,
                "acceptance_criteria": acceptance_criteria or ["operator review"],
                "allowed_capabilities": allowed_capabilities or ["code.read"],
                "data_scope_ids": data_scope_ids or ["scope_local"],
                "resource_policy_id": resource_policy_id,
                "max_wall_time_seconds": max_wall_time_seconds,
                "max_graph_nodes": max_graph_nodes,
                "max_active_sessions": max_active_sessions,
                "max_model_calls": max_model_calls,
            }
        }
        if idempotency_key:
            body["idempotency_key"] = idempotency_key
        data = self._json(self._client.post("/v1/missions", json=body))
        mission = data.get("mission")
        if not isinstance(mission, dict):
            raise SwarmClientError(500, "invalid_mission", "create_mission missing mission")
        return mission

    def get_mission(self, mission_id: str) -> dict[str, Any]:
        data = self._json(self._client.get(f"/v1/missions/{mission_id}"))
        mission = data.get("mission")
        if not isinstance(mission, dict):
            raise SwarmClientError(500, "invalid_mission", "get_mission missing mission")
        return mission

    def list_missions(self) -> list[dict[str, Any]]:
        data = self._json(self._client.get("/v1/missions"))
        rows = data.get("missions") or data.get("items") or []
        return [r for r in rows if isinstance(r, dict)]

    def cancel_mission(self, mission_id: str, *, reason: str | None = None) -> dict[str, Any]:
        body: dict[str, Any] = {}
        if reason:
            body["reason"] = reason
        data = self._json(self._client.post(f"/v1/missions/{mission_id}/cancel", json=body))
        mission = data.get("mission")
        if not isinstance(mission, dict):
            return data
        return mission

    def list_mission_artifacts(self, mission_id: str) -> list[dict[str, Any]]:
        data = self._json(self._client.get(f"/v1/missions/{mission_id}/artifacts"))
        rows = data.get("artifacts") or []
        return [r for r in rows if isinstance(r, dict)]

    def list_events(
        self,
        *,
        mission_id: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"limit": limit}
        if mission_id:
            params["mission_id"] = mission_id
        data = self._json(self._client.get("/v1/events", params=params))
        rows = data.get("items") or data.get("events") or []
        return [r for r in rows if isinstance(r, dict)]

    def list_workers(self, *, project_id: str | None = None) -> list[dict[str, Any]]:
        params = {"project_id": project_id} if project_id else None
        data = self._json(self._client.get("/v1/workers", params=params))
        rows = data.get("workers") or []
        return [r for r in rows if isinstance(r, dict)]

    def cancel_worker_lease(
        self,
        lease_id: str,
        *,
        reason: str = "sdk_operator_cancel",
    ) -> dict[str, Any]:
        return self._json(
            self._client.post(
                "/v1/workers/cancel-lease",
                json={"lease_id": lease_id, "reason": reason},
            )
        )

    def list_approvals(self, *, project_id: str | None = None) -> list[dict[str, Any]]:
        params = {"project_id": project_id} if project_id else None
        data = self._json(self._client.get("/v1/approvals", params=params))
        rows = data.get("approvals") or []
        return [r for r in rows if isinstance(r, dict)]

    def resolve_approval(
        self,
        approval_id: str,
        *,
        accept: bool,
        payload: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"accept": accept, "payload": payload}
        if idempotency_key:
            body["idempotency_key"] = idempotency_key
        return self._json(
            self._client.post(f"/v1/approvals/{approval_id}/resolve", json=body)
        )