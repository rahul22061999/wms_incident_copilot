from langchain_core.messages import HumanMessage, SystemMessage

from domain.states.supervisor.diagnose_graph_state import WMState
from domain.states.synthesizer_node_state import SynthesizerNodeReturnState
from infrastructure.operation_cache import SYNTHESIZER_NODE_CACHE
from models.model_loader import get_ollama_llm
import json

def synthesizer_node(state: WMState):
    #return parallel execution results and sequential results too

    llm = get_ollama_llm(cache=SYNTHESIZER_NODE_CACHE).with_structured_output(SynthesizerNodeReturnState)

    combined_results = {
        "parallel_results": getattr(state, "parallel_results", None) or [],
        "sequential_results": getattr(state, "sequential_results", None) or [],
        "schedular_results": getattr(state, "schedular_results", None) or [],
        "final_results": getattr(state, "final_results", None) or [],
    }

    messages = [
        SystemMessage(
            content=(
                "You are a WMS incident synthesizer. "
                "Return only structured output matching the schema. "
                "Do not return markdown, headings, bullets, or prose labels. "
                "Each citation must be an object with exactly these keys: "
                "`source_type` and `reference`. "
                "Example citation: "
                '{"source_type": "sql", "reference": "SELECT * FROM inventory"} '
                "Do not invent citations."
            )
        ),
        HumanMessage(
            content=(
                "Summarize the following results.\n"
                "Return:\n"
                "- summarized_issue: concise issue summary\n"
                "- confidence: float between 0.0 and 1.0\n"
                "- citations: list of objects, where each object has:\n"
                "  - source_type: one of sql, sop, node, other\n"
                "  - reference: exact supporting citation text\n\n"
                f"{json.dumps(combined_results, indent=2, default=str)}"
            )
        ),
    ]

    result: SynthesizerNodeReturnState = llm.invoke(messages)

    return {
        "summarized_result": result.model_dump()
    }






