from typing import List
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant.qdrant import QdrantClient, QdrantVectorStore
from qdrant_client.http.models import VectorParams, Distance
from config import settings


def embed_docs(documents: List[Document]):
    embedding_model = OpenAIEmbeddings(model=settings.OPENAI_EMBEDDING_MODEL, api_key=settings.OPENAI_API_KEY)

    def _create_vector_store():
        client = QdrantClient(
            path=settings.VECTOR_STORE_PATH
        )

        if not client.collection_exists(collection_name="warehouse_sop"):
            client.create_collection(
                collection_name="warehouse_sop",
                vectors_config=VectorParams(
                    size=1536,
                    distance=Distance.COSINE
                )
            )

        return client

    vectorstore = QdrantVectorStore(
        client=_create_vector_store(),
        collection_name="warehouse_sop",
        embedding=embedding_model

    )
    vectorstore.add_documents(documents)

    return True
