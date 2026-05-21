"""
Synthesizer hallucination and citation fidelity evaluation.

Tests the synthesizer node in isolation against pre-built input payloads.
Two evaluators:
- no_hallucination: uses GPT-4o as an independent judge to verify every claim
  in the synthesized output can be traced back to the raw input data. Uses a
  different model than the one being evaluated to avoid self-serving judgements.
- citations_reference_real_sources: checks that the "reference" field of every
  citation actually appears in the raw input string — a structural check that
  doesn't require an LLM judge.

raw_inputs is serialized to a string and stored in run.outputs so both
evaluators can access it without re-running the synthesizer.
"""

import asyncio
import json

from dotenv import load_dotenv
from langsmith import Client
from langsmith.evaluation import aevaluate
from langchain_openai import ChatOpenAI

from domain.states.supervisor.diagnose_graph_state import WMState
from workflows.nodes.synthesizer_node import synthesizer_node

load_dotenv()
client = Client()
judge_llm = ChatOpenAI(model="gpt-4o", temperature=0)


async def run_synthesizer(inputs: dict) -> dict:
    state = WMState(
        ticket_number="EVAL-001",
        session_id="eval-sess",
        user_id="eval-user",
        description="",
        parallel_results=inputs.get("parallel_results", []),
        sequential_results=inputs.get("sequential_results", []),
    )
    result = await synthesizer_node(state)
    summarized = result.get("summarized_result") or {}
    return {
        "summarized_issue": summarized.get("summarized_issue", ""),
        "confidence": summarized.get("confidence", 0.0),
        "citations": summarized.get("citations", []),
        "raw_inputs": json.dumps(inputs, default=str),
    }


def no_hallucination(run, example) -> dict:
    summary = run.outputs.get("summarized_issue", "")
    raw_inputs = run.outputs.get("raw_inputs", "")

    prompt = (
        "You are a hallucination checker for a warehouse AI system.\n\n"
        f"INPUT DATA (all facts the model was given):\n{raw_inputs}\n\n"
        f"MODEL SUMMARY:\n{summary}\n\n"
        "Does the summary contain ANY claim, number, identifier, or conclusion "
        "that cannot be traced back to the input data?\n"
        "Answer YES (hallucination present) or NO (all facts grounded). Only answer YES or NO."
    )

    response = judge_llm.invoke(prompt)
    hallucination_detected = "yes" in response.content.strip().lower()
    return {
        "key": "no_hallucination",
        "score": int(not hallucination_detected),
        "comment": response.content.strip(),
    }


def citations_reference_real_sources(run, example) -> dict:
    citations = run.outputs.get("citations", [])
    raw_inputs = run.outputs.get("raw_inputs", "").lower()

    if not citations:
        return {"key": "citations_reference_real_sources", "score": 0, "comment": "no citations produced"}

    bad = [c["reference"] for c in citations if c.get("reference", "").lower() not in raw_inputs]
    return {
        "key": "citations_reference_real_sources",
        "score": int(len(bad) == 0),
        "comment": f"ungrounded citations: {bad}" if bad else "all citations grounded",
    }


async def main():
    results = await aevaluate(
        run_synthesizer,
        data="wms-synthesizer-fidelity-evals",
        evaluators=[no_hallucination, citations_reference_real_sources],
        experiment_prefix="synthesizer-fidelity",
        client=client,
        max_concurrency=2,
    )
    print(results)


if __name__ == "__main__":
    asyncio.run(main())
