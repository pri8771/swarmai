"""TH-04: durable CAS artifacts reopen with identical hash after API restart."""

from __future__ import annotations

from pathlib import Path

import pytest

from swarm.api.store import ProductStore
from swarm.contracts.enums import MissionStatus
from swarm.contracts.fixtures import sample_mission
from swarm.workspace.artifacts import ArtifactStore, ChecksumMismatchError


def test_artifact_store_survives_new_process(tmp_path: Path) -> None:
    root = tmp_path / "cas"
    first = ArtifactStore(root)
    content = b"TH-04 durable blob payload\n"
    ref = first.put(
        content,
        media_type="text/plain",
        owner_scope="proj_th04",
        retention_class="mission",
    )
    assert first.blob_path(ref.content_hash).is_file()
    assert (root / "index.json").is_file()

    # Simulate API container restart: new ArtifactStore instance, same volume root.
    second = ArtifactStore(root)
    reopened = second.resolve(ref.id, allowed_scopes={"*"})
    assert reopened.content_hash == ref.content_hash
    assert second.get_bytes_by_hash(ref.content_hash) == content
    assert second.get_bytes(ref.id, allowed_scopes={"proj_th04"}) == content


def test_artifact_store_rejects_corrupt_hash_read(tmp_path: Path) -> None:
    store = ArtifactStore(tmp_path / "cas")
    content = b"ok"
    ref = store.put(content, media_type="text/plain", owner_scope="s", retention_class="mission")
    path = store.blob_path(ref.content_hash)
    path.write_bytes(b"tampered")
    with pytest.raises(ChecksumMismatchError):
        store.get_bytes_by_hash(ref.content_hash)


def test_publish_mission_artifact_lists_content_hash(tmp_path: Path) -> None:
    store = ProductStore(repo_root=tmp_path, db_reachable=False)
    mission = sample_mission().model_copy(
        update={
            "id": "msn_th04_test",
            "project_id": "proj_th04_test",
            "status": MissionStatus.RUNNING,
            "objective": "TH-04 unit publish",
        }
    )
    store.controller.missions[mission.id] = mission
    store._persist_mission_record(mission, source="test")

    published = store.publish_mission_artifact(
        mission.id,
        kind="result",
        content=b"hello durable world\n",
        media_type="text/plain",
        owner_scope=mission.project_id,
        summary="unit artifact",
        actor="tester",
    )
    assert published["content_hash"]
    assert len(published["content_hash"]) == 64

    listed = store.mission_artifacts(mission.id)
    matching = [a for a in listed if a.get("artifact_id") == published["artifact_id"]]
    assert matching
    assert matching[0].get("content_hash") == published["content_hash"]

    # New ProductStore instance shares durable repo_root (restart simulation).
    cold = ProductStore(repo_root=tmp_path, db_reachable=False)
    cold.controller.missions[mission.id] = mission
    data, meta = cold.read_mission_artifact_bytes(mission.id, published["artifact_id"])
    assert data == b"hello durable world\n"
    assert meta.get("content_hash") == published["content_hash"]
