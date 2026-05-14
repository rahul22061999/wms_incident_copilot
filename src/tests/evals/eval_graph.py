from langsmith.evaluation import evaluate
from workflows.graph.application_graph import graph

async def run_graph(inputs: dict) -> dict:
    result = await graph.ainvoke(inputs)
    return {
        "task": result.get("task"),
        "final_response": result.get("final_response"),
        "schedular_results": result.get("schedular_results"),
        "parallel_results": result.get("parallel_results"),
    }

def has_final_response(run, example) -> dict:
    return {
        "key": "has_final_response",
        "score": int(bool(run.outputs.get("final_response"))),
    }

def correct_route(run, example) -> dict:
    expected = example.outputs["expected_route"]
    actual_tasks = run.outputs.get("task", [])
    return {
        "key": "correct_route",
        "score": int(expected in actual_tasks),
        "comment": f"expected={expected!r} in tasks={actual_tasks}",
    }

def schedule_result_present(run, example) -> dict:
    # Only applies to schedule route
    if example.outputs["expected_route"] != "schedule":
        return {"key": "schedule_result_present", "score": None}  # N/A
    results = run.outputs.get("schedular_results", [])
    return {
        "key": "schedule_result_present",
        "score": int(len(results) > 0),
    }

results = evaluate(
    run_graph,
    data="wms-graph-evals",
    evaluators=[has_final_response, correct_route, schedule_result_present],
    experiment_prefix="graph-eval",
)