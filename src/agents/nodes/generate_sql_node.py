from domain.states.sql_subgraph_state.sql_graph_state import SQLGraphState
from models.model_loader import get_google_llm, get_openai_fast_llm
from prompts.generate_sql_system_prompt import get_sql_prompt
from dotenv import load_dotenv
load_dotenv()

def sql_generate_query_node(state: SQLGraphState) -> dict[str, str]:
    llm = (
        get_google_llm()
        .with_fallbacks([
        get_openai_fast_llm()
    ]))

    prompt = get_sql_prompt()


    response = (prompt | llm ).invoke(
        {
            "description": state.user_question,
            "skill_context": state.skill_context,
        }
    )

    generated_sql = response.content.strip()

    return {"generated_sql": generated_sql}


