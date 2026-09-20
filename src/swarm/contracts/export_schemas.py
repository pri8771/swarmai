"""Export JSON Schema for shared contracts."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel

from swarm.contracts.fixtures import all_required_type_instances


def main() -> None:
    root = Path(__file__).resolve().parents[3] / "schemas" / "contracts"
    root.mkdir(parents=True, exist_ok=True)
    for name, obj in all_required_type_instances().items():
        assert isinstance(obj, BaseModel)
        schema = obj.__class__.model_json_schema()
        path = root / f"{name}.schema.json"
        path.write_text(json.dumps(schema, indent=2) + "\n")
        print(path)


if __name__ == "__main__":
    main()
