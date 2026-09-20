"""Authentication and project scope isolation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Annotated

from fastapi import Depends, Header, Request

from swarm.api.errors import ApiError
from swarm.contracts.common import new_id


@dataclass(frozen=True)
class Principal:
    subject: str
    token_id: str
    project_ids: frozenset[str]
    roles: frozenset[str] = field(default_factory=frozenset)
    allow_canary: bool = False
    allow_eval: bool = False


@dataclass
class AuthRegistry:
    """In-memory token registry — tokens are opaque IDs, never provider secrets."""

    tokens: dict[str, Principal] = field(default_factory=dict)
    require_auth: bool = True
    loopback_mock_token: str | None = None

    def issue(
        self,
        *,
        subject: str,
        project_ids: set[str],
        roles: set[str] | None = None,
        allow_canary: bool = False,
        allow_eval: bool = False,
        token: str | None = None,
    ) -> str:
        token = token or new_id("atk_")
        if any(k in token.lower() for k in ("sk-", "api_key", "secret=")):
            raise ApiError(
                "invalid_token_shape",
                "token must not embed provider secrets",
                status_code=500,
            )
        self.tokens[token] = Principal(
            subject=subject,
            token_id=token[:12],
            project_ids=frozenset(project_ids),
            roles=frozenset(roles or {"operator"}),
            allow_canary=allow_canary,
            allow_eval=allow_eval,
        )
        return token

    def resolve(self, authorization: str | None, *, client_host: str | None) -> Principal:
        if authorization and authorization.lower().startswith("bearer "):
            raw = authorization.split(" ", 1)[1].strip()
            principal = self.tokens.get(raw)
            if principal is None:
                raise ApiError("unauthorized", "invalid bearer token", status_code=401)
            return principal
        # Loopback-only mock mode may use a seeded token without Authorization
        # when require_auth is False (explicit test/demo). Non-loopback always requires auth.
        is_loopback = client_host in {None, "127.0.0.1", "::1", "testclient", "localhost"}
        if not self.require_auth and is_loopback and self.loopback_mock_token:
            principal = self.tokens.get(self.loopback_mock_token)
            if principal is not None:
                return principal
        if not is_loopback:
            raise ApiError(
                "auth_required",
                "non-loopback requests require Authorization",
                status_code=401,
            )
        raise ApiError("unauthorized", "missing bearer token", status_code=401)

    def require_project(self, principal: Principal, project_id: str) -> None:
        if project_id not in principal.project_ids and "admin" not in principal.roles:
            raise ApiError(
                "forbidden_project",
                "principal cannot access this project",
                status_code=403,
                details={"project_id": project_id},
            )


def get_auth(request: Request) -> AuthRegistry:
    return request.app.state.auth  # type: ignore[no-any-return]


def get_principal(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
    auth: AuthRegistry = Depends(get_auth),
) -> Principal:
    client_host = request.client.host if request.client else None
    return auth.resolve(authorization, client_host=client_host)
