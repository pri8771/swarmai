"""FastAPI application — health, auth, /v1 product API."""

from __future__ import annotations

import json
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from swarm import __version__
from swarm.api.auth import AuthRegistry
from swarm.api.errors import ApiError, api_error_handler
from swarm.api.routes_v1 import router as v1_router
from swarm.api.routes_v23 import build_v23_runtime, v23_session_factory
from swarm.api.routes_v23 import router as v23_router
from swarm.api.store import ProductStore
from swarm.contracts.common import new_id


def _install_identity_path(repo_root: Path) -> Path:
    return repo_root / "var" / "install" / "identity.json"


def resolve_install_project_id(repo_root: Path) -> str:
    """Per-install project id — never hard-codes proj_demo/proj_other.

    Order:
    1. SWARM_INSTALL_PROJECT_ID env (explicit operator mapping)
    2. Persisted var/install/identity.json
    3. Generate and persist a new install-local id
    """
    env_id = (os.environ.get("SWARM_INSTALL_PROJECT_ID") or "").strip()
    if env_id:
        if env_id in {"proj_demo", "proj_other"}:
            raise ApiError(
                "invalid_install_project",
                "SWARM_INSTALL_PROJECT_ID must not use demo project ids",
                status_code=500,
            )
        return env_id

    path = _install_identity_path(repo_root)
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            pid = str(data.get("project_id") or "").strip()
            if pid and pid not in {"proj_demo", "proj_other"}:
                return pid
        except (OSError, json.JSONDecodeError, TypeError):
            pass

    project_id = new_id("proj_install_")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "project_id": project_id,
                "subject": "install-operator",
                "note": "install-local identity — not demo fixture membership",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return project_id


def create_app(
    *,
    require_auth: bool = True,
    seed_loopback_token: str | None = None,
    seed_fixtures: bool = False,
    db_reachable: bool | None = None,
    repo_root: Path | None = None,
    install_project_id: str | None = None,
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
            # Product-compose console publishes host 43127 → container 8080;
            # Vite preview / alternate local binds may use 8080 directly.
            "http://127.0.0.1:8080",
            "http://localhost:8080",
        ],
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Idempotency-Key", "Accept"],
    )

    root = repo_root
    if root is None:
        env_root = (os.environ.get("SWARM_REPO_ROOT") or "").strip()
        if env_root:
            root = Path(env_root)
        else:
            # Prefer package-adjacent repo root (…/swarm-ai) for editable checkouts.
            root = Path(__file__).resolve().parents[3]

    if db_reachable is None and (os.environ.get("SWARM_DATABASE_URL") or "").strip():
        # Probe only when an explicit DSN is configured (secret-drop / .env).
        try:
            from swarm.db.engine import create_db_engine, ping

            db_reachable = ping(create_db_engine())
        except Exception:
            db_reachable = False

    store = ProductStore(db_reachable=db_reachable, repo_root=root)
    store.bootstrap_durable()
    if seed_fixtures:
        store.seed_catalog()
        store.fixture_mode = True
        store.execution_mode = "mock"
    auth = AuthRegistry(require_auth=require_auth)
    if seed_loopback_token:
        if seed_fixtures:
            # Fixture/test bootstrap may use known demo project membership.
            auth.issue(
                subject="loopback-operator",
                project_ids={"proj_demo", "proj_other"},
                roles={"operator"},
                allow_canary=False,
                allow_eval=False,
                token=seed_loopback_token,
            )
        else:
            # Operational bootstrap: install-local project only — no demo IDs.
            project_id = install_project_id or resolve_install_project_id(root)
            auth.issue(
                subject="install-operator",
                project_ids={project_id},
                roles={"operator"},
                allow_canary=False,
                allow_eval=False,
                token=seed_loopback_token,
            )
            app.state.install_project_id = project_id
        auth.loopback_mock_token = seed_loopback_token
    if seed_fixtures:
        # Explicit test/fixture seeding — separate from operational bootstrap.
        auth.issue(
            subject="policy-operator",
            project_ids={"proj_demo"},
            roles={"operator"},
            allow_canary=True,
            allow_eval=True,
            token="atk_policy_demo",
        )
        auth.issue(
            subject="other-project-user",
            project_ids={"proj_other"},
            roles={"operator"},
            token="atk_other_project",
        )
        if seed_loopback_token is None:
            # Tests that only set seed_fixtures still need a demo loopback principal.
            auth.issue(
                subject="loopback-operator",
                project_ids={"proj_demo", "proj_other"},
                roles={"operator"},
                allow_canary=False,
                allow_eval=False,
                token="atk_loopback_demo",
            )
            auth.loopback_mock_token = "atk_loopback_demo"

    app.state.store = store
    app.state.auth = auth
    app.state.repo_root = root
    from swarm.learning import LearningRepository
    from swarm.objectives import ObjectiveRepository
    from swarm.observability import OpsEventLog, SqlOpsSink

    app.state.objective_repo = ObjectiveRepository()
    app.state.learning_repo = LearningRepository()
    v23_factory = v23_session_factory(bool(db_reachable))
    app.state.ops_events = OpsEventLog(sink=SqlOpsSink(v23_factory) if v23_factory else None)
    app.state.v23 = build_v23_runtime(
        workers=store.workers, ops=app.state.ops_events, session_factory=v23_factory
    )
    if not hasattr(app.state, "install_project_id"):
        app.state.install_project_id = None

    @app.get("/health/live")
    async def live() -> dict[str, str]:
        return {"status": "ok", "service": "swarm", "version": __version__}

    @app.get("/health/ready")
    async def ready() -> dict[str, object]:
        return store.health_ready()

    app.include_router(v1_router)
    app.include_router(v23_router)
    return app


def _env_loopback_token() -> str | None:
    """Optional private install bootstrap. Empty/unset = no seeded identities."""
    raw = (os.environ.get("SWARM_SEED_LOOPBACK_TOKEN") or "").strip()
    return raw or None


app = create_app(seed_loopback_token=_env_loopback_token(), seed_fixtures=False)
