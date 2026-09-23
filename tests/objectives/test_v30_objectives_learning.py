"""V3.0 objectives + governed learning tests."""

from __future__ import annotations

import pytest

from swarm.learning import LearningError, LearningProposal, LearningRepository
from swarm.objectives import ObjectiveContract, ObjectiveError, ObjectiveRepository


def test_objective_trigger_dedupe_and_admission() -> None:
    repo = ObjectiveRepository()
    obj = repo.create(
        ObjectiveContract(
            project_id="proj",
            goal="keep parser green",
            allowed_mission_templates=["parser_health"],
            spend_usd_ceiling=0.0,
            rate_limit_per_hour=10,
            max_active_missions=1,
        )
    )
    p1 = repo.trigger(obj.objective_id, dedupe_key="slot-1", trigger_kind="schedule")
    assert p1.state == "proposed"
    dup = repo.trigger(obj.objective_id, dedupe_key="slot-1", trigger_kind="schedule")
    assert dup.state == "duplicate"
    admitted = repo.admit_to_mission(p1.proposal_id)
    assert admitted.state == "admitted"
    assert admitted.mission_id
    with pytest.raises(ObjectiveError, match="max_active"):
        repo.trigger(obj.objective_id, dedupe_key="slot-2", trigger_kind="manual")


def test_objective_rejects_paid_ceiling_under_zero_spend() -> None:
    repo = ObjectiveRepository()
    with pytest.raises(ObjectiveError, match="paid_spend"):
        repo.create(
            ObjectiveContract(project_id="p", goal="x", spend_usd_ceiling=1.0)
        )


def test_learning_state_machine_and_holdout_rules() -> None:
    repo = LearningRepository()
    with pytest.raises(LearningError, match="holdout_plaintext"):
        repo.create(
            LearningProposal(
                project_id="p",
                change_summary="tweak",
                sealed_holdout_ref="answer=42",
            )
        )
    prop = repo.create(
        LearningProposal(
            project_id="p",
            change_summary="prompt tweak",
            sealed_holdout_ref="seal:holdout/v1#digest",
        )
    )
    repo.transition(prop.proposal_id, "validated")
    repo.transition(prop.proposal_id, "calibrating")
    repo.transition(prop.proposal_id, "frozen")
    repo.transition(prop.proposal_id, "held_out_eval")
    repo.transition(prop.proposal_id, "review")
    with pytest.raises(LearningError, match="independent_review"):
        repo.transition(prop.proposal_id, "canary")
    prop.review_ref = "review:independent/1"
    repo.transition(prop.proposal_id, "canary")
    rolled = repo.rollback(prop.proposal_id)
    assert rolled.state == "rolled_back"
