from agents.nodes.inventory_agent_node import inventory_agent
from agents.nodes.outbound_agent_node import outbound_agent
from prompts.generate_supervisor_prompt import supervisor_prompt
from config import settings
from domain.states.supervisor.diagnose_graph_state import WMState
from models.model_loader import get_google_llm, get_openai_fast_llm
from dotenv import load_dotenv
from utils.supervisor.supervisor_subagent_handoff import create_supervisor_handoff_tool
from utils.supervisor.supervisor_fallback import force_final_answer
from utils.supervisor.supervisor_previous_context import get_previous_task_findings
from langgraph_supervisor import create_supervisor, create_handoff_tool
from agents.nodes.inbound_agent_node import inbound_agent

load_dotenv()

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
        self.max_loops = settings.SUPERVISOR_MAX_LOOP
        ##system prompt and chat prompt built in
        self.prompt = supervisor_prompt

        ##all agents as tools
        self.tools = [
            create_handoff_tool(
                agent_name="inbound_agent",
                name="handoff_to_inbound_agent",
                description="Delegate receiving, dock, ASN, PO, putaway, and inbound throughput investigations."
            ),
            create_handoff_tool(
                agent_name="outbound_agent",
                name="handoff_to_outbound_agent",
                description="Delegate picking, packing, wave, shipping, and outbound execution investigations."
            ),
            create_handoff_tool(
                agent_name="inventory_agent",
                name="handoff_to_inventory_agent",
                description="Delegate inventory accuracy, adjustments, stock discrepancies, and location state investigations."
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
            parallel_tool_calls=True,
            supervisor_name="warehouse_supervisor",
        ).compile(name="warehouse_supervisor")

    async def __call__(self, state: WMState):
        current_loop = state.get("loop_count", 0)

        if current_loop >= self.max_loops:
            return force_final_answer(state, current_loop, self.max_loops)

        enriched_message = (
            f"Ticket: {state.get('description', 'No description')}\n\n"
        )

        result = self.warehouse_supervisor.invoke({
            "messages": [{"role": "user", "content": enriched_message}]
        }, config={"recursion_limit": 25},)

        final = result["messages"][-1].content
        return {
            "final_responses": final,
            "loop_count": current_loop + 1,
            "messages": result["messages"],
        }





