"""R01 — deterministic reviewer grounding against actual diff/target/checks."""

from __future__ import annotations

from swarm.mission.acceptance import (
    changed_paths_from_diff,
    ground_semantic_review,
    symbols_added_in_diff,
)

LEDGER_DIFF = """\
diff --git a/src/swarm/cost/ledger.py b/src/swarm/cost/ledger.py
index 1111111..2222222 100644
--- a/src/swarm/cost/ledger.py
+++ b/src/swarm/cost/ledger.py
@@ -10,6 +10,8 @@ class CostLedger:
     def load_entry(self, cost: dict) -> CostEntry:
-        return CostEntry(route_id=None, model=None)
+        entry = (cost.get("entries") or [{}])[0]
+        return CostEntry(route_id=entry.get("route_id"), model=entry.get("model"))
"""


def test_changed_paths_and_symbols_from_diff() -> None:
    paths = changed_paths_from_diff(LEDGER_DIFF)
    assert paths == ["src/swarm/cost/ledger.py"]
    # No new top-level def/class in this hunk; path grounding still applies.
    assert isinstance(symbols_added_in_diff(LEDGER_DIFF), set)


def test_rejects_stale_inclusive_range_review_for_ledger_diff() -> None:
    decision = ground_semantic_review(
        review_text=(
            "The inclusive_range_count fix is not directly related to the changes "
            "shown. The diff adds route_id and model fields."
        ),
        diff_text=LEDGER_DIFF,
        verify_commands=[{"cmd": ["uv", "run", "pytest", "tests/mission", "-q"]}],
    )
    assert decision.grounded is False
    assert decision.checks["stale_unrelated_symbols_absent"] is False
    assert any("stale_symbols" in r for r in decision.reasons)


def test_rejects_broad_mission_suite_without_focused_ledger_check() -> None:
    decision = ground_semantic_review(
        review_text=(
            "ledger.py correctly reads route_id/model from cost.entries for CostEntry."
        ),
        diff_text=LEDGER_DIFF,
        verify_commands=[{"cmd": ["uv", "run", "pytest", "tests/mission", "-q"]}],
    )
    assert decision.grounded is False
    assert decision.checks.get("broad_unrelated_suite_only") is True
    assert "broad_unrelated_suite_only" in decision.reasons


def test_accepts_grounded_review_with_focused_check() -> None:
    decision = ground_semantic_review(
        review_text=(
            "src/swarm/cost/ledger.py now loads route_id and model from cost.entries; "
            "the CostEntry accounting loss is repaired."
        ),
        diff_text=LEDGER_DIFF,
        verify_commands=[
            {
                "cmd": [
                    "uv",
                    "run",
                    "pytest",
                    "tests/cost/test_ledger.py",
                    "-q",
                ]
            }
        ],
        focused_check_paths=["tests/cost/test_ledger.py"],
    )
    assert decision.grounded is True
    assert decision.checks["review_references_changed_target"] is True
    assert decision.checks["stale_unrelated_symbols_absent"] is True
    assert "review_grounded" in decision.reasons


def test_rejects_review_that_never_names_changed_target() -> None:
    decision = ground_semantic_review(
        review_text="Looks fine overall. Ship it.",
        diff_text=LEDGER_DIFF,
        verify_commands=[
            {"cmd": ["uv", "run", "pytest", "tests/cost/test_ledger.py", "-q"]}
        ],
    )
    assert decision.grounded is False
    assert decision.checks["review_references_changed_target"] is False
