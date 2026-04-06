from langchain.agents import create_agent
from langchain_core.messages import AIMessage
from langgraph.types import Command
from domain.states.supervisor.supervisor_worker_payload_state import SupervisorWorkerPayloadState
from models.model_loader import get_google_llm, get_openai_fast_llm
from tools.sql_lookup_tool import sql_lookup_tool
from dotenv import load_dotenv
load_dotenv()
from langchain_openai import ChatOpenAI
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

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

outbound_agent = create_agent(
    model=llm,
    tools=[sql_lookup_tool],
    system_prompt=OUTBOUND_PROMPT,
    name="outbound_agent",
)

