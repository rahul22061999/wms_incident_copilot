from domain.states.supervisor.diagnose_graph_state import WMState
from domain.states.synthesizer_node_state import SynthesizerNodeReturnState
from infrastructure.operation_cache import SYNTHESIZER_NODE_CACHE
from models.model_loader import get_ollama_llm
from prompts.generate_synthesizer_prompt import synthesizer_prompt
import json

async def synthesizer_node(state: WMState):
    #return parallel execution results and sequential results too

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






