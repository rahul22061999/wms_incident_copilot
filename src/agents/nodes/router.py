from langchain_core.messages import SystemMessage, HumanMessage
from domain.routing_node_state import RoutingState
from domain.diagnose_graph_state import WMState
from models.model_loader import get_openai_fast_llm, get_google_llm
from models.prompts.task_prompt import ROUTER_NODE_PROMPT


def router_node(state: WMState) -> dict[str, str | None]:
    """Classify the request intent and business domain."""



    model = get_openai_fast_llm().with_structured_output(RoutingState)

    response = model.invoke(
        [
        SystemMessage(content=ROUTER_NODE_PROMPT),
        HumanMessage(content=state.description)
        ]
    )

    return {
        "intent": response.intent,
        "domain": response.domain,
    }



