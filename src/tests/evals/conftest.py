"""
Shared pytest fixtures and assertion helpers for the eval suite.

assert_contains_required_terms / assert_excludes_forbidden_terms are used
across multiple eval files. Centralising them here means the error messages and
matching logic stay consistent — a change to case sensitivity or whitespace
handling only needs to happen in one place.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def fake_user_id():
    return "rahul"


@pytest.fixture
def fake_ticket_number():
    return "INC0003"


@pytest.fixture
def fake_request():
    request = MagicMock()
    request.is_disconnected = AsyncMock(return_value=False)
    return request


@pytest.fixture
def fake_llm_response():
    return {
        "answer": "The issue appears related to old cartons being cancelled and reallocated. New cartons contain the remaining lines, which can cause aged orders if old carton lines were not completed or deleted.",
        "confidence": 0.91,
        "sources": ["job_schedule_event", "pickwork", "ord_line"],
    }


def assert_contains_required_terms(text: str, required_terms: list[str]):
    text_lower = text.lower()

    missing = [
        term for term in required_terms
        if term.lower() not in text_lower
    ]

    assert not missing, f"Missing required terms: {missing}"


def assert_excludes_forbidden_terms(text: str, forbidden_terms: list[str]):
    text_lower = text.lower()

    present = [
        term for term in forbidden_terms
        if term.lower() in text_lower
    ]

    assert not present, f"Forbidden terms found: {present}"