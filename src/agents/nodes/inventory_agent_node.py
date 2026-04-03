from langchain.agents import create_agent
from langchain_core.messages import AIMessage
from domain.states.supervisor.supervisor_worker_payload_state import SupervisorWorkerPayloadState
from langgraph.types import Command
from models.model_loader import get_google_llm, get_openai_fast_llm
from tools.sql_lookup_tool import sql_lookup_tool
from dotenv import load_dotenv
load_dotenv()


_llm = (
    get_google_llm()
    .with_retry(stop_after_attempt=2)
    .with_fallbacks([
        get_openai_fast_llm()
        .with_retry(stop_after_attempt=2)
    ])
)

_inventory_agent = create_agent(
    model=_llm,
    tools=[sql_lookup_tool],
    system_prompt="hello",
)


def inventory_agent_node(state: SupervisorWorkerPayloadState) -> Command:
    """Inventory domain agent node"""

    agent_name = state.subagent_name
    task_description = state.worker_task

    try:
        result = _inventory_agent.invoke(
            {"messages": [{"role": "user", "content": task_description}]}
        )
        final_answer = result["messages"][-1].content
    except Exception as e:
        final_answer = f"[inventory_agent] Failed: {e}"

    return Command(
        update={
            "messages": [
                AIMessage(
                    content=final_answer,
                    name=agent_name,
                    additional_kwargs={"loop": state.loop_counter}),
            ]
        },
        goto="supervisor_node",
    )