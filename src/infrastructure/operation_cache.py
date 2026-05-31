"""
Per-node LLM response caches.

Each node gets its own SQLite file rather than a shared cache. This isolation
means a cache miss in the router never evicts a warm synthesizer entry, and
clearing one node's cache during debugging doesn't affect the others.

SQLiteCache keys on (prompt, llm_string) so the same input to the same model
always hits. This is particularly valuable for the router and parallel-planner
nodes, which see repeated queries during development and eval runs.

The .cache/ directory is gitignored — cache files are local to each developer's
machine and should never be committed.
"""

from langchain_community.cache import SQLiteCache

from config import settings

_CACHE_DIR = settings.BASE_DIR / ".cache"
_CACHE_DIR.mkdir(exist_ok=True)


ROUTER_CACHE = SQLiteCache(database_path=str(_CACHE_DIR / "router.db"))
SOP_CACHE = SQLiteCache(database_path=str(_CACHE_DIR / "sop.db"))
SEQUENTIAL_NODE_CACHE = SQLiteCache(database_path=str(_CACHE_DIR / "sequential.db"))
PARALLEL_SUBTASK_NODE_CACHE = SQLiteCache(database_path=str(_CACHE_DIR / "parallel.db"))

GENERATE_SQL_QUERY_NODE_CACHE = SQLiteCache(database_path=str(_CACHE_DIR / "generate.db"))
SYNTHESIZER_NODE_CACHE = SQLiteCache(database_path=str(_CACHE_DIR / "synthesize.db"))