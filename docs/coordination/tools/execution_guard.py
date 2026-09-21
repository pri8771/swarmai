#!/usr/bin/env python3
"""Read-only readiness guard over the EXISTING SwarmAI packet DAGs.

This tool grants no permission and never accepts artifacts. It applies the lead's
additive dependency corrections, distinguishes build work from gated execution,
and fails closed on malformed input. Use alongside validate_plan.py, which checks
registry coverage. No network, model call, scheduler, write, or external action.
"""
from __future__ import annotations

import argparse
import copy
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

FILES = {
    'v17': 'V17_RECOVERY_PACKET_QUEUE.json',
    'v23': 'V17_TO_V23_PACKET_QUEUE.json',
    'v30': 'FUTURE_EXECUTION_GRAPH_V18_TO_V30.json',
}
BUILD_TYPES = {'code', 'test', 'infra', 'ops', 'transplant', 'design', 'contract'}
COMPLETE = {'impl_complete', 'live_checkpointed'}
CLOSED_GATE = {'satisfied', 'closed', 'verified'}
TERMINAL = {'split', 'gaps_found', 'changes_required', 'blocked_external',
            'wall_clock_pending', 'review_pending', 'evidence_only', *COMPLETE}


def deps(packet: dict[str, Any]) -> list[str]:
    return list(dict.fromkeys(packet.get('depends', []) + packet.get('depends_on', [])))


def heartbeat_assessment(heartbeat: dict[str, Any], now: datetime) -> dict[str, Any]:
    """Never confuse a fresh daemon tick with fresh implementation activity."""
    hb = heartbeat.get('last_heartbeat', heartbeat)
    def age(value: Any) -> float | None:
        if not isinstance(value, str):
            return None
        try:
            stamp = datetime.fromisoformat(value.replace('Z', '+00:00'))
            if stamp.tzinfo is None:
                return None
            return (now - stamp).total_seconds()
        except (TypeError, ValueError):
            return None
    tick_age = age(hb.get('timestamp_utc'))
    activity_age = age(hb.get('last_meaningful_activity_at'))
    if tick_age is None or tick_age < -60:
        state = 'unknown_or_invalid_timestamp'
    elif tick_age > 12 * 60:
        state = 'stale_heartbeat'
    elif activity_age is None or activity_age < -60:
        state = 'daemon_alive_activity_unknown'
    elif activity_age > 15 * 60:
        state = 'daemon_alive_activity_stale_verify_process_or_long_job'
    else:
        state = 'recent_tick_and_reported_activity_not_acceptance'
    return {'state': state, 'heartbeat_age_seconds': tick_age,
            'activity_age_seconds': activity_age, 'packet': hb.get('current_packet'),
            'source_sha': hb.get('branch_sha')}


def evaluate(documents: dict[str, dict[str, Any]], control: dict[str, Any],
             phase: str = 'v17') -> dict[str, Any]:
    nodes: dict[str, dict[str, Any]] = {}
    origins: dict[str, str] = {}
    gates: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    for family, doc in documents.items():
        packets = doc.get('v30_packets', []) if family == 'v30' else doc.get('packets', [])
        for packet in packets:
            pid = packet.get('id')
            if not isinstance(pid, str) or pid in nodes:
                errors.append(f'duplicate_or_missing_packet:{pid}')
                continue
            nodes[pid] = copy.deepcopy(packet)
            origins[pid] = family
        for gate in doc.get('gates', []):
            gid = gate.get('id')
            if not isinstance(gid, str) or gid in gates:
                errors.append(f'duplicate_or_missing_gate:{gid}')
            else:
                gates[gid] = gate

    # Overlay changes dependencies only, never status, evidence, or acceptance.
    for pid, extra in control.get('dependency_additions', {}).items():
        if pid not in nodes:
            errors.append(f'overlay_missing_packet:{pid}')
            continue
        nodes[pid]['depends'] = list(dict.fromkeys(nodes[pid].get('depends', []) + extra))
    for pid, packet in nodes.items():
        for dep in deps(packet) + packet.get('remediation', []) + packet.get('split_into', []):
            if dep not in nodes:
                errors.append(f'{pid}:missing_reference:{dep}')
        if packet.get('status') == 'split' and not packet.get('split_into'):
            errors.append(f'{pid}:empty_split')
        gid = packet.get('gate')
        if gid and gid not in gates:
            errors.append(f'{pid}:undefined_gate:{gid}')
    for pid, required in control.get('execution_gates', {}).items():
        if pid not in nodes:
            errors.append(f'gate_policy_missing_packet:{pid}')
        for gid in required:
            if gid not in gates:
                errors.append(f'{pid}:undefined_execution_gate:{gid}')
    for pid, required in control.get('review_before', {}).items():
        if pid not in nodes or any(dep not in nodes for dep in required):
            errors.append(f'invalid_review_hold:{pid}')
    if phase not in FILES:
        errors.append(f'invalid_phase:{phase}')

    # Expand splits in execution dependencies. Intentional repair->parent edges
    # consume only that parent's audited baseline, not its own unfinished repair.
    def expanded(pid: str, dependant: str, trail: tuple[str, ...] = ()) -> list[str]:
        if pid in trail:
            errors.append('expansion_cycle:' + '->'.join((*trail, pid)))
            return []
        packet = nodes.get(pid, {})
        status = packet.get('status')
        if status == 'split':
            out: list[str] = []
            for child in packet.get('split_into', []):
                out.extend(expanded(child, dependant, (*trail, pid)))
            return out
        if status in {'gaps_found', 'changes_required'}:
            repairs = packet.get('remediation', [])
            if dependant in repairs:
                return []
            if repairs:
                out = []
                for repair in repairs:
                    out.extend(expanded(repair, dependant, (*trail, pid)))
                return out
        return [pid]

    graph = {pid: [leaf for dep in deps(p) for leaf in expanded(dep, pid)]
             for pid, p in nodes.items()}
    seen: dict[str, int] = {}
    def visit(pid: str, trail: tuple[str, ...] = ()) -> None:
        if seen.get(pid) == 1:
            errors.append('dependency_cycle:' + '->'.join((*trail, pid)))
            return
        if seen.get(pid) == 2:
            return
        seen[pid] = 1
        for dep in graph.get(pid, []):
            if dep in nodes:
                visit(dep, (*trail, pid))
        seen[pid] = 2
    for pid in nodes:
        visit(pid)

    ready: list[str] = []
    preflight: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    active: list[str] = []
    for pid, packet in nodes.items():
        if origins[pid] != phase:
            continue
        if packet.get('status') == 'in_progress':
            active.append(pid)
            continue
        if packet.get('status') not in {'ready', 'planned'}:
            continue
        reasons: list[str] = []
        kind = packet.get('type', 'unspecified')
        for dep in graph[pid]:
            if dep not in nodes:
                reasons.append(f'missing_dependency:{dep}')
                continue
            upstream = nodes[dep]
            status = upstream.get('status')
            if status in COMPLETE:
                continue
            # Audited historical implementation can enable ordinary repair work,
            # but evidence-only/review-pending is NEVER proof for a live checkpoint.
            if kind in BUILD_TYPES and status in {'evidence_only', 'review_pending'}:
                if upstream.get('audit') or upstream.get('evidence_refs'):
                    continue
            reasons.append(f'dependency:{dep}:{status}')
        if kind in {'audit', 'lead_decision', 'lead_sensitive'}:
            reasons.append('lead_owned_decision_not_worker_acceptance')
        if packet.get('requires_lead_freeze') and pid not in control.get('frozen_packets', []):
            reasons.append('lead_spec_freeze_required')
        for dep in control.get('review_before', {}).get(pid, []):
            receipt = control.get('reviewed_packets', {}).get(dep)
            if not isinstance(receipt, dict) or not receipt.get('review_ref') or not receipt.get('source_sha'):
                reasons.append(f'independent_review:{dep}')
        required = list(control.get('execution_gates', {}).get(pid, []))
        own_gate = packet.get('gate')
        if own_gate and kind not in BUILD_TYPES and own_gate not in control.get('result_only_gates', []):
            required.append(own_gate)
        probe = False
        for gid in dict.fromkeys(required):
            gate = gates.get(gid, {})
            if gate.get('status') in CLOSED_GATE and gate.get('evidence_refs'):
                continue
            if gid in control.get('runtime_probe_gates', []) and gate.get('status') == 'preauthorized_if_existing_gh_session_available':
                probe = True
                continue
            reasons.append(f'execution_gate:{gid}:{gate.get("status", "missing")}')
        if reasons:
            blocked.append({'packet': pid, 'reasons': reasons})
        elif probe:
            preflight.append({'packet': pid, 'condition': 'read_only_auth_and_runtime_probe_required_before_any_mutation'})
        else:
            ready.append(pid)

    # Validation failure invalidates the whole recommendation, not just one row.
    if errors:
        ready, preflight = [], []
    return {'ok': not errors, 'phase': phase, 'ready': ready, 'preflight_only': preflight,
            'in_progress': active, 'blocked': blocked, 'errors': sorted(set(errors)),
            'meaning': 'engineering readiness only; no artifact acceptance or external authority',
            'packet_count': len(nodes)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--coord', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--phase', choices=tuple(FILES), default='v17')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    try:
        control = json.loads((args.coord / 'EXECUTION_CONTROL.json').read_text())
        documents = {name: json.loads((args.coord / filename).read_text()) for name, filename in FILES.items()}
        result = evaluate(documents, control, args.phase)
        hb_path = args.coord / control['heartbeat_path']
        if hb_path.exists():
            result['heartbeat'] = heartbeat_assessment(json.loads(hb_path.read_text()), datetime.now(timezone.utc))
    except (OSError, ValueError, KeyError, TypeError, RecursionError) as exc:
        result = {'ok': False, 'ready': [], 'errors': [f'input_error:{type(exc).__name__}:{exc}']}
    print(json.dumps(result, indent=2))
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
