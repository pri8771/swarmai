"""DispatchIntent service — all-or-nothing reservation with durable compensation.

State machine (ART-V23-MULTIMISSION_SCHEDULER "DispatchIntent"):

    PREPARED --reserve all ok--> RESERVED --mark_dispatched--> DISPATCHED --complete--> COMPLETED
    PREPARED --any reserve fails--> COMPENSATED   (every already-reserved part released)
    PREPARED|RESERVED --cancel--> CANCELLED       (reserved parts released)
    PREPARED|RESERVED --expired (recover_expired)--> EXPIRED (reserved parts released)

DISPATCHED is never auto-recovered: work may already run on a worker, so it needs
explicit completion/reconciliation, never a silent release.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta

from swarm.contracts.common import payload_hash, utc_now
from swarm.contracts.v23 import (
    TERMINAL_INTENT_STATES,
    DispatchIntent,
    DispatchIntentComponent,
    DispatchIntentState,
    SchedulingStore,
)

ReserveFn = Callable[[DispatchIntent, DispatchIntentComponent], str | None]
ReleaseFn = Callable[[DispatchIntent, DispatchIntentComponent], None]
Clock = Callable[[], datetime]


class DispatchIntentError(RuntimeError):
    pass


def attempt_digest(
    *, attempt_id: str, task_id: str, site_epoch: int, scheduler_epoch: int, generation: int
) -> str:
    return payload_hash(
        {
            "attempt_id": attempt_id,
            "task_id": task_id,
            "site_epoch": site_epoch,
            "scheduler_epoch": scheduler_epoch,
            "cancellation_generation": generation,
        }
    )


class DispatchIntentService:
    def __init__(
        self,
        store: SchedulingStore,
        *,
        reserve: ReserveFn,
        release: ReleaseFn,
        clock: Clock | None = None,
        ttl_seconds: float = 30.0,
    ) -> None:
        self.store = store
        self._reserve = reserve
        self._release = release
        self._clock: Clock = clock or utc_now
        self.ttl_seconds = ttl_seconds

    def prepare(
        self,
        *,
        attempt_id: str,
        project_id: str,
        mission_id: str,
        task_id: str,
        components: list[DispatchIntentComponent],
        site_epoch: int,
        scheduler_epoch: int,
        cancellation_generation: int,
    ) -> DispatchIntent:
        """Create the intent and reserve every component, or compensate all of them.

        Idempotent per ``attempt_id``: a second call returns the existing intent
        unchanged (duplicate scheduler ticks cannot double-reserve).
        """
        existing = self.store.get_intent_by_attempt(attempt_id)
        if existing is not None:
            return existing
        digest = attempt_digest(
            attempt_id=attempt_id,
            task_id=task_id,
            site_epoch=site_epoch,
            scheduler_epoch=scheduler_epoch,
            generation=cancellation_generation,
        )
        intent = self.store.put_intent(
            DispatchIntent(
                attempt_id=attempt_id,
                project_id=project_id,
                mission_id=mission_id,
                task_id=task_id,
                components=[c.model_copy(update={"reserved": False}) for c in components],
                site_epoch=site_epoch,
                scheduler_epoch=scheduler_epoch,
                cancellation_generation=cancellation_generation,
                attempt_digest=digest,
                expires_at=self._clock() + timedelta(seconds=self.ttl_seconds),
            ),
            expected_version=None,
        )
        for index, comp in enumerate(intent.components):
            # Persist the attempted reservation before crossing the external
            # boundary. A process death after reserve() succeeds can then be
            # compensated by recover_expired(); release callbacks are required
            # to be idempotent for an attempt that did not acquire capacity.
            attempted = comp.model_copy(update={"reserved": True})
            components = list(intent.components)
            components[index] = attempted
            intent = self.store.put_intent(
                intent.model_copy(update={"components": components}),
                expected_version=intent.version,
            )
            try:
                reservation_id = self._reserve(intent, attempted)
            except Exception as exc:  # noqa: BLE001 — any failure compensates
                # ReserveFn's contract is atomic for ordinary exceptions: a
                # raised Exception means this component was not acquired.
                # Abrupt process death never reaches this block, so the durable
                # attempted bit remains set for restart compensation.
                components = list(intent.components)
                components[index] = attempted.model_copy(update={"reserved": False})
                intent = self.store.put_intent(
                    intent.model_copy(update={"components": components}),
                    expected_version=intent.version,
                )
                attempted_components = [c for c in intent.components if c.reserved]
                return self._compensate(
                    intent,
                    attempted_components,
                    f"reserve_failed:{comp.kind}:{type(exc).__name__}",
                )
            components = list(intent.components)
            components[index] = attempted.model_copy(update={"reservation_id": reservation_id})
            intent = self.store.put_intent(
                intent.model_copy(update={"components": components}),
                expected_version=intent.version,
            )
        return self.store.put_intent(
            intent.model_copy(update={"state": DispatchIntentState.RESERVED}),
            expected_version=intent.version,
        )

    def mark_dispatched(self, intent_id: str) -> DispatchIntent:
        intent = self._require(intent_id)
        if intent.state == DispatchIntentState.DISPATCHED:
            return intent
        if intent.state != DispatchIntentState.RESERVED:
            raise DispatchIntentError(f"dispatch_illegal_from:{intent.state.value}")
        if self._clock() >= intent.expires_at:
            raise DispatchIntentError("intent_expired")
        return self.store.put_intent(
            intent.model_copy(update={"state": DispatchIntentState.DISPATCHED}),
            expected_version=intent.version,
        )

    def complete(self, intent_id: str) -> DispatchIntent:
        intent = self._require(intent_id)
        if intent.state == DispatchIntentState.COMPLETED:
            return intent
        if intent.state != DispatchIntentState.DISPATCHED:
            raise DispatchIntentError(f"complete_illegal_from:{intent.state.value}")
        return self.store.put_intent(
            intent.model_copy(update={"state": DispatchIntentState.COMPLETED}),
            expected_version=intent.version,
        )

    def cancel(self, intent_id: str, *, reason: str = "cancelled") -> DispatchIntent:
        intent = self._require(intent_id)
        if intent.state in TERMINAL_INTENT_STATES:
            return intent
        if intent.state == DispatchIntentState.DISPATCHED:
            raise DispatchIntentError("cancel_dispatched_requires_worker_cancel")
        self._release_all(intent)
        return self.store.put_intent(
            intent.model_copy(
                update={"state": DispatchIntentState.CANCELLED, "failure_reason": reason}
            ),
            expected_version=intent.version,
        )

    def recover_expired(self) -> list[DispatchIntent]:
        """Release and expire PREPARED/RESERVED intents past their TTL (restart path)."""
        now = self._clock()
        out: list[DispatchIntent] = []
        states = frozenset({DispatchIntentState.PREPARED, DispatchIntentState.RESERVED})
        for intent in self.store.list_intents(states=states):
            if now < intent.expires_at:
                continue
            self._release_all(intent)
            out.append(
                self.store.put_intent(
                    intent.model_copy(
                        update={"state": DispatchIntentState.EXPIRED, "failure_reason": "ttl"}
                    ),
                    expected_version=intent.version,
                )
            )
        return out

    def _compensate(
        self, intent: DispatchIntent, reserved: list[DispatchIntentComponent], reason: str
    ) -> DispatchIntent:
        for comp in reversed(reserved):
            self._release(intent, comp)
        released = [c.model_copy(update={"reserved": False}) for c in intent.components]
        return self.store.put_intent(
            intent.model_copy(
                update={
                    "state": DispatchIntentState.COMPENSATED,
                    "components": released,
                    "failure_reason": reason[:200],
                }
            ),
            expected_version=intent.version,
        )

    def _release_all(self, intent: DispatchIntent) -> None:
        for comp in reversed(intent.components):
            if comp.reserved:
                self._release(intent, comp)

    def _require(self, intent_id: str) -> DispatchIntent:
        intent = self.store.get_intent(intent_id)
        if intent is None:
            raise DispatchIntentError(f"intent_missing:{intent_id}")
        return intent
