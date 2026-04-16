import logging
from functools import lru_cache
from langchain.agents import create_agent
from langchain.agents.middleware import ModelFallbackMiddleware, ModelRetryMiddleware, ToolRetryMiddleware, \
    ModelCallLimitMiddleware, ToolCallLimitMiddleware, SummarizationMiddleware
from models.model_loader import get_google_llm, get_openai_fast_llm
from tools.rag_lookup_tool import sop_retrieval_tool
from tools.sql_lookup_tool import sql_lookup_tool
from dotenv import load_dotenv

from utils.logging.logging_config import setup_logging

load_dotenv()
setup_logging()
logger = logging.getLogger(__name__)

INVENTORY_PROMPT = """
You are an inventory domain agent for a warehouse management system.

You have two tools:

1. sql_lookup_tool
   - Use this for live system data, transactional facts, counts, timestamps, statuses,
     stock quantities, location assignments, lot and serial tracking, adjustment history,
     cycle count results, discrepancy records, hold and quarantine status, slotting data,
     replenishment triggers, and inventory aging analysis.
   - This tells you what actually exists in the system.

2. inventory_sop_lookup
   - Use this for SOP guidance, expected process flow, policy, operational rules,
     troubleshooting steps, and what should happen.
   - This tells you the intended inventory management process.

Tool selection rules:
- If the user asks about procedure, SOP, policy, expected behavior, or how a process should work,
  use inventory_sop_lookup first.
- If the user asks about actual records, current stock levels, location contents, adjustment
  transactions, discrepancies, counts, or system facts, use sql_lookup_tool first.
- If needed, use both:
  - SOP tool for expected behavior
  - SQL tool for actual behavior
  Then compare them and identify whether the issue is likely a process deviation, data issue,
  or system issue.

Do not default to SQL when the user is clearly asking a process/SOP question.
Ground every conclusion in tool output.
"""

@lru_cache(maxsize=1)
def inventory_agent():
    primary_llm = get_google_llm()
    fallback_llm = get_openai_fast_llm()

    logger.info("INVENTORY AGENT CALLED")

    return create_agent(
        model=primary_llm,
        tools=[sql_lookup_tool, sop_retrieval_tool],
        system_prompt=INVENTORY_PROMPT,
        name="inventory_agent",
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
            ),
            SummarizationMiddleware(
                model=fallback_llm,
                trigger=[
                    ("tokens", 10000),
                    ("messages", 5)
                ],
                keep=("messages", 20)
            )
        ]
    )

inventory_agent = inventory_agent()