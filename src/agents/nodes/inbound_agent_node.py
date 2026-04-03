from langchain.agents import create_agent
from langchain_core.messages import AIMessage
from domain.states.supervisor.supervisor_worker_payload_state import SupervisorWorkerPayloadState
from prompts.generate_inbound_agent_prompt import inbound_agent_prompt
from langgraph.types import Command
from models.model_loader import get_google_llm, get_openai_fast_llm
from tools.sql_lookup_tool import sql_lookup_tool
from dotenv import load_dotenv
load_dotenv()


# Build once at module level — not on every invocation
_llm = (
    get_google_llm()
    .with_fallbacks([
        get_openai_fast_llm()
    ])
)

_inbound_agent = create_agent(
    model=_llm,
    tools=[sql_lookup_tool],
    system_prompt=inbound_agent_prompt,
)


def inbound_agent_node(state: SupervisorWorkerPayloadState) -> Command:
    """Inbound domain agent node"""

    agent_name = state.subagent_name
    task_description = state.worker_task

    try:
        result = _inbound_agent.invoke(
            {"messages": [{"role": "user", "content": task_description}]}
        )
        final_answer = result["messages"][-1].content
    except Exception as e:
        final_answer = f"[inbound_agent] Failed: {e}"

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