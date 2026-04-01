from typing import List, Tuple, Optional
from langchain_core.messages import AIMessage
from langgraph.types import Send, Command
from langchain_core.prompts import ChatPromptTemplate
from config import settings
from data.state import WMState, WorkerInput, SupervisorDeligationItem
from models.model_loader import get_google_llm
from uuid import uuid4
from dotenv import load_dotenv
load_dotenv()


def get_previous_task_findings(state: WMState, task_id: str) -> List[Tuple[str, str]]:
    previous_task_findings = [
        (
            (f"Agent name {task.agent_name} \n",
             f"Messages {task.messages}")
            for prev_task in state.subagent_responses
            if prev_task.task_id == task_id
            for task in prev_task.subagent_responses
        )
    ]
    return previous_task_findings


class SupervisorNode:
    def __init__(self, llm=None):
        base_llm = llm or get_google_llm()
        self.llm = base_llm.with_structured_output(SupervisorDeligationItem)
        self.max_loops = settings.SUPERVISOR_MAX_LOOP
        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a senior WMS supervisor agent.\n"
                    "Your job is to inspect the ticket, review prior subagent findings for the current task, "
                    "and decide the next best orchestration action.\n\n"

                    "You must do exactly one of these:\n"
                    "1. Delegate one or more focused tasks to the appropriate subagents.\n"
                    "2. Stop delegating and provide the final answer if the findings are already sufficient.\n\n"

                    "Available subagents:\n"
                    "- inbound_agent: receiving, ASN, PO, putaway, dock, inbound flow, backlog, congestion\n"
                    "- outbound_agent: picking, packing, wave, allocation execution, shipment flow, UPH, labor flow\n"
                    "- inventory_agent: stock accuracy, holds, adjustments, location balance, availability, discrepancies\n\n"

                    "Decision rules:\n"
                    "- Use prior findings first. Do not ask subagents to repeat work that is already covered.\n"
                    "- Delegate only if there is still missing information needed to answer the ticket.\n"
                    "- If the ticket contains multiple distinct problems, you may delegate to multiple subagents.\n"
                    "- Each delegated task must be specific, investigatory, and independently actionable.\n"
                    "- Prefer the minimum number of delegations needed to reach a confident answer.\n"
                    "- If prior findings already explain the issue, stop and provide the final answer.\n\n"

                    "What good delegation looks like:\n"
                    "- Bad: 'Look into inbound'\n"
                    "- Good: 'Investigate dock congestion, receiving backlog, and ASN timing patterns to determine why inbound is delayed'\n"
                    "- Bad: 'Check inventory'\n"
                    "- Good: 'Investigate inventory discrepancies for SKU/location/hold status and determine whether stock is unavailable due to holds, adjustments, or mismatched balances'\n\n"

                    "Few-shot examples:\n\n"

                    "Example 1:\n"
                    "Ticket: 'UPH is low and picking is delayed.'\n"
                    "Previous findings: none\n"
                    "Reasoning outcome: missing outbound operational details, so delegate to outbound_agent.\n"
                    "Good delegated task: 'Investigate picking performance, labor distribution, wave release timing, and blocked work to determine why UPH is low and picking is delayed.'\n\n"

                    "Example 2:\n"
                    "Ticket: 'Inbound is congested and receipts are delayed.'\n"
                    "Previous findings: none\n"
                    "Reasoning outcome: this is mainly inbound, so delegate to inbound_agent.\n"
                    "Good delegated task: 'Investigate dock congestion, trailer backlog, ASN/PO receiving flow, and putaway delays to determine why inbound is congested and receipts are delayed.'\n\n"

                    "Example 3:\n"
                    "Ticket: 'Inventory is high but orders are not allocating.'\n"
                    "Previous findings: none\n"
                    "Reasoning outcome: this needs inventory availability analysis first.\n"
                    "Good delegated task: 'Investigate whether inventory is unavailable due to holds, status, location restrictions, adjustments, or stock mismatches causing allocation failure.'\n\n"

                    "Example 4:\n"
                    "Ticket: 'Picking is low, inbound has no work, and inventory discrepancies are rising.'\n"
                    "Previous findings: none\n"
                    "Reasoning outcome: this is multi-domain, so delegate to multiple subagents with focused tasks.\n"
                    "Good delegated tasks:\n"
                    "- outbound_agent: 'Investigate low picking performance, UPH, work release, and labor/work imbalance.'\n"
                    "- inbound_agent: 'Investigate why inbound has no work by checking receipts, ASN/PO flow, dock activity, and putaway pipeline.'\n"
                    "- inventory_agent: 'Investigate inventory discrepancies, adjustment patterns, stock accuracy issues, and availability impacts.'\n\n"

                    "Example 5:\n"
                    "Ticket: 'Orders are not allocating.'\n"
                    "Previous findings: inventory_agent found the only available stock is on hold and not allocatable.\n"
                    "Reasoning outcome: do not delegate again; provide the final answer because the root cause is already sufficient.\n\n"

                    "Return behavior:\n"
                    "- If more investigation is needed, return one or more precise delegations.\n"
                    "- If enough evidence already exists, return a final answer and no further delegations.\n\n"

                    "Previous findings for this task:\n{previous_findings}"
                ),
                (
                    "human",
                    "Ticket description:\n{description}"
                ),
            ]
        )

    async def __call__(self, state: WMState):
        """Entry point called by LangGraph."""

        current_loop = state.loop_count
        task_id = state.active_task_id or str(uuid4())

        if current_loop > settings.SUPERVISOR_MAX_LOOP:
            return self._force_final_answer(state, task_id, current_loop)

         ## {"task_id": Subagentresponse}
        previous_task_findings = get_previous_task_findings(state, task_id)

        ##inject messages from the task to the prompt
        decision = await self._invoke_llm(state.description, previous_task_findings)

        return self._build_command(decision, task_id, current_loop)


    def _force_final_answer(self, state: WMState, task_id: str, current_loop: int):
        findings = get_previous_task_findings(state, task_id)

        return Command(
            update={
                "active_task_id": task_id,
                "loop_count": current_loop + 1,
                "messages": [
                    AIMessage(
                        content=(
                            f"[supervisor] Max investigation loops ({self.max_loops}) reached. "
                            f"Best-effort summary based on findings so far:\n{findings}"
                        )
                    )
                ],
            },
            goto=[],
        )

    def _invoke_llm(self, task_description: str,  previous_findings) -> Optional[SupervisorDeligationItem]:
        messages = self.prompt.format_messages(
            previous_findings= previous_findings,
            description=task_description,
        )

        try:
            result = self.llm.ainvoke(messages)
        except Exception:
            return None

        return result

    def _build_command(
            self,
            decision: SupervisorDeligationItem,
            task_id: str,
            current_loop: int) -> Command:
        """Convert a structured LLM decision into a LangGraph Command."""

        sends: list[Send] = []
        supervisor_messages: list[AIMessage] = []

        for event in decision.deligations:
            subagent_task = event.subagent_task
            agent_name = event.agent_name

            worker_state = WorkerInput(
                agent_name=agent_name,
                task_id=str(task_id),
                task=subagent_task,
            )

            sends.append(
                Send(agent_name, worker_state)
            )
            supervisor_messages.append(
                AIMessage(
                    content=(
                        f"Supervisor delegated task {event.agent_name} to {task_id}"
                    )
                )
            )

        return Command(
            update={
                "active_task_id": task_id,
                "loop_count": current_loop + 1,
                "messages": supervisor_messages,
            },
            goto=sends
        )



