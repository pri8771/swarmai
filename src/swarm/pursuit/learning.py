"""Evaluated pursuit lessons — adopt affects behavior; rollback restores strategy."""

from __future__ import annotations

from typing import TYPE_CHECKING

from swarm.contracts.common import utc_now
from swarm.pursuit.models import LessonState, PursuitLesson

if TYPE_CHECKING:
    from swarm.pursuit.durable_accounting import LessonPersistence


class PursuitLearningError(RuntimeError):
    pass


_TRANSITIONS: dict[LessonState, set[LessonState]] = {
    LessonState.CANDIDATE: {LessonState.EVALUATED, LessonState.REJECTED},
    LessonState.EVALUATED: {LessonState.ADOPTED, LessonState.REJECTED},
    LessonState.ADOPTED: {LessonState.ROLLED_BACK},
    LessonState.ROLLED_BACK: set(),
    LessonState.REJECTED: set(),
}


class PursuitLessonStore:
    def __init__(self, persistence: LessonPersistence | None = None) -> None:
        self._lessons: dict[str, PursuitLesson] = {}
        self._by_goal: dict[str, list[str]] = {}
        self._persistence = persistence
        if persistence is not None:
            for lesson in persistence.load_all():
                self._lessons[lesson.lesson_id] = lesson
                self._by_goal.setdefault(lesson.goal_id, []).append(lesson.lesson_id)

    def _store(self, lesson: PursuitLesson) -> PursuitLesson:
        """Durable first: a persistence failure leaves memory unchanged."""
        if self._persistence is not None:
            self._persistence.put(lesson)
        self._lessons[lesson.lesson_id] = lesson
        return lesson

    def propose(self, lesson: PursuitLesson) -> PursuitLesson:
        self._store(lesson)
        self._by_goal.setdefault(lesson.goal_id, []).append(lesson.lesson_id)
        return lesson

    def get(self, lesson_id: str) -> PursuitLesson:
        if lesson_id not in self._lessons:
            raise PursuitLearningError("lesson_missing")
        return self._lessons[lesson_id]

    def list_for_goal(self, goal_id: str) -> list[PursuitLesson]:
        return [self._lessons[i] for i in self._by_goal.get(goal_id, []) if i in self._lessons]

    def adopted_for_goal(self, goal_id: str) -> list[PursuitLesson]:
        return [
            lesson for lesson in self.list_for_goal(goal_id) if lesson.state == LessonState.ADOPTED
        ]

    def evaluate(
        self,
        lesson_id: str,
        *,
        holdout_check_id: str,
        holdout_passed: bool,
    ) -> PursuitLesson:
        lesson = self.get(lesson_id)
        if lesson.state != LessonState.CANDIDATE:
            raise PursuitLearningError(f"evaluate_illegal_from:{lesson.state.value}")
        if not holdout_check_id:
            raise PursuitLearningError("holdout_required")
        if "answer=" in holdout_check_id:
            raise PursuitLearningError("holdout_plaintext_forbidden")
        updated = lesson.model_copy(
            update={
                "holdout_check_id": holdout_check_id,
                "holdout_passed": holdout_passed,
                "state": LessonState.EVALUATED if holdout_passed else LessonState.REJECTED,
                "updated_at": utc_now().isoformat(),
            }
        )
        return self._store(updated)

    def adopt(self, lesson_id: str, *, current_strategy: str) -> PursuitLesson:
        lesson = self.get(lesson_id)
        if lesson.state != LessonState.EVALUATED:
            raise PursuitLearningError(f"adopt_illegal_from:{lesson.state.value}")
        if lesson.holdout_passed is not True:
            raise PursuitLearningError("holdout_not_passed")
        updated = lesson.model_copy(
            update={
                "state": LessonState.ADOPTED,
                "prior_strategy": current_strategy,
                "updated_at": utc_now().isoformat(),
            }
        )
        return self._store(updated)

    def rollback(self, lesson_id: str) -> PursuitLesson:
        lesson = self.get(lesson_id)
        if lesson.state != LessonState.ADOPTED:
            raise PursuitLearningError(f"rollback_illegal_from:{lesson.state.value}")
        updated = lesson.model_copy(
            update={"state": LessonState.ROLLED_BACK, "updated_at": utc_now().isoformat()}
        )
        return self._store(updated)

    def applied_strategy(self, goal_id: str, base_strategy: str) -> str:
        adopted = self.adopted_for_goal(goal_id)
        if not adopted:
            return base_strategy
        deltas = [lesson.strategy_delta for lesson in adopted if lesson.strategy_delta]
        if not deltas:
            return base_strategy
        return (base_strategy + " | " + " | ".join(deltas)).strip(" |")
