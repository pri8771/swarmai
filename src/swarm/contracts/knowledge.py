"""ART-V16 / V2B-003a knowledge domain contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import ConfigDict, Field

from swarm.contracts.common import StrictModel, new_id, payload_hash, utc_now

KnowledgeClass = Literal[
    "source",
    "observation",
    "hypothesis",
    "accepted_fact",
    "procedure",
    "summary",
]

AcceptanceState = Literal[
    "unreviewed",
    "accepted",
    "disputed",
    "superseded",
    "deleted",
]

KnowledgeRelation = Literal[
    "derived_from",
    "supports",
    "contradicts",
    "supersedes",
    "summarizes",
]

_MODEL_SAFE_CLASSES = frozenset({"observation", "hypothesis", "summary", "source"})


class KnowledgeItem(StrictModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, populate_by_name=True)

    schema_version: str = "1.0"
    item_id: str = Field(default_factory=lambda: new_id("kni_"))
    version: int = 1
    project_id: str
    mission_id: str | None = None
    class_: KnowledgeClass = Field(alias="class")
    topic: str
    body: str
    provenance_refs: list[str] = Field(default_factory=list)
    source_digests: list[str] = Field(default_factory=list)
    producer_type: str = "system"
    producer_ref: str | None = None
    acceptance_state: AcceptanceState = "unreviewed"
    confidence: float | None = None
    created_at: datetime = Field(default_factory=utc_now)
    observed_at: datetime | None = None
    expires_at: datetime | None = None
    supersedes: list[str] = Field(default_factory=list)
    permission_labels: list[str] = Field(default_factory=list)
    retrieval_labels: list[str] = Field(default_factory=list)
    content_digest: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)

    def ensure_content_digest(self) -> str:
        if self.content_digest:
            return self.content_digest
        digest = payload_hash(
            {
                "item_id": self.item_id,
                "version": self.version,
                "project_id": self.project_id,
                "class": self.class_,
                "topic": self.topic,
                "body": self.body,
            }
        )
        object.__setattr__(self, "content_digest", digest)
        return digest


class KnowledgeLink(StrictModel):
    schema_version: str = "1.0"
    link_id: str = Field(default_factory=lambda: new_id("knl_"))
    project_id: str
    from_item_id: str
    from_version: int
    relation: KnowledgeRelation
    to_item_id: str
    to_version: int
    evidence_ref: str | None = None
    created_at: datetime = Field(default_factory=utc_now)


class KnowledgeTombstone(StrictModel):
    schema_version: str = "1.0"
    tombstone_id: str = Field(default_factory=lambda: new_id("knt_"))
    item_id: str
    project_id: str
    deleted_version: int
    deleted_at: datetime = Field(default_factory=utc_now)
    reason_class: str
    replacement_item_id: str | None = None
    replacement_version: int | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


def assert_model_output_class(knowledge_class: str, *, producer_type: str) -> None:
    """Model producers cannot emit accepted_fact (ART-V16 write rule)."""
    if producer_type in {"model", "llm", "worker_model"} and knowledge_class == "accepted_fact":
        raise ValueError("model_output_cannot_be_accepted_fact")
    if (
        producer_type in {"model", "llm", "worker_model"}
        and knowledge_class not in _MODEL_SAFE_CLASSES
    ):
        raise ValueError(f"model_output_class_forbidden:{knowledge_class}")


QueryMode = Literal["default", "include_superseded", "audit_all_versions"]


class RetrievalActor(StrictModel):
    """Caller identity for permission-first retrieval (V2B-003b)."""

    actor_id: str
    project_id: str
    permission_labels: list[str] = Field(default_factory=list)
    scopes: list[str] = Field(default_factory=list)


class RetrievalQuery(StrictModel):
    schema_version: str = "1.0"
    actor: RetrievalActor
    query_text: str = ""
    topics: list[str] = Field(default_factory=list)
    retrieval_labels: list[str] = Field(default_factory=list)
    classes: list[str] = Field(default_factory=list)
    mode: QueryMode = "default"
    token_budget: int = 512
    max_items: int = 16
    policy_version: str = "v16-retrieval-1"


class SelectedKnowledgeRef(StrictModel):
    item_id: str
    version: int
    class_: KnowledgeClass = Field(alias="class")
    topic: str
    acceptance_state: AcceptanceState
    provenance_refs: list[str] = Field(default_factory=list)
    content_digest: str
    tokens_estimate: int
    rank_score: float = 0.0
    why_selected: str = ""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, populate_by_name=True)


class RetrievalReceipt(StrictModel):
    """Versioned receipt for observability / ART-V16 retrieval contract."""

    schema_version: str = "1.0"
    receipt_id: str = Field(default_factory=lambda: new_id("krr_"))
    project_id: str
    actor_id: str
    actor_scope_digest: str
    query_digest: str
    selected: list[SelectedKnowledgeRef] = Field(default_factory=list)
    conflict_sets: list[list[str]] = Field(default_factory=list)
    omitted_reason_counts: dict[str, int] = Field(default_factory=dict)
    token_budget: int
    tokens_used: int
    tokens_avoided_estimate: int = 0
    retrieval_policy_version: str = "v16-retrieval-1"
    created_at: datetime = Field(default_factory=utc_now)
    context_text: str = ""


class KnowledgeContextBundle(StrictModel):
    receipt: RetrievalReceipt
    items: list[KnowledgeItem] = Field(default_factory=list)
