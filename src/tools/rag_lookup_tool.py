from functools import lru_cache

from langchain_core.tools import tool
from langchain_qdrant.qdrant import QdrantClient, QdrantVectorStore
from langchain_classic.storage import LocalFileStore
from langchain_classic.embeddings import CacheBackedEmbeddings
from langchain_openai import OpenAIEmbeddings
from config import settings, BASE_DIR
import pickle
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()
QDRANT_PATH = BASE_DIR / "vectorstore"
DOCUMENT_EMBED_CACHE_PATH = BASE_DIR / "vectorstore" / "document_embedding_cache"
QUERY_EMBED_CACHE_PATH = BASE_DIR / "vectorstore" / "query_embedding_cache"
COLLECTION_NAME   = "warehouse_sop"
PARENT_STORE_PATH  = BASE_DIR/ "src" / "parent_documents.pkl"



@lru_cache(maxsize=1)
def _load_cached_embeddings():
    """OpenAI embeddings wrapped with persistent disk cache."""
    underlying_embeddings = OpenAIEmbeddings(
        model=settings.OPENAI_EMBEDDING_MODEL,
        api_key=settings.OPENAI_API_KEY,
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
        )

@lru_cache(maxsize=1)
def _get_parent_dict() -> dict:
    with open(PARENT_STORE_PATH, "rb") as f:
        return pickle.load(f)

@tool("inbound_sop_lookup",
    description=(
        "Search inbound SOP/process documentation. "
        "Use this when the question is about expected process, policy, procedure, "
        "triage steps, business rules, receiving flow, ASN/PO handling, dock process, "
        "putaway process, or what should happen operationally. "
        "Do not use this for live transactional counts or current system state."
    ))
def sop_retrieval_tool(query: str, k: int = 3) -> list:
    """Retrieve relevant inbound SOP guidance for a natural-language question."""
    vectorstore = _get_vectorstore()
    parent_dict = _get_parent_dict()

        # Step 1 + 2: embedding + vector search happen here
    children = vectorstore.similarity_search(query, k=k)

        # Step 3: dedupe children → parents
    seen, parents = set(), []
    for child in children:
        pid = child.metadata.get("parent_id")
        if pid and pid not in seen and pid in parent_dict:
            seen.add(pid)
            parents.append(parent_dict[pid])

    return parents

