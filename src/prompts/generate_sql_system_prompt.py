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
            
            Skill context:
            {skill_context}
        """
    )

    sql_human_message = HumanMessagePromptTemplate.from_template(
        """ User request:
            {description}
        """
    )

    return ChatPromptTemplate.from_messages([
        sql_system_message,
        sql_human_message,
    ])