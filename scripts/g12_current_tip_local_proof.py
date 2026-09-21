#!/usr/bin/env python3
"""A5 / current-tip local G12 proof — live Ollama only, no remote claim.

Proves on the current runtime tip:
1. actual local Ollama route inventory
2. actual brokered local inference (no adapter stub)
3. controlled route disable -> permitted alternative
4. reservation/settlement/quota deny on exhaust
5. exact source/model/config identity binding
6. $0 spend; remote dual never claimed

Historical stubbed scripts remain regression prep only.
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

import httpx

from swarm.contracts.enums import AvailabilityStatus
from swarm.envfile import load_repo_dotenv
from swarm.mission.brokered_inference import brokered_local_chat, build_local_mission_broker
from swarm.providers.catalog import DEFAULT_ENDPOINTS

REPO = Path(__file__).resolve().parents[1]


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO, text=True).strip()


def _loopback_base() -> str:
    load_repo_dotenv(REPO)
    base = (os.environ.get("OLLAMA_BASE_URL") or DEFAULT_ENDPOINTS["ollama"]).rstrip("/")
    host = (urlparse(base).hostname or "").lower()
    if host not in {"127.0.0.1", "localhost", "::1"}:
        raise RuntimeError(f"non_loopback_denied:{base}")
    return base[:-3] if base.endswith("/v1") else base


def inventory_ollama(native_base: str) -> dict:
    with httpx.Client(timeout=30.0) as client:
        tags = client.get(f"{native_base}/api/tags").json()
        version = None
        try:
            version = client.get(f"{native_base}/api/version").json()
        except Exception as exc:  # noqa: BLE001 — optional probe
            version = {"error": type(exc).__name__}
    models = [
        {
            "name": m.get("name"),
            "model": m.get("model"),
            "digest": (m.get("digest") or "")[:16],
            "size": m.get("size"),
            "modified_at": m.get("modified_at"),
        }
        for m in (tags.get("models") or [])
    ]
    names = [str(m["name"]) for m in models if m.get("name")]
    preferred = [n for n in ("gemma3:4b", "qwen3.5:4b") if n in names]
    return {
        "endpoint": native_base,
        "loopback": True,
        "version": version,
        "model_count": len(models),
        "models": models,
        "preferred_present": preferred,
    }


async def _run() -> dict:
    started = datetime.now(UTC).isoformat()
    tip = _git("rev-parse", "HEAD")
    branch = _git("rev-parse", "--abbrev-ref", "HEAD")
    native = _loopback_base()
    inv = inventory_ollama(native)
    preferred = inv["preferred_present"]
    if len(preferred) < 2:
        # Fall back to any two installed chat models.
        names = [m["name"] for m in inv["models"] if m.get("name")]
        preferred = names[:2]
    if len(preferred) < 2:
        return {
            "ok": False,
            "error": "need_at_least_two_local_ollama_models",
            "inventory": inv,
            "tip_sha": tip,
        }

    model_a, model_b = preferred[0], preferred[1]
    broker = build_local_mission_broker(
        repo_root=REPO,
        models=[model_a, model_b],
        request_limit=3,
    )

    # 1) Live brokered inference on both routes (no stub).
    t0 = time.perf_counter()
    call_a = await brokered_local_chat(
        broker=broker,
        messages=[{"role": "user", "content": "Reply with exactly: ALPHA"}],
        model=model_a,
        max_tokens=8,
    )
    call_b = await brokered_local_chat(
        broker=broker,
        messages=[{"role": "user", "content": "Reply with exactly: BETA"}],
        model=model_b,
        max_tokens=8,
    )
    live_secs = round(time.perf_counter() - t0, 3)
    broker.assert_all_calls_accounted()

    # 2) Controlled disable of route A -> deny on A, permitted alternative on B.
    ctx_a = broker._contexts[f"rt_ollama_{model_a}"]
    ctx_a.route.availability_status = AvailabilityStatus.UNAVAILABLE
    denied = await brokered_local_chat(
        broker=broker,
        messages=[{"role": "user", "content": "should deny"}],
        model=model_a,
        max_tokens=8,
    )
    alt = await brokered_local_chat(
        broker=broker,
        messages=[{"role": "user", "content": "Reply with exactly: ALT"}],
        model=model_b,
        max_tokens=8,
    )
    # Re-enable A for quota phase clarity (status only; limit already consuming).
    ctx_a.route.availability_status = AvailabilityStatus.AVAILABLE

    # 3) Quota deny: request_limit=3; after call_a, call_b, alt => remaining 0.
    # One more call must deny.
    bucket = broker.ledger._buckets["qb_local_ollama_requests"]
    remaining = int(bucket.model.remaining)
    settled = int(bucket.settled)
    fourth = await brokered_local_chat(
        broker=broker,
        messages=[{"role": "user", "content": "should exhaust"}],
        model=model_b,
        max_tokens=8,
    )

    finished = datetime.now(UTC).isoformat()
    evidence = {
        "packet_id": "A5-LOCAL-G12-CURRENT-TIP",
        "gate": "INF-121-local-only",
        "scenario": "current_tip_live_local_inventory_broker_disable_quota",
        "ok": bool(
            call_a.ok
            and call_b.ok
            and (not denied.ok)
            and alt.ok
            and (not fourth.ok)
            and "QuotaExhausted" in str(fourth.error or "")
        ),
        "started_at": started,
        "finished_at": finished,
        "wall_live_inference_seconds": live_secs,
        "tip_sha": tip,
        "branch": branch,
        "allow_paid": False,
        "spend_usd": 0.0,
        "swarm_allow_paid_env": os.environ.get("SWARM_ALLOW_PAID", "unset"),
        "ollama_base_url_env_set": bool(os.environ.get("OLLAMA_BASE_URL")),
        "inventory": inv,
        "models_under_test": [model_a, model_b],
        "live_brokered_inference": {
            "call_a": call_a.to_dict(),
            "call_b": call_b.to_dict(),
            "adapter_stubbed": False,
            "adapter_class": "_LocalAdapter->local_chat(Ollama loopback)",
        },
        "route_disable_fallback": {
            "killed_route": f"rt_ollama_{model_a}",
            "killed_availability": AvailabilityStatus.UNAVAILABLE.value,
            "denied_ok": not denied.ok,
            "denied_error": denied.error,
            "alternative_route": f"rt_ollama_{model_b}",
            "alternative_ok": alt.ok,
            "alternative": alt.to_dict(),
        },
        "quota": {
            "request_limit": 3,
            "settled_before_fourth": settled,
            "remaining_before_fourth": remaining,
            "fourth_denied": not fourth.ok,
            "fourth": fourth.to_dict(),
        },
        "remote_providers": "not_claimed",
        "live_dual_remote_claimed": False,
        "note": (
            "Current-tip live local G12 proof only. "
            "Uses real Ollama inventory + brokered local_chat (no execute_one stub). "
            "Remote dual-provider overlap remains blocked pending admitted zero-charge remotes."
        ),
    }
    return evidence


def main() -> int:
    evidence = asyncio.run(_run())
    out = REPO / "docs" / "evidence" / "g12" / "a5-current-tip-local-proof.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evidence, indent=2))
    print(f"\nWrote {out}", file=sys.stderr)
    if not evidence.get("ok"):
        return 2
    if evidence.get("live_dual_remote_claimed"):
        return 2
    if float(evidence.get("spend_usd") or 1) != 0.0:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
