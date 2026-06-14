from typing import List

from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant.fastembed_sparse import FastEmbedSparse
from langchain_qdrant import RetrievalMode
from langchain_qdrant.qdrant import QdrantClient, QdrantVectorStore
from qdrant_client.conversions.common_types import SparseVectorParams
from qdrant_client.http.models import Distance, VectorParams, SparseIndexParams

from config import settings


def embed_docs(documents: List[Document]):
    embedding_model = OpenAIEmbeddings(model=settings.OPENAI_EMBEDDING_MODEL, api_key=settings.OPENAI_API_KEY)

    sparse_embeddings_model = FastEmbedSparse(model_name="Qdrant/bm25")

    def _create_vector_store():
        # Absolute path — must match rag_lookup_tool._get_qdrant_client(),
        # otherwise indexing and retrieval use different folders.
        client = QdrantClient(
            path=str(settings.BASE_DIR / "vectorstore")
        )

        if not client.collection_exists(collection_name="warehouse_sop"):
            client.create_collection(
                collection_name="warehouse_sop",
                vectors_config={
                    "dense": VectorParams(size=1536, distance=Distance.COSINE)
                },
                sparse_vectors_config={
                    "sparse": SparseVectorParams(
                        index=SparseIndexParams(on_disk=False)
                    )
                },
            )

        return client

    vectorstore = QdrantVectorStore(
        client=_create_vector_store(),
        collection_name="warehouse_sop",
        embedding=embedding_model,
        sparse_embedding=sparse_embeddings_model,
        retrieval_mode=RetrievalMode.HYBRID,
        sparse_vector_name="sparse",
        vector_name="dense"
    )

    vectorstore.add_documents(documents)

    return True
