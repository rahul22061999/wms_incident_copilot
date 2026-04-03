from typing import Optional
from langchain_core.runnables import Runnable
from langchain_core.prompts import ChatPromptTemplate
from domain.states.supervisor.supervisor_subagent_task_state import SupervisorToSubAgentDeligationItem


async def invoke_llm(
        task_description: str,
        previous_findings,
        prompt: ChatPromptTemplate,
        llm: Runnable) -> Optional[SupervisorToSubAgentDeligationItem]:

    messages = prompt.format_messages(
        previous_findings=previous_findings,
        description=task_description,
    )

    try:
        result = await llm.ainvoke(messages)
        return result
    except Exception as e:
        print(f"[supervisor] LLM call failed: {e}")
        return None