"""Layered memory + lesson provenance (PC-07 / L4)."""

from __future__ import annotations

from pathlib import Path

import pytest

from swarm.memory.layered import LayeredMemoryAccessError, LayeredMemoryService
from swarm.memory.lesson_provenance import LessonProvenanceLedger
from swarm.memory.store import MemoryRecord, MemoryStore
from swarm.pursuit.models import PursuitLesson


def test_layered_retrieval_provenance_and_truncation(tmp_path: Path) -> None:
    store = MemoryStore(tmp_path / "mem")
    svc = LayeredMemoryService(store, max_tool_output_tokens=8)
    working = MemoryRecord(
        memory_id="w1",
        project_id="proj_a",
        mission_id="msn_1",
        kind="durable_fact",
        topic="constraint",
        content="do not expand budget",
        provenance="mission:msn_1:constraint",
        tokens_estimate=4,
        confidence=1.0,
        tags=["mission"],
    )
    svc.set_working_context("msn_1", [working])
    big = "word " * 40
    clipped, truncated, prov = svc.truncate_tool_output(big, provenance="tool:out")
    assert truncated is True
    assert "truncated_tool_output" in prov
    assert len(clipped.split()) == 8

    source = MemoryRecord(
        memory_id="s1",
        project_id="proj_a",
        mission_id="msn_1",
        kind="outcome",
        topic="email_count",
        content="extracted two emails from mac_local fixture",
        provenance="artifact:art_1",
        tokens_estimate=10,
        confidence=0.9,
        tags=["mac_local", "extract"],
    )
    svc.remember_source(source)

    receipt = svc.retrieve(
        project_id="proj_a",
        actor_id="agent_y",
        query="email extract mac_local",
        token_budget=40,
        mission_id="msn_1",
        actor_labels=["mac_local"],
    )
    assert receipt.working_items
    assert receipt.cues
    assert receipt.sources
    assert receipt.provenance_refs
    assert receipt.tokens_used <= 40


def test_unauthorized_source_denied(tmp_path: Path) -> None:
    store = MemoryStore(tmp_path / "mem")
    svc = LayeredMemoryService(store)
    svc.remember_source(
        MemoryRecord(
            memory_id="s2",
            project_id="proj_a",
            mission_id=None,
            kind="durable_fact",
            topic="secret",
            content="classified detail",
            provenance="src:secret",
            tokens_estimate=5,
            confidence=1.0,
            tags=["private"],
        )
    )
    with pytest.raises(LayeredMemoryAccessError, match="unauthorized"):
        svc.retrieve(
            project_id="proj_a",
            actor_id="outsider",
            query="secret",
            token_budget=20,
            actor_labels=["public_only"],
        )


def test_lesson_provenance_survives_restart(tmp_path: Path) -> None:
    ledger = LessonProvenanceLedger(root=tmp_path / "prov")
    lesson = PursuitLesson(
        goal_id="goal_1",
        summary="prefer multi-pass extract",
        scope=["contacts_extracted"],
        evidence_refs=["art_1", "evt_2"],
        strategy_delta="prefer:multi-pass",
    )
    stored, ev = ledger.propose_with_provenance(lesson, actor_id="agent_x", artifact_refs=["art_1"])
    assert ev.kind == "proposed"
    # Evaluate via underlying store then adopt with provenance.
    ledger.lessons.evaluate(
        stored.lesson_id, holdout_check_id="seal:holdout/v1#digest", holdout_passed=True
    )
    adopted, aev = ledger.adopt_with_provenance(
        stored.lesson_id, current_strategy="base", actor_id="operator"
    )
    assert adopted.state.value == "adopted"
    assert aev.kind == "adopted"
    rolled, rev = ledger.rollback_with_provenance(stored.lesson_id, actor_id="operator")
    assert rolled.state.value == "rolled_back"
    assert rev.kind == "rolled_back"

    ledger2 = LessonProvenanceLedger(root=tmp_path / "prov")
    hist = ledger2.history_for(stored.lesson_id)
    assert [e.kind for e in hist] == ["proposed", "adopted", "rolled_back"]
