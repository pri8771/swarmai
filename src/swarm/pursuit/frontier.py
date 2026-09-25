"""Justified frontier construction from gap assessment + lessons."""

from __future__ import annotations

from swarm.goals.models import Goal
from swarm.pursuit.models import (
    ContributionKind,
    FrontierCandidate,
    GapAssessment,
    PursuitLesson,
)
from swarm.pursuit.policy import resources_insufficient


def assess_gap(goal: Goal, *, satisfied: set[str]) -> GapAssessment:
    criteria = list(goal.verification_criteria)
    met = [c for c in criteria if c in satisfied]
    unmet = [c for c in criteria if c not in satisfied]
    progress = (len(met) / len(criteria)) if criteria else 1.0
    return GapAssessment(
        unmet_criteria=unmet,
        met_criteria=met,
        open_questions=list(goal.open_questions),
        blockers=list(goal.blockers),
        progress_ratio=progress,
    )


def build_frontier(
    goal: Goal,
    gap: GapAssessment,
    *,
    adopted_lessons: list[PursuitLesson] | None = None,
    failed_approaches: set[str] | None = None,
) -> list[FrontierCandidate]:
    """Build scored, justified candidates. Empty when waiting/asking is the only safe move."""
    adopted_lessons = adopted_lessons or []
    failed_approaches = failed_approaches or set()
    lesson_boost = {s for lesson in adopted_lessons for s in lesson.scope}

    candidates: list[FrontierCandidate] = []

    if gap.blockers:
        candidates.append(
            FrontierCandidate(
                kind=ContributionKind.REQUEST_HUMAN,
                title="Resolve blockers with operator",
                rationale=f"Blockers present: {', '.join(gap.blockers)}",
                addresses_criteria=list(gap.unmet_criteria[:1]),
                score=1.0,
            )
        )
        # Do not pursue ACT while human blockers remain.
        return _finalize(goal, candidates)

    if gap.resources_insufficient or gap.authority_insufficient:
        candidates.append(
            FrontierCandidate(
                kind=ContributionKind.WAIT,
                title="Wait for resources or authority",
                rationale="Envelope insufficient for remaining unmet criteria",
                addresses_criteria=list(gap.unmet_criteria),
                score=0.1,
            )
        )
        return _finalize(goal, candidates)

    if not gap.unmet_criteria:
        candidates.append(
            FrontierCandidate(
                kind=ContributionKind.WAIT,
                title="Goal criteria satisfied — await achievement transition",
                rationale="No unmet verification criteria remain",
                score=0.0,
            )
        )
        return _finalize(goal, candidates)

    for criterion in gap.unmet_criteria:
        approach = f"satisfy:{criterion}"
        if approach in failed_approaches:
            candidates.append(
                FrontierCandidate(
                    kind=ContributionKind.EXPERIMENT,
                    title=f"Try alternate approach for: {criterion}",
                    rationale="Prior approach failed; experiment rather than repeat",
                    addresses_criteria=[criterion],
                    commitment_key=approach,
                    score=0.55 + (0.15 if criterion in lesson_boost else 0.0),
                    estimated_cost_usd=0.0,
                    required_tools=_tools_hint(goal),
                    required_providers=_providers_hint(goal),
                )
            )
            candidates.append(
                FrontierCandidate(
                    kind=ContributionKind.ASK,
                    title=f"Ask clarifying question about: {criterion}",
                    rationale="Repeated failure — gather information before another act",
                    addresses_criteria=[criterion],
                    score=0.45,
                )
            )
        else:
            score = 0.7 + (0.2 if criterion in lesson_boost else 0.0)
            candidates.append(
                FrontierCandidate(
                    kind=ContributionKind.ACT,
                    title=f"Contribute toward: {criterion}",
                    rationale=f"Unmet criterion '{criterion}' remains; act within envelope",
                    addresses_criteria=[criterion],
                    commitment_key=approach,
                    score=score,
                    estimated_cost_usd=0.0,
                    required_tools=_tools_hint(goal),
                    required_providers=_providers_hint(goal),
                )
            )

    if gap.open_questions:
        candidates.append(
            FrontierCandidate(
                kind=ContributionKind.ASK,
                title="Clarify open questions",
                rationale=f"Open questions: {', '.join(gap.open_questions)}",
                addresses_criteria=list(gap.unmet_criteria[:1]),
                score=0.4,
            )
        )

    return _finalize(goal, candidates)


def choose_contribution(frontier: list[FrontierCandidate]) -> FrontierCandidate | None:
    runnable = [c for c in frontier if c.blocked_reason is None]
    if not runnable:
        return None
    return sorted(runnable, key=lambda c: (-c.score, c.kind.value, c.title))[0]


def _tools_hint(goal: Goal) -> list[str]:
    tools = list(
        goal.authority_envelope.get("tools") or goal.authority_envelope.get("allowed_tools") or []
    )
    return tools[:1]


def _providers_hint(goal: Goal) -> list[str]:
    providers = list(
        goal.authority_envelope.get("providers")
        or goal.authority_envelope.get("allowed_providers")
        or []
    )
    return providers[:1]


def _finalize(goal: Goal, candidates: list[FrontierCandidate]) -> list[FrontierCandidate]:
    out: list[FrontierCandidate] = []
    for c in candidates:
        if c.kind in {ContributionKind.ACT, ContributionKind.EXPERIMENT} and resources_insufficient(
            goal, c
        ):
            out.append(
                c.model_copy(
                    update={
                        "blocked_reason": "resources_or_authority_insufficient",
                        "score": min(c.score, 0.05),
                    }
                )
            )
        else:
            out.append(c)
    return sorted(out, key=lambda c: (-c.score, c.kind.value, c.title))
