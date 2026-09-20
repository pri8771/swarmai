"""SharedWorkspace — Workspace protocol implementation (offline text-only)."""

from __future__ import annotations

from pathlib import Path

from swarm.contracts.mission import TaskSpec
from swarm.contracts.workspace import ArtifactRef, ContextBundle, EventEnvelope, Finding
from swarm.workspace.artifacts import ArtifactStore
from swarm.workspace.context import ContextAssembler, ContextBudget
from swarm.workspace.events import EventBus
from swarm.workspace.findings import FindingStore


class SharedWorkspace:
    """In-process workspace. PostgreSQL repos remain authoritative for P02 persistence."""

    def __init__(
        self,
        artifact_root: Path,
        *,
        text_only: bool = True,
        default_scopes: set[str] | None = None,
    ) -> None:
        self.artifacts = ArtifactStore(artifact_root)
        self.findings = FindingStore()
        self.events = EventBus()
        self.context = ContextAssembler(self.findings, text_only=text_only)
        self.text_only = text_only
        self.default_scopes = default_scopes or set()
        self._temp_worker_files: set[str] = set()

    async def append_finding(self, finding: Finding) -> Finding:
        scopes = list(finding.acl) or [finding.project_id]
        stored = self.findings.append(finding, scopes=scopes)
        self.events.publish(
            EventEnvelope(
                project_id=finding.project_id,
                actor=finding.author,
                type="finding.appended",
                mission_id=None,
                task_id=finding.task_id,
                payload={
                    "finding_id": finding.id,
                    "status": finding.status.value,
                    # Never treat content as policy authority.
                    "content_is_untrusted_data": True,
                },
            )
        )
        return stored

    async def query_scoped(self, scopes: list[str], query: str) -> list[Finding]:
        if not scopes:
            return []
        # Cross-project isolation: scope strings encode project:scope
        project_id = scopes[0].split(":", 1)[0] if ":" in scopes[0] else scopes[0]
        allowed = set(scopes)
        return self.findings.query_scoped(
            project_id=project_id, allowed_scopes=allowed, query=query
        )

    async def build_context(self, task: TaskSpec) -> ContextBundle:
        allowed = set(task.scopes) | self.default_scopes
        bundle = self.context.build(task, allowed_scopes=allowed, budget=ContextBudget())
        self.events.publish(
            EventEnvelope(
                project_id=task.project_id,
                actor="workspace",
                type="context.built",
                mission_id=task.mission_id,
                task_id=task.id,
                payload={
                    "excerpt_count": len(bundle.excerpts),
                    "omission_notes": list(bundle.omission_notes),
                    "text_only": self.text_only,
                },
            )
        )
        return bundle

    async def put_artifact(self, artifact: ArtifactRef, content: bytes) -> ArtifactRef:
        expected = artifact.content_hash if artifact.content_hash else None
        # Empty/placeholder hashes: compute from content.
        if expected in {"", "pending"}:
            expected = None
        stored = self.artifacts.put(
            content,
            media_type=artifact.media_type,
            owner_scope=artifact.owner_scope,
            retention_class=artifact.retention_class,
            expected_hash=expected,
        )
        final = stored.model_copy(update={"id": artifact.id}) if artifact.id else stored
        self.artifacts.put_ref(final)
        self.events.publish(
            EventEnvelope(
                project_id=artifact.owner_scope.split(":", 1)[0]
                if ":" in artifact.owner_scope
                else "proj_unknown",
                actor="workspace",
                type="artifact.stored",
                payload={"artifact_id": final.id, "content_hash": final.content_hash},
            )
        )
        return final

    async def resolve_artifact(self, artifact_id: str) -> ArtifactRef:
        return self.artifacts.resolve(artifact_id, allowed_scopes={"*"})

    def register_temp_worker_file(self, path: str) -> None:
        self._temp_worker_files.add(path)

    def assert_text_only_no_network(self) -> None:
        if not self.text_only:
            raise RuntimeError("network_or_embedding_mode_enabled")
