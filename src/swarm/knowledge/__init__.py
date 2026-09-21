"""V1.6 scoped reusable knowledge."""

from swarm.knowledge.repository import (
    KnowledgeRepository,
    KnowledgeScopeError,
    KnowledgeWriteError,
)

__all__ = [
    "KnowledgeRepository",
    "KnowledgeScopeError",
    "KnowledgeWriteError",
]
