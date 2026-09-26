"""``swarm v23 …`` offline operator commands (scheduler, packs, portability).

Every command is local and deterministic: no network, no providers, no spending.
Output is one JSON document on stdout; failures print ``{"ok": false, "error": …}``
and exit 2.
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from swarm.capabilities import CapabilityPackManifest
from swarm.capabilities.signing import (
    PackSigningError,
    sign_manifest,
    trusted_keys_from_env,
    verify_manifest,
)
from swarm.contracts.v23 import DispatchIntent, DispatchIntentComponent, SchedulableTask
from swarm.product.portability import PortabilityService
from swarm.scheduling.epoch import InMemorySchedulerEpochService
from swarm.scheduling.memory_store import InMemorySchedulingStore
from swarm.scheduling.service import SchedulerService
from swarm.scheduling.wdrr import WdrrConfig

DEFAULT_POLICY = Path("config/v23/scheduler_policy.v1.json")
MAX_SIM_DECISIONS = 100_000


class CliError(ValueError):
    pass


def register(sub: Any) -> None:
    v23 = sub.add_parser("v23", help="V2.3 scheduler, packs and portability (offline)")
    v23_sub = v23.add_subparsers(dest="v23_command", required=True)

    pol = v23_sub.add_parser("scheduler-policy", help="Validate and print the WDRR policy")
    pol.add_argument("--policy", type=Path, default=DEFAULT_POLICY)

    sim = v23_sub.add_parser("scheduler-simulate", help="Offline WDRR share simulation")
    sim.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    sim.add_argument(
        "--projects", required=True, help="Comma list of project:weight, e.g. a:1,b:3"
    )
    sim.add_argument("--decisions", type=int, default=400)

    sign = v23_sub.add_parser("pack-sign", help="Sign a pack manifest with SWARM_PACK_KEY_*")
    sign.add_argument("--manifest", type=Path, required=True)
    sign.add_argument("--out", type=Path, required=True)

    ver = v23_sub.add_parser("pack-verify", help="Verify a pack manifest against trusted keys")
    ver.add_argument("--manifest", type=Path, required=True)

    exp = v23_sub.add_parser("export", help="Export a project portability bundle")
    exp.add_argument("--project-id", required=True)
    exp.add_argument("--out-dir", type=Path, default=Path("var/portability"))

    imp = v23_sub.add_parser("import", help="Validate and import a portability bundle")
    imp.add_argument("--bundle", type=Path, required=True)
    imp.add_argument("--target-project-id", default=None)


def _parse_projects(spec: str) -> dict[str, float]:
    out: dict[str, float] = {}
    for part in spec.split(","):
        name, _, weight = part.strip().partition(":")
        if not name or not weight:
            raise CliError(f"bad_project_spec:{part}")
        value = float(weight)
        if value <= 0:
            raise CliError(f"weight_must_be_positive:{name}")
        out[name] = value
    if len(out) < 1:
        raise CliError("no_projects")
    return out


def _reserve(intent: DispatchIntent, comp: DispatchIntentComponent) -> str:
    return f"sim_{intent.attempt_id}_{comp.kind}"


def _release(intent: DispatchIntent, comp: DispatchIntentComponent) -> None:
    return None


def simulate(policy: Path, projects: dict[str, float], decisions: int) -> dict[str, Any]:
    if not 1 <= decisions <= MAX_SIM_DECISIONS:
        raise CliError(f"decisions_out_of_range:1..{MAX_SIM_DECISIONS}")
    config = WdrrConfig.from_policy_file(policy)
    svc = SchedulerService(
        InMemorySchedulingStore(),
        epochs=InMemorySchedulerEpochService(),
        holder_id="cli_sim",
        reserve=_reserve,
        release=_release,
        config=config,
    )
    for pid, weight in projects.items():
        svc.register_project(pid, weight=weight)
        svc.register_mission(f"msn_{pid}", pid)
    counts = dict.fromkeys(projects, 0)
    enqueued = datetime(2026, 1, 1, tzinfo=UTC)
    for n in range(decisions):
        tasks = [
            SchedulableTask(
                task_id=f"t_{pid}_{n}",
                mission_id=f"msn_{pid}",
                project_id=pid,
                attempt_id=f"att_{pid}_{n}",
                enqueued_at=enqueued,
            )
            for pid in projects
        ]
        out = svc.schedule_once(tasks)
        if out.intent is not None and out.task is not None and out.decision.value == "admit":
            counts[out.task.project_id] += 1
            svc.mark_dispatched(out.intent.intent_id)
            svc.finish(out.intent.intent_id)
    total_w = sum(projects.values())
    admitted = sum(counts.values()) or 1
    return {
        "ok": True,
        "policy_version": config.policy_version,
        "decisions": decisions,
        "admitted": counts,
        "share": {p: round(c / admitted, 4) for p, c in counts.items()},
        "target_share": {p: round(w / total_w, 4) for p, w in projects.items()},
    }


def _load_manifest(path: Path) -> CapabilityPackManifest:
    return CapabilityPackManifest.model_validate(json.loads(path.read_text(encoding="utf-8")))


def pack_sign(manifest_path: Path, out: Path) -> dict[str, Any]:
    manifest = _load_manifest(manifest_path)
    if not manifest.publisher:
        raise CliError("manifest_publisher_required")
    keys = trusted_keys_from_env()
    key = keys.get(manifest.publisher)
    if key is None:
        raise CliError(f"no_trusted_key_for_publisher:{manifest.publisher}")
    signed = sign_manifest(manifest, key=key)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(signed.model_dump(mode="json"), indent=2) + "\n", encoding="utf-8")
    return {"ok": True, "pack_id": signed.pack_id, "version": signed.version, "out": str(out)}


def pack_verify(manifest_path: Path) -> dict[str, Any]:
    manifest = _load_manifest(manifest_path)
    try:
        verify_manifest(manifest, trusted_keys=trusted_keys_from_env())
    except PackSigningError as exc:
        return {"ok": False, "error": str(exc), "pack_id": manifest.pack_id}
    return {"ok": True, "pack_id": manifest.pack_id, "publisher": manifest.publisher}


def dispatch(args: argparse.Namespace) -> bool:
    """Handle ``swarm v23 …``. Returns False when ``args`` is another command."""
    if getattr(args, "command", None) != "v23":
        return False
    try:
        result = _run(args)
    except (CliError, ValueError, OSError, KeyError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        raise SystemExit(2) from exc
    print(json.dumps(result, indent=2, sort_keys=True))
    if not result.get("ok", False):
        raise SystemExit(2)
    return True


def _run(args: argparse.Namespace) -> dict[str, Any]:
    cmd = args.v23_command
    if cmd == "scheduler-policy":
        config = WdrrConfig.from_policy_file(args.policy)
        return {"ok": True, "policy": asdict(config)}
    if cmd == "scheduler-simulate":
        return simulate(args.policy, _parse_projects(args.projects), args.decisions)
    if cmd == "pack-sign":
        return pack_sign(args.manifest, args.out)
    if cmd == "pack-verify":
        return pack_verify(args.manifest)
    if cmd == "export":
        bundle = PortabilityService().export_project(
            project_id=args.project_id,
            project_config={"project_id": args.project_id},
            out_dir=args.out_dir,
        )
        path = Path(args.out_dir) / f"{bundle.bundle_id}.json"
        return {"ok": True, "bundle_id": bundle.bundle_id, "path": os.fspath(path)}
    if cmd == "import":
        bundle = PortabilityService().import_bundle(
            args.bundle, target_project_id=args.target_project_id
        )
        return {"ok": True, "bundle_id": bundle.bundle_id, "project_id": bundle.project_id}
    raise CliError(f"unknown_v23_command:{cmd}")
