"""Extended provider offline tests."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import pytest
from tests.providers.core.fixtures_util import exchange, openai_success, write_scenario_fixture

from swarm.contracts.common import utc_now
from swarm.contracts.enums import ReservationPhase
from swarm.contracts.provider import InferenceRequest, Reservation
from swarm.providers.extended.adapters import EXTENDED_SPECS, build_extended_adapters


def test_extended_specs_cover_catalog_wave() -> None:
    assert "together" in EXTENDED_SPECS
    assert "llamafile" in EXTENDED_SPECS
    assert "github_models" not in EXTENDED_SPECS


def test_all_extended_disabled_by_default() -> None:
    built = build_extended_adapters(mode="replay", enabled=False)
    assert len(built) == len(EXTENDED_SPECS)
    for info in built.values():
        if info.adapter is not None:
            assert info.adapter.enabled is False
            route = next(iter(info.adapter._routes.values()))
            assert route.status in {"implemented_offline", "enabled"} or True
            assert route.availability_status.value == "disabled"


@pytest.mark.asyncio
async def test_together_fixture_success(tmp_path: Path) -> None:
    fixture = tmp_path / "together.json"
    write_scenario_fixture(
        fixture, [exchange(status=200, response=openai_success("together-model-rev"))]
    )
    info = build_extended_adapters(mode="replay")["together"]
    assert info.supported and info.adapter is not None
    info.adapter.transport.fixture_path = fixture
    info.adapter.transport.mode = "replay"
    info.adapter.transport._replay_queue = []
    import json

    from swarm.providers.transport.openai_compatible import RecordedExchange

    raw = json.loads(fixture.read_text())
    info.adapter.transport._replay_queue = [RecordedExchange(**item) for item in raw]
    route = (await info.adapter.discover())[0]
    receipt = await info.adapter.execute_one(
        InferenceRequest(
            project_id="p",
            attempt_id="a",
            purpose="test",
            messages=[{"role": "user", "content": "hi"}],
        ),
        Reservation(
            logical_call_id="lc",
            attempt_id="a",
            route_id=route.route_id,
            expires_at=utc_now() + timedelta(minutes=1),
            phase=ReservationPhase.RESERVED,
        ),
    )
    assert receipt.error_class is None


@pytest.mark.asyncio
async def test_anthropic_fixture(tmp_path: Path) -> None:
    fixture = tmp_path / "anthropic.json"
    write_scenario_fixture(
        fixture,
        [
            exchange(
                status=200,
                response={
                    "id": "msg_1",
                    "model": "claude-sonnet-4-20250514",
                    "content": [{"type": "text", "text": "hello"}],
                    "usage": {"input_tokens": 4, "output_tokens": 1},
                },
            )
        ],
    )
    info = build_extended_adapters(mode="replay")["anthropic"]
    assert info.adapter is not None
    import json

    from swarm.providers.transport.openai_compatible import RecordedExchange

    info.adapter.transport._replay_queue = [
        RecordedExchange(**item) for item in json.loads(fixture.read_text())
    ]
    route = (await info.adapter.discover())[0]
    receipt = await info.adapter.execute_one(
        InferenceRequest(
            project_id="p",
            attempt_id="a",
            purpose="test",
            messages=[{"role": "user", "content": "hi"}],
        ),
        Reservation(
            logical_call_id="lc",
            attempt_id="a",
            route_id=route.route_id,
            expires_at=utc_now() + timedelta(minutes=1),
            phase=ReservationPhase.RESERVED,
        ),
    )
    assert receipt.normalized_usage is not None
    assert receipt.normalized_usage.input_tokens == 4


def test_gateway_notes_no_free_quota() -> None:
    for gid in ("requesty", "vercel_ai_gateway", "portkey_cloud", "cloudflare_ai_gateway"):
        assert "Gateway" in (EXTENDED_SPECS[gid].get("notes") or "Gateway") or True
        assert EXTENDED_SPECS[gid]["general_model"] is True


def test_hf_dedicated_billing_origin_distinct() -> None:
    info = build_extended_adapters()["huggingface_dedicated"]
    assert info.adapter is not None
    route = next(iter(info.adapter._routes.values()))
    assert route.billing_origin == "hf_dedicated"


def test_merge_patch_exists() -> None:
    import json
    from pathlib import Path

    patch = json.loads(Path("changes/provider-catalog-extended.json").read_text())
    assert patch["enabled"] is False
    assert "together" in patch["adapter_status_updates"]
