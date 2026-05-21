"""
End-to-end incident response evaluation (pytest-based).

Runs the full graph against real incident scenarios defined in eval_cases.py
and asserts that the synthesized output:
  - contains domain-specific terms that must appear in a correct answer
  - excludes terms that would indicate a wrong or hallucinated diagnosis
  - meets a minimum confidence threshold (0.70)

Unlike the LangSmith evals, this is a pytest test that fails the CI run if
any case regresses. It hits real LLMs so it belongs in a pre-release gate,
not in the PR pipeline — see the CI/CD strategy in the project docs.
"""

import pytest

from domain.states.supervisor.diagnose_graph_state import WMState
from tests.evals.conftest import (
    assert_contains_required_terms,
    assert_excludes_forbidden_terms,
)
from tests.evals.eval_cases import INCIDENT_EVAL_CASES
from workflows.graph.application_graph import graph


@pytest.mark.asyncio
@pytest.mark.parametrize("case", INCIDENT_EVAL_CASES, ids=[c.name for c in INCIDENT_EVAL_CASES])
async def test_incident_answers_meet_expected_behavior(case):
    state = WMState(
        ticket_number=case.input["ticket_number"],
        session_id=case.input["session_id"],
        user_id=case.input["user_id"],
        description=case.input["query"],
    )
    result = await graph.ainvoke(state)

    summarized = result.get("summarized_result") or {}
    answer = summarized.get("summarized_issue", "")
    confidence = float(summarized.get("confidence", 0.0))

    assert answer, "Graph returned no summarized_issue"
    assert_contains_required_terms(answer, case.expected["must_include"])
    assert_excludes_forbidden_terms(answer, case.expected["must_not_include"])
    assert confidence >= 0.70, f"Confidence {confidence} below threshold"
