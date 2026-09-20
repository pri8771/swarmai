"""V0.8 product experience — projects, contracts, history, journey."""

from swarm.product.contracts import public_product_contract
from swarm.product.history import HistoryIndex
from swarm.product.projects import ProjectConfig, ProjectStore

__all__ = [
    "HistoryIndex",
    "ProjectConfig",
    "ProjectStore",
    "public_product_contract",
    "run_product_journey",
]


def run_product_journey(repo):  # type: ignore[no-untyped-def]
    from swarm.product.journey import run_product_journey as _run

    return _run(repo)
