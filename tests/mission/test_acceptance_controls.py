"""G11 RUN-111 — acceptance controls (wrong-output reject / unsupported honesty)."""

from __future__ import annotations

from pathlib import Path

import pytest

from swarm.api.store import ProductStore
from swarm.contracts.enums import MissionStatus
from swarm.contracts.fixtures import sample_mission
from swarm.mission.acceptance import classify_task_support, review_attempt


def test_classify_supported_and_unsupported() -> None:
    ok = classify_task_support("triage")
    assert ok.supported is True
    bad = classify_task_support("teleportation")
    assert bad.supported is False
    assert "unsupported_task_family" in bad.reason


def test_review_rejects_wrong_output() -> None:
    decision = review_attempt(
        produced={"intentionally_wrong": True, "checks": {"tests_pass": True}},
        required_checks={"tests_pass": True},
    )
    assert decision.accepted is False
    assert "wrong_result_rejected" in decision.reasons


def test_review_rejects_mismatched_checks() -> None:
    decision = review_attempt(
        produced={"checks": {"tests_pass": False, "lint_clean": True}},
        required_checks={"tests_pass": True, "lint_clean": True},
    )
    assert decision.accepted is False
    assert any(r.startswith("check_failed:") for r in decision.reasons)


def test_review_accepts_only_when_checks_match() -> None:
    decision = review_attempt(
        produced={"checks": {"tests_pass": True, "lint_clean": True}},
        required_checks={"tests_pass": True, "lint_clean": True},
    )
    assert decision.accepted is True


def test_hidden_acceptance_rejects_plausible_wrong_output() -> None:
    """LEAD-012: nonempty/keyword-looking output must fail without hidden facts."""
    decision = review_attempt(
        produced={
            "checks": {
                "inference_ok": True,
                "nonempty_output": True,
                "no_known_answer_path": True,
            },
            "output_excerpt": "Here is a plausible generic JSON: {\"note\": \"nothing useful\"}",
        },
        required_checks={
            "inference_ok": True,
            "nonempty_output": True,
            "no_known_answer_path": True,
        },
        hidden_acceptance={
            "must_contain_all": ["Acme Nordics", "SEK"],
            "must_contain_any": ["450", "1200"],
            "min_output_chars": 40,
            "forbid_substrings": ["KNOWN_ANSWER_LEAK"],
        },
    )
    assert decision.accepted is False
    assert any(r.startswith("hidden_failed:") for r in decision.reasons)


def test_hidden_acceptance_passes_when_output_contains_required_facts() -> None:
    decision = review_attempt(
        produced={
            "checks": {"inference_ok": True, "nonempty_output": True},
            "output_excerpt": (
                '{"vendor":"Acme Nordics AB","currency":"SEK","line_totals":[450,1200]}'
            ),
        },
        required_checks={"inference_ok": True, "nonempty_output": True},
        hidden_acceptance={
            "must_contain_all": ["Acme Nordics", "SEK"],
            "must_contain_any": ["450", "1200"],
            "required_json_keys": ["vendor", "currency"],
            "min_output_chars": 20,
        },
    )
    assert decision.accepted is True
    assert decision.checks.get("hidden:must_contain_all") is True


def test_worker_never_needs_hidden_keys_in_produced_checks() -> None:
    """Hidden rules grade output_excerpt only — worker checks stay structural."""
    decision = review_attempt(
        produced={
            "checks": {"inference_ok": True},
            "output_excerpt": "Acme Nordics paid 450 SEK",
        },
        required_checks={"inference_ok": True},
        hidden_acceptance={"must_contain_all": ["Acme Nordics", "SEK", "450"]},
    )
    assert decision.accepted is True
    assert "Acme Nordics" not in str(decision.checks)  # facts not echoed as check ids


@pytest.mark.asyncio
async def test_unsupported_family_persists_failed_honest(tmp_path: Path) -> None:
    store = ProductStore(repo_root=tmp_path)
    mission = sample_mission().model_copy(
        update={"objective": "attempt unsupported teleportation workflow"}
    )
    created = await store.create_mission(
        mission, actor="tester", task_family="teleportation"
    )
    assert created.status == MissionStatus.FAILED
    record = store.mission_store().load(created.id)
    assert record.result.get("unsupported") is True
    assert record.plan.get("support", {}).get("supported") is False


@pytest.mark.asyncio
async def test_wrong_output_review_rejects_and_blocks_receipt(tmp_path: Path) -> None:
    store = ProductStore(repo_root=tmp_path)
    mission = sample_mission().model_copy(
        update={"objective": "triage unfamiliar queue drain race"}
    )
    created = await store.create_mission(
        mission,
        actor="tester",
        task_family="triage",
        required_checks={"root_cause_identified": True},
    )
    assert created.status != MissionStatus.FAILED
    rejected = await store.review_mission_attempt(
        created.id,
        actor="tester",
        produced={"intentionally_wrong": True, "checks": {"root_cause_identified": True}},
        required_checks={"root_cause_identified": True},
    )
    assert rejected["accepted"] is False
    assert rejected["acceptance_receipt_id"] is None
    assert store.get_mission(created.id).status == MissionStatus.FAILED
    assert store.get_mission(created.id).acceptance_receipt_id is None


@pytest.mark.asyncio
async def test_correct_review_sets_acceptance_receipt(tmp_path: Path) -> None:
    store = ProductStore(repo_root=tmp_path)
    mission = sample_mission().model_copy(
        update={"objective": "extract unfamiliar receipt line items"}
    )
    created = await store.create_mission(
        mission,
        actor="tester",
        task_family="extract",
        required_checks={"fields_extracted": True},
    )
    accepted = await store.review_mission_attempt(
        created.id,
        actor="tester",
        produced={"checks": {"fields_extracted": True}},
        required_checks={"fields_extracted": True},
    )
    assert accepted["accepted"] is True
    assert accepted["acceptance_receipt_id"]
    loaded = store.get_mission(created.id)
    assert loaded.status == MissionStatus.COMPLETED
    assert loaded.acceptance_receipt_id == accepted["acceptance_receipt_id"]
