"""V2A-003X isolated DBOS reuse spike — lease/fencing mapping observations.

Not a production queue replacement. Uses a private SQLite system DB and never
writes Swarm production schema. Maps Swarm claim/renew/expire concepts onto
DBOS workflow/step/idempotency primitives and records where Swarm must keep
authority in SQLAlchemy/Postgres.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from dbos import DBOS, DBOSConfig, SetWorkflowID


def _sqlite_url(path: Path) -> str:
    return f"sqlite:///{path.resolve()}"


@dataclass
class FakeLeaseAuthority:
    """In-memory stand-in for Swarm durable authority stamps (not production)."""

    task_id: str
    mission_revision: int = 1
    source_revision: str = "msnrev:1"
    cancellation_generation: int = 0
    cancelled: bool = False
    claim_count: int = 0
    renew_count: int = 0
    events: list[str] = field(default_factory=list)

    def claimable(self) -> bool:
        return not self.cancelled

    def stamp(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "mission_revision": self.mission_revision,
            "source_revision": self.source_revision,
            "cancellation_generation": self.cancellation_generation,
        }


class DbosLeaseMappingHarness:
    """Minimal DBOS harness exercising enqueue/claim-like idempotency + restart."""

    def __init__(self, db_path: Path, *, application_version: str = "v2a-003x-1") -> None:
        self.db_path = db_path
        self.application_version = application_version
        self.authority = FakeLeaseAuthority(task_id="tsk_spike_1")
        self._launched = False
        self.claim_workflow: Any = None
        self.renew_workflow: Any = None

    def launch(self) -> None:
        if self._launched:
            return
        try:
            DBOS.destroy(destroy_registry=True)
        except Exception:  # noqa: BLE001
            pass
        config: DBOSConfig = {
            "name": "swarm_v2a003x_lease_spike",
            "system_database_url": _sqlite_url(self.db_path),
            "application_version": self.application_version,
        }
        DBOS(config=config)
        self._register()
        DBOS.launch()
        self._launched = True

    def _register(self) -> None:
        harness = self

        @DBOS.step()
        def durable_claim_step(worker_id: str) -> dict[str, Any]:
            # Maps to Swarm claim bind — authority check must happen in Swarm SQL;
            # this step only proves DBOS step idempotency for a claim attempt.
            if not harness.authority.claimable():
                harness.authority.events.append("claim_denied_cancelled")
                return {"ok": False, "reason": "cancelled", "stamp": harness.authority.stamp()}
            harness.authority.claim_count += 1
            harness.authority.events.append(f"claim:{worker_id}")
            return {
                "ok": True,
                "worker_id": worker_id,
                "claim_count": harness.authority.claim_count,
                "stamp": harness.authority.stamp(),
            }

        @DBOS.step()
        def durable_renew_step(lease_id: str, stamp: dict[str, Any]) -> dict[str, Any]:
            # DBOS cannot know Swarm source/cancel drift — caller must supply current
            # stamps; spike rejects when fake authority drifted after claim.
            current = harness.authority.stamp()
            if (
                stamp.get("source_revision") != current["source_revision"]
                or stamp.get("cancellation_generation") != current["cancellation_generation"]
                or stamp.get("mission_revision") != current["mission_revision"]
                or harness.authority.cancelled
            ):
                harness.authority.events.append("renew_denied_stale")
                return {"ok": False, "reason": "authority_stale", "stamp": current}
            harness.authority.renew_count += 1
            harness.authority.events.append(f"renew:{lease_id}")
            return {"ok": True, "renew_count": harness.authority.renew_count, "stamp": current}

        @DBOS.workflow()
        def claim_workflow(worker_id: str) -> dict[str, Any]:
            return durable_claim_step(worker_id)

        @DBOS.workflow()
        def renew_workflow(lease_id: str, stamp: dict[str, Any]) -> dict[str, Any]:
            return durable_renew_step(lease_id, stamp)

        self.claim_workflow = claim_workflow
        self.renew_workflow = renew_workflow

    def destroy(self) -> None:
        if self._launched:
            try:
                DBOS.destroy(destroy_registry=True)
            except Exception:  # noqa: BLE001
                pass
            self._launched = False


async def run_idempotent_claim_spike(db_path: Path) -> dict[str, Any]:
    """Same workflow ID must not double-apply claim side effects across restart."""
    harness = DbosLeaseMappingHarness(db_path)
    harness.launch()
    try:
        assert harness.claim_workflow is not None
        wf_id = "claim:tsk_spike_1:attempt_1"
        with SetWorkflowID(wf_id):
            first = harness.claim_workflow("wrk_a")
        claim_count_after_first = harness.authority.claim_count
        # Restart DBOS process against same system DB.
        harness.destroy()
        harness2 = DbosLeaseMappingHarness(db_path)
        # Restore in-memory authority would normally come from Swarm SQL; for this
        # spike we re-seed to show DBOS alone does not persist Swarm authority.
        harness2.authority = FakeLeaseAuthority(task_id="tsk_spike_1")
        harness2.launch()
        try:
            assert harness2.claim_workflow is not None
            with SetWorkflowID(wf_id):
                second = harness2.claim_workflow("wrk_a")
            return {
                "first": first,
                "second": second,
                "claim_count_process_1": claim_count_after_first,
                "claim_count_process_2": harness2.authority.claim_count,
                "dbos_version": _dbos_version(),
                "note": (
                    "SetWorkflowID dedupes workflow execution in DBOS system DB; "
                    "Swarm authority stamps are NOT durable in DBOS and must stay in Postgres."
                ),
            }
        finally:
            harness2.destroy()
    finally:
        harness.destroy()


async def run_stale_renew_fence_spike(db_path: Path) -> dict[str, Any]:
    """Renew must fail when fake source/cancel stamps drift — Swarm-owned fence."""
    harness = DbosLeaseMappingHarness(db_path)
    harness.launch()
    try:
        assert harness.claim_workflow is not None and harness.renew_workflow is not None
        claim = harness.claim_workflow("wrk_b")
        stamp = dict(claim["stamp"])
        harness.authority.source_revision = "msnrev:drifted"
        renew = harness.renew_workflow("lease_1", stamp)
        return {
            "claim": claim,
            "renew": renew,
            "events": list(harness.authority.events),
            "dbos_version": _dbos_version(),
        }
    finally:
        harness.destroy()


def _dbos_version() -> str:
    try:
        from importlib.metadata import version

        return version("dbos")
    except Exception:  # noqa: BLE001
        return "unknown"


def mapping_observations() -> dict[str, Any]:
    """Static mapping used by ADR / evidence — not acceptance of production reuse."""
    return {
        "installed_dbos": _dbos_version(),
        "swarm_claim": "FOR UPDATE SKIP LOCKED + authority bind in Postgres",
        "dbos_analogue": "SetWorkflowID + @DBOS.step for idempotent workflow start",
        "swarm_renew_expire_fences": (
            "mission/task/attempt source/cancel/revision/project checks in LeaseLifecycleService"
        ),
        "dbos_gap": (
            "DBOS does not model Swarm cancellation_generation, source_revision, "
            "project isolation, or lease renewable_until; those remain Swarm SQL."
        ),
        "recommendation": "partial_reuse",
        "recommendation_detail": (
            "Reuse DBOS for durable workflow/step restart of worker-side execution "
            "only after V15 lease fencing is lead-verified; do not replace Swarm "
            "claim/renew/expire authority store with DBOS queues."
        ),
    }
