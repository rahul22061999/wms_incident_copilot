from agents.nodes.inventory_agent_node import inventory_agent
from agents.nodes.outbound_agent_node import outbound_agent
from prompts.generate_supervisor_prompt import supervisor_prompt
from config import settings
from domain.states.supervisor.diagnose_graph_state import WMState
from models.model_loader import get_google_llm, get_openai_fast_llm
from dotenv import load_dotenv
from utils.supervisor.supervisor_subagent_handoff import create_supervisor_handoff_tool
from utils.supervisor.supervisor_fallback import force_final_answer
from langgraph_supervisor import create_supervisor
from agents.nodes.inbound_agent_node import inbound_agent

load_dotenv()

def _is_final_message(messages: list[dict]) -> bool:
    if not messages:
        return False
    last = messages[-1]
    content = last.get("content", "")
    # convention: supervisor marks final answer with 'FINAL:' or '/final' (choose your own)
    return "FINAL:" in content or content.strip().startswith("/final")

class WarehouseSupervisorNode:
    def __init__(self):

        ##choose llm based on whats available
        self.llm = (
            get_google_llm()
            .with_fallbacks([
                get_openai_fast_llm()
            ])
        )

        ##set max loops for and llm to run over an issue
        self.max_loops = int(settings.SUPERVISOR_MAX_LOOP or 3)
        ##how many times child can loop
        self.child_max_loops = int(settings.CHILD_MAX_LOOP or 3)
        ##system prompt and chat prompt built in
        self.prompt = supervisor_prompt

        ##all agents as tools
        self.tools = [
            create_supervisor_handoff_tool(
                agent_name="inbound_agent",
                name="handoff_to_inbound_agent",
                description="Delegate receiving, dock, ASN, PO, putaway, and inbound throughput investigations.",
                default_max_turns=self.child_max_loops
            ),
            create_supervisor_handoff_tool(
                agent_name="outbound_agent",
                name="handoff_to_outbound_agent",
                description="Delegate picking, packing, wave, shipping, and outbound execution investigations.",
                default_max_turns=self.child_max_loops
            ),
            create_supervisor_handoff_tool(
                agent_name="inventory_agent",
                name="handoff_to_inventory_agent",
                description="Delegate inventory accuracy, adjustments, stock discrepancies, and location state investigations.",
                default_max_turns=self.child_max_loops
            )
        ]

        ##create a supervisor
        self.warehouse_supervisor = create_supervisor(
            agents=[
                inbound_agent,
                outbound_agent,
                inventory_agent,
            ],
            tools=self.tools,
            model=self.llm,
            output_mode="last_message",
            add_handoff_messages=False,
            parallel_tool_calls=False,
            supervisor_name="warehouse_supervisor",
        ).compile(name="warehouse_supervisor")

    async def __call__(self, state: WMState) -> dict:
        current_loop = int(state.loop_count or 0)
        if current_loop >= self.max_loops:
            # Use force_final_answer to create final_output string
            final_output = force_final_answer(state, current_loop + 1, self.max_loops, str(state.messages))
            return {
                "final_responses": final_output,
                "loop_count": current_loop + 1,
                "messages": state.messages,
                "final": True,
            }

        enriched_message = f"Ticket: {state.description}\n\n"
        # still include hint but also send explicit child max in tool args if possible
        enriched_message += f"[max_child_turns={self.child_max_loops}]\n[loop_count={current_loop}]\n"

        try:
            result = await self.warehouse_supervisor.ainvoke(
                {"messages": [{"role": "user", "content": enriched_message}]},
                config={"recursion_limit": min(25, self.max_loops * 10)},
            )
        except Exception as exc:
            return {
                "final_responses": f"Supervisor Error: {exc}",
                "loop_count": current_loop + 1,
                "messages": [],
                "error": str(exc),
                "final": True,
            }

        messages = result.get("messages", []) if isinstance(result, dict) else []
        final_detected = _is_final_message(messages)

        if final_detected or (current_loop + 1) >= self.max_loops:
            final = messages[-1].get("content") if messages else ""
            final_output = force_final_answer(state, current_loop + 1, self.max_loops, final)
            return {
                "final_responses": final_output,
                "loop_count": current_loop + 1,
                "messages": messages,
                "final": True,
            }

        # not final -> return patch for parent to merge
        return {
            "final_responses": messages[-1].get("content") if messages else "",
            "loop_count": current_loop + 1,
            "messages": messages,
            "final": False,
        }






