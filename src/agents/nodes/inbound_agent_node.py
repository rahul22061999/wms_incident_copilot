from langchain.agents import create_agent
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel

from data.state import WorkerInput
from models.model_loader import get_google_llm
from tools.sql_lookup_tool import sql_lookup_tool
from dotenv import load_dotenv
load_dotenv()

class InboundAgent(BaseModel):
    messages: str

def inbound_agent_node(state: WorkerInput):
    task_id = state.task_id
    agent_name = state.agent_name
    task = state.task

    llm = get_google_llm()


    agent = create_agent(
        model=llm,
        tools=[sql_lookup_tool],
        system_prompt="You are an inbound agent to research inbound issues."
    )

    result = agent.invoke({
    "messages": [
        {"role": "user", "content": task}
    ]
    })

    return {
        "task_id": task_id,
        "agent_name": agent_name,
        "messages": result["messages"][-1].content,
    }






