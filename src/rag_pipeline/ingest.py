from pathlib import Path
from typing import List, Optional
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_core.documents import Document
from config import BASE_DIR


def ingest_sop_docs(path: Optional[Path] = None) -> List[Document]:
    """Ingest data into RagPipeline"""

    if path is None or not path.exists():
        path = BASE_DIR / "data" / "sop"

    def _load_documents():
        doc_loader = PyPDFDirectoryLoader(str(path))
        loaded_document = doc_loader.load()

        return loaded_document

    return _load_documents()









