import logging
import pickle
from functools import lru_cache

from dotenv import load_dotenv
from langchain_classic.embeddings import CacheBackedEmbeddings
from langchain_classic.storage import LocalFileStore
from langchain_core.tools import tool
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import FastEmbedSparse, RetrievalMode
from langchain_qdrant.qdrant import QdrantClient, QdrantVectorStore
from qdrant_client.models import Fusion, FusionQuery, Prefetch, SparseVector

from config import settings

logger = logging.getLogger(__name__)
load_dotenv()

QDRANT_PATH = settings.BASE_DIR / "vectorstore"
DOCUMENT_EMBED_CACHE_PATH = settings.BASE_DIR / "vectorstore" / "document_embedding_cache"
QUERY_EMBED_CACHE_PATH = settings.BASE_DIR / "vectorstore" / "query_embedding_cache"
COLLECTION_NAME = "warehouse_sop"
PARENT_STORE_PATH = settings.BASE_DIR / "src" / "parent_documents.pkl"


@lru_cache(maxsize=1)
def _load_cached_embeddings():
    underlying_embeddings = OpenAIEmbeddings(
        model=settings.OPENAI_EMBEDDING_MODEL,
        api_key=settings.OPENAI_API_KEY
    )
    return CacheBackedEmbeddings.from_bytes_store(
        underlying_embeddings=underlying_embeddings,
        document_embedding_cache=LocalFileStore(str(DOCUMENT_EMBED_CACHE_PATH)),
        query_embedding_cache=LocalFileStore(str(QUERY_EMBED_CACHE_PATH)),
        namespace=settings.OPENAI_EMBEDDING_MODEL,
    )


@lru_cache(maxsize=1)
def _get_qdrant_client():
    return QdrantClient(path=str(QDRANT_PATH))


@lru_cache(maxsize=1)
def _get_vectorstore():
    return QdrantVectorStore(
        client=_get_qdrant_client(),
        collection_name=COLLECTION_NAME,
        embedding=_load_cached_embeddings(),
        sparse_embedding=FastEmbedSparse(model_name="Qdrant/bm25"),
        retrieval_mode=RetrievalMode.HYBRID,
        vector_name="dense",
        sparse_vector_name="sparse",
    )


@lru_cache(maxsize=1)
def _get_parent_dict() -> dict:
    with open(PARENT_STORE_PATH, "rb") as f:
        return pickle.load(f)

        # ↓ PUT IT HERE — after the cached helpers, before the @tool


async def _hybrid_search_tuned(query: str, k: int = 5, rrf_k: int = 60) -> list:
    """
    Direct Qdrant hybrid query — exposes RRF k for tuning.
    Returns raw Qdrant ScoredPoint objects.
    Called by sop_retrieval_tool instead of vectorstore.asimilarity_search().
    """
    client = _get_qdrant_client()
    embeddings = _load_cached_embeddings()
    sparse_model = FastEmbedSparse(model_name="Qdrant/bm25")

    dense_vector = await embeddings.aembed_query(query)

    sparse_embedding = sparse_model.embed_query(query)

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        prefetch=[
            Prefetch(
                query=dense_vector,
                using="dense",
                limit=k,
            ),
            Prefetch(
                query=SparseVector(
                    indices=sparse_embedding.indices,
                    values=sparse_embedding.values,
                ),
                using="sparse",
                limit=k,
            ),
        ],
        query=FusionQuery(fusion=Fusion.RRF),
        limit=k,
    )

    return results.points


# ↓ sop_retrieval_tool now calls _hybrid_search_tuned instead of asimilarity_search
@tool("sop_lookup",
      description=(
              "Search inbound SOP/process documentation. "
              "Use this when the question is about expected process, policy, procedure, "
              "triage steps, business rules, receiving flow, ASN/PO handling, dock process, "
              "putaway process, or what should happen operationally. "
              "Do not use this for live transactional counts or current system state."
      ))
async def sop_retrieval_tool(query: str, k: int = 5) -> list:
    parent_dict = _get_parent_dict()

    # CHANGED: was vectorstore.asimilarity_search() → now _hybrid_search_tuned()
    points = await _hybrid_search_tuned(query, k=k)

    # CHANGED: points are ScoredPoint objects, not LangChain Documents.
    # LangChain stores metadata under payload["metadata"] when indexing.
    seen, parents = set(), []
    for point in points:
        pid = point.payload.get("metadata", {}).get("parent_id")
        if pid and pid not in seen and pid in parent_dict:
            seen.add(pid)
            parent_doc = parent_dict[pid]
            parents.append({
                "text": parent_doc.page_content,
                "metadata": parent_doc.metadata,
            })

    return parents