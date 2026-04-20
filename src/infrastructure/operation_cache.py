

from langchain_community.cache import SQLiteCache

from config import BASE_DIR

_CACHE_DIR = BASE_DIR / ".cache"
_CACHE_DIR.mkdir(exist_ok=True)


ROUTER_CACHE = SQLiteCache(database_path=str(_CACHE_DIR / "router.db"))
SOP_CACHE = SQLiteCache(database_path=str(_CACHE_DIR / "sop.db"))
SEQUENTIAL_NODE_CACHE = SQLiteCache(database_path=str(_CACHE_DIR / "sequential.db"))
PARALLEL_SUBTASK_NODE_CACHE = SQLiteCache(database_path=str(_CACHE_DIR / "parallel.db"))

GENERATE_SQL_QUERY_NODE_CACHE = SQLiteCache(database_path=str(_CACHE_DIR / "generate.db"))
SYNTHESIZER_NODE_CACHE = SQLiteCache(database_path=str(_CACHE_DIR / "synthesize.db"))