"""Local revocation must serialize with committed effect admission, never adapter I/O."""

from __future__ import annotations

import os
import threading
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from swarm.db.engine import create_db_engine, make_session_factory
from swarm.db.models import Base
from swarm.mission.action_boundary import local_worktree_gateway
from swarm.tools.effects import DurableEffectRepository, EffectConflictError, InMemoryEffectStore
from swarm.tools.fences import ActorContext, RevocableFenceProvider


@pytest.fixture(params=["memory", "postgres"])
def effect_store(request: pytest.FixtureRequest) -> Iterator[Any]:
    if request.param == "memory":
        yield InMemoryEffectStore()
        return
    url = os.environ.get("SWARM_DATABASE_URL")
    if not url:
        pytest.skip("owned PostgreSQL not supplied")
    engine = create_db_engine(url)
    Base.metadata.create_all(engine)
    try:
        yield DurableEffectRepository(make_session_factory(engine))
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.mark.parametrize("winner", ["admission", "cancellation"])
def test_local_cancel_and_admission_have_one_serialized_winner(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, effect_store: Any, winner: str
) -> None:
    fences = RevocableFenceProvider()
    gateway = local_worktree_gateway(tmp_path, store=effect_store, fences=fences)
    adapter = gateway.registry.resolve("local.sandbox", "1")
    context = ActorContext(actor="review", project_id="local_race")
    envelope = adapter.normalize(
        {
            "project_id": context.project_id,
            "actor": context.actor,
            "mission_id": "mission",
            "task_id": "task",
            "attempt_id": "attempt",
            "lease_generation": 1,
            "cancellation_generation": 0,
            "operation": "fs.write_text",
            "path": "effect.txt",
            "text": "accounted effect",
        }
    )
    # The real RepoWorker supplies a bounded task/sequence key after normalization.
    envelope.effect_key = "local_race:mission:task:effect1"
    envelope.idempotency_key = envelope.effect_key
    envelope.approval_id = gateway.make_approval(envelope, context=context).approval_id
    paused, release = threading.Event(), threading.Event()
    cancel_started, cancelled = threading.Event(), threading.Event()
    errors: list[BaseException] = []
    receipts: list[Any] = []
    observed_admission: list[tuple[str, int]] = []

    if winner == "admission":
        original_reader = fences.reader

        def reader(**identity: Any) -> Any:
            read = original_reader(**identity)

            def pause_after_snapshot(session: Any) -> Any:
                snapshot = read(session)
                assert snapshot["cancellation_generation"] == 0
                paused.set()
                assert release.wait(5)
                return snapshot

            return pause_after_snapshot

        monkeypatch.setattr(fences, "reader", reader)
        original_observe = adapter.observe_pre_state

        def observe_after_guard(envelope: Any) -> Any:
            # Cancellation must finish even while adapter observation is paused.
            assert cancelled.wait(5), "admission guard leaked into adapter I/O"
            row = effect_store.get(project_id=context.project_id, effect_key=envelope.effect_key)
            grant = effect_store.get_approval(envelope.approval_id, project_id=context.project_id)
            observed_admission.append((row["state"], grant.used_count))
            return original_observe(envelope)

        monkeypatch.setattr(adapter, "observe_pre_state", observe_after_guard)
    else:
        original_begin = effect_store.begin_execution

        def pause_before_admission(*args: Any, **kwargs: Any) -> Any:
            paused.set()
            assert release.wait(5)
            return original_begin(*args, **kwargs)

        monkeypatch.setattr(effect_store, "begin_execution", pause_before_admission)

    def execute() -> None:
        try:
            receipts.append(gateway.execute_envelope_sync(envelope, context=context))
        except BaseException as exc:
            errors.append(exc)

    def cancel() -> None:
        cancel_started.set()
        fences.cancel()
        cancelled.set()

    execution = threading.Thread(target=execute)
    cancellation = threading.Thread(target=cancel)
    execution.start()
    try:
        assert paused.wait(5)
        cancellation.start()
        assert cancel_started.wait(5)
        if winner == "admission":
            assert not cancelled.wait(0.1), "cancel returned before admission committed"
        else:
            assert cancelled.wait(5)
    finally:
        release.set()
        execution.join(10)
        if cancellation.ident is not None:
            cancellation.join(10)
    assert not execution.is_alive() and not cancellation.is_alive()
    grant = effect_store.get_approval(envelope.approval_id, project_id=context.project_id)
    stored_receipts = effect_store.list_receipts(
        project_id=context.project_id, effect_key=envelope.effect_key
    )
    if winner == "admission":
        assert errors == []
        assert len(receipts) == len(stored_receipts) == 1
        assert receipts[0].outcome == "succeeded"
        assert (tmp_path / "effect.txt").read_text() == "accounted effect"
        assert observed_admission and observed_admission[0] == ("executing", 1)
        assert grant.used_count == 1
    else:
        assert len(errors) == 1 and isinstance(errors[0], EffectConflictError)
        assert "fence_changed_before_execute" in str(errors[0])
        assert receipts == stored_receipts == []
        assert not (tmp_path / "effect.txt").exists()
        assert grant.used_count == 0
