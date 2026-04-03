from typing import List, Tuple
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from domain.states.supervisor.diagnose_graph_state import WMState
from models.model_loader import get_google_llm, get_openai_fast_llm
from prompts.generate_summarizer_prompt import summarizer_prompt
TaskFindings = List[Tuple[str, str]]



# Build once at module level — not on every invocation
_llm = (
    get_google_llm()
    .with_retry(stop_after_attempt=2)
    .with_fallbacks([
        get_openai_fast_llm()
        .with_retry(stop_after_attempt=2)
    ])
)
def get_previous_task_findings(state: WMState) -> str:
    agent_names = {"inbound_agent", "outbound_agent", "inventory_agent"}
    current_loop = state.loop_count

    earlier = []
    latest = []

    for msg in state.messages:
        if not isinstance(msg, AIMessage) or msg.name not in agent_names:
            continue

        loop = msg.additional_kwargs.get("loop", 0)

        if loop == current_loop - 1:
            latest.append(msg)
        else:
            earlier.append(msg)

    parts = []

    # Summarize earlier findings if they exist
    if earlier:
        earlier_text = "\n\n".join(
            f"{msg.name}: {msg.content}" for msg in earlier
        )

        summary = _llm.ainvoke([
            SystemMessage(content=summarizer_prompt),
            HumanMessage(content=earlier_text),
        ])
        parts.append(f"**Earlier findings (summarized):**\n{summary.content}")

    # Keep latest findings full
    if latest:
        latest_text = "\n\n".join(
            f"**{msg.name}:** {msg.content}" for msg in latest
        )
        parts.append(f"**Latest findings:**\n{latest_text}")

    return "\n\n".join(parts) if parts else "None yet."