from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest

from swarm.providers.splitsignal_client import SplitSignalClient
from tests.fixtures.splitsignal_http.fake_splitsignal import SYNTHETIC_KEY, FakeSplitSignal

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "v23_splitsignal_smoke.py"


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location("v23_splitsignal_smoke", SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


smoke = _load()
ENV = {
    "SPLITSIGNAL_BASE_URL": "http://s.test/v1",
    "SPLITSIGNAL_API_KEY": SYNTHETIC_KEY,
    "SPLITSIGNAL_MODEL": "mock/ok",
}


@pytest.fixture
def approved(tmp_path: Path) -> Path:
    p = tmp_path / "DECISIONS.md"
    p.write_text("- SW-PREAPPROVAL-A3: APPROVED 2026-09-26\n", encoding="utf-8")
    return p


def factory(fake: FakeSplitSignal):  # type: ignore[no-untyped-def]
    return lambda base: SplitSignalClient(base, transport=fake.transport())


@pytest.fixture(autouse=True)
def key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SPLITSIGNAL_API_KEY", SYNTHETIC_KEY)


def test_pass_text_and_stream(approved: Path) -> None:
    fake = FakeSplitSignal()
    code, rep = smoke.run(env=ENV, decisions=approved, stream=True, client_factory=factory(fake))
    assert code == 0 and rep["status"] == "pass"
    assert [c["mode"] for c in rep["calls"]] == ["text", "stream"]
    assert rep["calls"][0]["cost_source"] == "reported"
    assert "Hello" not in json.dumps(rep)
    assert SYNTHETIC_KEY not in json.dumps(rep)
    assert len(fake.requests) == 3


@pytest.mark.parametrize(
    ("drop", "reason"),
    [
        ("SPLITSIGNAL_BASE_URL", "blocked:splitsignal_base_url_missing"),
        ("SPLITSIGNAL_API_KEY", "blocked:splitsignal_api_key_missing"),
    ],
)
def test_missing_env_blocks_without_network(approved: Path, drop: str, reason: str) -> None:
    fake = FakeSplitSignal()
    env = {k: v for k, v in ENV.items() if k != drop}
    code, rep = smoke.run(env=env, decisions=approved, stream=False, client_factory=factory(fake))
    assert (code, rep["status"]) == (3, reason)
    assert fake.requests == []


def test_pending_approval_blocks_without_network(tmp_path: Path) -> None:
    p = tmp_path / "DECISIONS.md"
    p.write_text(
        "- SW-PREAPPROVAL-A3: PENDING\n"
        "To approve, change it to `- SW-PREAPPROVAL-A3: APPROVED <date>`.\n",
        encoding="utf-8",
    )
    fake = FakeSplitSignal()
    code, rep = smoke.run(env=ENV, decisions=p, stream=False, client_factory=factory(fake))
    assert (code, rep["status"]) == (3, "blocked:sw_preapproval_a3_not_approved")
    assert fake.requests == []


def test_unlisted_model_blocks(approved: Path) -> None:
    env = {**ENV, "SPLITSIGNAL_MODEL": "gemini/not-listed"}
    code, rep = smoke.run(
        env=env, decisions=approved, stream=False, client_factory=factory(FakeSplitSignal())
    )
    assert (code, rep["status"]) == (3, "blocked:model_not_listed")
    assert rep["listed_route_ids"] == ["mock/ok", "mock/quota", "mock/unavailable"]
    assert rep["calls"] == []


def test_unset_model_uses_default(approved: Path) -> None:
    env = {k: v for k, v in ENV.items() if k != "SPLITSIGNAL_MODEL"}
    code, rep = smoke.run(
        env=env, decisions=approved, stream=False, client_factory=factory(FakeSplitSignal())
    )
    assert rep["model_source"] == "default"
    assert rep["route_requested"] == "gemini/gemini-3.5-flash-lite"
    assert (code, rep["status"]) == (3, "blocked:model_not_listed")


def test_upstream_error_fails(approved: Path) -> None:
    env = {**ENV, "SPLITSIGNAL_MODEL": "mock/quota"}
    code, rep = smoke.run(
        env=env, decisions=approved, stream=False, client_factory=factory(FakeSplitSignal())
    )
    assert code == 1 and rep["status"] == "fail:text:quota_exhausted:quota_exhausted"
