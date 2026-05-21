"""
Static incident eval cases for end-to-end pytest tests.

Each EvalCase pairs a realistic incident query with the terms that must (or must
not) appear in a correct diagnosis. must_include terms are chosen to be specific
enough to verify the model actually reasoned about the right domain — generic
terms like "issue" or "problem" would pass even on a wrong answer. must_not_include
terms catch known failure modes: hallucinated causes, off-topic explanations, or
stock refusals ("cannot answer").

Add new cases here as new incident types are observed in production. Keep the
must_include list tight (3-5 terms) — a long list makes cases brittle and hard
to maintain when the model wording changes.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class EvalCase:
    name: str
    input: dict[str, Any]
    expected: dict[str, Any]


INCIDENT_EVAL_CASES = [
    EvalCase(
        name="aged_orders_due_to_cancelled_old_cartons",
        input={
            "ticket_number": "INC0003",
            "query": "Why are orders aging and not releasing?",
            "user_id": "rahul",
            "session_id": "eval-session-001",
        },
        expected={
            "must_include": [
                "old cartons",
                "cancelled",
                "reallocated",
                "remaining lines",
            ],
            "must_not_include": [
                "random inventory issue",
                "network outage",
            ],
        },
    ),
    EvalCase(
        name="dock_overload_prediction",
        input={
            "ticket_number": "INC0004",
            "query": "Are docks overloaded based on current dock status and upcoming appointments?",
            "user_id": "rahul",
            "session_id": "eval-session-002",
        },
        expected={
            "must_include": [
                "current dock",
                "upcoming appointments",
                "available docks",
                "risk",
            ],
            "must_not_include": [
                "cannot answer",
            ],
        },
    ),
    EvalCase(
        name="rf_carton_alert_forward_pick_volume",
        input={
            "ticket_number": "INC0005",
            "query": "Why is alert 1030 missing some cartons?",
            "user_id": "rahul",
            "session_id": "eval-session-003",
        },
        expected={
            "must_include": [
                "RF cartons",
                "forward pick",
                "volume",
            ],
            "must_not_include": [
                "Temporal failure",
                "database corruption",
            ],
        },
    ),
]