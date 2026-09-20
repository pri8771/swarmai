"""FIX-005: scale scheduler must not force-progress without quota admission."""

from __future__ import annotations

from pathlib import Path

from swarm.runtime import scale as scale_mod


def test_scale_source_has_no_force_progress_bypass() -> None:
    src = Path(scale_mod.__file__).read_text(encoding="utf-8")
    assert "Force-progress" not in src
    assert "pop one without quota" not in src
    assert "popleft()" not in src or "Force-progress" not in src


def test_empty_dispatch_stops_without_popping_queue(tmp_path: Path) -> None:
    """When dispatch admits nothing, drain must stop (no silent queue pop)."""
    repo = Path(__file__).resolve().parents[2]

    class _DenySched:
        def __init__(self) -> None:
            from collections import deque

            self.queue = deque()
            self._stats = {"queue_depth": 1}

        def enqueue(self, *args: object, **kwargs: object) -> None:
            return None

        def dispatch(self, *args: object, **kwargs: object) -> tuple[list[object], dict[str, object]]:
            return [], {"denied": True}

        def complete(self, *args: object, **kwargs: object) -> None:
            return None

        def stats(self) -> dict[str, object]:
            return dict(self._stats)

    import swarm.runtime.scale as mod

    original = mod.make_scale_scheduler

    def _factory(**kwargs: object) -> _DenySched:
        return _DenySched()

    mod.make_scale_scheduler = _factory  # type: ignore[assignment]
    try:
        report = mod.run_scale_mission(
            repo=repo,
            goal="admission deny probe",
            agent_count=4,
            max_concurrency=2,
            use_supervisor_model=False,
            out_dir=tmp_path,
        )
    finally:
        mod.make_scale_scheduler = original  # type: ignore[assignment]

    assert report.completed == 0
    assert report.task_count >= 1
