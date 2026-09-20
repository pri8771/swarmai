"""Bounded context projection with ACL and omission notes."""

from __future__ import annotations

from dataclasses import dataclass

from typing import Any

from swarm.contracts.enums import FindingStatus
from swarm.contracts.mission import TaskSpec
from swarm.contracts.workspace import ContextBundle, Finding
from swarm.workspace.findings import FindingStore


@dataclass
class ContextBudget:
    max_findings: int = 8
    max_chars: int = 4000
    include_hypotheses: bool = False


class ContextAssembler:
    def __init__(
        self,
        findings: FindingStore,
        *,
        text_only: bool = True,
    ) -> None:
        self.findings = findings
        self.text_only = text_only  # no remote embedding/network

    def build(
        self,
        task: TaskSpec,
        *,
        allowed_scopes: set[str],
        budget: ContextBudget | None = None,
        prior_tool_outputs: list[dict[str, object]] | None = None,
        graph_revision: int = 1,
        policy_version: str = "ctx-v1",
    ) -> ContextBundle:
        if not self.text_only:
            raise RuntimeError("embedding_mode_requires_broker")  # pragma: no cover
        budget = budget or ContextBudget()
        statuses = {
            FindingStatus.ACCEPTED,
            FindingStatus.CORROBORATED,
            FindingStatus.DISPUTED,
        }
        if budget.include_hypotheses:
            statuses.add(FindingStatus.HYPOTHESIS)

        candidates = self.findings.query_scoped(
            project_id=task.project_id,
            allowed_scopes=allowed_scopes.intersection(set(task.scopes)) or allowed_scopes,
            query="",
            statuses=statuses,
        )
        # Enforce task scopes: findings must intersect task.scopes.
        scoped: list[Finding] = []
        for f in candidates:
            acl = set(f.acl) if f.acl else {task.project_id}
            if acl.intersection(set(task.scopes)) or acl.intersection(allowed_scopes):
                scoped.append(f)

        excerpts: list[dict[str, Any]] = []
        provenance: list[str] = []
        omission: list[str] = []
        used_chars = 0
        included = 0
        for f in scoped:
            if included >= budget.max_findings:
                omission.append(f"truncated_findings_after={f.id}")
                continue
            content = f.content or ""
            # Malicious instructions remain data in the excerpt.
            piece: dict[str, Any] = {
                "finding_id": f.id,
                "status": f.status.value,
                "content": content,
                "source_ids": list(f.source_ids),
                "untrusted_external_text": True,
            }
            size = len(content)
            if used_chars + size > budget.max_chars:
                omission.append(f"truncated_chars_at={f.id}")
                continue
            excerpts.append(piece)
            provenance.extend(f.source_ids)
            if f.artifact_ref:
                provenance.append(f.artifact_ref)
            used_chars += size
            included += 1

        if prior_tool_outputs:
            for i, tool in enumerate(prior_tool_outputs):
                text = str(tool.get("summary") or tool)
                if used_chars + len(text) > budget.max_chars:
                    omission.append(f"omitted_tool_output_{i}")
                    continue
                excerpts.append({"tool_output": tool, "untrusted_external_text": True})
                used_chars += len(text)

        if omission:
            omission.append("certainty_reduced_due_to_truncation")

        # Missing sources → explicit uncertainty note.
        missing_sources = [
            e
            for e in excerpts
            if isinstance(e, dict) and not e.get("source_ids") and e.get("finding_id")
        ]
        if missing_sources:
            omission.append("some_findings_lack_source_ids_treat_as_uncertain")

        return ContextBundle(
            mission_id=task.mission_id,
            task_id=task.id,
            graph_revision=graph_revision,
            excerpts=excerpts,
            provenance=list(dict.fromkeys(provenance)),
            omission_notes=omission,
            token_estimate=max(1, used_chars // 4),
            policy_version=policy_version,
        )
