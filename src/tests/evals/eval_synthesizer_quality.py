import asyncio

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langsmith import Client
from langsmith.evaluation import LangChainStringEvaluator, aevaluate

from domain.states.supervisor.diagnose_graph_state import WMState
from workflows.graph.application_graph import graph

load_dotenv()
client = Client()
llm = ChatOpenAI(model="gpt-4o", temperature=0)


async def run_graph(inputs: dict) -> dict:
    state = WMState(
        ticket_number=inputs.get("ticket_number", "EVAL-001"),
        session_id=inputs.get("session_id", "eval-sess"),
        user_id=inputs.get("user_id", "eval-user"),
        description=inputs["description"],
    )
    result = await graph.ainvoke(state)
    summarized = result.get("summarized_result") or {}
    return {"final_response": summarized.get("summarized_issue", "")}


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


async def main():
    results = await aevaluate(
        run_graph,
        data="wms-graph-evals",
        evaluators=[criteria_evaluator],
        experiment_prefix="synthesizer-quality",
        client=client,
        max_concurrency=2,
    )
    print(results)


if __name__ == "__main__":
    asyncio.run(main())
