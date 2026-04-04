from context.skills.sql_skills import SKILLS
from domain.states.sql_subgraph_state.sql_graph_state import SQLGraphState
from dotenv import load_dotenv
load_dotenv()

def sql_load_skills_node(state: SQLGraphState) -> dict:
    state_skill = state.domain
    domain_skill = SKILLS[state_skill]

    return {
        "skill_context": domain_skill["content"],
        "table_names": domain_skill["table_name"]
    }