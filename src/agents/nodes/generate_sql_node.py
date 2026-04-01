from typing import Literal

from langchain_core.messages import HumanMessage
from langgraph.types import Command

from data.state import WMState
from models.model_loader import get_google_llm


def generate_sql_node(state: WMState) -> Command[Literal["check_sql_node"]]:
    system_prompt = f"""
        You are generating SQL for a WMS workflow.
    
        User request:
        {state.description}
        
        Use only this skill context:
        {state.skill_context}
        
        Rules:
        - Return only SQL.
        - Use only the listed table(s).
        - Prefer the simplest correct query.
        """

    sql = get_google_llm().invoke([HumanMessage(content=system_prompt)]).content[0]["text"].strip()

    return Command(
        update={"sql": sql},
        goto="check_sql_node",
    )