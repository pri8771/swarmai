"""Explicit actor, policy and lease authority for the V1.7 gateway."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any, Protocol

from pydantic import Field
from sqlalchemy.orm import Session, sessionmaker

from swarm.contracts.common import StrictModel
from swarm.db.lease_fencing import LeaseClaimError, LeaseLifecycleService, read_current_fence


class FenceState(StrictModel):
    lease_generation: int
    cancellation_generation: int
    authority: dict[str, Any] = Field(default_factory=dict)


class ActorContext(StrictModel):
    actor: str
    project_id: str


class FenceProvider(Protocol):
    def current(
        self,
        *,
        project_id: str,
        mission_id: str | None,
        task_id: str | None,
        attempt_id: str | None,
    ) -> FenceState: ...

    def reader(
        self,
        *,
        project_id: str,
        mission_id: str | None,
        task_id: str | None,
        attempt_id: str | None,
    ) -> Callable[[Session], Mapping[str, int | None]]: ...


class StaticFenceProvider:
    """Explicit generations for deterministic tests and non-leased local work."""

    def __init__(self, lease_generation: int, cancellation_generation: int) -> None:
        self.state = FenceState(
            lease_generation=lease_generation,
            cancellation_generation=cancellation_generation,
        )

    def current(
        self,
        *,
        project_id: str,
        mission_id: str | None,
        task_id: str | None,
        attempt_id: str | None,
    ) -> FenceState:
        return self.state.model_copy(deep=True)

    def reader(
        self,
        *,
        project_id: str,
        mission_id: str | None,
        task_id: str | None,
        attempt_id: str | None,
    ) -> Callable[[Session], Mapping[str, int | None]]:
        def read(session: Session) -> Mapping[str, int | None]:
            return {
                "lease_generation": self.state.lease_generation,
                "cancellation_generation": self.state.cancellation_generation,
            }

        return read


class LeaseFenceProvider:
    """Delegate worker-table authority entirely to the lease module."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self.session_factory = session_factory

    def current(
        self,
        *,
        project_id: str,
        mission_id: str | None,
        task_id: str | None,
        attempt_id: str | None,
    ) -> FenceState:
        with self.session_factory() as session:
            values = read_current_fence(
                session,
                project_id=project_id,
                mission_id=mission_id,
                task_id=task_id,
                attempt_id=attempt_id,
            )
            return FenceState(
                lease_generation=values["lease_generation"],
                cancellation_generation=values["cancellation_generation"],
            )

    def reader(
        self,
        *,
        project_id: str,
        mission_id: str | None,
        task_id: str | None,
        attempt_id: str | None,
    ) -> Callable[[Session], Mapping[str, int | None]]:
        def read(session: Session) -> Mapping[str, int | None]:
            # Preserve the admission reader's mission -> lease -> attempt lock order
            # and its expiry, worker revocation and active-lease checks.
            if not mission_id or not task_id or not attempt_id:
                raise LeaseClaimError("lease_not_current")
            return LeaseLifecycleService(session).read_effect_fence(
                project_id=project_id,
                mission_id=mission_id,
                task_id=task_id,
                attempt_id=attempt_id,
            )

        return read


class PolicyProvider(Protocol):
    def effective_scopes(
        self,
        *,
        project_id: str,
        actor: str,
        integration_id: str,
        integration_version: str,
    ) -> frozenset[str]: ...

    def current_policy_version(self, *, project_id: str) -> str: ...


class StaticPolicyProvider:
    """A deterministic, explicitly supplied policy for bounded local tests."""

    def __init__(self, scopes: frozenset[str] | set[str], policy_version: str) -> None:
        self.scopes = frozenset(scopes)
        self.policy_version = policy_version

    def effective_scopes(
        self,
        *,
        project_id: str,
        actor: str,
        integration_id: str,
        integration_version: str,
    ) -> frozenset[str]:
        return self.scopes

    def current_policy_version(self, *, project_id: str) -> str:
        return self.policy_version
