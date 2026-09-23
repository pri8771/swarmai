"""V2B-003e / C5 — context-budget measurement helpers (honest when evidence thin)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from swarm.contracts.knowledge import KnowledgeItem, RetrievalActor, RetrievalQuery
from swarm.knowledge.repository import KnowledgeRepository
from swarm.knowledge.retrieval import PermissionFirstRetriever, estimate_tokens


@dataclass
class ContextBudgetReport:
    project_id: str
    mission_set_size: int
    selected_facts: int
    tokens_loaded: int
    tokens_whole_history: int
    tokens_avoided: int
    stale_or_irrelevant: int
    cross_project_leaks: int
    task_quality: str = "UNKNOWN_not_measured_this_harness"
    status: str = "pass_local_budget_math"
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "mission_set_size": self.mission_set_size,
            "selected_facts": self.selected_facts,
            "tokens_loaded": self.tokens_loaded,
            "tokens_whole_history": self.tokens_whole_history,
            "tokens_avoided": self.tokens_avoided,
            "stale_or_irrelevant": self.stale_or_irrelevant,
            "cross_project_leaks": self.cross_project_leaks,
            "task_quality": self.task_quality,
            "status": self.status,
            "notes": list(self.notes),
        }


def measure_context_budget(
    repo: KnowledgeRepository,
    *,
    project_id: str,
    actor_id: str = "budget_actor",
    permission_labels: list[str] | None = None,
    query_text: str = "",
    token_budget: int = 128,
    other_project_id: str | None = None,
) -> ContextBudgetReport:
    """Measure bounded retrieval vs whole-history token load for one project set."""
    labels = list(permission_labels or [])
    visible = repo.list_visible(project_id=project_id, permission_labels=labels, limit=1000)
    whole = sum(estimate_tokens(i.body) + estimate_tokens(i.topic) for i in visible)
    retriever = PermissionFirstRetriever(repo)
    bundle = retriever.retrieve(
        RetrievalQuery(
            actor=RetrievalActor(
                actor_id=actor_id,
                project_id=project_id,
                permission_labels=labels,
                scopes=[f"project:{project_id}"],
            ),
            query_text=query_text,
            token_budget=token_budget,
            max_items=8,
        )
    )
    receipt = bundle.receipt
    stale = int(receipt.omitted_reason_counts.get("stale_expired", 0)) + int(
        receipt.omitted_reason_counts.get("superseded", 0)
    )
    leaks = 0
    if other_project_id:
        foreign = retriever.retrieve(
            RetrievalQuery(
                actor=RetrievalActor(
                    actor_id=actor_id,
                    project_id=project_id,
                    permission_labels=labels,
                    scopes=[f"project:{project_id}"],
                ),
                query_text=query_text or "leakprobe",
                token_budget=token_budget,
            )
        )
        # Retrieving as project A must not return B item IDs.
        other_items = repo.list_visible(project_id=other_project_id, permission_labels=labels)
        # Existence leak check: retrieving as project A must not return B's item_ids.
        other_ids = {i.item_id for i in other_items}
        leaks = sum(1 for ref in foreign.receipt.selected if ref.item_id in other_ids)

    notes = []
    if whole <= receipt.tokens_used:
        notes.append("whole_history_not_larger_than_selected_or_empty_corpus")
    notes.append("task_quality_UNKNOWN_no_live_mission_eval_this_turn")

    return ContextBudgetReport(
        project_id=project_id,
        mission_set_size=len(visible),
        selected_facts=len(receipt.selected),
        tokens_loaded=receipt.tokens_used,
        tokens_whole_history=whole,
        tokens_avoided=receipt.tokens_avoided_estimate,
        stale_or_irrelevant=stale,
        cross_project_leaks=leaks,
        notes=notes,
    )


def seed_fixed_mission_knowledge(
    repo: KnowledgeRepository,
    *,
    project_id: str,
    permission_labels: list[str],
) -> list[KnowledgeItem]:
    """Small fixed set for budget measurements (not a live mission eval)."""
    bodies = [
        ("rate_limit", "API rate limit is 60 requests per minute"),
        ("auth", "Workers must use membership tokens hashed at rest"),
        ("noise1", "Unrelated chat history about lunch plans and weather"),
        ("noise2", "Long irrelevant transcript " + ("word " * 80)),
        ("procedure", "Drain workers before host maintenance windows"),
    ]
    items: list[KnowledgeItem] = []
    for topic, body in bodies:
        items.append(
            repo.create_item(
                KnowledgeItem.model_validate(
                    {
                        "project_id": project_id,
                        "class": "observation",
                        "topic": topic,
                        "body": body,
                        "producer_type": "system",
                        "permission_labels": permission_labels,
                        "retrieval_labels": [topic],
                    }
                )
            )
        )
    # Promote one fact via reviewer path for reuse.
    accepted = repo.accept_fact(
        project_id=project_id,
        item_id=items[0].item_id,
        version=items[0].version,
        reviewer_ref="budget_harness",
    )
    items.append(accepted)
    return items
