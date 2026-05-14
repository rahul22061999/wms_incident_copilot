# tests/evals/eval_synthesizer_quality.py
from langsmith.evaluation import LangChainStringEvaluator
from langchain_openai import ChatOpenAI
from langsmith.evaluation import evaluate

llm = ChatOpenAI(model="gpt-4o")

# LangSmith built-in criteria evaluator
criteria_evaluator = LangChainStringEvaluator(
    "criteria",
    config={
        "criteria": {
            "warehouse_relevance": "Does the response directly address the warehouse operations query?",
            "actionable": "Does the response provide actionable next steps or clear findings?",
            "concise": "Is the response concise without unnecessary filler?",
        },
        "llm": llm,
    },
    prepare_data=lambda run, example: {
        "input": example.inputs["description"],
        "prediction": run.outputs.get("final_response", ""),
    },
)

results = evaluate(
    run_graph,
    data="wms-graph-evals",
    evaluators=[criteria_evaluator],
    experiment_prefix="synthesizer-quality",
)