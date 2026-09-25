"""Layered memory: working context + cue index + source memory with provenance.

Permission filtering happens before ranking. Oversized tool output is truncated
with an explicit provenance note — never silently dropped as success.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Literal

from swarm.contracts.common import new_id, utc_now
from swarm.memory.store import MemoryRecord, MemoryStore

Layer = Literal["working", "cue", "source"]


@dataclass
class MemoryCue:
    cue_id: str
    project_id: str
    topic: str
    summary: str
    source_ref: str
    confidence: float
    tokens_estimate: int
    permission_labels: list[str] = field(default_factory=list)
    revision: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "cue_id": self.cue_id,
            "project_id": self.project_id,
            "topic": self.topic,
            "summary": self.summary,
            "source_ref": self.source_ref,
            "confidence": self.confidence,
            "tokens_estimate": self.tokens_estimate,
            "permission_labels": list(self.permission_labels),
            "revision": self.revision,
        }


@dataclass
class LayeredRetrievalReceipt:
    receipt_id: str
    project_id: str
    query: str
    actor_id: str
    token_budget: int
    tokens_used: int
    working_items: list[dict[str, Any]]
    cues: list[dict[str, Any]]
    sources: list[dict[str, Any]]
    omitted: dict[str, int]
    provenance_refs: list[str]
    truncated_tool_output: bool = False
    created_at: str = field(default_factory=lambda: utc_now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "receipt_id": self.receipt_id,
            "project_id": self.project_id,
            "query": self.query,
            "actor_id": self.actor_id,
            "token_budget": self.token_budget,
            "tokens_used": self.tokens_used,
            "working_items": list(self.working_items),
            "cues": list(self.cues),
            "sources": list(self.sources),
            "omitted": dict(self.omitted),
            "provenance_refs": list(self.provenance_refs),
            "truncated_tool_output": self.truncated_tool_output,
            "created_at": self.created_at,
        }


class LayeredMemoryAccessError(PermissionError):
    pass


class LayeredMemoryService:
    """Three-layer retrieval over MemoryStore with access + budget enforcement."""

    def __init__(
        self,
        store: MemoryStore,
        *,
        max_tool_output_tokens: int = 256,
    ) -> None:
        self.store = store
        self.max_tool_output_tokens = max_tool_output_tokens
        self._working: dict[str, list[MemoryRecord]] = {}  # mission_id -> facts
        self._cues: list[MemoryCue] = []
        self._receipts: list[LayeredRetrievalReceipt] = []

    def set_working_context(self, mission_id: str, records: list[MemoryRecord]) -> None:
        for rec in records:
            if not rec.provenance:
                raise ValueError("working_context_requires_provenance")
        self._working[mission_id] = list(records)

    def index_cue_from_record(
        self,
        record: MemoryRecord,
        *,
        permission_labels: list[str] | None = None,
    ) -> MemoryCue:
        summary = record.content[:160]
        cue = MemoryCue(
            cue_id=new_id("cue_"),
            project_id=record.project_id,
            topic=record.topic,
            summary=summary,
            source_ref=record.memory_id,
            confidence=record.confidence,
            tokens_estimate=max(1, min(40, record.tokens_estimate)),
            permission_labels=list(permission_labels or record.tags),
        )
        self._cues.append(cue)
        return cue

    def remember_source(self, record: MemoryRecord) -> MemoryRecord:
        if not record.provenance:
            raise ValueError("source_requires_provenance")
        self.store.append(record)
        self.index_cue_from_record(record)
        return record

    def truncate_tool_output(self, text: str, *, provenance: str) -> tuple[str, bool, str]:
        """Bound tool output; return (text, truncated, provenance_note)."""
        tokens = max(1, len(text.split()))
        if tokens <= self.max_tool_output_tokens:
            return text, False, provenance
        words = text.split()[: self.max_tool_output_tokens]
        clipped = " ".join(words)
        note = f"{provenance}|truncated_tool_output:{tokens}->{self.max_tool_output_tokens}"
        return clipped, True, note

    def retrieve(
        self,
        *,
        project_id: str,
        actor_id: str,
        query: str,
        token_budget: int,
        mission_id: str | None = None,
        actor_labels: list[str] | None = None,
        resolve_sources: bool = True,
    ) -> LayeredRetrievalReceipt:
        if token_budget <= 0:
            raise ValueError("token_budget_must_be_positive")
        labels = set(actor_labels or [])
        omitted = {
            "permission_denied": 0,
            "wrong_project": 0,
            "budget_truncated": 0,
            "source_unresolved": 0,
        }
        used = 0
        working_out: list[dict[str, Any]] = []
        cue_out: list[dict[str, Any]] = []
        source_out: list[dict[str, Any]] = []
        provenance_refs: list[str] = []
        truncated = False

        # Layer 1: indispensable working context for the mission.
        for rec in self._working.get(mission_id or "", []):
            if rec.project_id != project_id:
                omitted["wrong_project"] += 1
                continue
            cost = max(1, rec.tokens_estimate)
            if used + cost > token_budget and working_out:
                omitted["budget_truncated"] += 1
                continue
            working_out.append(rec.to_dict())
            used += cost
            provenance_refs.append(rec.provenance)

        # Layer 2: cue index (permission-first).
        q = query.lower()
        terms = {t for t in q.replace("/", " ").replace(".", " ").split() if len(t) > 2}
        scored_cues: list[tuple[float, MemoryCue]] = []
        for cue in self._cues:
            if cue.project_id != project_id:
                omitted["wrong_project"] += 1
                continue
            if cue.permission_labels and labels:
                if not labels.intersection(cue.permission_labels):
                    omitted["permission_denied"] += 1
                    continue
            blob = f"{cue.topic} {cue.summary}".lower()
            overlap = sum(1 for t in terms if t in blob)
            score = overlap + cue.confidence * 0.1
            if overlap or not terms:
                scored_cues.append((score, cue))
        scored_cues.sort(key=lambda x: x[0], reverse=True)

        selected_source_ids: list[str] = []
        for _score, cue in scored_cues:
            cost = max(1, cue.tokens_estimate)
            if used + cost > token_budget:
                omitted["budget_truncated"] += 1
                continue
            cue_out.append(cue.to_dict())
            used += cost
            provenance_refs.append(f"cue:{cue.cue_id}->{cue.source_ref}")
            selected_source_ids.append(cue.source_ref)

        # Layer 3: resolve sources when requested and budget remains.
        if resolve_sources:
            by_id = {r.memory_id: r for r in self.store.list_all()}
            for sid in selected_source_ids:
                rec = by_id.get(sid)
                if rec is None:
                    omitted["source_unresolved"] += 1
                    continue
                if rec.project_id != project_id:
                    omitted["wrong_project"] += 1
                    continue
                content = rec.content
                content, was_trunc, prov = self.truncate_tool_output(
                    content, provenance=rec.provenance
                )
                truncated = truncated or was_trunc
                cost = max(1, min(rec.tokens_estimate, len(content.split())))
                if used + cost > token_budget:
                    omitted["budget_truncated"] += 1
                    continue
                payload = rec.to_dict()
                payload["content"] = content
                payload["provenance"] = prov
                source_out.append(payload)
                used += cost
                provenance_refs.append(prov)

        # Deny empty unauthorized cross-project attempt when actor has no access.
        if not working_out and not cue_out and not source_out:
            # If all candidates were permission-denied, surface as access error.
            if omitted["permission_denied"] > 0 and omitted["wrong_project"] == 0:
                raise LayeredMemoryAccessError("unauthorized_source_memory_retrieval")

        receipt = LayeredRetrievalReceipt(
            receipt_id=new_id("mrr_"),
            project_id=project_id,
            query=query,
            actor_id=actor_id,
            token_budget=token_budget,
            tokens_used=used,
            working_items=working_out,
            cues=cue_out,
            sources=source_out,
            omitted=omitted,
            provenance_refs=provenance_refs,
            truncated_tool_output=truncated,
        )
        self._receipts.append(receipt)
        return receipt

    def receipt_digest(self, receipt: LayeredRetrievalReceipt) -> str:
        blob = (
            f"{receipt.receipt_id}:{receipt.project_id}:{receipt.tokens_used}:"
            f"{','.join(receipt.provenance_refs)}"
        )
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()
