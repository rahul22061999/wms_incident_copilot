from typing import Literal
from langgraph.types import Command
from context.skills.sql_skills import SKILLS
from domain.sql_graph_state import SQLGraphState
from dotenv import load_dotenv
load_dotenv()

def load_skills_node(state: SQLGraphState) -> Command[Literal["generate_sql_node"]]:
    state_skill = state.domain
    domain_skill = SKILLS[state_skill]

    return Command(
       update={
           "skill_context": domain_skill["content"],
            "table_names": domain_skill["table_name"],
       },
        goto="generate_sql_node",
    )

