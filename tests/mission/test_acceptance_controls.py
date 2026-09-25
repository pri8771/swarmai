"""G11 RUN-111 — acceptance controls (wrong-output reject / unsupported honesty)."""

from __future__ import annotations

import hashlib
import json
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
    # R1: review requires a published artifact binding before verdict.
    store.publish_mission_artifact(
        created.id,
        kind="result",
        content=b"triage notes",
        media_type="text/plain",
        owner_scope=created.project_id,
        actor="tester",
    )
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
    emails = ["a@example.com", "b@example.com"]
    payload = json.dumps({"emails": emails, "body": " ".join(emails)}).encode()
    digest = hashlib.sha256(payload).hexdigest()
    required = {
        "email_count": 2,
        "artifact_sha256": digest,
        "placement": "server_verified",
        "host_role": "protected_verifier",
        "runtime": "swarm_kernel",
    }
    created = await store.create_mission(
        mission,
        actor="tester",
        task_family="extract",
        required_checks=required,
    )
    store.publish_mission_artifact(
        created.id,
        kind="result",
        content=payload,
        media_type="application/json",
        owner_scope=created.project_id,
        expected_hash=digest,
        actor="tester",
    )
    # Worker-produced checks are ignored; server recomputes from artifact.
    accepted = await store.review_mission_attempt(
        created.id,
        actor="tester",
        produced={"checks": {"fields_extracted": True}},
        required_checks=required,
    )
    assert accepted["accepted"] is True
    assert accepted["acceptance_receipt_id"]
    loaded = store.get_mission(created.id)
    assert loaded.status == MissionStatus.COMPLETED
    assert loaded.acceptance_receipt_id == accepted["acceptance_receipt_id"]
