"""Minimal FastAPI application with health endpoints."""

from __future__ import annotations

from fastapi import FastAPI

from swarm import __version__


def create_app() -> FastAPI:
    app = FastAPI(title="SwarmAI", version=__version__)

    @app.get("/health/live")
    async def live() -> dict[str, str]:
        return {"status": "ok", "service": "swarm", "version": __version__}

    @app.get("/health/ready")
    async def ready() -> dict[str, object]:
        return {
            "status": "ready",
            "execution_mode": "mock",
            "providers_network": False,
            "allow_paid": False,
        }

    return app


app = create_app()
