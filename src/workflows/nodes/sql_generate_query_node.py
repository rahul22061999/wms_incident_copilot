import logging
from langsmith import traceable
from domain.states.sql_generate_subquery.sql_generate_subqueries_state import GenerateSubqueries
from domain.states.sql_subgraph_state.sql_graph_state import SQLGraphState
from infrastructure.operation_cache import GENERATE_SQL_QUERY_NODE_CACHE
from models.model_loader import get_google_llm, get_openai_fast_llm
from prompts.generate_sql_subquery_split_prompt import get_subquery_split_prompt
from prompts.generate_sql_system_prompt import get_sql_prompt

logger = logging.getLogger(__name__)

@traceable(name="sql_generate_query_node")
async def sql_generate_query_node(state: SQLGraphState) -> dict:
    domains = state.domain
    prompt = get_sql_prompt()
    results = {}

    logger.info("SQL Generate Query Node started")

    if len(domains) > 1:
        # Split + generate SQL per domain
        structured_llm = get_google_llm(cache=GENERATE_SQL_QUERY_NODE_CACHE).with_structured_output(GenerateSubqueries).with_fallbacks([
            get_openai_fast_llm(cache=GENERATE_SQL_QUERY_NODE_CACHE).with_structured_output(GenerateSubqueries)
        ])
        state.subqueries = await (get_subquery_split_prompt() | structured_llm).ainvoke({
            "description": state.user_question,
        })

        llm = get_google_llm(cache=GENERATE_SQL_QUERY_NODE_CACHE).with_fallbacks([get_openai_fast_llm()])

        for sq in state.subqueries.subqueries:
            response = await (prompt | llm).ainvoke({
                "skill_context": next(
                    (skill.get(sq.domain) for skill in state.skill_context if sq.domain in skill), ""
                ),
                "description": sq.query,
            })
            content = response.content
            if isinstance(content, list):
                content = "".join(b["text"] for b in content if b.get("type") == "text")
            results[sq.domain] = content

            # {"inbound": "SELECT ...", "outbound": "SELECT ..."}
    else:
        llm = get_google_llm(cache=GENERATE_SQL_QUERY_NODE_CACHE).with_fallbacks([get_openai_fast_llm(cache=GENERATE_SQL_QUERY_NODE_CACHE)])
        response = await (prompt | llm).ainvoke({
            "skill_context": state.skill_context[0] if state.skill_context else "",
            "description": state.user_question,
        })
        content = response.content
        if isinstance(content, list):
            content = "".join(b["text"] for b in content if b.get("type") == "text")
        results[str(domains[0])] = content


    logger.info("SQL Generate Query Node completed. Domains: %s", list(results.keys()))

    return {
        "validated_sql": results,
        "event_log": [{"node":"generate_sql_node", "message": "Completed generating SQL queries."}]
    }
