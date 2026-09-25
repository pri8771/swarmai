"""Envelope clamping, anti-duplicate keys, and authority checks."""

from __future__ import annotations

import hashlib
import re
from typing import Any

from swarm.goals.models import Goal
from swarm.pursuit.models import ContributionKind, FrontierCandidate, MissionProposalDraft


class PursuitPolicyError(RuntimeError):
    pass


_WS = re.compile(r"\s+")


def normalize_title(title: str) -> str:
    return _WS.sub(" ", title.strip().lower())


def dedupe_key_for(*, goal_id: str, kind: ContributionKind, title: str, criteria: list[str]) -> str:
    crit = ",".join(sorted(c.strip().lower() for c in criteria))
    raw = f"{goal_id}|{kind.value}|{normalize_title(title)}|{crit}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def clamp_budget(requested: float, envelope: dict[str, Any]) -> float:
    """Never expand spend via generated text — clamp to envelope ceiling (default 0)."""
    ceiling = float(envelope.get("spend_usd_ceiling", envelope.get("max_spend_usd", 0.0)) or 0.0)
    if ceiling < 0:
        ceiling = 0.0
    req = max(0.0, float(requested))
    return min(req, ceiling)


def admitted_tools(requested: list[str], envelope: dict[str, Any]) -> list[str]:
    allowed = list(envelope.get("tools") or envelope.get("allowed_tools") or [])
    if not allowed:
        # Empty authority tools means no expansion beyond empty set.
        return []
    allow_set = set(allowed)
    return [t for t in requested if t in allow_set]


def admitted_providers(requested: list[str], envelope: dict[str, Any]) -> list[str]:
    allowed = list(envelope.get("providers") or envelope.get("allowed_providers") or [])
    if not allowed:
        return []
    allow_set = set(allowed)
    return [p for p in requested if p in allow_set]


def resources_insufficient(goal: Goal, candidate: FrontierCandidate) -> bool:
    ceiling = float(
        goal.resource_envelope.get(
            "spend_usd_ceiling", goal.resource_envelope.get("max_spend_usd", 0.0)
        )
        or 0.0
    )
    if candidate.estimated_cost_usd > ceiling:
        return True
    tools = admitted_tools(candidate.required_tools, goal.authority_envelope)
    if candidate.required_tools and set(candidate.required_tools) - set(tools):
        return True
    providers = admitted_providers(candidate.required_providers, goal.authority_envelope)
    if candidate.required_providers and set(candidate.required_providers) - set(providers):
        return True
    return False


def admit_proposal(goal: Goal, draft: MissionProposalDraft) -> MissionProposalDraft:
    """Validate proposal against human envelopes; reject expansions."""
    if draft.requested_budget_usd < 0:
        raise PursuitPolicyError("negative_budget")
    admitted_budget = clamp_budget(draft.requested_budget_usd, goal.resource_envelope)
    tools = admitted_tools(draft.requested_tools, goal.authority_envelope)
    providers = admitted_providers(draft.requested_providers, goal.authority_envelope)

    # Generated text asked for more than allowed → reject, do not silently expand.
    if draft.requested_budget_usd > admitted_budget + 1e-9:
        return draft.model_copy(
            update={
                "state": "rejected",
                "rejection_reason": "budget_exceeds_envelope",
                "admitted_budget_usd": admitted_budget,
                "admitted_tools": tools,
                "admitted_providers": providers,
            }
        )
    if draft.requested_tools and set(draft.requested_tools) - set(tools):
        return draft.model_copy(
            update={
                "state": "rejected",
                "rejection_reason": "tools_outside_authority",
                "admitted_budget_usd": admitted_budget,
                "admitted_tools": tools,
                "admitted_providers": providers,
            }
        )
    if draft.requested_providers and set(draft.requested_providers) - set(providers):
        return draft.model_copy(
            update={
                "state": "rejected",
                "rejection_reason": "providers_outside_authority",
                "admitted_budget_usd": admitted_budget,
                "admitted_tools": tools,
                "admitted_providers": providers,
            }
        )
    return draft.model_copy(
        update={
            "admitted_budget_usd": admitted_budget,
            "admitted_tools": tools,
            "admitted_providers": providers,
        }
    )
