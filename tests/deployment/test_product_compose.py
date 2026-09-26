"""L6 product compose — console + api + worker packaging checks."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PRODUCT = ROOT / "deploy" / "compose" / "product.yml"
CONSOLE_DOCKERFILE = ROOT / "deploy" / "console" / "Dockerfile"
CONSOLE_NGINX = ROOT / "deploy" / "console" / "nginx.conf"
CONSOLE_ENTRY = ROOT / "deploy" / "console" / "docker-entrypoint.sh"
PRODUCT_ENV = ROOT / "deploy" / "env" / "product.env.example"


def test_product_compose_packages_real_path_services() -> None:
    text = PRODUCT.read_text(encoding="utf-8")
    assert "\n  api:" in text
    assert "\n  console:" in text
    assert "\n  worker:" in text
    assert "\n  db:" in text
    # No named lab hosts / public DNS as required topology.
    assert "r730" not in text.lower()
    assert "swarm.splitsignal.ai" not in text
    assert "mac-connector" not in text
    # Loopback publish for api + console; DB unpublished.
    assert "127.0.0.1:${SWARM_HOST_PORT" in text or "127.0.0.1:${SWARM_HOST_PORT:-8765}:8765" in text
    assert "SWARM_CONSOLE_HOST_PORT" in text
    db_idx = text.index("\n  db:")
    tail = text[db_idx:]
    end = len(tail)
    for marker in ("\nnetworks:", "\nvolumes:"):
        at = tail.find(marker)
        if at != -1:
            end = min(end, at)
    assert "ports:" not in tail[:end]
    assert "product_worker_ws" in text
    assert "SWARM_ALLOW_PAID: \"false\"" in text


def test_console_image_files_exist() -> None:
    assert CONSOLE_DOCKERFILE.is_file()
    assert CONSOLE_NGINX.is_file()
    assert CONSOLE_ENTRY.is_file()
    assert PRODUCT_ENV.is_file()
    nginx = CONSOLE_NGINX.read_text(encoding="utf-8")
    assert "proxy_pass http://api:8765" in nginx
    assert "location /v1/" in nginx
    assert "location /health/" in nginx
    entry = CONSOLE_ENTRY.read_text(encoding="utf-8")
    assert "__SWARM_CONSOLE__" in entry
    assert "SWARM_CONSOLE_TOKEN" in entry
    df = CONSOLE_DOCKERFILE.read_text(encoding="utf-8")
    assert "npm run build" in df
    assert "nginx" in df.lower()


def test_product_env_example_has_no_real_secrets() -> None:
    text = PRODUCT_ENV.read_text(encoding="utf-8")
    assert "replace-with" in text
    assert "sk-" not in text
    assert "SWARM_SEED_LOOPBACK_TOKEN" in text
    assert "SWARM_PG_PASSWORD" in text
    assert "SWARM_CONSOLE_HOST_PORT" in text


def _service_block(text: str, name: str) -> str:
    start = text.index(f"\n  {name}:\n")
    rest = text[start + 1 :]
    lines = rest.splitlines()
    block = [lines[0]]
    for line in lines[1:]:
        if line and not line.startswith("    ") and line.strip():
            break
        block.append(line)
    return "\n".join(block)


def test_worker_does_not_inherit_api_http_healthcheck() -> None:
    """V20-E10: the image HEALTHCHECK curls :8765, which the connector never serves."""
    text = PRODUCT.read_text(encoding="utf-8")
    worker = _service_block(text, "worker")
    assert "swarm.workers.connector" in worker
    assert "    healthcheck:\n      test:" in worker
    assert "/proc/1/cmdline" in worker
    assert "\n      disable: true" not in worker
    assert "8765/health" not in worker
    api = _service_block(text, "api")
    assert "http://127.0.0.1:8765/health/live" in api


def test_worker_healthcheck_command_is_valid_python() -> None:
    import subprocess
    import sys

    worker = _service_block(PRODUCT.read_text(encoding="utf-8"), "worker")
    code_line = next(ln for ln in worker.splitlines() if "/proc/1/cmdline" in ln)
    code = code_line.strip().removeprefix("- ").strip('"')
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=False
    )
    # PID 1 of the test host is not the connector: a clean "unhealthy" exit, no traceback.
    assert result.returncode == 1
    assert result.stderr == ""
