"""Resource limits and capacity slots for agent sessions."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ResourceLimits:
    max_model_calls: int = 20
    max_tool_calls: int = 50
    max_wall_time_seconds: int = 3600
    max_concurrent_sessions: int = 32


@dataclass
class CapacityPool:
    """Logical capacity — blocked-on-children releases execution slots."""

    limits: ResourceLimits = field(default_factory=ResourceLimits)
    active_sessions: set[str] = field(default_factory=set)
    waiting_sessions: set[str] = field(default_factory=set)

    def acquire(self, session_id: str) -> None:
        if session_id in self.active_sessions:
            return
        runnable = len(self.active_sessions) - len(self.waiting_sessions)
        if runnable >= self.limits.max_concurrent_sessions:
            raise RuntimeError("capacity_exhausted")
        self.active_sessions.add(session_id)

    def mark_waiting_children(self, session_id: str) -> None:
        self.waiting_sessions.add(session_id)

    def clear_waiting(self, session_id: str) -> None:
        self.waiting_sessions.discard(session_id)

    def release(self, session_id: str) -> None:
        self.active_sessions.discard(session_id)
        self.waiting_sessions.discard(session_id)

    def runnable_count(self) -> int:
        return len(self.active_sessions) - len(self.waiting_sessions)
