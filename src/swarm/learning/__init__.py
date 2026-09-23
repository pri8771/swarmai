"""V3.0 governed learning proposal state machine."""

from __future__ import annotations

from pydantic import Field

from swarm.contracts.common import StrictModel, new_id, utc_now

# Allowed transitions — software enforced.
TRANSITIONS: dict[str, set[str]] = {
    "proposed": {"validated", "rejected"},
    "validated": {"calibrating", "rejected"},
    "calibrating": {"frozen", "rejected"},
    "frozen": {"held_out_eval", "rejected"},
    "held_out_eval": {"review", "rejected", "contaminated"},
    "review": {"canary", "rejected"},
    "canary": {"accepted", "rolled_back", "rejected"},
    "accepted": {"drift_revalidation"},
    "drift_revalidation": {"accepted", "rolled_back", "contaminated"},
    "rolled_back": set(),
    "rejected": set(),
    "contaminated": set(),
}


class LearningProposal(StrictModel):
    proposal_id: str = Field(default_factory=lambda: new_id("lrn_"))
    project_id: str
    version: int = 1
    change_summary: str
    state: str = "proposed"
    sealed_holdout_ref: str | None = None
    calibration_ref: str | None = None
    review_ref: str | None = None
    canary_ref: str | None = None
    created_at: str = Field(default_factory=lambda: utc_now().isoformat())


class LearningError(RuntimeError):
    pass


class LearningRepository:
    def __init__(self) -> None:
        self._items: dict[str, LearningProposal] = {}
        self._history: list[tuple[str, str, str]] = []

    def create(self, proposal: LearningProposal) -> LearningProposal:
        # Held-out answers must never be stored as plaintext on the proposal.
        if proposal.sealed_holdout_ref and "answer=" in proposal.sealed_holdout_ref:
            raise LearningError("holdout_plaintext_forbidden")
        self._items[proposal.proposal_id] = proposal
        return proposal

    def get(self, proposal_id: str) -> LearningProposal:
        item = self._items.get(proposal_id)
        if item is None:
            raise LearningError("proposal_missing")
        return item

    def transition(self, proposal_id: str, new_state: str, *, note: str = "") -> LearningProposal:
        item = self.get(proposal_id)
        allowed = TRANSITIONS.get(item.state, set())
        if new_state not in allowed:
            raise LearningError(f"illegal_transition:{item.state}->{new_state}")
        # Independent review cannot be self-approved by missing review_ref.
        if new_state == "canary" and not item.review_ref:
            raise LearningError("independent_review_required")
        if new_state == "held_out_eval" and not item.sealed_holdout_ref:
            raise LearningError("sealed_holdout_required")
        prev = item.state
        item.state = new_state
        self._history.append((proposal_id, prev, new_state if not note else f"{new_state}:{note}"))
        return item

    def rollback(self, proposal_id: str) -> LearningProposal:
        item = self.get(proposal_id)
        if item.state not in {"canary", "accepted", "drift_revalidation"}:
            raise LearningError(f"rollback_illegal_from:{item.state}")
        return self.transition(proposal_id, "rolled_back")
