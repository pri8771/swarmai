"""CLI entrypoints for local development."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import uvicorn

from swarm.broker.explain import explain_capacity
from swarm.contracts.fixtures import sample_mission, sample_task
from swarm.controller.mission import MissionController, spawn_proposal
from swarm.db.engine import create_db_engine, database_url, ping
from swarm.evals.dataset import validate_dataset
from swarm.evals.plan import build_plan
from swarm.providers.catalog import list_providers
from swarm.tools.sandbox_runner import self_test as sandbox_self_test


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def cmd_serve(host: str, port: int) -> None:
    uvicorn.run("swarm.api.app:app", host=host, port=port, reload=False)


def cmd_export_openapi(path: Path | None = None) -> None:
    from swarm.api.app import create_app

    app = create_app()
    spec = app.openapi()
    target = path or (_repo_root() / "var" / "openapi.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(spec, indent=2) + "\n")
    print(str(target))



def cmd_db_migrate() -> None:
    root = _repo_root()
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=root,
        check=False,
    )
    raise SystemExit(result.returncode)


def cmd_db_validate() -> None:
    engine = create_db_engine()
    ping(engine)
    print(f"ok database={database_url().split('@')[-1]}")


def cmd_providers_list(*, mode: str) -> None:
    rows = list_providers(mode=mode)
    print(json.dumps({"mode": mode, "providers": rows}, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(prog="swarm", description="SwarmAI local CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    serve = sub.add_parser("serve", help="Run the local API")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8765)

    db = sub.add_parser("db", help="Database operations")
    db_sub = db.add_subparsers(dest="db_command", required=True)
    db_sub.add_parser("migrate", help="Apply Alembic migrations to head")
    db_sub.add_parser("validate", help="Ping configured database")

    providers = sub.add_parser("providers", help="Provider catalog operations")
    providers_sub = providers.add_subparsers(dest="providers_command", required=True)
    plist = providers_sub.add_parser("list", help="List providers")
    plist.add_argument(
        "--mode",
        default="mock",
        choices=["mock", "live"],
        help="mock=offline catalog view; live still does not call providers here",
    )

    sandbox = sub.add_parser("sandbox", help="Sandbox operations")
    sandbox_sub = sandbox.add_subparsers(dest="sandbox_command", required=True)
    st = sandbox_sub.add_parser("self-test", help="Run sandbox self-test")
    st.add_argument("--network", default="off", choices=["off"])

    capacity = sub.add_parser("capacity", help="Capacity / broker explain")
    capacity_sub = capacity.add_subparsers(dest="capacity_command", required=True)
    cexp = capacity_sub.add_parser("explain", help="Explain admission capacity")
    cexp.add_argument(
        "--mode",
        default="mock",
        choices=["mock", "live"],
        help="mock=offline fixtures; live requires configured accounts (not implemented as spend)",
    )
    cexp.add_argument("--purpose", default="mission")

    ev = sub.add_parser("eval", help="Benchmark / qualification")
    ev_sub = ev.add_subparsers(dest="eval_command", required=True)
    vd = ev_sub.add_parser("validate-dataset", help="Validate a JSONL benchmark dataset")
    vd.add_argument("path", nargs="?", default="benchmarks/starter.jsonl")
    ep = ev_sub.add_parser("plan", help="Build a bounded evaluation plan")
    ep.add_argument("--suite", default="starter")
    ep.add_argument("--mode", default="mock", choices=["mock", "live"])
    ep.add_argument("--max-cases", type=int, default=16)
    ep.add_argument("--dataset", default="benchmarks/starter.jsonl")

    demo = sub.add_parser("demo", help="Mock demonstrations")
    demo_sub = demo.add_subparsers(dest="demo_command", required=True)
    dyn = demo_sub.add_parser("dynamic", help="Dynamic swarm controller mock demo")
    dyn.add_argument("--mode", default="mock", choices=["mock"])

    worker = sub.add_parser("worker", help="Worker operations")
    worker_sub = worker.add_subparsers(dest="worker_command", required=True)
    wst = worker_sub.add_parser("self-test", help="Worker membership self-test")
    wst.add_argument("--mode", default="mock", choices=["mock"])

    api = sub.add_parser("api", help="API utilities")
    api_sub = api.add_subparsers(dest="api_command", required=True)
    exp = api_sub.add_parser("export-openapi", help="Write OpenAPI JSON to disk")
    exp.add_argument("--out", type=Path, default=None)

    args = parser.parse_args()
    if args.command == "serve":
        cmd_serve(args.host, args.port)
    elif args.command == "api" and args.api_command == "export-openapi":
        cmd_export_openapi(args.out)
    elif args.command == "db" and args.db_command == "migrate":
        cmd_db_migrate()
    elif args.command == "db" and args.db_command == "validate":
        cmd_db_validate()
    elif args.command == "providers" and args.providers_command == "list":
        cmd_providers_list(mode=args.mode)
    elif args.command == "sandbox" and args.sandbox_command == "self-test":
        print(json.dumps(sandbox_self_test(network=args.network), indent=2))
    elif args.command == "capacity" and args.capacity_command == "explain":
        import asyncio

        print(
            json.dumps(
                asyncio.run(explain_capacity(mode=args.mode, purpose=args.purpose)),
                indent=2,
                default=str,
            )
        )
    elif args.command == "eval" and args.eval_command == "validate-dataset":
        path = Path(args.path)
        if not path.is_absolute():
            path = _repo_root() / path
        print(json.dumps(validate_dataset(path), indent=2))
    elif args.command == "eval" and args.eval_command == "plan":
        path = Path(args.dataset)
        if not path.is_absolute():
            path = _repo_root() / path
        plan = build_plan(
            path, suite=args.suite, mode=args.mode, max_cases=args.max_cases
        )
        print(json.dumps(plan.to_dict(), indent=2))
    elif args.command == "demo" and args.demo_command == "dynamic":
        import asyncio

        print(json.dumps(asyncio.run(_demo_dynamic_mock()), indent=2, default=str))
    elif args.command == "worker" and args.worker_command == "self-test":
        from swarm.workers.registry import worker_self_test

        print(json.dumps(worker_self_test(mode=args.mode), indent=2))


async def _demo_dynamic_mock() -> dict[str, object]:
    ctrl = MissionController(inference_slots=2, worker_slots=2)
    mission = await ctrl.submit_mission(sample_mission())
    children = [
        sample_task().model_copy(update={"id": "demo_child_1", "objective": "extract"}),
        sample_task().model_copy(update={"id": "demo_child_2", "objective": "classify"}),
    ]
    prop = spawn_proposal(mission, author_session_id="as_demo", parent=None, children=children)
    await ctrl.propose_graph_change(prop)
    rev = await ctrl.commit_validated_revision(prop.proposal_id)
    ready = await ctrl.choose_ready_work(mission.id)
    return {
        "mode": "mock",
        "mock_vs_live": "controller_fixtures_only",
        "mission_id": mission.id,
        "revision": rev,
        "ready_count": len(ready),
        "ready_ids": [t.id for t in ready],
    }


if __name__ == "__main__":
    main()
