import logging
from context.skills.sql_skills import SKILLS
from domain.states.sql_subgraph_state.sql_graph_state import SQLGraphState

logger = logging.getLogger(__name__)

def sql_load_skills_node(state: SQLGraphState) -> dict:
    ##read and write from the state itself

    logger.info(
        "sql_load_skills_node started | domains=%s count=%d",
        state.domain,
        len(state.domain),
    )

    skill_context = [
        {domain_name: SKILLS.get(domain_name, {}).get("content")}
        for domain_name in state.domain
    ]

    logger.info(
        "sql_load_skills_node completed | requested=%d loaded=%d",
        len(state.domain),
        len(skill_context),
    )

    return {
        "skill_context": skill_context,
        "event_log": [
            {
                "node": "sql_load_skills_node",
                "message": "Completed loading skills"
            }
        ],
    }

