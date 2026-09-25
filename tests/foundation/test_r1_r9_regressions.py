"""Protected regressions for Cursor review findings R1–R9.

Converted from ``docs/reviews/CURSOR_REVIEW_2026-09-25/CURSOR_REVIEW_PROBES.py``.
Isolated temporary state only — no live providers.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from swarm.api.app import create_app
from swarm.contracts.fixtures import sample_mission
from swarm.evals.dataset import load_dataset
from swarm.evals.graders import grade_case
from swarm.evals.synthetic_harness import LiveGateBlocked, LiveGrant, run_synthetic_harness
from swarm.runtime.adapters.native import NativeRuntimeAdapter
from swarm.runtime.adapters.qualify import qualification_report
from swarm.tools.sandbox_runner import IsolatedCodeRunner
from swarm.workspace.artifacts import ArtifactStore

ROOT = Path(__file__).resolve().parents[2]
STARTER = ROOT / "benchmarks" / "starter.jsonl"


@pytest.fixture(autouse=True)
def _clear_swarm_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in list(os.environ):
        if key.startswith("SWARM_"):
            monkeypatch.delenv(key, raising=False)


def _app(path: Path) -> TestClient:
    app = create_app(
        repo_root=path,
        seed_loopback_token="review-only-token",
        install_project_id="proj_review",
        db_reachable=False,
    )
    return TestClient(app)


HEADERS = {"Authorization": "Bearer review-only-token"}


def test_r1_cannot_forge_acceptance_with_check_override(tmp_path: Path) -> None:
    client = _app(tmp_path / "server")
    mission = sample_mission().model_copy(update={"id": "msn_r1", "project_id": "proj_review"})
    created = client.post(
        "/v1/missions",
        headers=HEADERS,
        json={
            "mission": mission.model_dump(mode="json"),
            "task_family": "extract",
            "required_checks": {"count": 99},
        },
    )
    assert created.status_code == 200, created.text
    review = client.post(
        "/v1/missions/msn_r1/review",
        headers=HEADERS,
        json={
            "produced": {"checks": {"count": 1}},
            "required_checks": {"count": 1},
        },
    )
    body = review.json()
    assert review.status_code in {200, 400, 403, 409}
    assert body.get("accepted") is not True
    mission_status = (body.get("mission") or {}).get("status") or body.get("mission_status")
    if mission_status:
        assert mission_status != "completed"


def test_r2_workers_survive_app_reconstruction(tmp_path: Path) -> None:
    root = tmp_path / "server"
    client = _app(root)
    enrollment = client.post(
        "/v1/workers/enroll",
        headers=HEADERS,
        json={"project_id": "proj_review"},
    )
    assert enrollment.status_code == 200, enrollment.text
    enrolled = enrollment.json()
    before = len(client.get("/v1/workers", headers=HEADERS).json()["workers"])
    assert before == 1
    cold = _app(root)
    heartbeat = cold.post(
        "/v1/workers/heartbeat",
        headers=HEADERS,
        json={
            "worker_id": enrolled["worker"]["worker_id"],
            "generation": enrolled["worker"]["lease_generation"],
            "token": enrolled["membership_token"],
        },
    )
    assert heartbeat.status_code == 200, heartbeat.text
    after = len(cold.get("/v1/workers", headers=HEADERS).json()["workers"])
    assert after == 1


def test_r3_artifact_idempotency_and_multi_writer(tmp_path: Path) -> None:
    root = tmp_path / "server"
    client = _app(root)
    mission = sample_mission().model_copy(update={"id": "msn_r3", "project_id": "proj_review"})
    assert (
        client.post(
            "/v1/missions",
            headers=HEADERS,
            json={"mission": mission.model_dump(mode="json"), "task_family": "extract"},
        ).status_code
        == 200
    )
    replay_headers = {**HEADERS, "Idempotency-Key": "artifact-review-replay"}
    payload = {"kind": "result", "content_text": "review payload"}
    first = client.post("/v1/missions/msn_r3/artifacts", headers=replay_headers, json=payload)
    assert first.status_code == 200, first.text
    first_id = first.json()["artifact"]["artifact_id"]
    cold = _app(root)
    replay = cold.post("/v1/missions/msn_r3/artifacts", headers=replay_headers, json=payload)
    assert replay.status_code == 200, replay.text
    assert replay.json()["artifact"]["artifact_id"] == first_id
    assert (
        cold.get(f"/v1/missions/msn_r3/artifacts/{first_id}/content", headers=HEADERS).status_code
        == 200
    )

    cas = tmp_path / "shared-cas"
    a = ArtifactStore(cas)
    b = ArtifactStore(cas)
    refa = a.put(b"A", media_type="text/plain", owner_scope="p")
    refb = b.put(b"B", media_type="text/plain", owner_scope="p")
    reloaded = ArtifactStore(cas)
    assert refa.id in reloaded._meta
    assert refb.id in reloaded._meta
    assert len(reloaded._meta) >= 2


def test_r4_deleted_artifact_content_not_served(tmp_path: Path) -> None:
    root = tmp_path / "server"
    client = _app(root)
    mission = sample_mission().model_copy(update={"id": "msn_r4", "project_id": "proj_review"})
    assert (
        client.post(
            "/v1/missions",
            headers=HEADERS,
            json={"mission": mission.model_dump(mode="json"), "task_family": "extract"},
        ).status_code
        == 200
    )
    published = client.post(
        "/v1/missions/msn_r4/artifacts",
        headers=HEADERS,
        json={"kind": "result", "content_text": "to-delete"},
    )
    assert published.status_code == 200
    art_id = published.json()["artifact"]["artifact_id"]
    client.app.state.store.artifact_store().delete(art_id)
    deleted_read = client.get(
        f"/v1/missions/msn_r4/artifacts/{art_id}/content", headers=HEADERS
    )
    assert deleted_read.status_code == 404


def test_r5_forged_stdout_and_sandbox_escape_fail() -> None:
    cases = load_dataset(STARTER)
    case = next(c for c in cases if c.grader["kind"] == "python_unit")
    grade = grade_case(case, 'print(\'{"ok": true}\')\nraise SystemExit(0)\n')
    assert grade.correct is False

    import tempfile

    with tempfile.TemporaryDirectory(prefix="swarm-r5-") as tmp:
        root = Path(tmp)
        marker = root / "outside-sandbox-marker.txt"
        marker.write_text("review-only-marker")
        sandbox = root / "sandbox"
        sandbox.mkdir()
        (sandbox / "probe.py").write_text(
            "from pathlib import Path\nprint(Path(" + repr(str(marker)) + ").read_text())\n"
        )
        result = IsolatedCodeRunner(sandbox, network=False).run_python("probe.py")
        assert result.stdout.strip() != "review-only-marker"


def test_r6_native_admission_requires_proven_capabilities() -> None:
    q = NativeRuntimeAdapter().qualify()
    assert q.kernel_mediation_proven is False
    report = qualification_report()
    # Native may be discoverable but not fully mission-admissible until mandatory caps proven.
    policy = report["policy"]
    if "native" in policy["mission_admissible_runtimes"]:
        native = next(r for r in report["runtimes"] if r["runtime_id"] == "native")
        assert native.get("kernel_mediation_proven") is False or native.get(
            "mission_admission"
        ) in {"partial", "fixture_only", "not_admitted"}


def test_r8_zero_dollar_grant_and_reproducible_hash(tmp_path: Path) -> None:
    grant = LiveGrant(
        grant_id="review",
        routes=("verified_free_route",),
        budget_usd=0.0,
        purpose="zero-spend-eval",
        approved=True,
        free_routes_only=True,
        max_calls=2,
        max_tokens=1024,
        max_wall_seconds=30,
    )
    grant.assert_usable()
    with pytest.raises(LiveGateBlocked, match="not enabled|fake|dispatch"):
        run_synthetic_harness(
            dataset_path=STARTER,
            mode="live",
            live_grant=grant,
            max_cases=1,
        )
    report = run_synthetic_harness(
        dataset_path=STARTER, max_cases=1, out_dir=tmp_path / "reports"
    )
    saved = json.loads((tmp_path / "reports" / "latest.json").read_text())
    claimed = saved["report_hash"]
    saved["report_hash"] = None
    recomputed = hashlib.sha256(
        json.dumps(saved, sort_keys=True, default=str).encode()
    ).hexdigest()
    assert recomputed == claimed
    assert report.report_hash == claimed
