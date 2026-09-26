#!/usr/bin/env python3
"""SW-X2-S1: one bounded live smoke of SwarmAI -> SplitSignal (zero spend).

Exit 0 = pass, 1 = fail, 3 = blocked (an honest external gate; evidence says why).

Runs only when every gate holds; otherwise it records ``blocked:<reason>`` and
makes no network call:
* ``SPLITSIGNAL_BASE_URL`` and ``SPLITSIGNAL_API_KEY`` are set (``SPLITSIGNAL_MODEL``
  defaults to ``DEFAULT_SPLITSIGNAL_MODEL``);
* the decisions log has a line starting ``- SW-PREAPPROVAL-A3: APPROVED``;
* a zero-dollar, free-routes-only LiveGrant (built here from that approval, at
  most 2 calls, 16 output tokens per call, 60 s) passes ``preflight_live_grant``;
* the model is listed by ``GET /v1/models`` and admissible.

Evidence keeps only sanitized metadata: no prompt or response text, no key.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from swarm.evals.synthetic_harness import LiveGrant
from swarm.providers.router_client import RouterClientError
from swarm.providers.splitsignal_client import (
    DEFAULT_SPLITSIGNAL_MODEL,
    SPLITSIGNAL_CONTRACT,
    SplitSignalClient,
)
from swarm.pursuit.live_grant import preflight_live_grant

ROOT = Path(__file__).resolve().parents[1]
DECISIONS = ROOT / "docs" / "swarm-mvp" / "DECISIONS.md"
OUT = ROOT / "docs" / "evidence" / "v23" / "splitsignal_live.json"
APPROVAL_LINE = re.compile(r"^- SW-PREAPPROVAL-A3: APPROVED\b", re.MULTILINE)
PROMPT = "Reply with the single word: ok"


def _receipt(r: Any) -> dict[str, Any]:
    return {
        "request_id": r.request_id,
        "route_id": r.route_id,
        "billing": str(r.billing),
        "usage_known": r.usage_known,
        "prompt_tokens": r.prompt_tokens,
        "completion_tokens": r.completion_tokens,
        "cost_amount": getattr(r, "cost_amount", None),
        "cost_source": getattr(r, "cost_source", "unknown"),
        "status_code": r.status_code,
    }


def run(
    *,
    env: Mapping[str, str],
    decisions: Path,
    stream: bool,
    client_factory: Callable[[str], SplitSignalClient] = SplitSignalClient,
) -> tuple[int, dict[str, Any]]:
    report: dict[str, Any] = {
        "packet": "SW-X2-S1-SPLITSIGNAL-LIVE-SMOKE",
        "contract": SPLITSIGNAL_CONTRACT,
        "started_at": datetime.now(UTC).isoformat(),
        "stream_requested": stream,
        "calls": [],
    }

    def blocked(reason: str) -> tuple[int, dict[str, Any]]:
        report["status"] = f"blocked:{reason}"
        return 3, report

    base = env.get("SPLITSIGNAL_BASE_URL", "").strip()
    model = env.get("SPLITSIGNAL_MODEL", "").strip()
    report["model_source"] = "env" if model else "default"
    model = model or DEFAULT_SPLITSIGNAL_MODEL
    if not base:
        return blocked("splitsignal_base_url_missing")
    if not env.get("SPLITSIGNAL_API_KEY", "").strip():
        return blocked("splitsignal_api_key_missing")
    report["route_requested"] = model
    try:
        approved = APPROVAL_LINE.search(decisions.read_text(encoding="utf-8")) is not None
    except OSError:
        approved = False
    if not approved:
        return blocked("sw_preapproval_a3_not_approved")
    grant = LiveGrant(
        grant_id="SW-PREAPPROVAL-A3",
        routes=(model,),
        budget_usd=0.0,
        purpose="splitsignal_live_smoke",
        approved=True,
        free_routes_only=True,
        max_calls=2,
        max_tokens=16,
        max_wall_seconds=60,
    )
    pre = preflight_live_grant(grant, purpose="splitsignal_live_smoke", required_route=model)
    if not pre.ready:
        return blocked(pre.blocked_reason or "live_grant_not_ready")

    client = client_factory(base)
    deadline = time.monotonic() + 60
    try:
        try:
            models = {m.model_id: m for m in client.list_models()}
        except RouterClientError as exc:
            report["status"] = f"fail:list_models:{exc.error_class.value}:{exc.code}"
            return 1, report
        report["models_listed"] = len(models)
        cap = models.get(model)
        if cap is None:
            report["listed_route_ids"] = sorted(models)[:20]
            return blocked("model_not_listed")
        ok, why = cap.admissible()
        if not ok:
            return blocked(f"model_not_admissible:{why}")
        body = {
            "model": model,
            "messages": [{"role": "user", "content": PROMPT}],
            "max_tokens": 16,
        }
        calls: list[dict[str, Any]] = report["calls"]
        modes = ["text", "stream"] if stream else ["text"]
        for mode in modes[: grant.max_calls]:
            if time.monotonic() > deadline:
                report["status"] = "fail:wall_clock_exceeded"
                return 1, report
            try:
                if mode == "text":
                    result = client.chat(body)
                    text = str(result.message.get("content") or "")
                    receipt = result.receipt
                else:
                    sresult = client.chat_stream(body)
                    text, receipt = sresult.text, sresult.receipt
            except RouterClientError as exc:
                calls.append(
                    {"mode": mode, "error_class": exc.error_class.value, "error_code": exc.code}
                )
                report["status"] = f"fail:{mode}:{exc.error_class.value}:{exc.code}"
                return 1, report
            calls.append({"mode": mode, "answer_chars": len(text), **_receipt(receipt)})
            if not text.strip():
                report["status"] = f"fail:{mode}:empty_answer"
                return 1, report
    finally:
        client.close()
    report["status"] = "pass"
    return 0, report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stream", action="store_true", help="also run one streamed call (SP5)")
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args(argv)
    code, report = run(env=os.environ, decisions=DECISIONS, stream=args.stream)
    report["finished_at"] = datetime.now(UTC).isoformat()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(report["status"])
    return code


if __name__ == "__main__":
    sys.exit(main())
