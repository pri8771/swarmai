"""V1.0 freeze / first-run / validation tests."""

from __future__ import annotations

from pathlib import Path

from swarm.release.contract_freeze import freeze_public_contracts
from swarm.release.first_run import run_first_run
from swarm.release.verify import verify_release

ROOT = Path(__file__).resolve().parents[2]


def test_contract_freeze(tmp_path: Path) -> None:
    # Use real repo schemas + write freeze under tmp by copying minimal tree.
    report = freeze_public_contracts(ROOT)
    assert report.ok is True
    assert report.hash
    assert (ROOT / "schemas" / "v1" / "product_contract.v1.json").is_file()


def test_first_run_ok() -> None:
    report = run_first_run(ROOT)
    assert report.ok is True
    assert report.project_id


def test_release_verify_includes_v1_docs() -> None:
    report = verify_release(ROOT)
    assert report.passed is True
    assert any(i.item_id.endswith("CHANGELOG.md") for i in report.items)
