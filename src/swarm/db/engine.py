"""Database engine and session helpers."""

from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

DEFAULT_DATABASE_URL = "postgresql+psycopg://swarm:swarm@127.0.0.1:5432/swarm"


def database_url() -> str:
    return os.environ.get("SWARM_DATABASE_URL", DEFAULT_DATABASE_URL)


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
