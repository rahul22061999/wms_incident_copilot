from langchain.agents import create_agent
from langchain.agents.middleware import ModelFallbackMiddleware, ModelRetryMiddleware, ToolRetryMiddleware, \
    ToolCallLimitMiddleware, SummarizationMiddleware, ModelCallLimitMiddleware, ContextEditingMiddleware, \
    ClearToolUsesEdit
from langchain_core.messages import HumanMessage

from domain.models import TicketAuditEvent
from domain.states.supervisor.diagnose_graph_state import WMState
from infrastructure.operation_cache import SEQUENTIAL_NODE_CACHE
from models.model_loader import get_ollama_llm, get_openai_fast_llm
from prompts.generate_sequential_agent_prompt import sequential_agent_prompt
from services.audit_service import insert_ticket_audit_event
from tools.rag_lookup_tool import sop_retrieval_tool
from tools.sql_lookup_tool import sql_lookup_tool


async def sequential_agent(state: WMState):

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

    result = await sequential_agent.ainvoke({
        "messages": [HumanMessage(content=state.enriched_query)]
    })

    messages = result.get("messages", [])

    await insert_ticket_audit_event(
        ticket_number=state.ticket_number,
        user_id=state.user_id,
        node_name="sequential_agent",
        action_name="complete_sequential_agent",
        action_type="agent",
        job_id=None,
        status="success",
        action=f"Sequential agent completed successfully. Message count: {len(messages)}",
    )

    return {
        "sequential_results": [{
                "source": "sequential_agent",
                "query": state.enriched_query,
                "status": "success",
                "result": result.get("messages"),
            }],
    }