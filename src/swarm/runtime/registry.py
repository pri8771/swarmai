"""Stable agent-profile registration with dynamic session IDs."""

from __future__ import annotations

from dataclasses import dataclass, field

from swarm.contracts.common import new_id
from swarm.contracts.mission import AgentProfile, AgentSession


@dataclass
class RegistrationIdentity:
    """Framework-stable identity — one per agent profile, not per session."""

    registration_id: str
    agent_profile_id: str
    role: str
    instructions_version: str


@dataclass
class SessionRegistry:
    """Dynamic sessions reuse a bounded set of profile registrations."""

    max_registrations: int = 64
    _profiles: dict[str, AgentProfile] = field(default_factory=dict)
    _registrations: dict[str, RegistrationIdentity] = field(default_factory=dict)
    _sessions: dict[str, AgentSession] = field(default_factory=dict)
    _by_profile: dict[str, str] = field(default_factory=dict)

    def register_profile(self, profile: AgentProfile) -> RegistrationIdentity:
        existing = self._by_profile.get(profile.id)
        if existing is not None:
            return self._registrations[existing]
        if len(self._registrations) >= self.max_registrations:
            raise RuntimeError("registration_cap_exceeded")
        reg_id = f"reg_{profile.role}_{profile.instructions_version}"
        # Stable key: do not allocate new framework registrations per session.
        if reg_id in self._registrations:
            identity = self._registrations[reg_id]
            self._profiles[profile.id] = profile
            self._by_profile[profile.id] = reg_id
            return identity
        identity = RegistrationIdentity(
            registration_id=reg_id,
            agent_profile_id=profile.id,
            role=profile.role,
            instructions_version=profile.instructions_version,
        )
        self._registrations[reg_id] = identity
        self._profiles[profile.id] = profile
        self._by_profile[profile.id] = reg_id
        return identity

    def open_session(
        self, profile: AgentProfile, *, task_id: str | None = None
    ) -> AgentSession:
        self.register_profile(profile)
        session = AgentSession(
            id=new_id("as_"),
            agent_profile_id=profile.id,
            assigned_task_id=task_id,
            status="idle",
        )
        self._sessions[session.id] = session
        return session

    def get_session(self, session_id: str) -> AgentSession:
        return self._sessions[session_id]

    def registration_count(self) -> int:
        return len(self._registrations)

    def session_count(self) -> int:
        return len(self._sessions)
