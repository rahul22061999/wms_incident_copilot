"""
Synthesizer node — merges all worker results into a single grounded diagnosis.

Receives outputs from every parallel branch (parallel_results), the sequential
agent (sequential_results), and any scheduler confirmation (schedular_results)
via their respective operator.add reducers in WMState, then produces one
coherent summarized_result with a confidence score and source citations.

json.dumps with default=str handles datetime objects and other non-JSON-native
types that may appear in SQL query results or tool outputs — without it, the
prompt construction would raise a TypeError on datetime fields.

method="json_schema" forces the LLM to return output that conforms exactly to
SynthesizerNodeReturnState's JSON Schema, which is stricter than the default
function-calling approach and reduces hallucinated field names.
"""

import json

from domain.states.supervisor.diagnose_graph_state import WMState
from domain.states.synthesizer_node_state import SynthesizerNodeReturnState
from infrastructure.llm_clients import get_ollama_llm, get_openai_fast_llm
from infrastructure.operation_cache import SYNTHESIZER_NODE_CACHE
from workflows.prompts.generate_synthesizer_prompt import synthesizer_prompt


async def synthesizer_node(state: WMState):
    llm = (get_ollama_llm(cache=SYNTHESIZER_NODE_CACHE)
           .with_structured_output(SynthesizerNodeReturnState, method="json_schema"))

    content = json.dumps({
        "parallel_results": getattr(state, "parallel_results", None) or [],
        "sequential_results": getattr(state, "sequential_results", None) or [],
        "schedular_results": getattr(state, "schedular_results", None) or [],
        "final_results": getattr(state, "final_results", None) or [],
    }, indent=2, default=str)

    result: SynthesizerNodeReturnState = await (synthesizer_prompt | llm).ainvoke({
        "content": content,
    })

    return {
        "summarized_result": result.model_dump()
    }






