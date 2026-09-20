"""Findings store with ACL, supersession, and text search (no remote embeddings)."""

from __future__ import annotations

from dataclasses import dataclass, field

from swarm.contracts.enums import FindingStatus
from swarm.contracts.workspace import Finding


@dataclass
class FindingRecord:
    finding: Finding
    scopes: list[str]
    topics: list[str] = field(default_factory=list)
    source_deleted: bool = False


class FindingStore:
    def __init__(self) -> None:
        self._items: dict[str, FindingRecord] = {}

    def append(
        self,
        finding: Finding,
        *,
        scopes: list[str] | None = None,
        topics: list[str] | None = None,
    ) -> Finding:
        scopes = scopes or list(finding.acl) or [finding.project_id]
        if finding.supersedes:
            prior = self._items.get(finding.supersedes)
            if prior is not None and prior.finding.status != FindingStatus.SUPERSEDED:
                prior.finding = prior.finding.model_copy(
                    update={"status": FindingStatus.SUPERSEDED}
                )
        rec = FindingRecord(
            finding=finding, scopes=list(scopes), topics=list(topics or [])
        )
        self._items[finding.id] = rec
        return finding

    def get(self, finding_id: str) -> Finding | None:
        rec = self._items.get(finding_id)
        return None if rec is None else rec.finding

    def mark_source_deleted(self, finding_id: str) -> None:
        rec = self._items.get(finding_id)
        if rec is not None:
            rec.source_deleted = True

    def query_scoped(
        self,
        *,
        project_id: str,
        allowed_scopes: set[str],
        query: str = "",
        statuses: set[FindingStatus] | None = None,
    ) -> list[Finding]:
        """ACL before ranking. Malicious source text is data only."""
        hits: list[tuple[int, Finding]] = []
        q = query.lower().strip()
        for rec in self._items.values():
            f = rec.finding
            if f.project_id != project_id:
                continue
            if not allowed_scopes.intersection(set(rec.scopes)) and "*" not in allowed_scopes:
                continue
            if statuses and f.status not in statuses:
                continue
            score = 0
            blob = " ".join(
                [
                    f.content or "",
                    " ".join(f.source_ids),
                    " ".join(rec.topics),
                ]
            ).lower()
            if q:
                if q not in blob:
                    continue
                score = blob.count(q)
            # Prefer accepted over hypothesis; superseded remains auditable via get().
            if f.status == FindingStatus.ACCEPTED:
                score += 10
            elif f.status == FindingStatus.CORROBORATED:
                score += 5
            elif f.status == FindingStatus.DISPUTED:
                score += 1
            elif f.status == FindingStatus.SUPERSEDED:
                score -= 5
            if rec.source_deleted:
                score -= 20
            hits.append((score, f))
        hits.sort(key=lambda t: t[0], reverse=True)
        return [f for _, f in hits]
