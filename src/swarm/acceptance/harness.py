"""V2.0 acceptance campaign harness — gate-separated runs.

Deterministic probes may execute. Live requires an operator-supplied approved
LiveGrant (never invented). Host and elapsed gates remain external/not_started
unless explicitly configured without simulating wall-clock time.

When an approved grant is present, the harness distinguishes missing
authorization from missing live implementation, and exercises fake-upstream
wiring first. It never fabricates grants or performs unauthorized live calls.
"""

from __future__ import annotations

import hashlib
import json
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from swarm.acceptance.freeze import AcceptanceFreeze, ScenarioSpec, load_freeze
from swarm.acceptance.probes import PROBES, ProbeResult
from swarm.contracts.common import new_id, utc_now
from swarm.contracts.fixtures import sample_route
from swarm.contracts.provider import InferenceRequest
from swarm.evals.synthetic_harness import LiveGateBlocked, LiveGrant
from swarm.fakes.broker import FakeInferenceBroker
from swarm.fakes.provider import FakeProviderAdapter
from swarm.mission.protected_verify import protected_review
from swarm.workspace.artifacts import ArtifactStore

HARNESS_VERSION = "v20-acceptance-campaign-v1"

ScenarioStatus = Literal[
    "pass_deterministic",
    "scaffold_ready_not_integrated",
    "pass_deterministic_gate_only",
    "blocked_live_grant",
    "blocked_missing_implementation",
    "pass_fake_upstream_wiring",
    "blocked_host_gate",
    "blocked_elapsed_window",
    "fail",
    "not_run",
]


@dataclass
class ScenarioResult:
    scenario_id: str
    title: str
    primary_gate: str
    status: str
    ok: bool
    version_accepted: bool
    detail: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "title": self.title,
            "primary_gate": self.primary_gate,
            "status": self.status,
            "ok": self.ok,
            "version_accepted": self.version_accepted,
            "detail": self.detail,
        }


@dataclass
class CampaignReport:
    run_id: str
    harness_version: str
    freeze_id: str
    freeze_hash: str
    public_hostname: str
    mode: str
    generated_at: str
    results: list[ScenarioResult] = field(default_factory=list)
    gate_summary: dict[str, Any] = field(default_factory=dict)
    version_claim: dict[str, Any] = field(default_factory=dict)
    live_gate: dict[str, Any] = field(default_factory=dict)
    spend_usd: float = 0.0
    report_hash: str | None = None
    note: str = (
        "Acceptance campaign harness: scenarios frozen before run; "
        "deterministic ≠ live ≠ host ≠ elapsed; versions not accepted by harness"
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "harness_version": self.harness_version,
            "freeze_id": self.freeze_id,
            "freeze_hash": self.freeze_hash,
            "public_hostname": self.public_hostname,
            "mode": self.mode,
            "generated_at": self.generated_at,
            "results": [r.to_dict() for r in self.results],
            "gate_summary": self.gate_summary,
            "version_claim": self.version_claim,
            "live_gate": self.live_gate,
            "spend_usd": self.spend_usd,
            "allow_paid": False,
            "report_hash": self.report_hash,
            "note": self.note,
            "any_version_accepted": False,
        }


def _live_meta(grant: LiveGrant | None) -> dict[str, Any]:
    if grant is None:
        return {
            "grant_present": False,
            "grant_approved": False,
            "invented": False,
            "blocked": True,
            "authorization": "missing",
            "reason": "no_operator_live_grant",
        }
    return {
        "grant_present": True,
        "grant_approved": grant.approved,
        "grant_id": grant.grant_id,
        "routes": list(grant.routes),
        "budget_usd": grant.budget_usd,
        "free_routes_only": grant.free_routes_only,
        "invented": False,
        "blocked": not grant.approved,
        "authorization": "approved" if grant.approved else "not_approved",
        "reason": "operator_grant" if grant.approved else "grant_not_approved",
    }


def _run_deterministic(spec: ScenarioSpec, work: Path) -> ProbeResult:
    probe_name = spec.deterministic_probe
    if not probe_name or probe_name not in PROBES:
        return ProbeResult(
            False,
            "fail",
            {"error": f"unknown_or_missing_probe:{probe_name}"},
        )
    return PROBES[probe_name](work)


def run_fake_upstream_wiring(work: Path) -> dict[str, Any]:
    """Exercise authorized-route mechanics against fake upstreams (no spend).

    This is the required first step when an approved LiveGrant is present.
    It does not perform live provider calls.
    """
    adapter = FakeProviderAdapter([sample_route()])
    broker = FakeInferenceBroker(adapter)
    request = InferenceRequest(
        project_id="proj_accept_fake_upstream",
        attempt_id=new_id("att_"),
        route_id="rt_fake_alpha",
        purpose="v20_campaign_fake_upstream_wiring",
        messages=[{"role": "user", "content": "extract contacts"}],
        estimated_input_tokens=12,
    )

    async def _run() -> dict[str, Any]:
        routes = await broker.assess(request)
        if not routes:
            return {"ok": False, "error": "no_routes_assessed"}
        ticket = await broker.reserve(request, routes[0])
        receipt = await broker.invoke(ticket)
        broker.assert_all_calls_accounted()
        cas = ArtifactStore(work / "cas")
        raw = (
            b"Fake-upstream campaign wiring extract.\n"
            b"Contact fake-agent@example.com and ops@example.com.\n"
        )
        art = cas.put(raw, media_type="text/plain", owner_scope="proj_accept_fake_upstream")
        decision = protected_review(
            task_family="extract",
            required_checks={"email_count": 2, "artifact_sha256": art.content_hash},
            artifact_id=art.id,
            artifact_bytes=raw,
            content_hash=art.content_hash,
            worker_produced={"checks": {"email_count": 999, "artifact_sha256": "deadbeef"}},
        )
        return {
            "ok": bool(decision.accepted),
            "route_id": receipt.actual_route,
            "model_calls": broker.request_count,
            "artifact_id": art.id,
            "protected_accepted": decision.accepted,
            "spend_usd": 0.0,
            "live_dispatch": False,
            "solver": "fake_inference_broker",
        }

    import asyncio

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(_run())
    # Nested event loop (rare in harness): run in a fresh threadless path via
    # a dedicated loop so pytest-asyncio hosts still work.
    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(lambda: asyncio.run(_run())).result()


def _also_gate_statuses(
    spec: ScenarioSpec,
    *,
    live_grant: LiveGrant | None,
    host_qualified: bool,
    elapsed_window_started: bool,
) -> dict[str, dict[str, Any]]:
    """Secondary gate coverage — never satisfied by inventing grants or faking time."""
    out: dict[str, dict[str, Any]] = {}
    for gate in spec.also_gates:
        if gate == "live":
            meta = _live_meta(live_grant)
            if meta["blocked"]:
                status = "blocked_live_grant"
            else:
                # Grant present/approved: also-gate is authorized but live
                # implementation is a separate primary-path concern.
                status = "grant_approved_implementation_separate"
            out[gate] = {
                "status": status,
                **meta,
            }
        elif gate == "host":
            out[gate] = {
                "status": "ready" if host_qualified else "blocked_host_gate",
                "host_qualified": host_qualified,
                "policy": "two_local_processes_not_two_host",
            }
        elif gate == "elapsed":
            out[gate] = {
                "status": (
                    "window_external" if elapsed_window_started else "blocked_elapsed_window"
                ),
                "simulate_elapsed_time": False,
                "window_started": elapsed_window_started,
            }
        elif gate == "deterministic":
            out[gate] = {"status": "covered_by_primary_or_side_probe"}
    return out


def _evaluate_live_primary(
    spec: ScenarioSpec,
    *,
    work: Path,
    live_grant: LiveGrant | None,
    also: dict[str, dict[str, Any]],
    live_dispatcher: Any | None = None,
) -> ScenarioResult:
    """Evaluate a live-primary scenario with auth vs implementation separation."""
    meta = _live_meta(live_grant)
    det = _run_deterministic(spec, work)
    detail: dict[str, Any] = {
        "live_gate": meta,
        "deterministic_side": det.to_dict(),
        "also_gates": also,
        "spend_usd": 0.0,
    }

    # Missing / unapproved authorization → blocked_live_grant only.
    if live_grant is None or not live_grant.approved:
        detail["note"] = "Live path blocked: missing or unapproved operator LiveGrant"
        detail["blocker_class"] = "authorization"
        return ScenarioResult(
            scenario_id=spec.id,
            title=spec.title,
            primary_gate="live",
            status="blocked_live_grant",
            ok=True,
            version_accepted=False,
            detail=detail,
        )

    try:
        live_grant.assert_usable()
    except LiveGateBlocked as exc:
        detail["error"] = str(exc)
        detail["blocker_class"] = "authorization"
        detail["note"] = "Grant present but not usable"
        return ScenarioResult(
            scenario_id=spec.id,
            title=spec.title,
            primary_gate="live",
            status="blocked_live_grant",
            ok=True,
            version_accepted=False,
            detail=detail,
        )

    # Authorization OK — fake-upstream wiring first (no live spend).
    wiring = run_fake_upstream_wiring(work / "fake_upstream")
    detail["fake_upstream_wiring"] = wiring
    detail["blocker_class"] = "implementation"
    detail["authorization"] = "approved"

    if not wiring.get("ok"):
        detail["note"] = "Approved grant acknowledged; fake-upstream wiring failed"
        return ScenarioResult(
            scenario_id=spec.id,
            title=spec.title,
            primary_gate="live",
            status="fail",
            ok=False,
            version_accepted=False,
            detail=detail,
        )

    # Optional explicit live dispatcher (qualification runner). Never invented.
    if live_dispatcher is not None:
        try:
            live_result = live_dispatcher(live_grant, work)
        except LiveGateBlocked as exc:
            detail["live_dispatch_error"] = str(exc)
            detail["note"] = (
                "Approved grant + fake-upstream wiring OK; live dispatcher blocked"
            )
            return ScenarioResult(
                scenario_id=spec.id,
                title=spec.title,
                primary_gate="live",
                status="blocked_missing_implementation",
                ok=True,
                version_accepted=False,
                detail=detail,
            )
        detail["live_dispatch"] = live_result
        detail["note"] = "Scoped live dispatcher consumed approved grant"
        return ScenarioResult(
            scenario_id=spec.id,
            title=spec.title,
            primary_gate="live",
            status=str(live_result.get("status") or "pass_fake_upstream_wiring"),
            ok=bool(live_result.get("ok", True)),
            version_accepted=False,
            detail=detail,
        )

    # Default: wiring proven; live adapter not enabled — not an auth block.
    detail["note"] = (
        "Approved grant acknowledged; fake-upstream wiring exercised; "
        "live adapter dispatch not enabled (missing implementation, not missing auth)"
    )
    detail["live_dispatch"] = False
    return ScenarioResult(
        scenario_id=spec.id,
        title=spec.title,
        primary_gate="live",
        status="blocked_missing_implementation",
        ok=True,
        version_accepted=False,
        detail=detail,
    )


def _evaluate_scenario(
    spec: ScenarioSpec,
    *,
    work: Path,
    live_grant: LiveGrant | None,
    host_qualified: bool,
    elapsed_window_started: bool,
    gates_filter: set[str] | None,
    live_dispatcher: Any | None = None,
) -> ScenarioResult:
    gate = spec.primary_gate
    also = _also_gate_statuses(
        spec,
        live_grant=live_grant,
        host_qualified=host_qualified,
        elapsed_window_started=elapsed_window_started,
    )

    if gates_filter is not None and gate not in gates_filter:
        return ScenarioResult(
            scenario_id=spec.id,
            title=spec.title,
            primary_gate=gate,
            status="not_run",
            ok=True,
            version_accepted=False,
            detail={
                "reason": "filtered_out_by_gate_selector",
                "gate": gate,
                "also_gates": also,
            },
        )

    if gate == "live":
        return _evaluate_live_primary(
            spec,
            work=work,
            live_grant=live_grant,
            also=also,
            live_dispatcher=live_dispatcher,
        )

    if gate == "host":
        det = _run_deterministic(spec, work)
        if not host_qualified:
            return ScenarioResult(
                scenario_id=spec.id,
                title=spec.title,
                primary_gate=gate,
                status="blocked_host_gate",
                ok=True,
                version_accepted=False,
                detail={
                    "host_qualified": False,
                    "policy": "two_local_processes_not_two_host",
                    "deterministic_side": det.to_dict(),
                    "also_gates": also,
                },
            )
        return ScenarioResult(
            scenario_id=spec.id,
            title=spec.title,
            primary_gate=gate,
            status=det.status,
            ok=det.ok,
            version_accepted=False,
            detail={"host_qualified": True, "probe": det.to_dict(), "also_gates": also},
        )

    if gate == "elapsed":
        return ScenarioResult(
            scenario_id=spec.id,
            title=spec.title,
            primary_gate=gate,
            status="blocked_elapsed_window" if not elapsed_window_started else "not_run",
            ok=True,
            version_accepted=False,
            detail={
                "simulate_elapsed_time": False,
                "window_started": elapsed_window_started,
                "also_gates": also,
                "note": "Predeclared observation window required; do not simulate",
            },
        )

    det = _run_deterministic(spec, work)
    detail = det.to_dict()
    detail["also_gates"] = also
    return ScenarioResult(
        scenario_id=spec.id,
        title=spec.title,
        primary_gate=gate,
        status=det.status if det.ok else "fail",
        ok=det.ok,
        version_accepted=False,
        detail=detail,
    )


def run_acceptance_campaign(
    *,
    freeze: AcceptanceFreeze | None = None,
    freeze_path: Path | None = None,
    live_grant: LiveGrant | None = None,
    host_qualified: bool = False,
    elapsed_window_started: bool = False,
    gates: list[str] | None = None,
    out_dir: Path | None = None,
    work_dir: Path | None = None,
    invent_live_grant: bool = False,
    live_dispatcher: Any | None = None,
) -> CampaignReport:
    """Run frozen §10 scenarios with explicit gate separation.

    ``invent_live_grant`` is always refused — present only to hard-fail misuse.
    ``live_dispatcher`` is an optional qualification runner that may consume a
    scoped approved grant; the default path only exercises fake-upstream wiring.
    """
    if invent_live_grant:
        raise LiveGateBlocked(
            "live_qualification_blocked: invent_live_grant is forbidden; "
            "supply an operator-approved LiveGrant or leave live blocked"
        )
    if live_grant is not None and getattr(live_grant, "_harness_invented", False):
        raise LiveGateBlocked("live_qualification_blocked: harness-invented grant refused")

    catalog = freeze or load_freeze(freeze_path)
    gates_filter = set(gates) if gates else None
    run_id = new_id("v20camp_")
    results: list[ScenarioResult] = []

    with tempfile.TemporaryDirectory(prefix="v20_accept_") as tmp:
        work = Path(work_dir) if work_dir else Path(tmp)
        work.mkdir(parents=True, exist_ok=True)
        for spec in catalog.scenarios:
            scenario_work = work / spec.id
            scenario_work.mkdir(parents=True, exist_ok=True)
            results.append(
                _evaluate_scenario(
                    spec,
                    work=scenario_work,
                    live_grant=live_grant,
                    host_qualified=host_qualified,
                    elapsed_window_started=elapsed_window_started,
                    gates_filter=gates_filter,
                    live_dispatcher=live_dispatcher,
                )
            )

    by_gate: dict[str, dict[str, int]] = {}
    for r in results:
        bucket = by_gate.setdefault(r.primary_gate, {"total": 0, "ok": 0, "fail": 0, "blocked": 0})
        bucket["total"] += 1
        if r.status.startswith("blocked_"):
            bucket["blocked"] += 1
        elif r.ok:
            bucket["ok"] += 1
        else:
            bucket["fail"] += 1

    report = CampaignReport(
        run_id=run_id,
        harness_version=HARNESS_VERSION,
        freeze_id=catalog.freeze_id,
        freeze_hash=catalog.content_hash,
        public_hostname=catalog.public_hostname,
        mode="campaign",
        generated_at=utc_now().isoformat(),
        results=results,
        gate_summary=by_gate,
        version_claim={
            "any_version_accepted": False,
            "policy": catalog.version_claim_policy,
            "versions": {
                ver: {
                    "accepted": False,
                    "required_scenarios": list(meta.get("required_scenarios") or []),
                }
                for ver, meta in catalog.version_matrices.items()
            },
        },
        live_gate=_live_meta(live_grant),
        spend_usd=0.0,
    )
    payload = report.to_dict()
    payload["report_hash"] = None
    report.report_hash = hashlib.sha256(
        json.dumps(payload, sort_keys=True, default=str).encode()
    ).hexdigest()
    payload["report_hash"] = report.report_hash

    if out_dir is not None:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        text = json.dumps(payload, indent=2, default=str) + "\n"
        (out_dir / f"{report.run_id}.json").write_text(text, encoding="utf-8")
        (out_dir / "latest.json").write_text(text, encoding="utf-8")
    return report
