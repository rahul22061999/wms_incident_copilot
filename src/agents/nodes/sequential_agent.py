from langchain.agents import create_agent
from langchain.agents.middleware import ModelFallbackMiddleware, ModelRetryMiddleware, ToolRetryMiddleware, \
    ToolCallLimitMiddleware, SummarizationMiddleware, ModelCallLimitMiddleware, ContextEditingMiddleware, \
    ClearToolUsesEdit
from langchain_core.messages import HumanMessage
from domain.states.supervisor.diagnose_graph_state import WMState
from infrastructure.operation_cache import SEQUENTIAL_NODE_CACHE
from models.model_loader import get_ollama_llm, get_openai_fast_llm
from prompts.generate_sequential_agent_prompt import sequential_agent_prompt
from tools.rag_lookup_tool import sop_retrieval_tool
from tools.sql_lookup_tool import sql_lookup_tool


def sequential_agent(state: WMState):

    ## prompt tools and query
    sequential_agent = create_agent(
        model=get_openai_fast_llm(
            cache=SEQUENTIAL_NODE_CACHE
        ),
        system_prompt=sequential_agent_prompt,
        name="sequential_agent",
        tools=[sop_retrieval_tool, sql_lookup_tool],
        middleware=[
            ModelFallbackMiddleware(get_openai_fast_llm()),
            ModelRetryMiddleware(max_retries=2, on_failure="error"),
            ToolRetryMiddleware(max_retries=2, on_failure="return_message",
                                tools=[sop_retrieval_tool, sql_lookup_tool]),
            ModelCallLimitMiddleware(
            thread_limit=20,
            run_limit=6,
            exit_behavior="end"),
            ToolCallLimitMiddleware(
                tool_name="sql_lookup_tool",
                thread_limit=10,
                run_limit=10,
                exit_behavior="error"),
            SummarizationMiddleware(
                model=get_ollama_llm(),
                trigger=[
                    ("tokens", 10000),
                ],
                keep=("messages", 20)),
            ContextEditingMiddleware(
                edits=[
                    ClearToolUsesEdit(
                        trigger=10000,
                        keep=3,
                        placeholder="[cleared]"
                    )
                ]
            )
        ]
    )

    result = sequential_agent.invoke({
        "messages": [HumanMessage(content=state.enriched_query)]
    })

    return {
        "sequential_results": [{
                "source": "sequential_agent",
                "query": state.enriched_query,
                "status": "success",
                "result": result.get("messages"),
            }],
    }