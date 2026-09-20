"""Graph proposal validation — cycles, scopes, duplicates."""

from __future__ import annotations

from dataclasses import dataclass

from swarm.contracts.enums import GraphOperation, TaskStatus
from swarm.contracts.mission import GraphProposal, TaskSpec


@dataclass
class ValidationResult:
    accepted: bool
    reason: str
    merged_into: str | None = None


def _would_cycle(tasks: dict[str, TaskSpec], new_specs: list[TaskSpec]) -> bool:
    graph: dict[str, list[str]] = {tid: list(t.dependency_ids) for tid, t in tasks.items()}
    for spec in new_specs:
        graph[spec.id] = list(spec.dependency_ids)
    # Kahn / DFS cycle detect
    visiting: set[str] = set()
    visited: set[str] = set()

    def dfs(node: str) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        for dep in graph.get(node, []):
            if dfs(dep):
                return True
        visiting.remove(node)
        visited.add(node)
        return False

    return any(dfs(n) for n in graph)


def validate_proposal(
    proposal: GraphProposal,
    *,
    tasks: dict[str, TaskSpec],
    mission_revision: int,
    mission_scopes: set[str],
    max_graph_nodes: int,
) -> ValidationResult:
    if proposal.based_on_revision != mission_revision:
        return ValidationResult(False, "stale_revision")
    if proposal.operation == GraphOperation.STOP:
        return ValidationResult(True, "stop_ok")

    for spec in proposal.task_specs:
        # Cross-scope dependencies rejected.
        for dep in spec.dependency_ids:
            parent = tasks.get(dep)
            if parent is None:
                continue
            if set(spec.scopes) and set(parent.scopes):
                if not set(spec.scopes).intersection(set(parent.scopes)):
                    return ValidationResult(False, "cross_scope_dependency")
        if not set(spec.scopes).issubset(mission_scopes) and mission_scopes:
            # Allow if mission_scopes empty (tests) or intersection.
            if mission_scopes and not set(spec.scopes).intersection(mission_scopes):
                return ValidationResult(False, "scope_not_in_mission")

    projected = dict(tasks)
    if proposal.operation in {GraphOperation.SPAWN, GraphOperation.SPLIT}:
        for spec in proposal.task_specs:
            # Duplicate spawn merge: same objective+family+parent.
            for existing in tasks.values():
                if (
                    existing.objective == spec.objective
                    and existing.task_family == spec.task_family
                    and existing.parent_task_id == spec.parent_task_id
                    and existing.status not in {TaskStatus.CANCELLED, TaskStatus.SUPERSEDED}
                ):
                    return ValidationResult(
                        False, "duplicate_merged", merged_into=existing.id
                    )
            projected[spec.id] = spec
        if len(projected) > max_graph_nodes:
            return ValidationResult(False, "max_graph_nodes")
        if _would_cycle(projected, proposal.task_specs):
            return ValidationResult(False, "cycle_rejected")
        return ValidationResult(True, "spawn_ok")

    if proposal.operation == GraphOperation.MERGE:
        return ValidationResult(True, "merge_ok")
    if proposal.operation == GraphOperation.CHALLENGE:
        return ValidationResult(True, "challenge_ok")
    if proposal.operation == GraphOperation.REASSIGN:
        return ValidationResult(True, "reassign_ok")
    if proposal.operation == GraphOperation.REVISE_DEPENDENCY:
        if _would_cycle(projected, proposal.task_specs):
            return ValidationResult(False, "cycle_rejected")
        return ValidationResult(True, "revise_ok")
    return ValidationResult(True, "accepted")
