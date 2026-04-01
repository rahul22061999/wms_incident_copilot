from langchain_core.messages import SystemMessage, HumanMessage
from data.state import WMState, RoutingState
from models.model_loader import get_openai_fast_llm, get_google_llm
from models.prompts.task_prompt import ROUTER_NODE_PROMPT


def router_node(state: WMState) -> dict:
    """Classifies intent of the question and routes it to the right node"""

    description = state.description

    model = get_google_llm().with_structured_output(RoutingState)

    response = model.invoke(
        [
        SystemMessage(content=ROUTER_NODE_PROMPT),
        HumanMessage(content=description)
        ]
    )

    return {
        "intent": response.intent,
        "domain": response.domain,
    }



