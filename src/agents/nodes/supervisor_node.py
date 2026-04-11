# import logging
#
# from langchain_core.messages import ToolMessage, AIMessageChunk
# from agents.nodes.inbound_agent_node import inbound_agent
# from agents.nodes.outbound_agent_node import outbound_agent
# from agents.nodes.inventory_agent_node import inventory_agent
# from prompts.generate_supervisor_prompt import supervisor_prompt
# from config import settings
# from langgraph_supervisor import create_supervisor
# from langchain_openai import ChatOpenAI
# from langchain.messages import HumanMessage
# from domain.states.supervisor.diagnose_graph_state import WMState
# from utils.logging.logging_config import setup_logging
#
# setup_logging()
# logger = logging.getLogger(__name__)
#
#
# class WarehouseSupervisorNode:
#     def __init__(self):
#         self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, streaming=True)
#
#         self.max_loops = int(settings.SUPERVISOR_MAX_LOOP or 3)
#         self.child_max_loops = int(settings.CHILD_MAX_LOOP or 3)
#         self.prompt = supervisor_prompt
#
#         self.warehouse_supervisor = create_supervisor(
#             agents=[
#                 inbound_agent,
#                 outbound_agent,
#                 inventory_agent],
#             model=self.llm,
#             prompt=self.prompt,
#             output_mode="last_message",
#             add_handoff_messages=True,
#             parallel_tool_calls=False,
#             supervisor_name="warehouse_supervisor"
#         ).compile(name="warehouse_supervisor")
#
#     async def __call__(self, state: WMState) -> dict:
#         """Supervisor call method: stream messages and optionally capture final state.
#
#         Tuple shapes from graph.astream(..., stream_mode=["messages","values"], subgraphs=True):
#           (namespace, mode, payload)
#
#           - mode == "messages": payload is (chunk, meta)
#           - mode == "values"  and namespace == (): payload is the final outer graph state (dict)
#         """
#
#         final_text = ""
#
#         inputs = {
#             "messages": [HumanMessage(content=state.description)]
#         }
#
#         try:
#             async for namespace, mode, payload in self.warehouse_supervisor.astream(
#                     inputs,
#                     config={"recursion_limit": min(25, self.max_loops * 10)},
#                     stream_mode=["messages"],
#                     subgraphs=True
#             ):
#                 if mode != "messages":
#                     continue
#                 message_chunk, metadata = payload
#
#                 if isinstance(message_chunk, ToolMessage):
#                     continue
#
#                 raw_content = getattr(message_chunk, "content", "") or ""
#
#                 # content can be str OR list of content blocks
#                 if isinstance(raw_content, list):
#                     # extract text from content blocks
#                     text = "".join(
#                         block.get("text", "")
#                         for block in raw_content
#                         if isinstance(block, dict) and block.get("type") == "text"
#                     )
#                 else:
#                     text = raw_content
#
#                 if text:
#                     yield text
#                     final_text += text
#
#
#         except Exception as exc:
#             return {
#                 "diagnosis_result": str(exc),
#                 "error": str(exc),
#             }
#
#         logger.info("SUPERVISOR NODE CALLED")
#         return {
#             "status": "done",
#             "event_log": [{"node":"supervisor_node", "status":"Completed" \
#                           if final_text else "failed" }],
#             "diagnosis_result": final_text,
#             "error": None
#         }
#
#
import logging
from langchain_core.messages import ToolMessage, HumanMessage
from langgraph.config import get_stream_writer
from langgraph_supervisor import create_supervisor
from langchain_openai import ChatOpenAI

from agents.nodes.inbound_agent_node import inbound_agent
from agents.nodes.outbound_agent_node import outbound_agent
from agents.nodes.inventory_agent_node import inventory_agent
from prompts.generate_supervisor_prompt import supervisor_prompt
from config import settings
from domain.states.supervisor.diagnose_graph_state import WMState

logger = logging.getLogger(__name__)


class WarehouseSupervisorNode:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        self.max_loops = int(settings.SUPERVISOR_MAX_LOOP or 3)
        self.prompt = supervisor_prompt

        self.warehouse_supervisor = create_supervisor(
            agents=[inbound_agent, outbound_agent, inventory_agent],
            model=self.llm,
            prompt=self.prompt,
            output_mode="last_message",
            add_handoff_messages=True,
            parallel_tool_calls=False,
            supervisor_name="warehouse_supervisor",
        ).compile(name="warehouse_supervisor")

    def __call__(self, state: WMState) -> dict:
        writer = get_stream_writer()   # ← grabs the parent stream's writer
        final_text = ""

        inputs = {"messages": [HumanMessage(content=state.description)]}

        try:
            for namespace, mode, payload in self.warehouse_supervisor.stream(
                inputs,
                config={"recursion_limit": min(25, self.max_loops * 10)},
                stream_mode=["messages"],
                subgraphs=True,
            ):
                if mode != "messages":
                    continue
                message_chunk, metadata = payload
                if isinstance(message_chunk, ToolMessage):
                    continue

                raw = getattr(message_chunk, "content", "") or ""
                if isinstance(raw, list):
                    text = "".join(
                        b.get("text", "")
                        for b in raw
                        if isinstance(b, dict) and b.get("type") == "text"
                    )
                else:
                    text = raw

                if text:
                    writer({"token": text})   # ← emit to outer stream
                    final_text += text

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
            "diagnosis_result": final_text,
            "error": None,
        }