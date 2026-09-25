"""Stagnation and diminishing-returns detection."""

from __future__ import annotations

from swarm.pursuit.models import ContributionKind, CycleRecord


class StagnationReport:
    def __init__(
        self,
        *,
        stagnant: bool,
        reason: str | None = None,
        repeated_failures: int = 0,
        no_progress_streak: int = 0,
    ) -> None:
        self.stagnant = stagnant
        self.reason = reason
        self.repeated_failures = repeated_failures
        self.no_progress_streak = no_progress_streak


def detect_stagnation(
    history: list[CycleRecord],
    *,
    max_repeated_failures: int = 3,
    max_no_progress: int = 3,
) -> StagnationReport:
    """Detect repeated identical failures or diminishing returns."""
    if not history:
        return StagnationReport(stagnant=False)

    fail_keys: list[str] = []
    no_progress = 0
    for cycle in reversed(history):
        if cycle.outcome is None and cycle.decided_kind in {
            ContributionKind.WAIT,
            ContributionKind.REQUEST_HUMAN,
            ContributionKind.ASK,
        }:
            continue
        if cycle.outcome is not None and not cycle.outcome.success:
            title = cycle.proposal.title if cycle.proposal else ""
            key = f"{cycle.decided_kind}:{title}:{cycle.outcome.failure_class}"
            fail_keys.append(key)
            if cycle.verification and not cycle.verification.newly_met:
                no_progress += 1
            continue
        if cycle.verification is not None and not cycle.verification.newly_met:
            no_progress += 1
            if cycle.outcome is not None and cycle.outcome.success:
                # Success without criterion progress counts as diminishing return.
                continue
        break

    repeated = 0
    if fail_keys:
        first = fail_keys[0]
        for k in fail_keys:
            if k == first:
                repeated += 1
            else:
                break

    if repeated >= max_repeated_failures:
        return StagnationReport(
            stagnant=True,
            reason="repeated_identical_failures",
            repeated_failures=repeated,
            no_progress_streak=no_progress,
        )
    if no_progress >= max_no_progress:
        return StagnationReport(
            stagnant=True,
            reason="diminishing_returns",
            repeated_failures=repeated,
            no_progress_streak=no_progress,
        )
    return StagnationReport(
        stagnant=False,
        repeated_failures=repeated,
        no_progress_streak=no_progress,
    )
