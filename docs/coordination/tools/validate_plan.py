#!/usr/bin/env python3
"""Validate the SwarmAI machine-readable plan (stdlib only, read-only).

Usage:  python3 docs/coordination/tools/validate_plan.py [--ready] [--json]

Checks the three packet DAG files against each other and against
ARTIFACT_REGISTRY.json so human plans and machine-readable DAGs cannot drift
silently. Exits 1 on any error. It never writes a file and never changes
artifact state.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

COORD = Path(__file__).resolve().parents[1]
REPO = COORD.parents[1]

V17 = COORD / "V17_RECOVERY_PACKET_QUEUE.json"
V23 = COORD / "V17_TO_V23_PACKET_QUEUE.json"
FUT = COORD / "FUTURE_EXECUTION_GRAPH_V18_TO_V30.json"
REG = COORD / "ARTIFACT_REGISTRY.json"

# Milestone/gate labels that packets may name instead of a registry artifact.
SYNTHETIC_ARTIFACTS = {
    "handoff",
    "cross-version-verification",
    "V1.7-live-integration",
    "V1.7-integrated-audit",
    "V1.9-live",
    "V2.3-live",
    "V2.3-integrated-audit",
    "V2.3-integrated-evidence",
    "V3-integrated-evidence",
}
# Registry artifacts that are design inputs to other packets' specs rather than
# something a packet produces. Each entry must say which packets consume it.
CONTRACT_ONLY = {
    "ART-V17-DURABLE-EFFECT-SCHEMA": "accepted lead design; implemented by R27a-R27e",
    "ART-V20-INTEGRATION-CONTRACT": "accepted lead design; service shapes used by R25a, R27c, R17c, 20-01",
}
# A dependency in one of these states lets a dependant start.
SATISFIED = {"impl_complete", "live_checkpointed", "evidence_only", "review_pending"}


def load(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def artifacts_of(packet: dict) -> list[str]:
    found: list[str] = []
    if isinstance(packet.get("artifact"), str):
        found.append(packet["artifact"])
    found.extend(packet.get("artifacts", []))
    found.extend(packet.get("artifacts_also", []))
    return found


def deps_of(packet: dict) -> list[str]:
    return list(packet.get("depends", [])) + list(packet.get("depends_on", []))


def main(argv: list[str]) -> int:
    errors: list[str] = []
    warnings: list[str] = []

    v17, v23, fut, reg = load(V17), load(V23), load(FUT), load(REG)
    sources = {
        "V17": v17["packets"],
        "V18-V23": v23["packets"],
        "FUTURE-coarse": fut["packets"],
        "V30": fut.get("v30_packets", []),
    }

    nodes: dict[str, dict] = {}
    origin: dict[str, str] = {}
    for name, packets in sources.items():
        for packet in packets:
            pid = packet.get("id")
            if not pid:
                errors.append(f"{name}: packet without id: {packet}")
                continue
            if pid in nodes:
                errors.append(f"duplicate packet id {pid} in {name} and {origin[pid]}")
                continue
            nodes[pid] = packet
            origin[pid] = name

    gates: dict[str, dict] = {}
    for doc_name, doc in (("V17", v17), ("V18-V23", v23), ("FUTURE", fut)):
        for gate in doc.get("gates", []):
            if gate["id"] in gates:
                errors.append(f"duplicate gate id {gate['id']} ({doc_name})")
            gates[gate["id"]] = gate

    # --- reference integrity
    for pid, packet in nodes.items():
        for dep in deps_of(packet):
            if dep is None or dep not in nodes:
                errors.append(f"{pid}: dependency {dep!r} does not resolve")
        for key in ("split_into", "remediation", "maps_to"):
            for ref in packet.get(key, []):
                if ref not in nodes:
                    errors.append(f"{pid}: {key} -> {ref!r} does not resolve")
        gate = packet.get("gate")
        if gate and gate not in gates:
            errors.append(f"{pid}: gate {gate!r} is not defined in any gates list")
        spec = packet.get("spec")
        if spec and not (REPO / spec).is_file():
            errors.append(f"{pid}: spec file missing: {spec}")

    # --- status vocabulary (V1.7 queue only declares one)
    vocabulary = set(v17.get("status_vocabulary", []))
    for packet in v17["packets"]:
        if vocabulary and packet.get("status") not in vocabulary:
            errors.append(f"{packet['id']}: status {packet.get('status')!r} not in vocabulary")
        if packet.get("status") in {"verified", "accepted"}:
            errors.append(f"{packet['id']}: queues may not carry registry states")
        if packet.get("status") == "split" and not packet.get("split_into"):
            errors.append(f"{packet['id']}: split without split_into")
        if packet.get("status") == "gaps_found" and not packet.get("remediation"):
            errors.append(f"{packet['id']}: gaps_found without remediation")
        if packet.get("status") == "blocked_external" and not packet.get("gate"):
            errors.append(f"{packet['id']}: blocked_external without gate")

    # --- cycles (dependencies + split expansion)
    graph = {pid: [d for d in deps_of(p) if d in nodes] for pid, p in nodes.items()}
    state: dict[str, int] = {}

    def visit(node: str, trail: list[str]) -> None:
        if state.get(node) == 2:
            return
        if state.get(node) == 1:
            errors.append("cycle: " + " -> ".join(trail + [node]))
            return
        state[node] = 1
        for nxt in graph[node]:
            visit(nxt, trail + [node])
        state[node] = 2

    sys.setrecursionlimit(10000)
    for pid in graph:
        visit(pid, [])

    # --- artifacts
    registry_ids = {a["artifact_id"] for a in reg["artifacts"]}
    covered: set[str] = set()
    for pid, packet in nodes.items():
        for art in artifacts_of(packet):
            if art in registry_ids:
                covered.add(art)
            elif art not in SYNTHETIC_ARTIFACTS:
                errors.append(f"{pid}: artifact {art!r} is neither in the registry nor a known milestone label")
    planned_versions = {"1.7", "1.8", "1.9", "2.0", "2.3", "3.0"}
    for art in reg["artifacts"]:
        if art["target_version"] in planned_versions and art["artifact_id"] not in covered:
            if art["artifact_id"] in CONTRACT_ONLY:
                continue
            errors.append(f"registry artifact {art['artifact_id']} (v{art['target_version']}) has no packet")

    # --- aliases must not collide with real ids
    for pid, packet in nodes.items():
        for alias in packet.get("aliases", []):
            if alias in nodes and origin[alias] != "FUTURE-coarse":
                errors.append(f"{pid}: alias {alias!r} collides with a real execution id")

    # --- coarse groups must map to every fine packet of their version
    mapped = {ref for p in fut["packets"] for ref in p.get("maps_to", [])}
    for packet in list(v23["packets"]) + list(fut.get("v30_packets", [])):
        if packet["id"] not in mapped and packet["id"] != "18-00":
            warnings.append(f"{packet['id']} is not referenced by any coarse maps_to")

    # --- ready set for the active queue
    def satisfied(pid: str, dependant: str | None = None) -> bool:
        packet = nodes[pid]
        status = packet.get("status")
        if status == "split":
            return all(satisfied(child, dependant) for child in packet.get("split_into", []))
        if status in {"gaps_found", "changes_required"}:
            # The audited parent is a valid base for its own remediation packets;
            # everything else waits until the remediation is done.
            remediation = packet.get("remediation", [])
            if dependant in remediation:
                return True
            return bool(remediation) and all(satisfied(r, dependant) for r in remediation)
        return status in SATISFIED

    # `gate` on a planned packet names what must clear before its artifact can
    # advance; only status `blocked_external` means the packet cannot start.
    ready = []
    for packet in v17["packets"]:
        if packet.get("status") not in {"ready", "planned"}:
            continue
        if all(satisfied(dep, packet["id"]) for dep in deps_of(packet)):
            ready.append(packet["id"])

    counts = {name: len(packets) for name, packets in sources.items()}
    report = {
        "ok": not errors,
        "packet_counts": counts,
        "gate_count": len(gates),
        "registry_artifacts": len(registry_ids),
        "ready_v17": ready,
        "errors": errors,
        "warnings": warnings,
    }
    if "--json" in argv:
        print(json.dumps(report, indent=2))
    else:
        print(f"packets: {counts}  gates: {len(gates)}  registry artifacts: {len(registry_ids)}")
        if "--ready" in argv or not errors:
            print("ready (V1.7 queue, file order):", ", ".join(ready) or "none")
        for line in warnings:
            print("WARN ", line)
        for line in errors:
            print("ERROR", line)
        print("OK" if not errors else f"FAILED with {len(errors)} error(s)")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
