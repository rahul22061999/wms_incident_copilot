from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langgraph.types import Command

from data.state import WorkerInput, SubAgentResponse, WMState
from models.model_loader import get_google_llm
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

def outbound_agent_node(state: WorkerInput) -> Command:
    """Inbound domain agent node"""

    task_id = state.task_id
    agent_name = state.agent_name
    task = state.task

    llm = get_google_llm()

    agent = create_agent(
        model=llm,
        tools=[sql_lookup_tool],
        system_prompt=OUTBOUND_PROMPT
    )

    try:
        result = agent.invoke(HumanMessage(content=task))
        final_answer = result["messages"][-1].content

    except Exception as e:
        return None

    return Command(
        update={
            "subagent_responses": [
                SubAgentResponse(
                    task_id=task_id,
                    agent_name=agent_name,
                    messages=final_answer,
                )
            ]
        },
        goto="supervisor_node",
    )





