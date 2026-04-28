import asyncio

_graph_semaphore: asyncio.Semaphore | None = None

def init_graph_semaphore(max_concurrent_runs: int):
    global _graph_semaphore
    if _graph_semaphore is None:
        _graph_semaphore = asyncio.Semaphore(max_concurrent_runs)

def get_graph_semaphore() -> asyncio.Semaphore:
    global _graph_semaphore
    if _graph_semaphore is None:
        raise RuntimeError('Graph semaphore not initialized')
    return _graph_semaphore