"""Structured API errors — schema-versioned, no secrets."""

from __future__ import annotations

from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import Field

from swarm.contracts.common import StrictModel, new_id, utc_now


class ApiErrorBody(StrictModel):
    schema_version: str = "1.0"
    error_id: str = Field(default_factory=lambda: new_id("err_"))
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    occurred_at: object = Field(default_factory=utc_now)


class ApiError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}

    def body(self) -> ApiErrorBody:
        return ApiErrorBody(code=self.code, message=self.message, details=self.details)


async def api_error_handler(_request: Request, exc: ApiError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content=exc.body().model_dump(mode="json"))
