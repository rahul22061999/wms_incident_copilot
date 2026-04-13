import logging
from langchain_core.messages import HumanMessage
from langgraph_supervisor import create_supervisor
from langchain_openai import ChatOpenAI
from agents.nodes.inbound_agent_node import inbound_agent
from agents.nodes.outbound_agent_node import outbound_agent
from agents.nodes.inventory_agent_node import inventory_agent
from prompts.generate_supervisor_prompt import supervisor_prompt
from config import settings
from domain.states.supervisor.diagnose_graph_state import WMState
from tools.sql_lookup_tool import sql_lookup_tool
from utils.verification.evidence_collector import EvidenceCollector

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
            model=self.llm,
            prompt=self.prompt,
            output_mode="last_message",
            add_handoff_messages=True,
            parallel_tool_calls=False,
            supervisor_name="warehouse_supervisor",
        ).compile(name="warehouse_supervisor")

    def __call__(self, state: WMState) -> dict: # ← grabs the parent stream's writer
        final_text = ""

        ##Feedback from verification node
        verification = state.verification_result
        feedback = verification.missing_checks if verification and verification.missing_checks else None

        user_content = state.description
        if feedback:
            user_content = (
                f"{state.description}\n\n"
                f"## Prior attempt was incomplete\n"
                f"The verification step flagged the following missing checks. "
                f"You MUST address each one before producing a final diagnosis:\n"
                f"{feedback}"
            )
            logger.info("Supervisor re-invoked with %d missing checks", len(feedback))

        inputs = {"messages": [HumanMessage(content=user_content)]}
        ## runtime context injection
        collector = EvidenceCollector(existing=state.evidence_records)
        config = {"recursion_limit": min(25, self.max_loops * 10),
                  "configurable": {
                      "evidence_collector" : collector
                  }}

        try:
            result = self.warehouse_supervisor.invoke(
                inputs,
                config=config,
            )

            messages = result.get("messages", [])
            structured_output = messages[-1].content if messages else "No response"
            new_evidence = collector.flush()
        except Exception as exc:
            return {
                "diagnosis_result": str(exc),
                "error": str(exc),
            }

        logger.info("SUPERVISOR NODE CALLED")
        return {
            "status": "done",
            "event_log": [{"node": "supervisor_node", "status": "completed"}],
            "result": structured_output,
            "evidence_records": new_evidence,
            "error": None,
        }