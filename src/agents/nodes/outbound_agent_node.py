from langchain.agents import create_agent
from langchain_core.messages import AIMessage
from langgraph.types import Command
from domain.states.supervisor.supervisor_worker_payload_state import SupervisorWorkerPayloadState
from models.model_loader import get_google_llm, get_openai_fast_llm
from tools.rag_lookup_tool import sop_retrieval_tool
from tools.sql_lookup_tool import sql_lookup_tool
from dotenv import load_dotenv
load_dotenv()
from langchain_openai import ChatOpenAI
OUTBOUND_PROMPT = """
You are an outbound domain agent for a warehouse management system.

You have two tools:

1. sql_lookup_tool
   - Use this for live system data, transactional facts, counts, timestamps, statuses,
     wave and work release records, pick performance, pack and ship activity, allocation
     results, staging dwell, carrier assignment, and order backlog analysis.
   - This tells you what actually happened in the system.

2. outbound_sop_lookup
   - Use this for SOP guidance, expected process flow, policy, operational rules,
     troubleshooting steps, and what should happen.
   - This tells you the intended outbound process.

Tool selection rules:
- If the user asks about procedure, SOP, policy, expected behavior, or how a process should work,
  use outbound_sop_lookup first.
- If the user asks about actual records, current status, counts, delays, timing, or system facts,
  use sql_lookup_tool first.
- If needed, use both:
  - SOP tool for expected behavior
  - SQL tool for actual behavior
  Then compare them and identify whether the issue is likely a process deviation, data issue, or system issue.

Do not default to SQL when the user is clearly asking a process/SOP question.
Ground every conclusion in tool output.
"""


from functools import lru_cache
from langchain.agents.middleware import ModelFallbackMiddleware, ModelRetryMiddleware, ToolRetryMiddleware, \
    ModelCallLimitMiddleware, ToolCallLimitMiddleware
from models.model_loader import get_google_llm, get_openai_fast_llm
from tools.sql_lookup_tool import sql_lookup_tool
from tools.rag_lookup_tool import sop_retrieval_tool
from langchain.agents import create_agent
import logging

from utils.logging.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def outbound_agent():
    primary_llm = get_google_llm()
    fallback_llm = get_openai_fast_llm()

    logger.info("OUTBOUND AGENT CALLED")

    return create_agent(
        model=primary_llm,
        tools=[sql_lookup_tool, sop_retrieval_tool],
        system_prompt=OUTBOUND_PROMPT,
        name="outbound_agent",
        middleware=[
            ModelFallbackMiddleware(fallback_llm),
            ModelRetryMiddleware(max_retries=2, on_failure="error"),
            ToolRetryMiddleware(max_retries=2, on_failure="error",
                                tools=[sql_lookup_tool, sop_retrieval_tool]
                                ),
            ModelCallLimitMiddleware(
                thread_limit=20,
                run_limit=6,
                exit_behavior="end"
            ),
            ToolCallLimitMiddleware(
                tool_name="sql_lookup_tool",
                thread_limit=10,
                run_limit=3,
                exit_behavior="error"
            )
        ]
    )

outbound_agent = outbound_agent()