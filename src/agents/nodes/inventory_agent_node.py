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

inventory_agent = create_agent(
    model=_llm,
    tools=[sql_lookup_tool],
    system_prompt="hello",
    name="inventory_agent",
)

