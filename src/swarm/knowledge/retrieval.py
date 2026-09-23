"""V2B-003b / ART-V16 — permission-first knowledge retrieval.

Mandatory order:
1. resolve actor/project authorization
2. filter permitted item IDs/versions
3. remove deleted/stale/superseded per query mode
4. rank ONLY the permitted candidate set
5. assemble bounded context
6. emit retrieval receipt

Never rank a cross-project global corpus then filter afterward.
"""

from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any

from swarm.contracts.common import payload_hash, utc_now
from swarm.contracts.knowledge import (
    KnowledgeContextBundle,
    KnowledgeItem,
    RetrievalQuery,
    RetrievalReceipt,
    SelectedKnowledgeRef,
)
from swarm.knowledge.repository import KnowledgeRepository, KnowledgeScopeError


def estimate_tokens(text: str) -> int:
    return max(1, len(text.split()))


class PermissionFirstRetriever:
    """Project-scoped retriever; ranking never sees unauthorized rows."""

    def __init__(
        self,
        repo: KnowledgeRepository,
        *,
        invalidation_log: list[dict[str, Any]] | None = None,
    ) -> None:
        self.repo = repo
        self.invalidation_log = invalidation_log if invalidation_log is not None else []

    def retrieve(
        self, query: RetrievalQuery, *, now: datetime | None = None
    ) -> KnowledgeContextBundle:
        clock = now or utc_now()
        omitted: dict[str, int] = {
            "wrong_project": 0,
            "permission_denied": 0,
            "deleted": 0,
            "superseded": 0,
            "stale_expired": 0,
            "invalidated_summary": 0,
            "budget_truncated": 0,
            "ranked_out": 0,
        }

        # 1) Resolve actor/project authorization
        self._authorize_actor(query)

        # 2+3) Filter permitted IDs/versions then lifecycle (project-first SQL)
        candidates = self._permitted_candidates(query, omitted=omitted, now=clock)

        # Conflict sets among permitted candidates only
        conflict_sets = self._conflict_sets(query.actor.project_id, candidates)

        # 4) Rank ONLY permitted candidates
        ranked = self._rank(candidates, query)

        # 5) Assemble bounded context within token budget
        selected_items: list[KnowledgeItem] = []
        selected_refs: list[SelectedKnowledgeRef] = []
        tokens_used = 0
        for score, item, why in ranked:
            tokens = estimate_tokens(item.body) + estimate_tokens(item.topic)
            if len(selected_items) >= query.max_items:
                omitted["ranked_out"] += 1
                continue
            if tokens_used + tokens > query.token_budget and selected_items:
                omitted["budget_truncated"] += 1
                continue
            if tokens_used + tokens > query.token_budget and not selected_items:
                # Always allow at least one truncated item if budget tiny.
                if tokens > query.token_budget:
                    omitted["budget_truncated"] += 1
                    continue
            selected_items.append(item)
            tokens_used += tokens
            selected_refs.append(
                SelectedKnowledgeRef.model_validate(
                    {
                        "item_id": item.item_id,
                        "version": item.version,
                        "class": item.class_,
                        "topic": item.topic,
                        "acceptance_state": item.acceptance_state,
                        "provenance_refs": list(item.provenance_refs),
                        "content_digest": item.content_digest or item.ensure_content_digest(),
                        "tokens_estimate": tokens,
                        "rank_score": score,
                        "why_selected": why,
                    }
                )
            )

        # Whole-history avoidance estimate: sum of non-selected candidate tokens.
        all_tokens = sum(estimate_tokens(i.body) + estimate_tokens(i.topic) for i in candidates)
        tokens_avoided = max(0, all_tokens - tokens_used)

        context_text = "\n\n".join(
            f"[{item.class_} v{item.version} {item.item_id}] {item.topic}: {item.body}"
            for item in selected_items
        )

        # 6) Emit retrieval receipt
        receipt = RetrievalReceipt(
            project_id=query.actor.project_id,
            actor_id=query.actor.actor_id,
            actor_scope_digest=self._scope_digest(query),
            query_digest=self._query_digest(query),
            selected=selected_refs,
            conflict_sets=conflict_sets,
            omitted_reason_counts=omitted,
            token_budget=query.token_budget,
            tokens_used=tokens_used,
            tokens_avoided_estimate=tokens_avoided,
            retrieval_policy_version=query.policy_version,
            created_at=clock,
            context_text=context_text,
        )
        return KnowledgeContextBundle(receipt=receipt, items=selected_items)

    def _authorize_actor(self, query: RetrievalQuery) -> None:
        actor = query.actor
        if not actor.actor_id or not actor.project_id:
            raise KnowledgeScopeError("actor_or_project_missing")
        project_scope = f"project:{actor.project_id}"
        if actor.scopes and project_scope not in actor.scopes and (
            actor.project_id not in actor.scopes
        ):
            raise KnowledgeScopeError("actor_project_scope_mismatch")

    def _permitted_candidates(
        self,
        query: RetrievalQuery,
        *,
        omitted: dict[str, int],
        now: datetime,
    ) -> list[KnowledgeItem]:
        include_superseded = query.mode in {"include_superseded", "audit_all_versions"}
        # Project filter is inside list_visible — never scan other projects.
        rows = self.repo.list_visible(
            project_id=query.actor.project_id,
            permission_labels=list(query.actor.permission_labels),
            classes=list(query.classes) if query.classes else None,
            include_superseded=include_superseded,
            limit=500,
        )
        invalidated = {
            (e.get("item_id"), e.get("version"))
            for e in self.invalidation_log
            if e.get("project_id") == query.actor.project_id
            and e.get("kind") in {"summary_invalidated", "cache_invalidate", "export_invalidate"}
        }
        out: list[KnowledgeItem] = []
        for item in rows:
            if item.project_id != query.actor.project_id:
                omitted["wrong_project"] += 1
                continue
            if item.acceptance_state == "deleted":
                omitted["deleted"] += 1
                continue
            if item.acceptance_state == "superseded" and not include_superseded:
                omitted["superseded"] += 1
                continue
            if item.expires_at is not None and item.expires_at <= now:
                omitted["stale_expired"] += 1
                continue
            if (item.item_id, item.version) in invalidated and item.class_ == "summary":
                omitted["invalidated_summary"] += 1
                continue
            if query.topics and item.topic not in query.topics:
                # Topic filter after permission — still on permitted set only.
                continue
            if query.retrieval_labels:
                labels = set(item.retrieval_labels)
                if labels and labels.isdisjoint(set(query.retrieval_labels)):
                    continue
            out.append(item)
        return out

    def _rank(
        self, candidates: list[KnowledgeItem], query: RetrievalQuery
    ) -> list[tuple[float, KnowledgeItem, str]]:
        """Lexical rank over the already-permitted candidate set only."""
        q = query.query_text.lower().strip()
        topic_boost = set(query.topics)
        scored: list[tuple[float, KnowledgeItem, str]] = []
        for item in candidates:
            score = 0.0
            why_parts: list[str] = []
            if item.acceptance_state == "accepted":
                score += 5.0
                why_parts.append("accepted")
            if item.class_ == "accepted_fact":
                score += 3.0
                why_parts.append("accepted_fact")
            if item.class_ == "procedure":
                score += 2.0
            if item.topic in topic_boost:
                score += 4.0
                why_parts.append("topic_match")
            if q:
                body_l = item.body.lower()
                topic_l = item.topic.lower()
                if q in topic_l:
                    score += 6.0
                    why_parts.append("query_in_topic")
                elif q in body_l:
                    score += 3.0
                    why_parts.append("query_in_body")
                else:
                    # Token overlap
                    q_tokens = set(q.split())
                    overlap = q_tokens.intersection(body_l.split()) | q_tokens.intersection(
                        topic_l.split()
                    )
                    score += 0.5 * len(overlap)
                    if overlap:
                        why_parts.append("token_overlap")
            if item.confidence is not None:
                score += float(item.confidence)
            scored.append((score, item, ",".join(why_parts) or "permitted_candidate"))
        scored.sort(key=lambda t: (-t[0], t[1].created_at, t[1].item_id))
        return scored

    def _conflict_sets(self, project_id: str, candidates: list[KnowledgeItem]) -> list[list[str]]:
        ids = {i.item_id for i in candidates}
        links = self.repo.list_links(project_id=project_id, relation="contradicts")
        sets: list[list[str]] = []
        seen: set[frozenset[str]] = set()
        for link in links:
            pair = frozenset({link.from_item_id, link.to_item_id})
            if pair <= ids and pair not in seen and len(pair) == 2:
                seen.add(pair)
                sets.append(sorted(pair))
        return sets

    @staticmethod
    def _scope_digest(query: RetrievalQuery) -> str:
        return payload_hash(
            {
                "actor_id": query.actor.actor_id,
                "project_id": query.actor.project_id,
                "permission_labels": sorted(query.actor.permission_labels),
                "scopes": sorted(query.actor.scopes),
            }
        )

    @staticmethod
    def _query_digest(query: RetrievalQuery) -> str:
        # Avoid persisting raw sensitive query when policy prefers digest-only.
        raw = f"{query.query_text}|{','.join(query.topics)}|{','.join(query.classes)}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()
