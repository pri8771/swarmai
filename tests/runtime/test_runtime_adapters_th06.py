"""TH-06 runtime adapter qualification honesty."""

from __future__ import annotations

from pathlib import Path

from swarm.runtime.adapters.base import (
    REQUIRED_CAPABILITIES,
    CapabilityStatus,
    RuntimeAvailability,
)
from swarm.runtime.adapters.hermes import HermesRuntimeAdapter
from swarm.runtime.adapters.native import NativeRuntimeAdapter
from swarm.runtime.adapters.opencode import OpenCodeRuntimeAdapter, resolve_opencode_binary
from swarm.runtime.adapters.qualify import qualification_report


def test_required_capability_set_complete() -> None:
    assert "dispatch_events" in REQUIRED_CAPABILITIES
    assert "nested_delegation_accounting" in REQUIRED_CAPABILITIES
    assert len(REQUIRED_CAPABILITIES) == 8


def test_native_available_with_partial_capability_proof() -> None:
    q = NativeRuntimeAdapter().qualify()
    assert q.availability == RuntimeAvailability.AVAILABLE
    # R6: partial proofs do not claim full kernel mediation.
    assert q.kernel_mediation_proven is False
    assert q.config_alone_enforces_swarm_contracts is False
    by_cap = {c.capability: c for c in q.capabilities}
    assert by_cap["dispatch_events"].status == CapabilityStatus.AVAILABLE
    assert by_cap["nested_delegation_accounting"].status == CapabilityStatus.UNPROVEN


def test_hermes_unavailable_when_missing() -> None:
    q = HermesRuntimeAdapter().qualify()
    assert q.availability == RuntimeAvailability.UNAVAILABLE
    assert q.config_alone_enforces_swarm_contracts is False
    assert q.kernel_mediation_proven is False
    assert all(c.status == CapabilityStatus.UNAVAILABLE for c in q.capabilities)
    assert any("config" in b.lower() or "prompt" in b.lower() for b in q.blockers)


def test_opencode_missing_binary_is_unavailable(tmp_path: Path) -> None:
    q = OpenCodeRuntimeAdapter(binary=tmp_path / "missing").qualify()
    assert q.availability == RuntimeAvailability.UNAVAILABLE
    assert q.config_alone_enforces_swarm_contracts is False
    assert all(c.status == CapabilityStatus.UNAVAILABLE for c in q.capabilities)
    assert resolve_opencode_binary(explicit=str(tmp_path / "missing")) is None


def test_opencode_discovered_but_unqualified(tmp_path: Path) -> None:
    fake = tmp_path / "opencode"
    fake.write_text("#!/bin/sh\necho 'opencode v2.0.15'\n", encoding="utf-8")
    fake.chmod(0o755)

    def _probe(_binary: Path, *, timeout_s: float = 8.0) -> str:
        return "v2.0.15"

    import swarm.runtime.adapters.opencode as oc

    original = oc.probe_opencode_version
    oc.probe_opencode_version = _probe  # type: ignore[assignment]
    try:
        q = OpenCodeRuntimeAdapter(binary=fake).qualify()
    finally:
        oc.probe_opencode_version = original  # type: ignore[assignment]

    assert q.availability == RuntimeAvailability.DISCOVERED_UNQUALIFIED
    assert q.config_alone_enforces_swarm_contracts is False
    assert q.kernel_mediation_proven is False
    assert all(c.status == CapabilityStatus.UNAVAILABLE for c in q.capabilities)
    assert any("do not enforce" in b.lower() for b in q.blockers)


def test_qualification_report_admission_policy() -> None:
    report = qualification_report(
        [
            NativeRuntimeAdapter(),
            OpenCodeRuntimeAdapter(binary=Path("/nonexistent/opencode")),
            HermesRuntimeAdapter(),
        ]
    )
    assert report["config_alone_enforces_swarm_contracts"] is False
    assert report["hostname_public"] == "swarm.splitsignal.ai"
    # Native is available/partial but not fully mission-admissible until mandatory caps proven.
    assert "native" not in report["policy"]["mission_admissible_runtimes"]
    assert "opencode" not in report["policy"]["mission_admissible_runtimes"]
    assert "hermes" not in report["policy"]["mission_admissible_runtimes"]
    assert "hermes" in report["summary"]["unavailable"]
    native = next(r for r in report["runtimes"] if r["runtime_id"] == "native")
    assert native["mission_admission"] == "partial"
