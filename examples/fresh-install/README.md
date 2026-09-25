# Fresh-install example

Portable mock/standalone startup with **no personal credentials or paths**.

Full walkthrough: [`docs/install/FRESH_INSTALL.md`](../../docs/install/FRESH_INSTALL.md)

```sh
# From repository root
uv sync
cp .env.example .env
cp examples/fresh-install/portable.env.example examples/fresh-install/portable.env
uv run swarm deploy doctor --profile mock
uv run swarm serve --host 127.0.0.1 --port 8765
```

Do not fill provider keys for the mock path. Do not substitute personal home directories into these commands.
