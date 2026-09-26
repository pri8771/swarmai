# SW-X2-S1 — SplitSignal live smoke (SP4/SP5) and joint V2.3 finish record (SP6)

Copy this whole file into a fresh Cursor session opened on the **swarmai** repository. Follow it top to bottom. It is self-contained: do not read other plans to decide what to do.

| Field | Value |
|---|---|
| Session ID | `SW-X2-S1` |
| Repository | `pri8771/swarmai` (GitHub remote `origin`; **public** repo) |
| Base branch | `cursor/sw-v23-integration-460c` — always the **current** `origin/cursor/sw-v23-integration-460c` (plan baseline `dev` @ `8e1c0fde`) |
| Your branch | `cursor/v23-x2-s1-splitsignal-live` |
| Branch-suffix rule | If your environment forces a suffix (for example `-460c`), append it **once** to *your* branch and write the exact final name in the handoff. Never add a suffix to `cursor/sw-v23-integration-460c`: it already ends in `-460c`. |
| PR target | `cursor/sw-v23-integration-460c` — **draft** PR. Never `dev`, never `main`. |
| Wave | X (after W4-S1 and X1-S1; external gates SP4/SP5/SP6; approval SW-PREAPPROVAL-A3) |
| Depends on | SW-X1-S1, SW-W4-S1 |
| Handoff file | `docs/v2.3/sessions/SW-X2-S1.md` |
| Independent reviewer | Codex (owner decision D2). You never accept your own work. |
| Plan | `docs/plans/v2.3/PLAN.md`; owner preflight `docs/plans/v2.3/OWNER_PREFLIGHT.md`; decisions `docs/swarm-mvp/DECISIONS.md` |

## 0. Hard rules (read twice)
1. Edit **only** the files listed in “Files you own” plus your handoff file. If another file must change, do not change it: write the exact change under “Needs other owner” in the handoff.
2. Never push to, or merge into, `main`, `dev` or `cursor/sw-v23-integration-460c`. Never merge any PR, never force-push, never rewrite history, never delete branches. Only the wave MERGE prompts (`SW-MERGE-*`) push to `cursor/sw-v23-integration-460c`.
3. Zero spend. The **only** network calls allowed are the ones section 5 names, only after the approval line `SW-PREAPPROVAL-A3: APPROVED` is present, and at most the number section 5 states. No account creation, no deploys, no paid APIs.
4. Never commit or print secrets, tokens, `.env` files, customer data or raw logs. Test tokens are fake literals such as `atk_policy_demo`. Check environment variables only with `test -n "$NAME"`.
5. Passing tests are *not* acceptance. Never write “accepted”, “complete”, “released” or “V2.3 done”. Use “implemented” and “tested”.
6. `src/swarm/contracts/v23.py`, `src/swarm/db/models.py` and `migrations/` belong to SW-W0-S2. Import from them; never edit them (unless you *are* SW-W0-S2).
7. Do not edit `.github/workflows/`, `pyproject.toml`, `uv.lock`, `package.json` or lockfiles.
8. If a step can be read two ways, choose the reading that changes fewer lines inside your own files, and write the choice under “Decisions” in the handoff.

## 1. Setup
```bash
git status --porcelain            # must print nothing; otherwise STOP (S1)
git fetch origin cursor/sw-v23-integration-460c
git ls-remote --exit-code origin refs/heads/cursor/sw-v23-integration-460c >/dev/null && echo INTEG_OK || echo INTEG_MISSING
```
If it prints `INTEG_MISSING`, STOP (S2): SW-W0-S1 or the executor creates it.
```bash
git checkout -b cursor/v23-x2-s1-splitsignal-live origin/cursor/sw-v23-integration-460c
git log -1 --format='%H %s'       # record this SHA in the handoff as 'base'
command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh   # then: export PATH=$HOME/.local/bin:$PATH
uv sync
git clean -fdX -- var/
```

## 2. Dependency and environment check
Depends on: SW-X1-S1, SW-W4-S1. Their PRs must already be merged into `cursor/sw-v23-integration-460c` (by the wave MERGE prompt).
Run every command below. Each must print `OK`. If any prints `MISSING`, STOP (condition S2 in section 10).

```bash
git fetch origin cursor/sw-v23-integration-460c
git cat-file -e origin/cursor/sw-v23-integration-460c:src/swarm/providers/splitsignal_client.py && echo "OK src/swarm/providers/splitsignal_client.py" || echo "MISSING src/swarm/providers/splitsignal_client.py"
git cat-file -e origin/cursor/sw-v23-integration-460c:tests/fixtures/splitsignal_http/fake_splitsignal.py && echo "OK tests/fixtures/splitsignal_http/fake_splitsignal.py" || echo "MISSING tests/fixtures/splitsignal_http/fake_splitsignal.py"
git cat-file -e origin/cursor/sw-v23-integration-460c:docs/v2.3/EXIT_CHECKLIST.md && echo "OK docs/v2.3/EXIT_CHECKLIST.md" || echo "MISSING docs/v2.3/EXIT_CHECKLIST.md"
```

This session needs these environment variables (set by the owner preflight, `docs/plans/v2.3/OWNER_PREFLIGHT.md`). Check names only; never print values:
```bash
test -n "$SPLITSIGNAL_BASE_URL" && echo "SPLITSIGNAL_BASE_URL SET" || echo "SPLITSIGNAL_BASE_URL MISSING"
test -n "$SPLITSIGNAL_API_KEY" && echo "SPLITSIGNAL_API_KEY SET" || echo "SPLITSIGNAL_API_KEY MISSING"
```
If any prints `MISSING`, STOP (condition S6). Cursor may withhold secrets from this **public** repo; that is a preflight gap for the owner, not something to work around.

## 3. Files you own (the ONLY files you may create or modify)
- `scripts/v23_splitsignal_smoke.py` — create
- `tests/providers/test_v23_splitsignal_smoke.py` — create
- `docs/evidence/v23/splitsignal_live.json` — create
- `docs/v2.3/EXIT_CHECKLIST.md` — modify (the SplitSignal row only)
- `docs/v2.3/STATUS.md` — modify (append one section only)
- `docs/v2.3/sessions/SW-X2-S1.md` — create (your handoff)

## 4. Do NOT touch
- Any file not listed in section 3 (in particular: `src/swarm/api/app.py`, `src/swarm/api/store.py`, `src/swarm/cli.py`, `src/swarm/db/models.py`, `migrations/`, `docs/agents/*`, `docs/plans/v2.3/*`, `CHANGELOG.md`, `README.md`, `.github/`, unless listed above).
- The `inference_server` repository: read-only, and only through the commands in section 5.
- The branches `main`, `dev`, `cursor/sw-v23-integration-460c`, `cursor/v23-plan-460c`, and any other session's branch.
- Generated files that tests rewrite: `schemas/v1/*`, `docs/evidence/fix-004/*`, `var/*` — always restore them before committing (section 6).

## 5. Steps
**Goal.** Record SwarmAI's side of the joint V2.3 finish with SplitSignal (owner decision D4). One bounded live smoke test proves sync points SP4 (non-streaming) and SP5 (streaming) from SwarmAI's side, and SP6 is checked against inference_server's evidence. The session makes **at most 2 live calls in total**: one run of the script, one text call and one streamed call, each with `max_tokens` 16, on a route SplitSignal lists as free. Zero spend.

**Gates, in order.** Each one is checked before anything touches the network.
1. The environment variables (section 2): `SPLITSIGNAL_BASE_URL` (the public URL + `/v1`), `SPLITSIGNAL_API_KEY`. `SPLITSIGNAL_MODEL` is optional: when unset, the script uses `gemini/gemini-3.5-flash-lite` and records `model_source: default`.
2. The approval line, `SW-PREAPPROVAL-A3: APPROVED`, in `docs/swarm-mvp/DECISIONS.md`.
3. SW-X1-S1 and SW-W4-S1 merged (section 2).
4. inference_server sync point SP4 (and, for the streamed call, SP5) recorded on `cursor/is-v23-integration-460c` (Step 0b). The joint schedule (`docs/plans/v2.3/JOINT_PLAN.md`) runs this session after IS-W8-MERGE, so SP6 is normally reached too and no re-run is needed.

### Step 0 — approval line (read-only)
```bash
grep -c "^- SW-PREAPPROVAL-A3: APPROVED" docs/swarm-mvp/DECISIONS.md
```
It must print `1`. If it prints `0`, STOP (S7, section 10) with reason `SW-PREAPPROVAL-A3 not approved`. Never add or edit that line yourself.

### Step 0b — inference_server sync points SP4/SP5 (read-only, no call to SplitSignal)
inference_server writes one marker line per sync point, starting at column 0, into `docs/evidence/m1/hosted-v05.md` on its integration branch (IS-W2-DEPLOY writes `SP3:`/`SP4:`; IS-W4-MERGE, or the IS-W6/W8-MERGE fallback, writes `SP5:`).
```bash
gh api "repos/pri8771/inference_server/contents/docs/evidence/m1/hosted-v05.md?ref=cursor/is-v23-integration-460c" --jq .content 2>/dev/null \
  | base64 -d 2>/dev/null > /tmp/is_hosted_v05.md || true
SP4=$(grep -c '^SP4: reached' /tmp/is_hosted_v05.md 2>/dev/null || true); SP5=$(grep -c '^SP5: reached' /tmp/is_hosted_v05.md 2>/dev/null || true)
echo "SP4=${SP4:-0} SP5=${SP5:-0}"
if [ "${SP5:-0}" -ge 1 ]; then STREAM_FLAG=--stream; else STREAM_FLAG=; fi; echo "STREAM_FLAG=${STREAM_FLAG:-none}"
```
- `SP4=0`: STOP (S7) with reason `external gate SP4 not reached`. No live call is made, and the approval stays unused for a later run.
- If `gh api repos/pri8771/inference_server --jq .full_name` does not print `pri8771/inference_server`, this environment cannot read the private repo: STOP (S7) with reason `inference_server not readable from this environment` (launch this session from an environment that has both repos, JOINT_PLAN §4).
- `SP4` ≥ 1 and `SP5=0`: continue without `--stream` (one text call). Record `SP5: not reached (inference_server SP5 line absent)`.

### Step 1 — `scripts/v23_splitsignal_smoke.py` (create, exactly)
```python
#!/usr/bin/env python3
"""SW-X2-S1: one bounded live smoke of SwarmAI -> SplitSignal (zero spend).

Exit 0 = pass, 1 = fail, 3 = blocked (an honest external gate; evidence says why).

Runs only when every gate holds; otherwise it records ``blocked:<reason>`` and
makes no network call:
* ``SPLITSIGNAL_BASE_URL`` and ``SPLITSIGNAL_API_KEY`` are set (``SPLITSIGNAL_MODEL``
  defaults to ``DEFAULT_SPLITSIGNAL_MODEL``);
* the decisions log has a line starting ``- SW-PREAPPROVAL-A3: APPROVED``;
* a zero-dollar, free-routes-only LiveGrant (built here from that approval, at
  most 2 calls, 64 output tokens, 60 s) passes ``preflight_live_grant``;
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
        max_tokens=64,
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
```

### Step 2 — `tests/providers/test_v23_splitsignal_smoke.py` (create, exactly)
```python
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest

from swarm.providers.splitsignal_client import SplitSignalClient
from tests.fixtures.splitsignal_http.fake_splitsignal import SYNTHETIC_KEY, FakeSplitSignal

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "v23_splitsignal_smoke.py"


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location("v23_splitsignal_smoke", SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


smoke = _load()
ENV = {
    "SPLITSIGNAL_BASE_URL": "http://s.test/v1",
    "SPLITSIGNAL_API_KEY": SYNTHETIC_KEY,
    "SPLITSIGNAL_MODEL": "mock/ok",
}


@pytest.fixture
def approved(tmp_path: Path) -> Path:
    p = tmp_path / "DECISIONS.md"
    p.write_text("- SW-PREAPPROVAL-A3: APPROVED 2026-09-26\n", encoding="utf-8")
    return p


def factory(fake: FakeSplitSignal):  # type: ignore[no-untyped-def]
    return lambda base: SplitSignalClient(base, transport=fake.transport())


@pytest.fixture(autouse=True)
def key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SPLITSIGNAL_API_KEY", SYNTHETIC_KEY)


def test_pass_text_and_stream(approved: Path) -> None:
    fake = FakeSplitSignal()
    code, rep = smoke.run(env=ENV, decisions=approved, stream=True, client_factory=factory(fake))
    assert code == 0 and rep["status"] == "pass"
    assert [c["mode"] for c in rep["calls"]] == ["text", "stream"]
    assert rep["calls"][0]["cost_source"] == "reported"
    assert "Hello" not in json.dumps(rep)
    assert SYNTHETIC_KEY not in json.dumps(rep)
    assert len(fake.requests) == 3


@pytest.mark.parametrize(
    ("drop", "reason"),
    [
        ("SPLITSIGNAL_BASE_URL", "blocked:splitsignal_base_url_missing"),
        ("SPLITSIGNAL_API_KEY", "blocked:splitsignal_api_key_missing"),
    ],
)
def test_missing_env_blocks_without_network(approved: Path, drop: str, reason: str) -> None:
    fake = FakeSplitSignal()
    env = {k: v for k, v in ENV.items() if k != drop}
    code, rep = smoke.run(env=env, decisions=approved, stream=False, client_factory=factory(fake))
    assert (code, rep["status"]) == (3, reason)
    assert fake.requests == []


def test_pending_approval_blocks_without_network(tmp_path: Path) -> None:
    p = tmp_path / "DECISIONS.md"
    p.write_text(
        "- SW-PREAPPROVAL-A3: PENDING\n"
        "To approve, change it to `- SW-PREAPPROVAL-A3: APPROVED <date>`.\n",
        encoding="utf-8",
    )
    fake = FakeSplitSignal()
    code, rep = smoke.run(env=ENV, decisions=p, stream=False, client_factory=factory(fake))
    assert (code, rep["status"]) == (3, "blocked:sw_preapproval_a3_not_approved")
    assert fake.requests == []


def test_unlisted_model_blocks(approved: Path) -> None:
    env = {**ENV, "SPLITSIGNAL_MODEL": "gemini/not-listed"}
    code, rep = smoke.run(
        env=env, decisions=approved, stream=False, client_factory=factory(FakeSplitSignal())
    )
    assert (code, rep["status"]) == (3, "blocked:model_not_listed")
    assert rep["listed_route_ids"] == ["mock/ok", "mock/quota", "mock/unavailable"]
    assert rep["calls"] == []


def test_unset_model_uses_default(approved: Path) -> None:
    env = {k: v for k, v in ENV.items() if k != "SPLITSIGNAL_MODEL"}
    code, rep = smoke.run(
        env=env, decisions=approved, stream=False, client_factory=factory(FakeSplitSignal())
    )
    assert rep["model_source"] == "default"
    assert rep["route_requested"] == "gemini/gemini-3.5-flash-lite"
    assert (code, rep["status"]) == (3, "blocked:model_not_listed")


def test_upstream_error_fails(approved: Path) -> None:
    env = {**ENV, "SPLITSIGNAL_MODEL": "mock/quota"}
    code, rep = smoke.run(
        env=env, decisions=approved, stream=False, client_factory=factory(FakeSplitSignal())
    )
    assert code == 1 and rep["status"] == "fail:text:quota_exhausted:quota_exhausted"
```
Run the offline tests first: `uv run pytest tests/providers/test_v23_splitsignal_smoke.py -q` must print `7 passed`. These tests make no network call.

### Step 3 — the live run (once; the only permitted second run is the `model_not_listed` case below)
```bash
uv run python scripts/v23_splitsignal_smoke.py $STREAM_FLAG; echo "exit=$?"
```
`$STREAM_FLAG` comes from Step 0b (`--stream` only when SP5 is recorded). The script writes `docs/evidence/v23/splitsignal_live.json` and prints its `status`.
- `exit=0`, status `pass`: with `--stream`, SP4 **and** SP5 are verified from SwarmAI's side; without it, SP4 is verified and SP5 stays `not reached` (Step 0b).
- `exit=1`: read `calls` in the JSON.
  - If `calls[0].mode` is `text` and it has no `error_class`, SP4 is verified and SP5 is not reached. Record `SP5: not reached (<status>)`.
  - Otherwise, SP4 is not reached. Record `SP4: not reached (<status>)`.
  - Either way, continue to Step 4 and do not re-run the script.
- `exit=3` with status `blocked:model_not_listed`: no model call was made. Read `listed_route_ids` in the JSON.
  - If exactly one id starts with `gemini/`, run the command **once more** as `SPLITSIGNAL_MODEL=<that id> uv run python scripts/v23_splitsignal_smoke.py $STREAM_FLAG; echo "exit=$?"`. The 2-call cap still holds, because the first run made no model call. Then handle its exit code with these same rules, except that this bullet no longer applies. Record `SPLITSIGNAL_MODEL substituted: <old> -> <new>` under "Decisions" and under "Needs other owner" (the owner sets the Cursor Environment Variable `SPLITSIGNAL_MODEL` to the new id).
  - Otherwise, STOP (S7) with reason `model_not_listed`.
- `exit=3` with any other `blocked:<reason>`: no live call was made. STOP (S7) with that reason. The JSON is honest evidence: commit it.

Check that the evidence holds no secret and no content:
```bash
grep -c "ss_live_" docs/evidence/v23/splitsignal_live.json   # must print 0
grep -c '"content"' docs/evidence/v23/splitsignal_live.json  # must print 0
```
If either prints anything other than `0`, delete the file, write `evidence withheld: <which check>` in the handoff, and STOP (S3).

### Step 4 — SP6 check (read-only)
```bash
gh api "repos/pri8771/inference_server/contents/docs/evidence/v2.3-offline.md?ref=cursor/is-v23-integration-460c" --jq .content 2>/dev/null \
  | base64 -d 2>/dev/null | grep -c "swarmai-consumer 1\." || true
```
- A number of 1 or more: SP6 is reached (inference_server records the same contract). Record `SP6: reached (swarmai-consumer 1.x)`.
- `0`, or no output: record `SP6: not reached yet`. This is **not** a STOP. The coordinator re-runs this prompt on a new branch named `cursor/v23-x2-s1-splitsignal-live-r2`, then `-r3`, and so on, after SP6. Before any re-run, the coordinator adds a fresh approval line `SW-PREAPPROVAL-A3-R<n>: APPROVED` for the extra calls. Those extra calls are outside the joint 7-call budget (IS-A6 5 + SW-A3 2), so the owner must approve them explicitly. Without it, the re-run skips Step 3 and reuses the committed evidence.

### Step 5 — `docs/v2.3/EXIT_CHECKLIST.md` (the SplitSignal row only)
Replace the status cell of the row that starts `| SplitSignal consumer adapter` with exactly `done (fake SplitSignal); live SP4 <verified/not reached>, SP5 <verified/not reached>; SP6 <reached/not reached yet>`, filled in from Steps 3–4. In the evidence cell of the same row, append `; docs/evidence/v23/splitsignal_live.json`. Change nothing else in the file.

### Step 6 — `docs/v2.3/STATUS.md` (append one section at the end)
```markdown
## SplitSignal sync points (SW-X2-S1, <UTC date>)
Contract `swarmai-consumer 1.x`; evidence `docs/evidence/v23/splitsignal_live.json` (status `<status>`); live calls made: <0, 1 or 2>, `max_tokens` 16, spend: none reported (`cost_source` <value>).
| SP | Meaning | SwarmAI state |
|---|---|---|
| SP1 | contract frozen | reached (SW-X1-S1 merged) |
| SP2 | mock testable | <reached / not run> |
| SP3 | key issuable | <reached if SP4 reached, otherwise unknown> |
| SP4 | live non-streaming | <verified / not reached (reason)> |
| SP5 | live streaming | <verified / not reached (reason)> |
| SP6 | joint V2.3 finish | <reached / not reached yet> |
Not claimed: V2.3 accepted.
```

### Acceptance (this session)
- [ ] Step 0 printed `1`, and the environment check printed three `SET` lines.
- [ ] `tests/providers/test_v23_splitsignal_smoke.py` gives 7 passed offline.
- [ ] The live script ran exactly once (at most 2 calls), and its exit code and status are in the handoff.
- [ ] The evidence JSON contains no `ss_live_` and no `"content"`.
- [ ] The SplitSignal checklist row and the appended STATUS section match the evidence.
- [ ] The SP4/SP5/SP6 states in the handoff are copied from Steps 3–4, not assumed.

## 6. Verify (run exactly; all must pass)
```bash
git clean -fdX -- var/            # F-15: stale runtime state breaks re-runs
# Private database for this session: concurrent sessions on one host must never share one.
sudo -u postgres psql -c "CREATE DATABASE swarm_sw_x2_s1 OWNER swarm;" || true
export SWARM_DATABASE_URL=postgresql+psycopg://swarm:swarm@127.0.0.1:5432/swarm_sw_x2_s1
uv run ruff check .
uv run mypy src/swarm
uv run alembic heads               # must print exactly ONE line ending in (head)
uv run pytest tests/providers -q
uv run pytest tests/contracts tests/spikes tests/api tests/broker tests/controller tests/chaos tests/deployment tests/evals tests/extensions tests/foundation tests/goals tests/pursuit tests/sdk tests/knowledge tests/load tests/memory tests/mission tests/objectives tests/onboarding tests/product tests/providers tests/recovery tests/regressions tests/release tests/runtime tests/selfdev tests/tools tests/ui tests/workers tests/workspace tests/e2e tests/acceptance tests/portability -q --ignore=tests/integration

# PostgreSQL integration (install steps in “PostgreSQL” below)
uv run pytest tests/integration -q -m integration

git checkout -- schemas/v1 docs/evidence/fix-004 var   # tests rewrite these tracked files
git status --porcelain            # every path listed must be one of YOUR files
```

### PostgreSQL (for the integration line)
```bash
pg_isready -h 127.0.0.1 || {
  sudo apt-get update && sudo apt-get install -y postgresql && sudo service postgresql start
  sudo -u postgres psql -c "CREATE USER swarm WITH PASSWORD 'swarm' SUPERUSER;" || true
}
```
Run this block before section 6. Section 6 creates your private database and exports `SWARM_DATABASE_URL` for **both** pytest lines; never unset it and never point it at the shared `swarm` database.
If `pg_isready -h 127.0.0.1` still fails after running this block twice, write `integration: SKIPPED (postgres unavailable: <last error line>)` in the handoff and continue. Never claim integration passed without running it.

## 7. Acceptance checklist (tick every box in the handoff)
- [ ] Every step in section 5 done; every acceptance box in section 5 ticked.
- [ ] `uv run ruff check .` and `uv run mypy src/swarm` pass.
- [ ] `uv run alembic heads` prints exactly one head.
- [ ] Full offline CI list passes (paste the final `N passed` line into the handoff).
- [ ] Integration run passed, or SKIPPED with reason in the handoff.
- [ ] `git status --porcelain` lists only files from section 3 + the handoff.
- [ ] No secrets, no network calls beyond section 5, no `accepted`/`complete` claims.
- [ ] The Codex review packet (section 11) is in the PR description and the handoff.

## 8. Commit, push, draft PR
```bash
git checkout -- schemas/v1 docs/evidence/fix-004 var
git add scripts/v23_splitsignal_smoke.py tests/providers/test_v23_splitsignal_smoke.py docs/evidence/v23/splitsignal_live.json docs/v2.3/EXIT_CHECKLIST.md docs/v2.3/STATUS.md docs/v2.3/sessions/SW-X2-S1.md
git status --porcelain            # nothing unexpected staged or left over
git commit -m "test(splitsignal): bounded live smoke via SplitSignal (SP4/SP5) and joint V2.3 sync-point record (SP6)" -m "Session: SW-X2-S1. Plan: docs/plans/v2.3/PLAN.md."
git push -u origin cursor/v23-x2-s1-splitsignal-live
gh pr create --draft --base cursor/sw-v23-integration-460c --head cursor/v23-x2-s1-splitsignal-live --title "[SW-X2-S1] SplitSignal live smoke (SP4/SP5) and joint V2.3 finish record (SP6)" --body-file docs/v2.3/sessions/SW-X2-S1.md
git ls-remote origin refs/heads/cursor/v23-x2-s1-splitsignal-live   # must print the same SHA as: git rev-parse HEAD
```
If `gh pr create` is refused (read-only `gh`), the environment opens the PR: check that its base is `cursor/sw-v23-integration-460c` and that it is a draft, and put the PR URL (or the compare URL from section 10, step 4) into the handoff.
If push fails for network reasons, retry up to 4 times waiting 4 s, 8 s, 16 s, 32 s; then STOP (S8).
Docs to update: only your handoff file, plus any doc listed in section 3.

## 9. Handoff file (create before committing)
Create `docs/v2.3/sessions/SW-X2-S1.md` with exactly these headings:
```markdown
# SW-X2-S1 handoff
- Branch: <exact branch name>   Base SHA: <from setup>   Head SHA: <git rev-parse HEAD>
- PR: <url, or compare URL>
## Done
<bullet list of what you implemented>
## Verification
<each command from section 6 and its final result line; integration PASSED/SKIPPED(reason)>
## Acceptance
<copy the checkboxes from sections 5 and 7, ticked>
## Decisions
<choices you made under hard rule 8, or 'none'>
## Needs other owner
<files outside your scope that should change, with the exact change; or 'none'>
## Codex review packet
<the block from section 11, filled in>
## Status
implemented + tested (NOT accepted; needs Codex review)
```

## 10. STOP conditions (never wait for a human)
STOP immediately when any of these is true:
- **S1** `git status --porcelain` is not empty before Setup. (Do not commit, stash or discard anything; skip steps 1–4 below and only report.)
- **S2** a dependency check prints `MISSING`.
- **S3** a command in section 6, or a check in section 5, still fails after **2 attempts**. One attempt = one edit to *your own files* followed by re-running the failing command.
- **S4** a “currently reads” / before-block in section 5 does not match the file, or a function named in section 5 does not exist.
- **S5** finishing would require editing a file that is not in section 3.
- **S6** a required environment variable prints `MISSING`.
- **S7** an external gate check (inference_server sync point or approval line) in section 5 fails.
- **S8** `git push` still fails after 4 retries (waits 4 s, 8 s, 16 s, 32 s).

What to do on STOP, in this order:
1. Commit whatever is complete inside your own files: `git add <your files> docs/v2.3/sessions/SW-X2-S1.md` then `git commit -m "WIP(SW-X2-S1): <one-line reason>"`.
2. Write the handoff (section 9) with `## Status` = `BLOCKED: <condition id> <one-line reason>`, and under `## Needs other owner` the exact file, function and change you need. Commit it.
3. Push: `git push -u origin cursor/v23-x2-s1-splitsignal-live` (plus your suffix).
4. Open the draft PR against `cursor/sw-v23-integration-460c` with the title prefix `[BLOCKED]`, or record the compare URL `https://github.com/pri8771/swarmai/compare/cursor/sw-v23-integration-460c...cursor/v23-x2-s1-splitsignal-live?expand=1` in the handoff.
5. End the session with a final message: the condition id, the reason, the branch and the head SHA.
Never work around a STOP by editing other files, weakening tests, or adding `skip`/`xfail`.

If `tests/tools/test_v20_cancel_killbound.py` fails once in the full run and you did not touch `sandbox_runner.py` or that test, re-run the full list once. If it passes, record both result lines in the handoff under Verification and continue; if it fails twice, STOP (S3). (The known race was fixed by SW-FIX-FLAKE; a new failure is worth reporting.)

## 11. Codex review packet (put this in the PR description and in the handoff)
```markdown
### Codex review packet — SW-X2-S1
- PR: <PR URL — fill in after the PR exists>
- Branch: <exact branch name>  Base: origin/cursor/sw-v23-integration-460c @ <base SHA from Setup>
- Head SHA: <output of `git rev-parse HEAD`; must equal `git ls-remote origin refs/heads/<branch>`>
- Diff for review: `git diff <base SHA>...<head SHA>`
- Files to review: `scripts/v23_splitsignal_smoke.py`, `tests/providers/test_v23_splitsignal_smoke.py`, `docs/evidence/v23/splitsignal_live.json`, `docs/v2.3/EXIT_CHECKLIST.md`, `docs/v2.3/STATUS.md`, `docs/v2.3/sessions/SW-X2-S1.md`
- Review focus (AGENTS.md Code Review Rules): cross-tenant/project access; secret disclosure; financial accounting (unknown usage or cost is never zero); unbounded retries; silently changed model behaviour; recovery gaps after a crash/restart; unsupported release claims ("accepted", "complete"). Session-specific: at most 2 live calls, approval line checked before any network call, evidence has no prompt/response text and no key.
- Checks run: <paste the final result line of every command in section 6>
- Verdict requested: `RECOMMEND_ACCEPT <head SHA>` or `REQUEST_CHANGES` with file:line findings.
```
