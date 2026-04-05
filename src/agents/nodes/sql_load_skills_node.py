from context.skills.sql_skills import SKILLS
from domain.states.sql_subgraph_state.sql_graph_state import SQLGraphState
from dotenv import load_dotenv
load_dotenv()

def sql_load_skills_node(state: SQLGraphState) -> SQLGraphState:
    ##read and write from the state itself


    state.skill_context = [
        {domain_name:SKILLS.get(domain_name).get("content")}
        for domain_name in state.domain
    ]

    for domain in state.domain:
        state.scratch[domain] = SKILLS.get(domain).get('table_name','')

    return state