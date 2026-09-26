"""SW-W0-S2: V2.3 shared contract shapes (offline)."""

from __future__ import annotations

from datetime import timedelta

import pytest
from pydantic import ValidationError

from swarm.contracts.common import utc_now
from swarm.contracts.v23 import (
    SCHEDULABLE_MISSION_STATES,
    TERMINAL_INTENT_STATES,
    TRUST_RANK,
    V23_POLICY_VERSION,
    DispatchIntent,
    DispatchIntentState,
    MissionQueueLifecycle,
    MissionQueueState,
    ProjectQueueState,
    ReasonCode,
    SchedulerDecision,
    SchedulingDecisionReceipt,
    TrustClass,
)


def test_project_state_defaults_and_validation() -> None:
    state = ProjectQueueState(project_id="proj_a")
    assert state.weight == 1.0
    assert state.credit == 0.0
    assert state.version == 0
    assert state.policy_version == V23_POLICY_VERSION
    with pytest.raises(ValidationError):
        ProjectQueueState(project_id="proj_a", weight=0)
    with pytest.raises(ValidationError):
        ProjectQueueState(project_id="proj_a", unknown_field=1)  # type: ignore[call-arg]


def test_mission_schedulable_states() -> None:
    assert MissionQueueLifecycle.QUEUED in SCHEDULABLE_MISSION_STATES
    assert MissionQueueLifecycle.PAUSED not in SCHEDULABLE_MISSION_STATES
    mission = MissionQueueState(mission_id="msn_1", project_id="proj_a")
    assert mission.lifecycle == MissionQueueLifecycle.QUEUED


def test_receipt_digest_ignores_id_and_timestamp() -> None:
    a = SchedulingDecisionReceipt(
        sequence=1,
        decision=SchedulerDecision.ADMIT,
        reason_code=ReasonCode.ADMITTED,
        project_id="proj_a",
        scores={"proj_a": 1.0},
    )
    b = a.model_copy(update={"receipt_id": "sdr_other", "created_at": utc_now()})
    assert a.digest() == b.digest()
    c = a.model_copy(update={"sequence": 2})
    assert a.digest() != c.digest()


def test_intent_terminal_states_and_trust_rank() -> None:
    intent = DispatchIntent(
        attempt_id="att_1",
        project_id="proj_a",
        mission_id="msn_1",
        task_id="tsk_1",
        expires_at=utc_now() + timedelta(seconds=30),
    )
    assert intent.state == DispatchIntentState.PREPARED
    assert DispatchIntentState.DISPATCHED not in TERMINAL_INTENT_STATES
    assert TRUST_RANK[TrustClass.OBSERVE_ONLY] < TRUST_RANK[TrustClass.INTEGRATION_WORKER]
    assert sorted(TRUST_RANK.values()) == [0, 1, 2, 3, 4]
