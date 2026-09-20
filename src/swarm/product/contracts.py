"""Public product contract surface — aligned CLI/API fields, no internal leakage."""

from __future__ import annotations

from typing import Any

from swarm.product.projects import scrub_config

# Stable public resource names exposed by CLI + API.
PUBLIC_RESOURCES = (
    "project",
    "mission",
    "task",
    "agent",
    "artifact",
    "approval",
    "provider",
    "report",
)

# Fields that must never leave the product boundary.
INTERNAL_ONLY_FIELDS = frozenset(
    {
        "runtime_client",
        "secret_value",
        "api_key",
        "membership_token_raw",
        "broker_internal",
        "lease_token_plain",
        "_workers",
        "idempotency",
    }
)


def strip_internal(obj: Any) -> Any:
    """Remove internal-only keys recursively."""
    if isinstance(obj, dict):
        return {
            k: strip_internal(v)
            for k, v in obj.items()
            if k not in INTERNAL_ONLY_FIELDS and not str(k).startswith("_")
        }
    if isinstance(obj, list):
        return [strip_internal(x) for x in obj]
    return obj


def mission_public_view(record: dict[str, Any]) -> dict[str, Any]:
    """Normalize a mission record into the public product shape."""
    raw = strip_internal(scrub_config(record))
    return {
        "mission_id": raw.get("mission_id") or raw.get("id"),
        "project_id": raw.get("project_id")
        or (raw.get("plan") or {}).get("project_id"),
        "goal": raw.get("goal") or raw.get("objective"),
        "status": raw.get("status"),
        "revision": raw.get("revision"),
        "tasks": [
            {
                "task_id": t.get("id") or t.get("task_id"),
                "status": t.get("status"),
                "task_family": t.get("task_family"),
                "ok": t.get("ok"),
                "objective": t.get("objective"),
            }
            for t in (raw.get("tasks") or [])
        ],
        "agents": raw.get("agents") or [],
        "artifacts": raw.get("artifacts") or {},
        "approvals": raw.get("approvals") or [],
        "timeline": raw.get("timeline") or [],
        "model_assignments": raw.get("model_assignments") or [],
        "validation": raw.get("validation") or {},
        "cost": raw.get("cost") or {},
        "result": raw.get("result") or {},
        "created_at": raw.get("created_at"),
        "updated_at": raw.get("updated_at"),
        "report_refs": raw.get("report_refs") or [],
    }


def public_product_contract() -> dict[str, Any]:
    """Machine-readable CLI/API product contract (V0.8)."""
    return {
        "schema_version": "0.8.0",
        "resources": list(PUBLIC_RESOURCES),
        "endpoints": {
            "project": ["POST /v1/projects", "GET /v1/projects", "GET /v1/projects/{id}"],
            "mission": [
                "POST /v1/missions",
                "GET /v1/missions",
                "GET /v1/missions/{id}",
                "GET /v1/missions/{id}/graph",
                "GET /v1/missions/{id}/report",
            ],
            "task": ["GET /v1/missions/{id}/graph"],
            "agent": ["GET /v1/missions/{id}", "GET /v1/workers"],
            "artifact": [
                "GET /v1/missions/{id}/artifacts",
                "GET /v1/history/{mission_id}",
            ],
            "approval": [
                "GET /v1/approvals",
                "POST /v1/approvals/{id}/resolve",
            ],
            "provider": ["GET /v1/providers", "GET /v1/routes"],
            "report": ["GET /v1/missions/{id}/report", "GET /v1/history"],
        },
        "cli": {
            "project": ["swarm projects create|list|show|update"],
            "mission": ["swarm mission plan|run|status|list|report"],
            "history": ["swarm product history|reopen"],
            "journey": ["swarm product journey"],
            "contract": ["swarm product contract"],
        },
        "internal_fields_stripped": sorted(INTERNAL_ONLY_FIELDS),
        "secrets_policy": "never_persist_or_return_secret_values",
        "spend_policy_default": "zero",
    }
