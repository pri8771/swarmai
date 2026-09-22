"""Authenticated operator service for legacy effect disposition; no scheduler.

This service does not expose a new HTTP route or run an external action. The
caller must supply the registered bearer token of a project operator/admin.
"""

from __future__ import annotations

from typing import Any

from swarm.api.auth import AuthRegistry
from swarm.api.errors import ApiError
from swarm.tools.effects import DurableEffectRepository


def disposition_legacy_effect(
    *,
    store: DurableEffectRepository,
    auth: AuthRegistry,
    authorization: str | None,
    client_host: str,
    project_id: str,
    effect_key: str,
    expected_execution: tuple[str | None, int, str],
    reason: str,
    evidence_ref: str,
) -> dict[str, Any]:
    # Recovery never uses the unauthenticated loopback demo fallback.
    if not authorization or not authorization.lower().startswith("bearer "):
        raise ApiError("unauthorized", "explicit bearer token required", status_code=401)
    principal = auth.resolve(authorization, client_host=client_host)
    auth.require_project(principal, project_id)
    if not principal.roles.intersection({"operator", "admin"}):
        raise ApiError("operator_required", "operator role required", status_code=403)
    return store.disposition_legacy_executing(
        project_id=project_id,
        effect_key=effect_key,
        operator_subject=principal.subject,
        reason=reason,
        evidence_ref=evidence_ref,
        expected_execution=expected_execution,
    )
