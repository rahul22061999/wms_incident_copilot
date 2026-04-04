# from typing import Annotated
# from langchain_core.messages import ToolMessage
# from langchain_core.tools import BaseTool, tool, InjectedToolCallId
# from langgraph.prebuilt import InjectedState
# from langgraph.types import Command
# from langgraph_supervisor.handoff import METADATA_KEY_HANDOFF_DESTINATION
#
# from domain.states.supervisor.diagnose_graph_state import WMState
#
#
# def create_supervisor_handoff_tool(agent_name: str, name: str, description:str ) -> BaseTool:
#
#     @tool(name, description=description)
#     def handoff_to_agent(
#             state: Annotated[WMState, InjectedState],
#             subagent_task: Annotated[
#                 str,
#                 "Detailed task for the next agent. Include the specific warehouse issue to investigate and relevant context."
#             ],
#             tool_call_id: Annotated[str, InjectedToolCallId]
#     ):
#
#
#
#         tool_message = ToolMessage(
#             content=f"Successfully transferred to {agent_name}",
#             name=name,
#             tool_call_id=tool_call_id,
#         )
#
#         return Command(
#             goto=agent_name,
#             graph=Command.PARENT,
#             update={
#                 # keep the supervisor history clean and explicit
#                 "messages": state.messages + [tool_message],
#
#                 # custom state you want to carry
#                 "active_agent": agent_name,
#                 "task_description": subagent_task,
#                 "loop_count": state.loop_count + 1,
#             },
#         )
#
#     handoff_to_agent.metadata = {
#         METADATA_KEY_HANDOFF_DESTINATION: agent_name,
#     }
#
#     return handoff_to_agent
#
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command
from langgraph_supervisor.handoff import METADATA_KEY_HANDOFF_DESTINATION

def create_supervisor_handoff_tool(agent_name: str, name: str, description: str):
    @tool(name, description=description)
    def handoff_to_agent(subagent_task: str, runtime: ToolRuntime) -> Command:
        state = runtime.state

        return Command(
            goto=agent_name,
            graph=Command.PARENT,
            update={
                "messages": list(state.messages) + [
                    ToolMessage(
                        content=f"Successfully transferred to {agent_name}",
                        tool_call_id=runtime.tool_call_id,
                    )
                ],
                "active_agent": agent_name,
                "task_description": subagent_task,
                "loop_count": state.loop_count + 1,
            },
        )

    handoff_to_agent.metadata = {
        METADATA_KEY_HANDOFF_DESTINATION: agent_name,
    }
    return handoff_to_agent
