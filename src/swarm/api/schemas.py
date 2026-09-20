"""Request/response schemas for the product API."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from swarm.contracts.common import StrictModel
from swarm.contracts.mission import Mission


class MissionCreateRequest(StrictModel):
    mission: Mission
    idempotency_key: str | None = None


class CancelRequest(StrictModel):
    reason: str | None = None
    idempotency_key: str | None = None


class WorkerEnrollRequest(StrictModel):
    project_id: str
    capabilities: list[str] = Field(default_factory=lambda: ["chat", "tools"])
    capacity_units: float = 1.0
    privacy_classes: list[str] = Field(default_factory=lambda: ["local"])
    named_inference_urls: list[str] = Field(default_factory=list)
    idempotency_key: str | None = None


class WorkerHeartbeatRequest(StrictModel):
    worker_id: str
    generation: int
    token: str


class ApprovalResolveRequest(StrictModel):
    accept: bool
    payload: dict[str, Any] | None = None
    idempotency_key: str | None = None


class ProbeRequest(StrictModel):
    """Bounded provider probe — requires canary policy admission."""

    purpose: str = "prototype"
    idempotency_key: str | None = None


class EvaluationCreateRequest(StrictModel):
    suite: str = "starter"
    mode: str = "mock"
    max_cases: int = 8
    idempotency_key: str | None = None


class PageMeta(StrictModel):
    limit: int
    cursor: str | None = None
    has_more: bool = False
