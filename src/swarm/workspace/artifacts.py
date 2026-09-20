"""Content-addressed artifact store with checksum verification."""

from __future__ import annotations

import hashlib
from pathlib import Path

from swarm.contracts.workspace import ArtifactRef


class ChecksumMismatchError(ValueError):
    pass


class ArtifactStore:
    """Durable-by-hash blob store. Worker temp files stay outside this store."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self._meta: dict[str, ArtifactRef] = {}
        self._deleted: set[str] = set()

    @staticmethod
    def content_hash(content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()

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
        path = self.root / digest[:2] / digest
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_bytes(content)
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
        return ref

    def get_bytes(self, artifact_id: str, *, allowed_scopes: set[str]) -> bytes:
        ref = self.resolve(artifact_id, allowed_scopes=allowed_scopes)
        path = Path(ref.uri.removeprefix("file://"))
        data = path.read_bytes()
        if self.content_hash(data) != ref.content_hash:
            raise ChecksumMismatchError("read_checksum_failed")
        return data

    def resolve(self, artifact_id: str, *, allowed_scopes: set[str]) -> ArtifactRef:
        if artifact_id in self._deleted:
            raise FileNotFoundError(f"artifact_deleted:{artifact_id}")
        ref = self._meta.get(artifact_id)
        if ref is None:
            raise KeyError(artifact_id)
        if ref.owner_scope not in allowed_scopes and "*" not in allowed_scopes:
            raise PermissionError(f"artifact_scope_denied:{ref.owner_scope}")
        return ref

    def put_ref(self, ref: ArtifactRef) -> None:
        self._meta[ref.id] = ref
        self._deleted.discard(ref.id)

    def delete(self, artifact_id: str, *, retention_ok: bool = False) -> None:
        ref = self._meta.get(artifact_id)
        if ref is None:
            return
        if ref.retention_class == "legal_hold" and not retention_ok:
            raise PermissionError("retention_blocks_delete")
        self._deleted.add(artifact_id)
