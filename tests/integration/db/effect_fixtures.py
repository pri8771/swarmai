"""Real lease authority for synthetic consequential gateway integration tests."""

from swarm.contracts.actions import ActionEnvelope
from swarm.contracts.common import new_id
from swarm.db.lease_fencing import LeaseLifecycleService
from swarm.db.repositories import MissionRepository
from tests.integration.db.test_lease_claim_renew_expire import (
    _insert_ready_task,
    _register_worker,
    _unique_mission,
)


def bind_lease(factory, envelope: ActionEnvelope) -> ActionEnvelope:
    """Bind this fixture's unchanged project/payload to a real committed claim."""
    with factory() as session:
        mission = _unique_mission().model_copy(update={"project_id": envelope.project_id})
        MissionRepository(session).insert(mission)
        session.flush()
        task = _insert_ready_task(session, mission=mission, required_capabilities=["code.read"])
        token = new_id("test_token_")
        worker_id = _register_worker(
            session, project_id=mission.project_id, capabilities=["code.read"], token=token
        )
        claim = LeaseLifecycleService(session).claim_eligible_attempt(
            worker_id=worker_id, membership_token=token, lease_seconds=300
        )
        assert claim is not None and claim.task_id == task.id
        envelope.mission_id = mission.id
        envelope.task_id = task.id
        envelope.attempt_id = claim.attempt_id
        envelope.lease_generation = claim.worker_generation
        envelope.cancellation_generation = mission.cancellation_generation
        session.commit()
    return envelope
