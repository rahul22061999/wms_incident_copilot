import re
from pathlib import Path
from typing import List, Dict
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
import pickle

CHAPTER_PATTERN = re.compile(r"(?m)^(\d+)\s+((?!\d)[A-Z][^\n]+?)\s*$")
SECTION_PATTERN = re.compile(r"(?m)^(\d+\.\d+)\s+(.+)$")


def chunk_text(document: List[Document]) -> list:
    """List of documents returned by ingesting"""
    docs = document
    child_documents = []

    def _all_merged_text():
        full_text = "\n\n".join(
            f"[PAGE {doc.metadata.get('page', i + 1)}]\n{doc.page_content}"
            for i, doc in enumerate(docs)
            if "table of contents" not in doc.page_content.lower()

        )
        return full_text

    def _create_parent_document():
        all_text = _all_merged_text()
        chapter_matches = list(CHAPTER_PATTERN.finditer(all_text))
        section_matches = list(SECTION_PATTERN.finditer(all_text))

        parent_documents = []

        for i, match in enumerate(chapter_matches):
            start = match.start()
            end = chapter_matches[i+1].start() if i + 1 < len(chapter_matches) else len(all_text)

            section_number = match.group(1)
            section_title = match.group(2)
            heading = match.group(0).strip()

            section_text = all_text[start:end]

            parent_documents.append(
                Document(
                    page_content=section_text,
                    metadata={
                        "parent_id": f"parent_{i}",
                        "section_number": section_number,
                         "heading": heading,
                         "title": section_title,
                         "doc_id": "warehouse_sop"
                    }
                )
            )
        return parent_documents


    def _save_parent_document(parent_documents_loaded: List):
        save_path = Path("src/parent_documents.pkl")

        if not save_path.exists():
            save_path.parent.mkdir(parents=True, exist_ok=True)

            parent_dict = {doc.metadata["parent_id"]: doc for doc in parent_documents_loaded}

            with open(save_path, "wb") as f:
                pickle.dump(parent_dict, f)

    def _split_child_document():
        parent_documents_loaded = _create_parent_document()

        child_doc_splitter = RecursiveCharacterTextSplitter(
            chunk_size=700,
            chunk_overlap=100
        )

        child_documents.extend(child_doc_splitter.split_documents(parent_documents_loaded))
        _save_parent_document(parent_documents_loaded)

    _split_child_document()

    return child_documents




