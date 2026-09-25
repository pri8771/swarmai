"""Content-addressed artifact store with checksum verification."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from swarm.contracts.workspace import ArtifactRef


class ChecksumMismatchError(ValueError):
    pass


class ArtifactStore:
    """Durable-by-hash blob store. Worker temp files stay outside this store.

    Blobs live at ``{root}/{hash[:2]}/{hash}``. Metadata is mirrored to
    ``{root}/index.json`` so a new process (API restart) can resolve and reopen
    artifacts without relying on in-memory state.
    """

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self._meta: dict[str, ArtifactRef] = {}
        self._deleted: set[str] = set()
        self._index_path = self.root / "index.json"
        self._load_index()

    @staticmethod
    def content_hash(content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()

    def blob_path(self, content_hash: str) -> Path:
        return self.root / content_hash[:2] / content_hash

    def put(
        self,
        content: bytes,
        *,
        media_type: str,
        owner_scope: str,
        retention_class: str = "mission",
        expected_hash: str | None = None,
    ) -> ArtifactRef:
        digest = self.content_hash(content)
        if expected_hash is not None and expected_hash != digest:
            raise ChecksumMismatchError(
                f"expected={expected_hash} actual={digest}"
            )
        path = self.blob_path(digest)
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            # Write temp then rename so a crash mid-write cannot leave a partial
            # blob that later verifies as the content-addressed path.
            tmp = path.with_suffix(".partial")
            tmp.write_bytes(content)
            tmp.replace(path)
        else:
            # Verify existing blob still matches.
            if self.content_hash(path.read_bytes()) != digest:
                raise ChecksumMismatchError("corrupt_on_disk")
        ref = ArtifactRef(
            content_hash=digest,
            uri=f"file://{path}",
            media_type=media_type,
            byte_length=len(content),
            owner_scope=owner_scope,
            retention_class=retention_class,
        )
        self._meta[ref.id] = ref
        self._deleted.discard(ref.id)
        self._persist_index()
        return ref

    def get_bytes(self, artifact_id: str, *, allowed_scopes: set[str]) -> bytes:
        ref = self.resolve(artifact_id, allowed_scopes=allowed_scopes)
        return self.get_bytes_by_hash(ref.content_hash)

    def get_bytes_by_hash(self, content_hash: str) -> bytes:
        """Reopen a blob by content hash after process restart (no in-memory meta)."""
        path = self.blob_path(content_hash)
        if not path.is_file():
            raise FileNotFoundError(f"artifact_blob_missing:{content_hash}")
        data = path.read_bytes()
        if self.content_hash(data) != content_hash:
            raise ChecksumMismatchError("read_checksum_failed")
        return data

    def resolve(self, artifact_id: str, *, allowed_scopes: set[str]) -> ArtifactRef:
        if artifact_id in self._deleted:
            raise FileNotFoundError(f"artifact_deleted:{artifact_id}")
        ref = self._meta.get(artifact_id)
        if ref is None:
            # Cold start: index may still list the id after reload race.
            self._load_index()
            ref = self._meta.get(artifact_id)
        if ref is None:
            raise KeyError(artifact_id)
        if ref.owner_scope not in allowed_scopes and "*" not in allowed_scopes:
            raise PermissionError(f"artifact_scope_denied:{ref.owner_scope}")
        return ref

    def put_ref(self, ref: ArtifactRef) -> None:
        self._meta[ref.id] = ref
        self._deleted.discard(ref.id)
        self._persist_index()

    def delete(self, artifact_id: str, *, retention_ok: bool = False) -> None:
        ref = self._meta.get(artifact_id)
        if ref is None:
            return
        if ref.retention_class == "legal_hold" and not retention_ok:
            raise PermissionError("retention_blocks_delete")
        self._deleted.add(artifact_id)
        self._persist_index()

    def _load_index(self) -> None:
        if not self._index_path.is_file():
            return
        try:
            raw = json.loads(self._index_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, TypeError):
            return
        meta = raw.get("artifacts") or {}
        deleted = set(raw.get("deleted") or [])
        loaded: dict[str, ArtifactRef] = {}
        if isinstance(meta, dict):
            for key, val in meta.items():
                if not isinstance(val, dict):
                    continue
                try:
                    loaded[str(key)] = ArtifactRef.model_validate(val)
                except (TypeError, ValueError, KeyError):
                    continue
        self._meta = loaded
        self._deleted = {str(x) for x in deleted}

    def _persist_index(self) -> None:
        payload = {
            "schema_version": "1.0",
            "artifacts": {
                art_id: ref.model_dump(mode="json") for art_id, ref in self._meta.items()
            },
            "deleted": sorted(self._deleted),
        }
        tmp = self._index_path.with_suffix(".partial")
        tmp.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
        tmp.replace(self._index_path)
