"""
LangSmith evaluation for the parallel execution planner node.

Tests three properties of the planner in isolation:
- correct_subtask_count: the number of subtasks matches the expected count.
- no_over_decomposition: for single-intent queries (is_single_intent=True),
  the planner must return exactly 1 subtask. Over-decomposition fragments
  context and produces worse synthesized answers.
- correct_tool_assignment: the set of tools assigned across all subtasks
  matches the expected set (sql_lookup_tool, sop_lookup, or both).

Runs the planner node directly rather than the full graph so failures are
attributable to the planner prompt, not the router or synthesizer.
"""

import asyncio

from dotenv import load_dotenv
from langsmith import Client
from langsmith.evaluation import aevaluate

from domain.states.supervisor.diagnose_graph_state import WMState
from workflows.nodes.parallel_execution_node import plan_parallel_subtask_node

load_dotenv()
client = Client()


async def run_parallel_node(inputs: dict) -> dict:
    state = WMState(
        ticket_number="EVAL-001",
        session_id="eval-sess",
        user_id="eval-user",
        description="",
        enriched_query=inputs["description"],
    )
    result = await plan_parallel_subtask_node(state)
    subtasks = result.get("subtasks", [])
    return {
        "subtask_count": len(subtasks),
        "tools_used": [t.tool for t in subtasks],
        "domains": [t.domain for t in subtasks],
    }


def correct_subtask_count(run, example) -> dict:
    expected = example.outputs["expected_subtask_count"]
    actual = run.outputs.get("subtask_count", 0)
    return {
        "key": "correct_subtask_count",
        "score": int(actual == expected),
        "comment": f"expected={expected} got={actual}",
    }


def no_over_decomposition(run, example) -> dict:
    if not example.outputs.get("is_single_intent"):
        return {"key": "no_over_decomposition", "score": None}
    count = run.outputs.get("subtask_count", 0)
    return {
        "key": "no_over_decomposition",
        "score": int(count == 1),
        "comment": f"single-intent query produced {count} subtasks",
    }


def correct_tool_assignment(run, example) -> dict:
    expected_tools = set(example.outputs.get("expected_tools", []))
    actual_tools = set(run.outputs.get("tools_used", []))
    return {
        "key": "correct_tool_assignment",
        "score": int(expected_tools == actual_tools),
        "comment": f"expected={expected_tools} got={actual_tools}",
    }


async def main():
    results = await aevaluate(
        run_parallel_node,
        data="wms-parallel-node-evals",
        evaluators=[correct_subtask_count, no_over_decomposition, correct_tool_assignment],
        experiment_prefix="parallel-node-eval",
        client=client,
        max_concurrency=4,
    )
    print(results)


if __name__ == "__main__":
    asyncio.run(main())
