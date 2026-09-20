"""Transactional outbox publisher (DBOS enqueue bridge)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from sqlalchemy.orm import Session

from swarm.db.repositories import OutboxRepository

EnqueueFn = Callable[[str, dict[str, Any]], None]


class OutboxPublisher:
    """Publishes pending outbox rows. DBOS tables stay private to DBOS."""

    def __init__(self, session: Session, enqueue: EnqueueFn | None = None) -> None:
        self.session = session
        self.repo = OutboxRepository(session)
        self._enqueue = enqueue or (lambda _workflow_id, _payload: None)
        self.published: list[str] = []

    def drain(self, limit: int = 50) -> int:
        rows = self.repo.claim_pending(limit=limit)
        count = 0
        for row in rows:
            try:
                self._enqueue(row.stable_workflow_id, dict(row.payload))
                self.repo.mark_published(row)
                self.published.append(row.stable_workflow_id)
                count += 1
            except Exception as exc:  # noqa: BLE001
                self.repo.mark_failed(row, str(exc))
        return count
