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


def cmd_providers_list(*, mode: str, show_account_status: bool = False) -> None:
    if show_account_status:
        from swarm.onboarding.service import OnboardingService

        svc = OnboardingService(_repo_root() / "var" / "onboarding")
        print(json.dumps(svc.list_with_account_status(mode=mode), indent=2, default=str))
        return
    rows = list_providers(mode=mode)
    print(json.dumps({"mode": mode, "providers": rows}, indent=2))


def cmd_providers_onboarding_report() -> None:
    from swarm.onboarding.service import OnboardingService

    svc = OnboardingService(_repo_root() / "var" / "onboarding")
    print(json.dumps(svc.onboarding_report(), indent=2, default=str))


def cmd_providers_inspect(*, provider: str, metadata_only: bool) -> None:
    from swarm.onboarding.service import OnboardingService

    svc = OnboardingService(_repo_root() / "var" / "onboarding")
    print(json.dumps(svc.inspect_provider(provider, metadata_only=metadata_only), indent=2))


def cmd_providers_canary(
    *,
    route_id: str,
    policy: str,
    mode: str,
    billing_known_zero: bool = False,
) -> None:
    import asyncio

    from swarm.envfile import load_repo_dotenv
    from swarm.onboarding.canary import bounded_canary

    load_repo_dotenv(_repo_root())
    print(
        json.dumps(
            asyncio.run(
                bounded_canary(
                    route_id=route_id,
                    policy=policy,
                    mode=mode,
                    billing_known_zero=billing_known_zero,
                )
            ),
            indent=2,
            default=str,
        )
    )


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
    plist.add_argument(
        "--show-account-status",
        action="store_true",
        help="Include onboarding account/adapter/route layers (offline inventory)",
    )
    providers_sub.add_parser(
        "onboarding-report",
        help="Write offline onboarding report with essential next actions",
    )
    pins = providers_sub.add_parser("inspect", help="Inspect one provider (metadata)")
    pins.add_argument("--provider", required=True)
    pins.add_argument(
        "--metadata-only",
        action="store_true",
        default=True,
        help="Never call live inference (default)",
    )
    pcan = providers_sub.add_parser("canary", help="Bounded canary via broker")
    pcan.add_argument("--route", required=True)
    pcan.add_argument("--policy", default="bounded_probe", choices=["bounded_probe"])
    pcan.add_argument("--mode", default="mock", choices=["mock", "live"])
    pcan.add_argument(
        "--billing-known-zero",
        action="store_true",
        help="Operator asserts route is known-zero cost (required for --mode live)",
    )
    pcap = providers_sub.add_parser(
        "capability-report",
        help="Build live capability registry (auth probes; no paid inference)",
    )
    pcap.add_argument(
        "--no-probe",
        action="store_true",
        help="Skip live auth probes; catalog + env presence only",
    )
    pcap.add_argument(
        "--save",
        action="store_true",
        help="Persist to var/providers/capability-registry.json",
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
    ep.add_argument("--purpose", default="evaluation")
    erun = ev_sub.add_parser("run", help="Execute qualification plan (mock default)")
    erun.add_argument("--plan", required=True, help="plan_id or path to plan JSON")
    erun.add_argument("--mode", default="mock", choices=["mock", "live"])
    erun.add_argument(
        "--route",
        action="append",
        dest="routes",
        default=None,
        help="Eligible route id (repeatable). Required for --mode live after P15 canary.",
    )
    erep = ev_sub.add_parser("report", help="Show a qualification run report")
    erep.add_argument("--run", required=True, help="run_id")
    eq = ev_sub.add_parser(
        "qualify-live",
        help="P28: run real multi-model qualification benchmarks (Ollama zero-spend)",
    )
    eq.add_argument("--dataset", default="benchmarks/starter.jsonl")
    eq.add_argument("--max-cases", type=int, default=8)
    eq.add_argument(
        "--model",
        action="append",
        dest="models",
        default=None,
        help="Ollama model id (repeatable). Default: preferred local set.",
    )
    eq.add_argument("--max-tokens", type=int, default=600)
    eq.add_argument("--purpose", default="v0.2_p28_model_qualification")
    eroute = ev_sub.add_parser(
        "route",
        help="P29: build evidence-based mission route plan (planner/worker/verifier)",
    )
    eroute.add_argument(
        "--model",
        action="append",
        dest="models",
        default=None,
        help="Constrain to these Ollama models (repeatable)",
    )

    demo = sub.add_parser("demo", help="Mock demonstrations")
    demo_sub = demo.add_subparsers(dest="demo_command", required=True)
    dyn = demo_sub.add_parser("dynamic", help="Dynamic swarm controller mock demo")
    dyn.add_argument("--mode", default="mock", choices=["mock"])
    parser_issue = demo_sub.add_parser(
        "parser-issue", help="P14 integrated parser-issue demo"
    )
    parser_issue.add_argument("--mode", default="mock", choices=["mock", "live"])
    parser_issue.add_argument(
        "--report-dir",
        type=Path,
        default=None,
        help="Write demo artifacts (default: var/reports/demo)",
    )
    selfdev = demo_sub.add_parser(
        "self-development", help="P19 controlled self-development mock"
    )
    selfdev.add_argument("--mode", default="mock", choices=["mock", "live"])
    selfdev.add_argument(
        "--variant",
        default="good",
        choices=["good", "failing", "malicious"],
        help="good=accepted patch; failing/malicious=rejected",
    )
    selfdev.add_argument(
        "--report-dir",
        type=Path,
        default=None,
        help="Write selfdev artifacts (default: var/reports/selfdev)",
    )

    worker = sub.add_parser("worker", help="Worker operations")
    worker_sub = worker.add_subparsers(dest="worker_command", required=True)
    wst = worker_sub.add_parser("self-test", help="Worker membership self-test")
    wst.add_argument("--mode", default="mock", choices=["mock"])

    api = sub.add_parser("api", help="API utilities")
    api_sub = api.add_subparsers(dest="api_command", required=True)
    exp = api_sub.add_parser("export-openapi", help="Write OpenAPI JSON to disk")
    exp.add_argument("--out", type=Path, default=None)

    deploy = sub.add_parser("deploy", help="Deployment utilities (local)")
    deploy_sub = deploy.add_subparsers(dest="deploy_command", required=True)
    doc = deploy_sub.add_parser("doctor", help="Check deploy profile safety")
    doc.add_argument(
        "--profile",
        default="standalone",
        choices=["mock", "standalone", "hybrid", "recovery"],
    )

    recovery = sub.add_parser("recovery", help="Recovery drills (local)")
    recovery_sub = recovery.add_subparsers(dest="recovery_command", required=True)
    rv = recovery_sub.add_parser("verify", help="Verify recovery profile artifacts")
    rv.add_argument("--profile", default="recovery", choices=["recovery"])

    load = sub.add_parser("load", help="Synthetic load scenarios (offline)")
    load_sub = load.add_subparsers(dest="load_command", required=True)
    lrun = load_sub.add_parser("run", help="Run a mock load scenario")
    lrun.add_argument(
        "--scenario", default="adaptive", choices=["adaptive", "fixed"]
    )
    lrun.add_argument("--mode", default="mock", choices=["mock", "live"])
    lrun.add_argument("--sessions", type=int, default=100)
    lrun.add_argument("--tasks", type=int, default=1000)
    lrun.add_argument("--concurrency", type=int, default=8)
    lrun.add_argument(
        "--report-dir",
        type=Path,
        default=None,
        help="Write load report JSON (default: var/reports/load)",
    )

    chaos = sub.add_parser("chaos", help="Fault-injection matrix (offline)")
    chaos_sub = chaos.add_subparsers(dest="chaos_command", required=True)
    crun = chaos_sub.add_parser("run", help="Run offline fault matrix")
    crun.add_argument("--mode", default="mock", choices=["mock", "live"])

    review = sub.add_parser("review", help="Independent review (P20)")
    review_sub = review.add_subparsers(dest="review_command", required=True)
    review_sub.add_parser("report", help="Emit offline review checklist JSON")

    release = sub.add_parser("release", help="Release candidate utilities")
    release_sub = release.add_subparsers(dest="release_command", required=True)
    release_sub.add_parser(
        "verify", help="Verify offline release-candidate readiness"
    )

    mission = sub.add_parser("mission", help="V0.1 real mission runtime")
    mission_sub = mission.add_subparsers(dest="mission_command", required=True)
    mplan = mission_sub.add_parser("plan", help="Inspect repo and emit structured task graph")
    mplan.add_argument("--goal", required=True)
    mplan.add_argument(
        "--dynamic",
        action="store_true",
        help="P32: form dynamic subteams (supervisor/specialists/workers/reviewers)",
    )
    mplan.add_argument("--max-agents", type=int, default=32)
    mrun = mission_sub.add_parser("run", help="Execute a real software mission end-to-end")
    mrun.add_argument("--goal", required=True)
    mrun.add_argument("--model", default="gemma3:4b")
    mrun.add_argument(
        "--no-evidence-router",
        action="store_true",
        help="Disable P29 heterogeneous routing (single --model for all tasks)",
    )
    mrun.add_argument(
        "--repo",
        type=Path,
        default=None,
        help="Target repository (default: this SwarmAI checkout)",
    )
    mstatus = mission_sub.add_parser("status", help="Show live mission state")
    mstatus.add_argument("--mission-id", required=True)
    mlist = mission_sub.add_parser("list", help="List persisted missions")
    _ = mlist
    mrep = mission_sub.add_parser("report", help="Print persisted mission report JSON")
    mrep.add_argument("--mission-id", required=True)

    cost = sub.add_parser("cost", help="Zero-spend cost ledger")
    cost_sub = cost.add_subparsers(dest="cost_command", required=True)
    cost_sub.add_parser("show", help="Show aggregated mission spend (USD)")

    scale = sub.add_parser("scale", help="V0.3 scale / swarm orchestration")
    scale_sub = scale.add_subparsers(dest="scale_command", required=True)
    srun = scale_sub.add_parser(
        "run",
        help="P34/P35: run lightweight multi-agent scale mission (zero-spend)",
    )
    srun.add_argument("--agents", type=int, default=48)
    srun.add_argument("--concurrency", type=int, default=8)
    srun.add_argument("--goal", default="Scale fingerprint swarm across python modules")
    srun.add_argument(
        "--no-supervisor-model",
        action="store_true",
        help="Skip live Ollama supervisor call (still real file work)",
    )

    mem = sub.add_parser("memory", help="V0.4 memory + recovery")
    mem_sub = mem.add_subparsers(dest="memory_command", required=True)
    mret = mem_sub.add_parser("retrieve", help="Retrieve bounded context for a query")
    mret.add_argument("--query", required=True)
    mret.add_argument("--token-budget", type=int, default=256)
    mrec = mem_sub.add_parser("recovery-proof", help="Interrupt/resume real mission proof")
    mrec.add_argument(
        "--goal",
        default="Fix off-by-one in sandbox/selfdev_issue/parser_helper.py",
    )

    tools = sub.add_parser("tools", help="V0.5 tools + permissions")
    tools_sub = tools.add_subparsers(dest="tools_command", required=True)
    tools_sub.add_parser(
        "permission-proof",
        help="Run allow/deny/human-gated tool mission proof",
    )

    args = parser.parse_args()
    if args.command == "serve":
        cmd_serve(args.host, args.port)
    elif args.command == "api" and args.api_command == "export-openapi":
        cmd_export_openapi(args.out)
    elif args.command == "deploy" and args.deploy_command == "doctor":
        from swarm.deploy.doctor import doctor

        print(
            json.dumps(
                doctor(profile=args.profile, repo_root=_repo_root()).to_dict(),
                indent=2,
            )
        )
    elif args.command == "recovery" and args.recovery_command == "verify":
        from swarm.deploy.doctor import recovery_verify

        print(
            json.dumps(
                recovery_verify(profile=args.profile, repo_root=_repo_root()).to_dict(),
                indent=2,
            )
        )
    elif args.command == "db" and args.db_command == "migrate":
        cmd_db_migrate()
    elif args.command == "db" and args.db_command == "validate":
        cmd_db_validate()
    elif args.command == "providers" and args.providers_command == "list":
        cmd_providers_list(
            mode=args.mode,
            show_account_status=bool(getattr(args, "show_account_status", False)),
        )
    elif args.command == "providers" and args.providers_command == "onboarding-report":
        cmd_providers_onboarding_report()
    elif args.command == "providers" and args.providers_command == "inspect":
        cmd_providers_inspect(provider=args.provider, metadata_only=args.metadata_only)
    elif args.command == "providers" and args.providers_command == "canary":
        cmd_providers_canary(
            route_id=args.route,
            policy=args.policy,
            mode=args.mode,
            billing_known_zero=bool(getattr(args, "billing_known_zero", False)),
        )
    elif args.command == "providers" and args.providers_command == "capability-report":
        from swarm.providers.capability_registry import (
            build_capability_registry,
            save_capability_registry,
        )

        report = build_capability_registry(probe=not args.no_probe, repo=_repo_root())
        if args.save:
            path = save_capability_registry(report, repo=_repo_root())
            report = {**report, "saved_to": str(path)}
        print(json.dumps(report, indent=2, default=str))
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
        from swarm.evals.qualify import build_and_save_starter_plan

        path = Path(args.dataset)
        if not path.is_absolute():
            path = _repo_root() / path
        out = _repo_root() / "benchmarks" / "live-plans"
        payload = build_and_save_starter_plan(
            dataset=path,
            purpose=args.purpose,
            mode=args.mode,
            out_dir=out,
            max_cases=args.max_cases,
        )
        print(json.dumps(payload, indent=2))
    elif args.command == "eval" and args.eval_command == "run":
        from swarm.envfile import load_repo_dotenv
        from swarm.evals.qualify import run_qualification

        load_repo_dotenv(_repo_root())
        plan_arg = Path(args.plan)
        if plan_arg.exists():
            plan_path = plan_arg
        else:
            plan_path = _repo_root() / "benchmarks" / "live-plans" / f"{args.plan}.json"
        out = _repo_root() / "var" / "reports" / "qualification"
        try:
            run = run_qualification(
                plan_path,
                mode=args.mode,
                out_dir=out,
                routes=getattr(args, "routes", None),
            )
        except PermissionError as exc:
            print(json.dumps({"error": str(exc), "mode": args.mode}, indent=2))
            raise SystemExit(2) from exc
        print(json.dumps(run.to_dict(), indent=2, default=str))
    elif args.command == "eval" and args.eval_command == "report":
        from swarm.evals.qualify import load_report

        data = load_report(
            args.run, _repo_root() / "var" / "reports" / "qualification"
        )
        print(json.dumps(data, indent=2))
    elif args.command == "eval" and args.eval_command == "qualify-live":
        from swarm.envfile import load_repo_dotenv
        from swarm.evals.live_benchmark import run_live_benchmarks

        load_repo_dotenv(_repo_root())
        ds = Path(args.dataset)
        if not ds.is_absolute():
            ds = _repo_root() / ds
        try:
            report = run_live_benchmarks(
                repo=_repo_root(),
                dataset=ds,
                models=getattr(args, "models", None),
                max_cases=args.max_cases,
                max_tokens=args.max_tokens,
                purpose=args.purpose,
            )
        except RuntimeError as exc:
            print(json.dumps({"error": str(exc)}, indent=2))
            raise SystemExit(2) from exc
        summary = {
            "run_id": report.run_id,
            "models": report.models,
            "case_ids": report.case_ids,
            "trial_count": len(report.trials),
            "passed": sum(1 for t in report.trials if t.correct),
            "failed": sum(1 for t in report.trials if not t.correct and not t.error),
            "errors": sum(1 for t in report.trials if t.error),
            "total_cost_usd": report.total_cost_usd,
            "mock_vs_live": report.mock_vs_live,
            "cells": report.cells,
            "profiles_summary": report.profiles_summary,
            "report_hash": report.report_hash,
        }
        print(json.dumps(summary, indent=2, default=str))
    elif args.command == "eval" and args.eval_command == "route":
        from swarm.envfile import load_repo_dotenv
        from swarm.evals.evidence_router import build_mission_route_plan, save_route_plan

        load_repo_dotenv(_repo_root())
        plan = build_mission_route_plan(
            repo=_repo_root(), models=getattr(args, "models", None)
        )
        path = save_route_plan(plan, repo=_repo_root())
        payload = plan.to_dict()
        payload["saved_to"] = str(path)
        print(json.dumps(payload, indent=2, default=str))
    elif args.command == "demo" and args.demo_command == "dynamic":
        import asyncio

        print(json.dumps(asyncio.run(_demo_dynamic_mock()), indent=2, default=str))
    elif args.command == "demo" and args.demo_command == "parser-issue":
        import asyncio

        root = _repo_root()
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))
        from examples.dynamic_demo.run_demo import run_parser_issue_demo

        if args.report_dir:
            report_dir = Path(args.report_dir)
        else:
            report_dir = root / "var" / "reports" / "demo"
        report = asyncio.run(
            run_parser_issue_demo(mode=args.mode, report_dir=report_dir.resolve())
        )
        print(json.dumps(report.to_dict(), indent=2, default=str))
    elif args.command == "demo" and args.demo_command == "self-development":
        from swarm.selfdev.runner import run_self_development

        report_dir = args.report_dir or (_repo_root() / "var" / "reports" / "selfdev")
        try:
            selfdev_report = run_self_development(
                mode=args.mode,
                variant=args.variant,
                report_dir=Path(report_dir),
            )
        except PermissionError as exc:
            print(json.dumps({"error": str(exc), "mode": args.mode}, indent=2))
            raise SystemExit(2) from exc
        print(json.dumps(selfdev_report.to_dict(), indent=2, default=str))
    elif args.command == "worker" and args.worker_command == "self-test":
        from swarm.workers.registry import worker_self_test

        print(json.dumps(worker_self_test(mode=args.mode), indent=2))
    elif args.command == "load" and args.load_command == "run":
        import asyncio

        from swarm.load.scenarios import LoadConfig, run_load_scenario

        report_dir = args.report_dir or (_repo_root() / "var" / "reports" / "load")
        try:
            load_run_report = asyncio.run(
                run_load_scenario(
                    LoadConfig(
                        scenario=args.scenario,
                        mode=args.mode,
                        logical_sessions=args.sessions,
                        queued_tasks=args.tasks,
                        actual_concurrency=args.concurrency,
                    ),
                    report_dir=Path(report_dir),
                )
            )
        except PermissionError as exc:
            print(json.dumps({"error": str(exc), "mode": args.mode}, indent=2))
            raise SystemExit(2) from exc
        print(json.dumps(load_run_report.to_dict(), indent=2, default=str))
    elif args.command == "chaos" and args.chaos_command == "run":
        import asyncio

        if args.mode == "live":
            print(
                json.dumps(
                    {
                        "error": "live_chaos_blocked: use mock until live capacity verified",
                        "mode": args.mode,
                    },
                    indent=2,
                )
            )
            raise SystemExit(2)
        from swarm.chaos.faults import run_fault_matrix

        print(json.dumps(asyncio.run(run_fault_matrix()), indent=2, default=str))
    elif args.command == "review" and args.review_command == "report":
        from swarm.review.checklist import build_offline_review

        print(json.dumps(build_offline_review().to_dict(), indent=2, default=str))
    elif args.command == "release" and args.release_command == "verify":
        from swarm.release.verify import verify_release, write_verify_report

        release_report = verify_release(_repo_root())
        write_verify_report(release_report, _repo_root() / "var" / "reports" / "release")
        print(json.dumps(release_report.to_dict(), indent=2, default=str))
        if not release_report.passed:
            raise SystemExit(2)
    elif args.command == "mission" and args.mission_command == "plan":
        from swarm.mission.planner import (
            build_software_mission,
            inspect_repo,
            plan_task_graph,
            serialize_plan,
        )

        repo = _repo_root()
        inspection = inspect_repo(repo)
        mission_obj = build_software_mission(goal=args.goal)
        if getattr(args, "dynamic", False):
            from swarm.mission.teams import plan_dynamic_task_graph

            proposal, team = plan_dynamic_task_graph(
                mission_obj, inspection, max_agents=args.max_agents
            )
            print(
                json.dumps(
                    {
                        "mission_id": mission_obj.id,
                        "mode": "dynamic_team",
                        "team": team.to_dict(),
                        "inspection": inspection.to_dict(),
                        "proposal": json.loads(serialize_plan(proposal)),
                    },
                    indent=2,
                    default=str,
                )
            )
        else:
            proposal = plan_task_graph(mission_obj, inspection)
            print(
                json.dumps(
                    {
                        "mission_id": mission_obj.id,
                        "mode": "fixed_crew",
                        "inspection": inspection.to_dict(),
                        "proposal": json.loads(serialize_plan(proposal)),
                    },
                    indent=2,
                    default=str,
                )
            )
    elif args.command == "mission" and args.mission_command == "run":
        from swarm.envfile import load_repo_dotenv
        from swarm.mission.runtime import run_mission

        load_repo_dotenv(_repo_root())
        repo = Path(args.repo).resolve() if args.repo else _repo_root()
        record = run_mission(
            args.goal,
            repo=repo,
            model=args.model,
            use_evidence_router=not getattr(args, "no_evidence_router", False),
        )
        print(json.dumps(record.to_dict(), indent=2, default=str))
        if record.status != "completed":
            raise SystemExit(2)
    elif args.command == "mission" and args.mission_command == "status":
        from swarm.mission.runtime import MissionRuntime

        runtime = MissionRuntime(_repo_root())
        print(json.dumps(runtime.status(args.mission_id), indent=2, default=str))
    elif args.command == "mission" and args.mission_command == "list":
        from swarm.mission.store import MissionStore

        store = MissionStore(_repo_root() / "var" / "missions")
        print(json.dumps({"missions": store.list_missions()}, indent=2, default=str))
    elif args.command == "mission" and args.mission_command == "report":
        from swarm.mission.store import MissionStore

        store = MissionStore(_repo_root() / "var" / "missions")
        print(json.dumps(store.load(args.mission_id).to_dict(), indent=2, default=str))
    elif args.command == "cost" and args.cost_command == "show":
        from swarm.cost.ledger import format_cost_show, load_mission_costs

        ledger = load_mission_costs(_repo_root() / "var" / "missions")
        print(json.dumps(format_cost_show(ledger), indent=2, default=str))
    elif args.command == "scale" and args.scale_command == "run":
        from swarm.envfile import load_repo_dotenv
        from swarm.runtime.scale import run_scale_mission

        load_repo_dotenv(_repo_root())
        report = run_scale_mission(
            repo=_repo_root(),
            goal=args.goal,
            agent_count=args.agents,
            max_concurrency=args.concurrency,
            use_supervisor_model=not args.no_supervisor_model,
        )
        summary = {
            "run_id": report.run_id,
            "agent_count": report.agent_count,
            "task_count": report.task_count,
            "completed": report.completed,
            "failed": report.failed,
            "duplicates_suppressed": report.duplicates_suppressed,
            "consensus": report.consensus,
            "total_cost_usd": report.total_cost_usd,
            "runtime_ms": report.runtime_ms,
            "scheduler_stats": report.scheduler_stats,
            "report_hash": report.report_hash,
            "mock_vs_live": report.mock_vs_live,
        }
        print(json.dumps(summary, indent=2, default=str))
        if report.consensus.get("decision") != "accept":
            raise SystemExit(2)
    elif args.command == "memory" and args.memory_command == "retrieve":
        from swarm.memory.store import MemoryStore, retrieve_context

        store = MemoryStore(_repo_root() / "var" / "memory")
        print(
            json.dumps(
                retrieve_context(
                    store, query=args.query, token_budget=args.token_budget
                ),
                indent=2,
                default=str,
            )
        )
    elif args.command == "memory" and args.memory_command == "recovery-proof":
        from swarm.memory.store import run_interrupt_resume_proof

        proof = run_interrupt_resume_proof(repo=_repo_root(), goal=args.goal)
        print(json.dumps(proof, indent=2, default=str))
        if not proof.get("ok"):
            raise SystemExit(2)


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
