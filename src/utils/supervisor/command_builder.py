from langchain_core.messages import AIMessage
from langgraph.types import Command, Send
from domain.states.supervisor.supervisor_subagent_task_state import SupervisorToSubAgentDeligationItem
from domain.states.supervisor.supervisor_worker_payload_state import SupervisorWorkerPayloadState


def build_command(
        decision: SupervisorToSubAgentDeligationItem,
        current_loop: int) -> Command:
    """Convert a structured LLM decision into a LangGraph Command."""

    sends: list[Send] = []
    supervisor_messages: list[AIMessage] = []

    for event in decision.subagent_deligations:
        subagent_research_task = event.subagent_task
        subagent_name = event.subagent_name
        domain_name = event.domain_name

        worker_payload = SupervisorWorkerPayloadState(
            subagent_name= subagent_name,
            worker_task=subagent_research_task,
            domain_name=domain_name,
            loop_counter=current_loop,
        )

        sends.append(
            Send(subagent_name, worker_payload)
        )

        supervisor_messages.append(
            AIMessage(
                content=(
                    f"Supervisor delegated task to {subagent_name}"
                )
            )
        )


    return Command(
        update={
            "loop_count": current_loop + 1,
            "messages": supervisor_messages,
        },
        goto=sends if sends else "diagnose_result_node"
    )



