"""Common envelope fields and helpers."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


def utc_now() -> datetime:
    return datetime.now(UTC)


def new_id(prefix: str = "") -> str:
    value = uuid4().hex
    return f"{prefix}{value}" if prefix else value


def payload_hash(payload: dict[str, Any] | BaseModel) -> str:
    if isinstance(payload, BaseModel):
        data = payload.model_dump(mode="json")
    else:
        data = payload
    encoded = json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


class StrictModel(BaseModel):
    """Reject unknown fields so permission/quota errors cannot be silently dropped."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Envelope(StrictModel):
    schema_version: str = "1.0"
    id: str = Field(default_factory=new_id)
    created_at: datetime = Field(default_factory=utc_now)
    project_id: str
    trace_id: str = Field(default_factory=lambda: new_id("tr_"))
    payload_hash: str | None = None
