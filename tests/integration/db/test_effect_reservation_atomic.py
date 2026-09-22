"""R27b / ART-V17-APPROVAL-BINDING — atomic reserve + single-winner CAS (Postgres).

Each thread owns its own Session and repository and commits after every
repository call, so the concurrency being proven is PostgreSQL's, not Python's.
"""

from __future__ import annotations

import os
import threading
from typing import Any

import pytest
from sqlalchemy import create_engine, text

from swarm.contracts.actions import ActionEnvelope
from swarm.contracts.common import new_id
from swarm.db.engine import make_session_factory, ping
from swarm.db.models import Base
from swarm.tools.effects import DurableEffectRepository, EffectConflictError

pytestmark = pytest.mark.integration

DATABASE_URL = os.environ.get(
    "SWARM_DATABASE_URL", "postgresql+psycopg://swarm:swarm@127.0.0.1:5432/swarm"
)
THREADS = 8


@pytest.fixture(scope="module")
def engine():
    eng = create_engine(
        DATABASE_URL, pool_pre_ping=True, pool_size=THREADS + 2, max_overflow=THREADS
    )
    try:
        ping(eng)
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"postgres_unavailable:{type(exc).__name__}")
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture()
def factory(engine):
    fac = make_session_factory(engine)
    yield fac
    with engine.begin() as conn:
        conn.execute(
            text("TRUNCATE action_receipts, action_effects, approvals RESTART IDENTITY CASCADE")
        )


def _envelope(
    *,
    project: str = "proj_a",
    effect_key: str | None = None,
    payload: dict[str, Any] | None = None,
    destination: str = "mcp://echo/default",
    operation: str = "echo",
) -> ActionEnvelope:
    env = ActionEnvelope(
        project_id=project,
        actor="worker",
        integration_id="mcp.echo",
        integration_version="1",
        operation=operation,
        destination=destination,
        normalized_payload=payload or {"body": "atomic"},
        side_effect_class="consequential",
        risk_class="medium",
        effect_key=effect_key or "",
    )
    return env.ensure_hashes()


def _run_threads(factory, envelope: ActionEnvelope, fn):
    """Run `fn(repo, envelope)` in THREADS threads released by one barrier."""
    barrier = threading.Barrier(THREADS)
    results: list[Any] = [None] * THREADS
    errors: list[BaseException | None] = [None] * THREADS

    def worker(index: int) -> None:
        sess = factory()
        try:
            repo = DurableEffectRepository(sess)
            barrier.wait(timeout=10)
            results[index] = fn(repo, envelope)
            sess.commit()
        except BaseException as exc:  # noqa: BLE001
            sess.rollback()
            errors[index] = exc
        finally:
            sess.close()

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(THREADS)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)
    assert not any(t.is_alive() for t in threads), "thread hung"
    return results, errors


def test_concurrent_reserve_same_key_one_row(factory) -> None:
    env = _envelope(effect_key="proj_a:concurrent-reserve")
    results, errors = _run_threads(factory, env, lambda repo, e: repo.reserve(e))
    assert all(err is None for err in errors), errors
    effect_ids = {r["effect_id"] for r in results}
    assert len(effect_ids) == 1
    assert sum(1 for r in results if r["created"] is True) == 1
    sess = factory()
    try:
        count = sess.execute(
            text("SELECT count(*) FROM action_effects WHERE effect_key = :k"),
            {"k": env.effect_key},
        ).scalar()
        assert count == 1
    finally:
        sess.close()


def test_concurrent_mark_executing_single_winner(factory) -> None:
    env = _envelope(effect_key="proj_a:concurrent-execute")
    sess = factory()
    try:
        DurableEffectRepository(sess).reserve(env)
        sess.commit()
    finally:
        sess.close()

    results, errors = _run_threads(
        factory,
        env,
        lambda repo, e: repo.mark_executing(
            project_id=e.project_id, effect_key=e.effect_key, executor_id=new_id("exe_")
        ),
    )
    winners = [r for r in results if r is not None]
    losers = [err for err in errors if err is not None]
    assert len(winners) == 1
    assert len(losers) == THREADS - 1
    assert all(
        isinstance(err, EffectConflictError) and str(err) == "effect_already_executing"
        for err in losers
    ), [str(e) for e in losers]
    assert winners[0]["state"] == "executing"
    assert winners[0]["attempt_count"] == 1
    assert winners[0]["executor_id"].startswith("exe_")


def _assert_mismatch(factory, first: ActionEnvelope, second: ActionEnvelope) -> None:
    sess = factory()
    try:
        repo = DurableEffectRepository(sess)
        repo.reserve(first)
        sess.commit()
        with pytest.raises(EffectConflictError, match="effect_key_binding_mismatch"):
            repo.reserve(second)
        sess.rollback()
        count = sess.execute(
            text("SELECT count(*) FROM action_effects WHERE effect_key = :k"),
            {"k": first.effect_key},
        ).scalar()
        assert count == 1
    finally:
        sess.close()


def test_reserve_binding_mismatch_payload(factory) -> None:
    key = "proj_a:explicit-key-payload"
    _assert_mismatch(
        factory,
        _envelope(effect_key=key, payload={"body": "one"}),
        _envelope(effect_key=key, payload={"body": "two"}),
    )


def test_reserve_binding_mismatch_destination(factory) -> None:
    key = "proj_a:explicit-key-destination"
    _assert_mismatch(
        factory,
        _envelope(effect_key=key, destination="mcp://echo/a"),
        _envelope(effect_key=key, destination="mcp://echo/b"),
    )


def test_reserve_binding_mismatch_operation(factory) -> None:
    key = "proj_a:explicit-key-operation"
    _assert_mismatch(
        factory,
        _envelope(effect_key=key, operation="echo"),
        _envelope(effect_key=key, operation="delete"),
    )


def test_failed_without_not_applied_reason_is_terminal(factory) -> None:
    env = _envelope(effect_key="proj_a:failed-terminal")
    sess = factory()
    try:
        repo = DurableEffectRepository(sess)
        repo.reserve(env)
        repo.mark_executing(
            project_id=env.project_id, effect_key=env.effect_key, executor_id="exe_1"
        )
        repo.finalize(project_id=env.project_id, effect_key=env.effect_key, state="failed")
        sess.commit()
        with pytest.raises(EffectConflictError, match="effect_terminal:failed"):
            repo.mark_executing(
                project_id=env.project_id, effect_key=env.effect_key, executor_id="exe_2"
            )
        sess.rollback()
        # Only a provable non-application re-arms the effect.
        sess.execute(
            text("UPDATE action_effects SET state_reason='not_applied' WHERE effect_key=:k"),
            {"k": env.effect_key},
        )
        sess.commit()
        row = repo.mark_executing(
            project_id=env.project_id, effect_key=env.effect_key, executor_id="exe_3"
        )
        assert row["state"] == "executing"
        assert row["attempt_count"] == 2
        assert row["state_reason"] is None
    finally:
        sess.close()


def test_project_b_same_effect_key_is_independent(factory) -> None:
    key = "shared-key"
    a = _envelope(project="proj_a", effect_key=key, payload={"body": "a"})
    b = _envelope(project="proj_b", effect_key=key, payload={"body": "b"})
    sess = factory()
    try:
        repo = DurableEffectRepository(sess)
        ra = repo.reserve(a)
        rb = repo.reserve(b)
        sess.commit()
        assert ra["created"] is True and rb["created"] is True
        assert ra["effect_id"] != rb["effect_id"]
        repo.mark_executing(project_id="proj_a", effect_key=key, executor_id="exe_a")
        sess.commit()
        assert repo.get(project_id="proj_b", effect_key=key)["state"] == "reserved"
        assert repo.get(project_id="proj_a", effect_key=key)["state"] == "executing"
    finally:
        sess.close()
