from langchain_core.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)

def get_sql_prompt() -> ChatPromptTemplate:
    sql_system_message = SystemMessagePromptTemplate.from_template(
        """You are generating SQL for a WMS workflow.

Rules:
- Return only SQL.
- Use only the listed table(s).
- Prefer the simplest correct query.
- Always generate aggregated SQL by default.
- Only generate row-level results when the user explicitly requests:
  - all results
  - all rows
  - raw data
  - detailed rows
  - record-level output
  - full results
  - each record
- Otherwise, summarize the answer using aggregation.
- Prefer COUNT, SUM, AVG, MIN, MAX, DISTINCT counts, and GROUP BY as needed.
- Do not use SELECT * unless explicitly requested.
- For ambiguous requests, choose aggregated output.

Skill context:
{skill_context}
"""
    )

    sql_human_message = HumanMessagePromptTemplate.from_template(
        """User request:
{description}
"""
    )

    return ChatPromptTemplate.from_messages([
        sql_system_message,
        sql_human_message,
    ])