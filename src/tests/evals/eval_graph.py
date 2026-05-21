"""
LangSmith end-to-end graph evaluation.

Runs the full compiled graph against the "wms-graph-evals" dataset and scores:
- has_summarized_result: the graph completed and produced output (liveness check).
- correct_route: the router sent the query down the expected task path.
- schedule_result_present: for schedule examples only — confirms the scheduler
  node ran and produced output. Returns score=None for non-schedule examples so
  LangSmith excludes them from the aggregate for this metric.

max_concurrency=2 is conservative because each graph run can spawn multiple
parallel LLM calls internally, and the shared graph_semaphore already limits
concurrency at the node level.
"""

import asyncio

from dotenv import load_dotenv
from langsmith import Client
from langsmith.evaluation import aevaluate

from domain.states.supervisor.diagnose_graph_state import WMState
from workflows.graph.application_graph import graph

load_dotenv()
client = Client()


async def run_graph(inputs: dict) -> dict:
    state = WMState(
        ticket_number=inputs.get("ticket_number", "EVAL-001"),
        session_id=inputs.get("session_id", "eval-sess"),
        user_id=inputs.get("user_id", "eval-user"),
        description=inputs["description"],
    )
    result = await graph.ainvoke(state)
    return {
        "task": result.get("task", []),
        "summarized_result": result.get("summarized_result"),
        "schedular_results": result.get("schedular_results", []),
    }


def has_summarized_result(run, example) -> dict:
    return {
        "key": "has_summarized_result",
        "score": int(bool(run.outputs.get("summarized_result"))),
    }


def correct_route(run, example) -> dict:
    expected = example.outputs["expected_route"]
    actual = run.outputs.get("task", [])
    return {
        "key": "correct_route",
        "score": int(expected in actual),
        "comment": f"expected={expected!r} in tasks={actual}",
    }


def schedule_result_present(run, example) -> dict:
    if example.outputs["expected_route"] != "schedule":
        return {"key": "schedule_result_present", "score": None}
    results = run.outputs.get("schedular_results", [])
    return {"key": "schedule_result_present", "score": int(len(results) > 0)}


async def main():
    results = await aevaluate(
        run_graph,
        data="wms-graph-evals",
        evaluators=[has_summarized_result, correct_route, schedule_result_present],
        experiment_prefix="graph-eval",
        client=client,
        max_concurrency=2,
    )
    print(results)


if __name__ == "__main__":
    asyncio.run(main())
