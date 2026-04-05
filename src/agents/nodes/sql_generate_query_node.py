from domain.states.sql_generate_subquery.sql_generate_subqueries_state import GenerateSubqueries
from domain.states.sql_subgraph_state.sql_graph_state import SQLGraphState
from models.model_loader import get_google_llm, get_openai_fast_llm
from prompts.generate_sql_subquery_split_prompt import get_subquery_split_prompt
from prompts.generate_sql_system_prompt import get_sql_prompt
from dotenv import load_dotenv
load_dotenv()

# sql_generate_query_node — writes to state
def sql_generate_query_node(state: SQLGraphState) -> SQLGraphState:
    domains = state.domain
    prompt = get_sql_prompt()

    if len(domains) > 1:
        # Split + generate SQL per domain
        structured_llm = get_google_llm().with_structured_output(GenerateSubqueries).with_fallbacks([
            get_openai_fast_llm().with_structured_output(GenerateSubqueries)
        ])
        state.subqueries = (get_subquery_split_prompt() | structured_llm).invoke({
            "description": state.user_question,
        })

        llm = get_google_llm().with_fallbacks([get_openai_fast_llm()])
        results = {}
        for sq in state.subqueries.subqueries:
            response = (prompt | llm).invoke({
                "skill_context": next(
                    (skill.get(sq.domain) for skill in state.skill_context if sq.domain in skill), ""
                ),
                "description": sq.query,
            })
            content = response.content
            if isinstance(content, list):
                content = "".join(b["text"] for b in content if b.get("type") == "text")
            results[sq.domain] = content.strip()

        state.generated_sql = results  # {"inbound": "SELECT ...", "outbound": "SELECT ..."}
    else:
        llm = get_google_llm().with_fallbacks([get_openai_fast_llm()])
        response = (prompt | llm).invoke({
            "skill_context": state.skill_context[0] if state.skill_context else "",
            "description": state.user_question,
        })
        content = response.content
        if isinstance(content, list):
            content = "".join(b["text"] for b in content if b.get("type") == "text")
        state.generated_sql[str(domains[0])] = content.strip()
    return state
