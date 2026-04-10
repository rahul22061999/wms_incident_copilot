import logging
from langsmith import traceable
from context.skills.sql_skills import SKILLS
from domain.states.sql_subgraph_state.sql_graph_state import SQLGraphState


from utils.logging.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

@traceable
def sql_load_skills_node(state: SQLGraphState) -> dict:
    ##read and write from the state itself

    skill_context = [
        {domain_name: SKILLS.get(domain_name, {}).get("content")}
        for domain_name in state.domain
    ]

    scratch_update = {
        domain_name: SKILLS.get(domain_name, {}).get("table_name", "")
        for domain_name in state.domain
    }

    logger.debug(f"SKILL NODE: SKILLS LOADED")

    return {
        "skill_context": skill_context,
        "scratch": scratch_update,
        "event_log": [{"node": "sql_load_skills_node", "message": "Completed loading skills"}],
    }