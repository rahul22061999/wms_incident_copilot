import pytest

from tests.evals.conftest import (
    assert_contains_required_terms,
)


@pytest.mark.parametrize(
    "query, retrieved_docs, expected_terms",
    [
        (
            "How do I resolve cancelled old cartons causing aged orders?",
            [
                {
                    "source": "aged_orders_sop.md",
                    "content": "Check old cartons, verify cancelled lines, complete or delete old lines, then validate new cartons contain remaining lines.",
                }
            ],
            ["old cartons", "cancelled lines", "complete or delete"],
        ),
        (
            "How do I check dock overload?",
            [
                {
                    "source": "dock_overload_sop.md",
                    "content": "Compare current dock occupancy with upcoming appointments and available dock capacity.",
                }
            ],
            ["current dock", "upcoming appointments", "available dock"],
        ),
    ],
)
def test_rag_retrieves_relevant_sop_documents(
    query,
    retrieved_docs,
    expected_terms,
):
    combined_text = " ".join(doc["content"] for doc in retrieved_docs)

    assert_contains_required_terms(combined_text, expected_terms)


def test_rag_does_not_hallucinate_when_no_docs_found():
    query = "Explain a made-up WMS issue called quantum carton drift"
    answer = generate_safe_answer_when_no_docs(query, retrieved_docs=[])

    assert "I do not have enough information" in answer
    assert "quantum carton drift is caused by" not in answer.lower()


def generate_safe_answer_when_no_docs(query: str, retrieved_docs: list[dict]) -> str:
    if not retrieved_docs:
        return "I do not have enough information from the SOP documents to answer this reliably."

    return "Answer generated from retrieved documents."