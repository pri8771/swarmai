"""V2B-003a / ART-V16 — versioned project-scoped knowledge repository."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from swarm.contracts.common import new_id, utc_now
from swarm.contracts.knowledge import (
    KnowledgeItem,
    KnowledgeLink,
    KnowledgeTombstone,
    assert_model_output_class,
)
from swarm.db.models import KnowledgeItemRow, KnowledgeLinkRow, KnowledgeTombstoneRow

_ALLOWED_RELATIONS = frozenset(
    {"derived_from", "supports", "contradicts", "supersedes", "summarizes"}
)
_ACCEPT_STATES = frozenset({"unreviewed", "accepted", "disputed", "superseded", "deleted"})


class KnowledgeScopeError(PermissionError):
    """Cross-project or unauthorized knowledge access."""


class KnowledgeWriteError(ValueError):
    """Invalid knowledge write (class/acceptance/version rules)."""


class KnowledgeRepository:
    """PostgreSQL-backed versioned knowledge store (not MemoryStore)."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create_item(self, item: KnowledgeItem) -> KnowledgeItem:
        try:
            assert_model_output_class(item.class_, producer_type=item.producer_type)
        except ValueError as exc:
            raise KnowledgeWriteError(str(exc)) from exc
        if item.acceptance_state == "accepted" and item.class_ != "accepted_fact":
            # Allow accepted procedures/sources via explicit reviewer path later.
            if item.class_ not in {"accepted_fact", "procedure", "source"}:
                raise KnowledgeWriteError("acceptance_requires_reviewable_class")
        if item.acceptance_state == "accepted" and item.producer_type in {
            "model",
            "llm",
            "worker_model",
        }:
            raise KnowledgeWriteError("model_cannot_self_accept")
        if item.acceptance_state not in _ACCEPT_STATES:
            raise KnowledgeWriteError(f"invalid_acceptance_state:{item.acceptance_state}")
        if item.version < 1:
            raise KnowledgeWriteError("version_must_be_positive")
        existing = self.get_item(
            project_id=item.project_id, item_id=item.item_id, version=item.version
        )
        if existing is not None:
            raise KnowledgeWriteError("version_already_exists")
        digest = item.ensure_content_digest()
        row = KnowledgeItemRow(
            row_id=new_id("knr_"),
            item_id=item.item_id,
            version=item.version,
            project_id=item.project_id,
            mission_id=item.mission_id,
            class_=item.class_,
            topic=item.topic,
            body=item.body,
            acceptance_state=item.acceptance_state,
            confidence=item.confidence,
            producer_type=item.producer_type,
            producer_ref=item.producer_ref,
            permission_labels=list(item.permission_labels),
            retrieval_labels=list(item.retrieval_labels),
            source_digests=list(item.source_digests),
            provenance_refs=list(item.provenance_refs),
            content_digest=digest,
            observed_at=item.observed_at,
            expires_at=item.expires_at,
            created_at=item.created_at,
            payload={**dict(item.payload), "supersedes": list(item.supersedes)},
        )
        self.session.add(row)
        self.session.flush()
        return self._to_item(row)

    def new_version(
        self,
        *,
        project_id: str,
        item_id: str,
        body: str | None = None,
        topic: str | None = None,
        acceptance_state: str | None = None,
        producer_type: str | None = None,
        producer_ref: str | None = None,
        class_: str | None = None,
        permission_labels: list[str] | None = None,
        retrieval_labels: list[str] | None = None,
        provenance_refs: list[str] | None = None,
        source_digests: list[str] | None = None,
        confidence: float | None = None,
        payload: dict[str, Any] | None = None,
    ) -> KnowledgeItem:
        """Edits create a new version — never silent overwrite."""
        latest = self.get_latest(project_id=project_id, item_id=item_id, include_deleted=True)
        if latest is None:
            raise KnowledgeWriteError("item_not_found")
        if latest.acceptance_state == "deleted":
            raise KnowledgeWriteError("item_deleted")
        nxt = latest.model_copy(
            update={
                "version": int(latest.version) + 1,
                "body": body if body is not None else latest.body,
                "topic": topic if topic is not None else latest.topic,
                "acceptance_state": (
                    acceptance_state if acceptance_state is not None else "unreviewed"
                ),
                "producer_type": producer_type or latest.producer_type,
                "producer_ref": producer_ref if producer_ref is not None else latest.producer_ref,
                "class_": class_ or latest.class_,
                "permission_labels": (
                    list(permission_labels)
                    if permission_labels is not None
                    else list(latest.permission_labels)
                ),
                "retrieval_labels": (
                    list(retrieval_labels)
                    if retrieval_labels is not None
                    else list(latest.retrieval_labels)
                ),
                "provenance_refs": (
                    list(provenance_refs)
                    if provenance_refs is not None
                    else list(latest.provenance_refs)
                ),
                "source_digests": (
                    list(source_digests)
                    if source_digests is not None
                    else list(latest.source_digests)
                ),
                "confidence": confidence if confidence is not None else latest.confidence,
                "created_at": utc_now(),
                "content_digest": None,
                "payload": dict(payload) if payload is not None else dict(latest.payload),
            }
        )
        return self.create_item(nxt)

    def accept_fact(
        self,
        *,
        project_id: str,
        item_id: str,
        version: int,
        reviewer_ref: str,
    ) -> KnowledgeItem:
        """Explicit control-plane acceptance — never automatic from model output."""
        item = self.get_item(project_id=project_id, item_id=item_id, version=version)
        if item is None:
            raise KnowledgeWriteError("item_not_found")
        if item.class_ not in {"observation", "hypothesis", "accepted_fact", "procedure", "source"}:
            raise KnowledgeWriteError("class_not_accept_eligible")
        return self.new_version(
            project_id=project_id,
            item_id=item_id,
            class_="accepted_fact" if item.class_ in {"observation", "hypothesis"} else item.class_,
            acceptance_state="accepted",
            producer_type="reviewer",
            producer_ref=reviewer_ref,
            body=item.body,
            topic=item.topic,
            provenance_refs=[*item.provenance_refs, f"accepted_from:v{version}"],
            permission_labels=list(item.permission_labels),
            retrieval_labels=list(item.retrieval_labels),
            source_digests=list(item.source_digests),
            confidence=item.confidence,
            payload={**item.payload, "accepted_from_version": version},
        )

    def add_link(self, link: KnowledgeLink) -> KnowledgeLink:
        if link.relation not in _ALLOWED_RELATIONS:
            raise KnowledgeWriteError(f"invalid_relation:{link.relation}")
        src = self.get_item(
            project_id=link.project_id, item_id=link.from_item_id, version=link.from_version
        )
        dst = self.get_item(
            project_id=link.project_id, item_id=link.to_item_id, version=link.to_version
        )
        if src is None or dst is None:
            raise KnowledgeWriteError("link_endpoint_missing")
        if src.project_id != dst.project_id or src.project_id != link.project_id:
            raise KnowledgeScopeError("cross_project_link_forbidden")
        row = KnowledgeLinkRow(
            link_id=link.link_id,
            project_id=link.project_id,
            from_item_id=link.from_item_id,
            from_version=link.from_version,
            relation=link.relation,
            to_item_id=link.to_item_id,
            to_version=link.to_version,
            evidence_ref=link.evidence_ref,
            created_at=link.created_at,
        )
        self.session.add(row)
        self.session.flush()
        return link

    def tombstone(
        self,
        *,
        project_id: str,
        item_id: str,
        version: int | None = None,
        reason_class: str = "operator_delete",
        replacement_item_id: str | None = None,
        replacement_version: int | None = None,
        now: datetime | None = None,
    ) -> KnowledgeTombstone:
        clock = now or utc_now()
        latest = self.get_latest(project_id=project_id, item_id=item_id, include_deleted=True)
        if latest is None:
            raise KnowledgeWriteError("item_not_found")
        deleted_version = int(version if version is not None else latest.version)
        row = self.session.scalar(
            select(KnowledgeItemRow).where(
                KnowledgeItemRow.project_id == project_id,
                KnowledgeItemRow.item_id == item_id,
                KnowledgeItemRow.version == deleted_version,
            )
        )
        if row is None:
            raise KnowledgeWriteError("version_not_found")
        row.acceptance_state = "deleted"
        row.deleted_at = clock
        stone = KnowledgeTombstone(
            item_id=item_id,
            project_id=project_id,
            deleted_version=deleted_version,
            deleted_at=clock,
            reason_class=reason_class,
            replacement_item_id=replacement_item_id,
            replacement_version=replacement_version,
        )
        self.session.add(
            KnowledgeTombstoneRow(
                tombstone_id=stone.tombstone_id,
                item_id=stone.item_id,
                project_id=stone.project_id,
                deleted_version=stone.deleted_version,
                deleted_at=stone.deleted_at,
                reason_class=stone.reason_class,
                replacement_item_id=stone.replacement_item_id,
                replacement_version=stone.replacement_version,
                payload=dict(stone.payload),
            )
        )
        self.session.flush()
        return stone

    def get_item(
        self, *, project_id: str, item_id: str, version: int
    ) -> KnowledgeItem | None:
        row = self.session.scalar(
            select(KnowledgeItemRow).where(
                KnowledgeItemRow.project_id == project_id,
                KnowledgeItemRow.item_id == item_id,
                KnowledgeItemRow.version == version,
            )
        )
        return None if row is None else self._to_item(row)

    def get_latest(
        self,
        *,
        project_id: str,
        item_id: str,
        include_deleted: bool = False,
    ) -> KnowledgeItem | None:
        stmt = (
            select(KnowledgeItemRow)
            .where(
                KnowledgeItemRow.project_id == project_id,
                KnowledgeItemRow.item_id == item_id,
            )
            .order_by(KnowledgeItemRow.version.desc())
            .limit(1)
        )
        row = self.session.scalar(stmt)
        if row is None:
            return None
        if not include_deleted and (
            row.deleted_at is not None or row.acceptance_state == "deleted"
        ):
            return None
        return self._to_item(row)

    def list_visible(
        self,
        *,
        project_id: str,
        permission_labels: list[str] | None = None,
        classes: list[str] | None = None,
        include_superseded: bool = False,
        limit: int = 100,
    ) -> list[KnowledgeItem]:
        """Permission-first listing: project filter before any ranking."""
        stmt = select(KnowledgeItemRow).where(
            KnowledgeItemRow.project_id == project_id,
            KnowledgeItemRow.deleted_at.is_(None),
            KnowledgeItemRow.acceptance_state != "deleted",
        )
        if not include_superseded:
            stmt = stmt.where(KnowledgeItemRow.acceptance_state != "superseded")
        if classes:
            stmt = stmt.where(KnowledgeItemRow.class_.in_(tuple(classes)))
        stmt = stmt.order_by(
            KnowledgeItemRow.created_at.desc(), KnowledgeItemRow.item_id.asc()
        ).limit(limit)
        rows = list(self.session.scalars(stmt))
        required = set(permission_labels or [])
        out: list[KnowledgeItem] = []
        for row in rows:
            labels = set(str(x) for x in (row.permission_labels or []))
            # Permission-first: labeled items require intersecting actor labels.
            if labels and required and labels.isdisjoint(required):
                continue
            if labels and not required:
                continue
            out.append(self._to_item(row))
        return out

    def get_tombstone(
        self, *, project_id: str, item_id: str, deleted_version: int
    ) -> KnowledgeTombstone | None:
        row = self.session.scalar(
            select(KnowledgeTombstoneRow).where(
                KnowledgeTombstoneRow.project_id == project_id,
                KnowledgeTombstoneRow.item_id == item_id,
                KnowledgeTombstoneRow.deleted_version == deleted_version,
            )
        )
        if row is None:
            return None
        return KnowledgeTombstone(
            tombstone_id=row.tombstone_id,
            item_id=row.item_id,
            project_id=row.project_id,
            deleted_version=row.deleted_version,
            deleted_at=row.deleted_at,
            reason_class=row.reason_class,
            replacement_item_id=row.replacement_item_id,
            replacement_version=row.replacement_version,
            payload=dict(row.payload or {}),
        )

    @staticmethod
    def _to_item(row: KnowledgeItemRow) -> KnowledgeItem:
        payload = dict(row.payload or {})
        supersedes = payload.get("supersedes") if isinstance(payload, dict) else []
        return KnowledgeItem.model_validate(
            {
                "item_id": row.item_id,
                "version": row.version,
                "project_id": row.project_id,
                "mission_id": row.mission_id,
                "class": row.class_,
                "topic": row.topic,
                "body": row.body,
                "provenance_refs": list(row.provenance_refs or []),
                "source_digests": list(row.source_digests or []),
                "producer_type": row.producer_type,
                "producer_ref": row.producer_ref,
                "acceptance_state": row.acceptance_state,
                "confidence": row.confidence,
                "created_at": row.created_at,
                "observed_at": row.observed_at,
                "expires_at": row.expires_at,
                "supersedes": list(supersedes or []),
                "permission_labels": list(row.permission_labels or []),
                "retrieval_labels": list(row.retrieval_labels or []),
                "content_digest": row.content_digest,
                "payload": payload,
            }
        )
