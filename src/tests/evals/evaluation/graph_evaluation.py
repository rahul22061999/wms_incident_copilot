import asyncio
import json
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from config import settings
from domain.states.supervisor.diagnose_graph_state import WMState
from infrastructure.app_context_builder import AppContextBuilder
from infrastructure.context_access import set_app_context
from tests.evals.evaluation.usage_tracker import UsageTracker
from workflows.graph.application_graph import graph as application_graph

load_dotenv()
evaluation_dataset_path = Path(settings.BASE_DIR /"src" / "tests" / "evals"/"datasets" / "graph_evaluation_dataset.jsonl")
def load_dataset(path: Path):
    rows = []
    with path.open( "r", encoding="utf-8") as f:
        for line in f:
            rows.append(json.loads(line))

    return rows

EVAL_LABELS = ["sequential", "parallel", "schedule", "cancel_schedule"]


def extract_predicted_task(result: Any) -> str:
    if isinstance(result, dict):
        tasks = result.get("selected_tasks") or result.get("task") or []
    else:
        tasks = getattr(result, "selected_tasks", None) or getattr(result, "task", [])

    if isinstance(tasks, str):
        return tasks
    return tasks[0] if tasks else "unknown"


def compute_metrics(y_true: list[str], y_pred: list[str]) -> dict:
    total = len(y_true)
    correct = sum(t == p for t, p in zip(y_true, y_pred))

    per_class = {}
    for label in EVAL_LABELS:
        tp = sum(t == label and p == label for t, p in zip(y_true, y_pred))
        fp = sum(t != label and p == label for t, p in zip(y_true, y_pred))
        fn = sum(t == label and p != label for t, p in zip(y_true, y_pred))
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
        per_class[label] = {"tp": tp, "fp": fp, "fn": fn, "precision": precision, "recall": recall, "f1": f1}

    return {
        "total": total,
        "correct": correct,
        "accuracy": correct / total if total else 0.0,
        "macro_precision": sum(v["precision"] for v in per_class.values()) / len(EVAL_LABELS),
        "macro_recall": sum(v["recall"] for v in per_class.values()) / len(EVAL_LABELS),
        "macro_f1": sum(v["f1"] for v in per_class.values()) / len(EVAL_LABELS),
        "per_class": per_class,
    }


async def evaluate_graph():
    rows = load_dataset(evaluation_dataset_path)
    print(f"Loaded {len(rows)} rows from dataset.")

    y_true, y_pred, failures = [], [], []

    usage_tracker = UsageTracker()

    for row in rows:
        expected_task = row["expected_task"][0]

        state = WMState(
            description=row["description"],
            ticket_number=row["ticket_number"],
            session_id=row.get("session_id", row["user_id"]),
            user_id=row["user_id"],
            is_scheduled_run=row.get("is_scheduled_run", False),
        )

        result = await application_graph.ainvoke(
            input=state,
            config={"callbacks": [usage_tracker]}
        )
        predicted_task = extract_predicted_task(result)

        y_true.append(expected_task)
        y_pred.append(predicted_task)

        if predicted_task != expected_task:
            failures.append({
                "ticket_number": row["ticket_number"],
                "expected": expected_task,
                "predicted": predicted_task,
            })

    metrics = compute_metrics(y_true, y_pred)

    print("\n===== EVALUATION SUMMARY =====")
    print(f"Total:      {metrics['total']}")
    print(f"Correct:    {metrics['correct']}")
    print(f"Accuracy:   {metrics['accuracy']:.3f}")
    print(f"Macro P:    {metrics['macro_precision']:.3f}")
    print(f"Macro R:    {metrics['macro_recall']:.3f}")
    print(f"Macro F1:   {metrics['macro_f1']:.3f}")
    print(f"\nInput tokens:  {usage_tracker.total_input_tokens}")
    print(f"Output tokens: {usage_tracker.total_output_tokens}")
    print(f"Est. cost:     ${usage_tracker.total_cost:.4f}")

    for model, cost in sorted(usage_tracker.cost_by_model.items(), key=lambda x: -x[1]):
        print(f"  {model:30} ${cost:.6f}")

    print("\n===== PER-CLASS =====")
    for label, v in metrics["per_class"].items():
        print(f"{label:16} P={v['precision']:.3f} R={v['recall']:.3f} F1={v['f1']:.3f} TP={v['tp']} FP={v['fp']} FN={v['fn']}")

    if failures:
        print("\n===== FAILURES =====")
        for f in failures:
            print(f"- {f['ticket_number']} | expected={f['expected']} | predicted={f['predicted']}")

    return metrics


async def main():
    builder = AppContextBuilder(settings)
    ctx, stack = await builder.build()
    set_app_context(ctx)

    try:
        result = await evaluate_graph()
        print(result)
    except Exception:
        await stack.aclose()

if __name__ == "__main__":
    asyncio.run(main())