import asyncio

from dotenv import load_dotenv
from langsmith import Client
from langsmith.evaluation import aevaluate

from workflows.nodes.router_node import router_node
from domain.states.supervisor.diagnose_graph_state import WMState

load_dotenv()

client = Client()


async def build_state(inputs: dict) -> WMState:
    return WMState(
        ticket_number=inputs.get("ticket_number", "EVAL-001"),
        session_id=inputs.get("session_id", "eval-sess"),
        user_id=inputs.get("user_id", "eval-user"),
        description=inputs.get("description", ""),
    )


async def run_router(inputs: dict) -> dict:
    state = await build_state(inputs)

    result = await router_node(state)

    return {
        "task": result["task"]
    }


def correct_route(run, example) -> dict:
    expected = example.outputs["task"]
    actual = run.outputs.get("task", [])

    expected_sorted = sorted(expected)
    actual_sorted = sorted(actual)

    return {
        "key": "correct_route",
        "score": int(expected_sorted == actual_sorted),
        "comment": f"expected={expected_sorted} got={actual_sorted}",
    }


def is_valid_task_list(run, example) -> dict:
    task = run.outputs.get("task", [])

    valid = {
        "parallel",
        "orchestrator",
        "schedule",
        "cancel_schedule",
    }

    all_valid = isinstance(task, list) and all(t in valid for t in task)

    return {
        "key": "valid_task_values",
        "score": int(all_valid and len(task) > 0),
        "comment": f"task={task}",
    }


async def main():
    results = await aevaluate(
        run_router,
        data="wms-router-evals",
        evaluators=[correct_route, is_valid_task_list],
        experiment_prefix="router-eval",
        client=client,
        max_concurrency=4,
    )

    print(results)


if __name__ == "__main__":
    asyncio.run(main())