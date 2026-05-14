import asyncio
from config import settings

_graph_semaphore: asyncio.Semaphore | None = None

def get_graph_semaphore() -> asyncio.Semaphore:
    global _graph_semaphore
    if _graph_semaphore is None:
        _graph_semaphore = asyncio.Semaphore(settings.MAX_GRAPH_SEMAPHORE)
    return _graph_semaphore

def init_graph_semaphore(max_concurrent_runs: int) -> None:
    """Optional eager init. Safe to call multiple times."""
    global _graph_semaphore
    if _graph_semaphore is None:
        _graph_semaphore = asyncio.Semaphore(max_concurrent_runs)