"""Keep Alembic on the database each integration module inspects.

``migrations/env.py`` resolves its URL from ``SWARM_DATABASE_URL`` at run time,
while these modules bind ``DATABASE_URL`` at import. If anything earlier in the
same pytest process changed the environment, ``command.upgrade`` would migrate a
different database than the one the test asserts on.
"""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _pin_alembic_database_url(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> None:
    url = getattr(request.module, "DATABASE_URL", None)
    if url:
        monkeypatch.setenv("SWARM_DATABASE_URL", url)
