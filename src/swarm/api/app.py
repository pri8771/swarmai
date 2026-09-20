"""FastAPI application — health, auth, /v1 product API."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from swarm import __version__
from swarm.api.auth import AuthRegistry
from swarm.api.errors import ApiError, api_error_handler
from swarm.api.routes_v1 import router as v1_router
from swarm.api.store import ProductStore


def create_app(
    *,
    require_auth: bool = True,
    seed_loopback_token: str | None = None,
    seed_fixtures: bool = False,
    db_reachable: bool | None = None,
    repo_root: Path | None = None,
) -> FastAPI:
    app = FastAPI(title="SwarmAI", version=__version__)
    app.add_exception_handler(ApiError, api_error_handler)  # type: ignore[arg-type]
    # Private console on loopback only — not a public deployment surface.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1:43127",
            "http://localhost:43127",
            "http://127.0.0.1:4177",
            "http://localhost:4177",
        ],
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Idempotency-Key", "Accept"],
    )

    root = repo_root
    if root is None:
        # Prefer package-adjacent repo root (…/swarm-ai).
        root = Path(__file__).resolve().parents[3]

    store = ProductStore(db_reachable=db_reachable, repo_root=root)
    if seed_fixtures:
        store.seed_catalog()
    auth = AuthRegistry(require_auth=require_auth)
    if seed_loopback_token:
        auth.issue(
            subject="loopback-operator",
            project_ids={"proj_demo", "proj_other"},
            roles={"operator"},
            allow_canary=False,
            allow_eval=False,
            token=seed_loopback_token,
        )
        auth.loopback_mock_token = seed_loopback_token
        # Elevated token for canary/eval policy tests (issued, not a default admin password).
        auth.issue(
            subject="policy-operator",
            project_ids={"proj_demo"},
            roles={"operator"},
            allow_canary=True,
            allow_eval=True,
            token="atk_policy_demo",
        )
        # Isolated project principal for isolation tests.
        auth.issue(
            subject="other-project-user",
            project_ids={"proj_other"},
            roles={"operator"},
            token="atk_other_project",
        )

    app.state.store = store
    app.state.auth = auth
    app.state.repo_root = root

    @app.get("/health/live")
    async def live() -> dict[str, str]:
        return {"status": "ok", "service": "swarm", "version": __version__}

    @app.get("/health/ready")
    async def ready() -> dict[str, object]:
        return store.health_ready()

    app.include_router(v1_router)
    return app


def _env_loopback_token() -> str | None:
    """Optional private install bootstrap. Empty/unset = no seeded identities."""
    raw = (os.environ.get("SWARM_SEED_LOOPBACK_TOKEN") or "").strip()
    return raw or None


app = create_app(seed_loopback_token=_env_loopback_token(), seed_fixtures=False)
