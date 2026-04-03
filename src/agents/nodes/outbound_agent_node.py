from langchain.agents import create_agent
from langchain_core.messages import AIMessage
from langgraph.types import Command
from domain.states.supervisor.supervisor_worker_payload_state import SupervisorWorkerPayloadState
from models.model_loader import get_google_llm, get_openai_fast_llm
from tools.sql_lookup_tool import sql_lookup_tool
from dotenv import load_dotenv
load_dotenv()

OUTBOUND_PROMPT = """\
You are an outbound domain agent for a warehouse management system.

Your job is to investigate outbound operational issues using the SQL tools available to you.

Domain scope:
- Picking performance (UPH, pick rates, labor distribution)
- Wave and work release (wave timing, release patterns, blocked work)
- Packing and shipment flow (pack rates, carrier allocation, staging)
- Allocation execution (order allocation failures, shortages)

Investigation guidelines:
- Start with the broadest relevant query to understand the situation.
- Drill into specifics only after the broad picture is clear.
- Always ground your findings in data from the tools — never speculate without evidence.
- Summarize your findings clearly, stating what you found, what it means, and confidence level.
- If a tool call returns no data, state that explicitly — absence of data is a finding."""


_llm = (
    get_google_llm()
    .with_retry(stop_after_attempt=2)
    .with_fallbacks([
        get_openai_fast_llm()
        .with_retry(stop_after_attempt=2)
    ])
)

_outbound_agent = create_agent(
    model=_llm,
    tools=[sql_lookup_tool],
    system_prompt=OUTBOUND_PROMPT,
)


def outbound_agent_node(state: SupervisorWorkerPayloadState) -> Command:
    """Outbound domain agent node"""

    agent_name = state.subagent_name
    task_description = state.worker_task

    try:
        result = _outbound_agent.invoke(
            {"messages": [{"role": "user", "content": task_description}]}
        )
        final_answer = result[-1]
    except Exception as e:
        final_answer = f"[outbound_agent] Failed: {e}"

    return Command(
        update={
            "messages": [
                AIMessage(
                    content=final_answer,
                    name=agent_name,
                    additional_kwargs={"loop": state.loop_counter},
                )
            ]
        },
        goto="supervisor_node",
    )