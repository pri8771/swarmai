"""V2B-003d / ART-V16 — conservative MemoryStore → knowledge migration adapter.

Never silently promotes legacy durable_fact / model_obs / outcome into accepted_fact.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from swarm.contracts.knowledge import KnowledgeItem
from swarm.knowledge.repository import KnowledgeRepository, KnowledgeWriteError
from swarm.memory.store import MemoryRecord, MemoryStore

# Conservative class mapping — no automatic accepted_fact.
_KIND_TO_CLASS: dict[str, str] = {
    "durable_fact": "observation",
    "transient_context": "observation",
    "decision": "observation",
    "outcome": "observation",
    "model_obs": "observation",
}


@dataclass
class MigrationReport:
    scanned: int = 0
    imported: int = 0
    quarantined: int = 0
    skipped_transient: bool = False
    errors: list[str] = field(default_factory=list)
    item_ids: list[str] = field(default_factory=list)
    quarantined_memory_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "scanned": self.scanned,
            "imported": self.imported,
            "quarantined": self.quarantined,
            "errors": list(self.errors),
            "item_ids": list(self.item_ids),
            "quarantined_memory_ids": list(self.quarantined_memory_ids),
            "note": "legacy durable_fact mapped to observation/unreviewed — never accepted_fact",
        }


class MemoryStoreKnowledgeAdapter:
    """Read-only migration from file-backed MemoryStore into KnowledgeRepository."""

    def __init__(self, repo: KnowledgeRepository) -> None:
        self.repo = repo

    def migrate(
        self,
        store: MemoryStore,
        *,
        include_transient: bool = False,
        default_permission_labels: list[str] | None = None,
    ) -> MigrationReport:
        report = MigrationReport()
        labels = list(default_permission_labels or [])
        for record in store.list_all():
            report.scanned += 1
            try:
                item = self.map_record(
                    record,
                    permission_labels=labels,
                    include_transient=include_transient,
                )
            except KnowledgeWriteError as exc:
                report.errors.append(f"{record.memory_id}:{exc}")
                report.quarantined += 1
                report.quarantined_memory_ids.append(record.memory_id)
                continue
            if item is None:
                if record.kind == "transient_context" and not include_transient:
                    report.skipped_transient = True
                continue
            try:
                created = self.repo.create_item(item)
            except Exception as exc:  # noqa: BLE001
                report.errors.append(f"{record.memory_id}:{type(exc).__name__}:{exc}")
                report.quarantined += 1
                report.quarantined_memory_ids.append(record.memory_id)
                continue
            report.imported += 1
            report.item_ids.append(created.item_id)
        return report

    def map_record(
        self,
        record: MemoryRecord,
        *,
        permission_labels: list[str] | None = None,
        include_transient: bool = False,
    ) -> KnowledgeItem | None:
        if not record.project_id or record.project_id in {"", "unknown", "None"}:
            raise KnowledgeWriteError("missing_or_unknown_project_id")
        if record.kind == "transient_context" and not include_transient:
            return None
        knowledge_class = _KIND_TO_CLASS.get(record.kind, "observation")
        producer_type = "model" if record.kind == "model_obs" else "migration"
        # Explicit: never accepted, even for durable_fact.
        return KnowledgeItem.model_validate(
            {
                "project_id": record.project_id,
                "mission_id": record.mission_id,
                "class": knowledge_class,
                "topic": record.topic,
                "body": record.content,
                "producer_type": producer_type,
                "producer_ref": f"memory:{record.memory_id}",
                "acceptance_state": "unreviewed",
                "confidence": float(record.confidence),
                "permission_labels": list(permission_labels or []),
                "retrieval_labels": list(record.tags or []),
                "provenance_refs": [record.provenance, f"memory_id:{record.memory_id}"],
                "source_digests": [],
                "payload": {
                    "legacy_kind": record.kind,
                    "legacy_memory_id": record.memory_id,
                    "legacy_created_at": record.created_at,
                    "migration_policy": "conservative_v2b003d_no_auto_accept",
                },
            }
        )
