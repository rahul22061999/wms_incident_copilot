import asyncio
import json
from pathlib import Path

from domain.states.supervisor.diagnose_graph_state import WMState
from workflows.nodes.router_node import router_node

DATASET_PATH = Path("src/tests/evals/datasets/router_dataset.jsonl")


def load_dataset(path: Path) -> list[dict]:
    rows = []

    with path.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                rows.append(json.loads(line))

    return rows


def normalize_task(task):
    if isinstance(task, list):
        return task[0]
    return task


def calculate_metrics(y_true, y_pred):
    labels = set(y_true + y_pred)

    print("\nPer-Class Metrics")
    print("-----------------")

    for label in labels:
        tp = fp = fn = 0

        for actual, predicted in zip(y_true, y_pred):
            if actual == label and predicted == label:
                tp += 1
            elif actual != label and predicted == label:
                fp += 1
            elif actual == label and predicted != label:
                fn += 1

        precision = tp / (tp + fp) if tp + fp else 0
        recall = tp / (tp + fn) if tp + fn else 0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0

        print(f"\nClass: {label}")
        print(f"Precision: {precision:.2%}")
        print(f"Recall:    {recall:.2%}")
        print(f"F1:        {f1:.2%}")


async def evaluate_router() -> None:
    rows = load_dataset(DATASET_PATH)

    total = 0
    correct = 0
    failures = []

    y_true = []
    y_pred = []

    for row in rows:
        state = WMState(
            description=row["description"],
            ticket_number=row["ticket_number"],
            user_id=row["user_id"],
            is_scheduled_run=row["is_scheduled_run"],
            session_id="rahul",
        )

        result = await router_node(state)

        actual_task = normalize_task(result["task"])
        expected_task = normalize_task(row["expected_task"])

        y_true.append(expected_task)
        y_pred.append(actual_task)

        total += 1

        if actual_task == expected_task:
            correct += 1
        else:
            failures.append(
                {
                    "description": row["description"],
                    "expected_task": expected_task,
                    "actual_task": actual_task,
                    "enriched_query": result.get("enriched_query"),
                }
            )

    accuracy = correct / total if total else 0

    print("\nRouter Eval Results")
    print("-------------------")
    print(f"Total:    {total}")
    print(f"Correct:  {correct}")
    print(f"Failed:   {len(failures)}")
    print(f"Accuracy: {accuracy:.2%}")

    calculate_metrics(y_true, y_pred)

    if failures:
        print("\nFailures:")
        for failure in failures:
            print(json.dumps(failure, indent=2))


if __name__ == "__main__":
    asyncio.run(evaluate_router())