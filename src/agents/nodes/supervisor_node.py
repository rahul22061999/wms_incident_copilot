from langchain_anthropic import ChatAnthropic
from langsmith import traceable
from agents.nodes.inventory_agent_node import inventory_agent
from agents.nodes.outbound_agent_node import outbound_agent
from prompts.generate_supervisor_prompt import supervisor_prompt
from config import settings
from domain.states.supervisor.diagnose_graph_state import WMState
from langgraph_supervisor import create_supervisor
from agents.nodes.inbound_agent_node import inbound_agent
from langchain_openai import ChatOpenAI
from langchain.messages import AIMessageChunk





@traceable(name="supervisor_node")
class WarehouseSupervisorNode:
    def __init__(self):

        ##choose llm based on whats available
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, streaming=True)


        ##set max loops for and llm to run over an issue
        self.max_loops = int(settings.SUPERVISOR_MAX_LOOP or 3)
        ##how many times child can loop
        self.child_max_loops = int(settings.CHILD_MAX_LOOP or 3)
        ##system prompt and chat prompt built in
        self.prompt = supervisor_prompt

        self.warehouse_supervisor = create_supervisor(
            agents=[
                inbound_agent,
                outbound_agent,
                inventory_agent,
            ],
            model=self.llm,
            prompt=self.prompt,
            output_mode="last_message",
            add_handoff_messages=False,
            parallel_tool_calls=False,
            supervisor_name="warehouse_supervisor",
        ).compile(name="warehouse_supervisor")

    async def __call__(self, state: WMState) -> dict:
        enriched = f"Ticket: {state.description}\n\n"

        try:
            async for chunk in self.warehouse_supervisor.astream(
                    {"messages": [{"role": "user", "content": enriched}]},
                    stream_mode="messages",
                    version="v2",
                    config={"recursion_limit": min(25, int(settings.SUPERVISOR_MAX_LOOP or 3) * 10)},
            ):
                msg, metadata = chunk["data"]
                if msg.content:
                    print(msg.content, end="", flush=True)

        except Exception as exc:
            return {
                "final_responses": f"Supervisor Error: {exc}",
                "error": str(exc),
                "final": True,
            }


        return {"diagnosis_result": "custom"}







