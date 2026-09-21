"""Database engine and session helpers.

V2A-H6A: operational default is empty/unconfigured. A secret-backed
``SWARM_DATABASE_URL`` must be set explicitly — never fall back to a
committed ``swarm:swarm`` password.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


class DatabaseConfigError(RuntimeError):
    """Raised when the operational database DSN is missing or unsafe."""


def database_url() -> str:
    """Return the configured DSN or fail closed when unconfigured."""
    url = (os.environ.get("SWARM_DATABASE_URL") or "").strip()
    if not url:
        raise DatabaseConfigError(
            "SWARM_DATABASE_URL is unset — operational default is empty/unconfigured; "
            "set an explicit secret-backed DSN (see deploy/compose/.env.example)"
        )
    if "swarm:swarm@" in url:
        raise DatabaseConfigError(
            "SWARM_DATABASE_URL uses the forbidden fixed demo credential swarm:swarm; "
            "generate an operator secret (scripts/generate_compose_env.py)"
        )
    return url


def create_db_engine(url: str | None = None, *, echo: bool = False) -> Engine:
    return create_engine(url or database_url(), pool_pre_ping=True, echo=echo)


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@contextmanager
def session_scope(factory: sessionmaker[Session]) -> Iterator[Session]:
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def ping(engine: Engine) -> bool:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return True
