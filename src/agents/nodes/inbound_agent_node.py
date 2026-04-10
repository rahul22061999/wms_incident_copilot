from functools import lru_cache
from langchain.agents.middleware import ModelFallbackMiddleware, ModelRetryMiddleware, ToolRetryMiddleware, \
    ModelCallLimitMiddleware, ToolCallLimitMiddleware, HumanInTheLoopMiddleware
from prompts.generate_inbound_agent_prompt import inbound_agent_prompt
from models.model_loader import get_google_llm, get_openai_fast_llm
from tools.sql_lookup_tool import sql_lookup_tool
from tools.rag_lookup_tool import sop_retrieval_tool
from langchain.agents import create_agent
import logging

from utils.logging.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

@lru_cache(maxsize=1)
def inbound_agent():
    primary_llm = get_google_llm()
    fallback_llm = get_openai_fast_llm()

    logger.info("INBOUND AGENT CALLED")

    return create_agent(
        model=primary_llm,
        tools=[sql_lookup_tool, sop_retrieval_tool],
        system_prompt=inbound_agent_prompt,
        name="inbound_agent",
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
            HumanInTheLoopMiddleware(
                interrupt_on={
                    "sop_retrieval_tool":{
                        "allowed_decisions": input("y or n")
                    },
                    "sql_lookup_tool": False
                }
            )

        ]
    )

inbound_agent = inbound_agent()


# llm = get_google_llm()
#
# inbound_agent = create_agent(
#     model=llm,
#     tools=[sql_lookup_tool, sop_retrieval_tool],
#     name="inbound_agent",
#     system_prompt=inbound_agent_prompt,
#
# )