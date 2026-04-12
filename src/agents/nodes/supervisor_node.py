import logging
from langchain_core.messages import HumanMessage
from langgraph_supervisor import create_supervisor
from langchain_openai import ChatOpenAI
from langgraph.prebuilt.chat_agent_executor import AgentStateWithStructuredResponse
from agents.nodes.inbound_agent_node import inbound_agent
from agents.nodes.outbound_agent_node import outbound_agent
from agents.nodes.inventory_agent_node import inventory_agent
from agents.nodes.sql_lookup_subgraph_node import sql_query_subgraph_node
from domain.states.supervisor.supervisor_result_schema import DiagnosisResult
from prompts.generate_supervisor_prompt import supervisor_prompt
from config import settings
from domain.states.supervisor.diagnose_graph_state import WMState
from tools.sql_lookup_tool import sql_lookup_tool

logger = logging.getLogger(__name__)


class WarehouseSupervisorNode:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        self.max_loops = int(settings.SUPERVISOR_MAX_LOOP or 3)
        self.prompt = supervisor_prompt

        self.warehouse_supervisor = create_supervisor(
            agents=[
                inbound_agent,
                outbound_agent,
                inventory_agent
            ],
            tools=[sql_lookup_tool],
            model=self.llm,
            prompt=self.prompt,
            output_mode="last_message",
            add_handoff_messages=True,
            parallel_tool_calls=False,
            supervisor_name="warehouse_supervisor",
        ).compile(name="warehouse_supervisor")

    def __call__(self, state: WMState) -> dict: # ← grabs the parent stream's writer
        final_text = ""

        inputs = {"messages": [HumanMessage(content=state.description)]}
        config = {"recursion_limit": min(25, self.max_loops * 10)}

        try:
            result = self.warehouse_supervisor.invoke(
                inputs,
                config=config,
            )

            structured_output = result.get("structured_response", "No structured response")

        except Exception as exc:
            return {
                "diagnosis_result": str(exc),
                "error": str(exc),
            }

        logger.info("SUPERVISOR NODE CALLED")
        return {
            "status": "done",
            "event_log": [{"node": "supervisor_node",
                           "status": "Completed" if final_text else "failed"}],
            "diagnosis_result": structured_output,
            "error": None,
        }