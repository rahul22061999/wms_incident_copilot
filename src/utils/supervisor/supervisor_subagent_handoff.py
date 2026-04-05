from typing import Dict, Any, Annotated
from langchain.tools import tool
from langgraph.prebuilt import InjectedState
from langgraph.types import Command
from langgraph_supervisor.handoff import METADATA_KEY_HANDOFF_DESTINATION

def create_supervisor_handoff_tool(agent_name: str, name: str, description: str, default_max_turns: int ):

    @tool(name, description=description)
    def handoff_to_agent(
            task_description: str,
            state: Annotated[dict, InjectedState]) -> Command:
        """Hand off task to a domain agent."""

        messages = state.get("messages") if isinstance(state, dict) else []

        update: Dict[str, Any] = {
            "messages": messages,
            "task_description": task_description,
        }

        if default_max_turns is not None:
            update["max_turns"] = default_max_turns

        return Command(
            goto=agent_name,
            graph=Command.PARENT,
            update=update,
        )

    handoff_to_agent.metadata = {METADATA_KEY_HANDOFF_DESTINATION: agent_name}
    return handoff_to_agent
