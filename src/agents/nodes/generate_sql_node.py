from typing import Literal
from langgraph.types import Command
from domain.sql_graph_state import SQLGraphState
from models.model_loader import get_google_llm, get_openai_fast_llm
from prompts.generate_sql_system_prompt import get_sql_prompt
from dotenv import load_dotenv
load_dotenv()

def generate_sql_node(state: SQLGraphState) -> Command[Literal["check_sql_node"]]:
    prompt = get_sql_prompt()
    main_llm = get_google_llm()
    fallback_llm = get_openai_fast_llm()

    try:
        response = (prompt | main_llm).invoke({
            "description": state.description,
            "skill_context": state.skill_context,
        })

        generated_sql = response.content.strip()

        return Command(
            update={"generated_sql": generated_sql},
            goto="check_sql_node",
        )

    except Exception as primary_exception:

        response = (prompt | fallback_llm).invoke({
            "description": state.description,
            "skill_context": state.skill_context,
        })

        generated_sql = response.content.strip()

        return Command(
            update={"generated_sql": generated_sql},
            goto="check_sql_node",
        )



