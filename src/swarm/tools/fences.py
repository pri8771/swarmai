"""Explicit actor, policy and lease authority for the V1.7 gateway."""

from __future__ import annotations

import threading
from collections.abc import Callable, Iterator, Mapping
from contextlib import AbstractContextManager, contextmanager, nullcontext
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
    def admission_guard(self) -> AbstractContextManager[None]: ...

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

    def admission_guard(self) -> AbstractContextManager[None]:
        return nullcontext()

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


class RevocableFenceProvider:
    """Thread-safe local fence provider that can invalidate an active mission turn.

    Local mission workers run synchronously in a background thread.  A runtime
    interruption must therefore invalidate the generation that the worker
    captured at task start; otherwise a worker that resumes after cancellation
    could mint a fresh matching generation and admit another effect.
    """

    def __init__(self, lease_generation: int = 1, cancellation_generation: int = 0) -> None:
        self._lock = threading.RLock()
        self._cancelled = False
        self._state = FenceState(
            lease_generation=lease_generation,
            cancellation_generation=cancellation_generation,
        )

    @contextmanager
    def admission_guard(self) -> Iterator[None]:
        """Serialize local revocation with admission, including its committed return."""
        with self._lock:
            yield

    def current(
        self,
        *,
        project_id: str,
        mission_id: str | None,
        task_id: str | None,
        attempt_id: str | None,
    ) -> FenceState:
        del project_id, mission_id, task_id, attempt_id
        with self._lock:
            return self._state.model_copy(deep=True)

    @property
    def cancelled(self) -> bool:
        """Whether this local mission fence has been revoked."""
        with self._lock:
            return self._cancelled

    def cancel(self) -> FenceState:
        """Advance cancellation generation so pre-cancel envelopes fail closed."""
        with self._lock:
            self._cancelled = True
            self._state = self._state.model_copy(
                update={"cancellation_generation": self._state.cancellation_generation + 1}
            )
            return self._state.model_copy(deep=True)

    def reader(
        self,
        *,
        project_id: str,
        mission_id: str | None,
        task_id: str | None,
        attempt_id: str | None,
    ) -> Callable[[Session], Mapping[str, int | None]]:
        def read(session: Session) -> Mapping[str, int | None]:
            del session
            state = self.current(
                project_id=project_id,
                mission_id=mission_id,
                task_id=task_id,
                attempt_id=attempt_id,
            )
            return {
                "lease_generation": state.lease_generation,
                "cancellation_generation": state.cancellation_generation,
            }

        return read


class LeaseFenceProvider:
    """Delegate worker-table authority entirely to the lease module."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self.session_factory = session_factory

    def admission_guard(self) -> AbstractContextManager[None]:
        return nullcontext()

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
