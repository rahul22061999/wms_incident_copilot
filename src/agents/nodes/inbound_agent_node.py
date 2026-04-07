from langchain.agents import create_agent
from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from prompts.generate_inbound_agent_prompt import inbound_agent_prompt
from langgraph.types import Command
from dataclasses import dataclass
from models.model_loader import get_google_llm, get_openai_fast_llm
from tools.sql_lookup_tool import sql_lookup_tool
from tools.rag_lookup_tool import sop_retrieval_tool
from langchain_core.messages import AnyMessage
from dotenv import load_dotenv
from typing import TypedDict, NotRequired
from langchain.agents import create_agent

load_dotenv()


# Build once at module level — not on every invocation
_llm = (
    get_google_llm()
    .with_fallbacks([
        get_openai_fast_llm()
    ])
)
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

inbound_agent = create_agent(
        model=llm,
        tools=[sql_lookup_tool, sop_retrieval_tool],
        system_prompt=inbound_agent_prompt,
        name="inbound_agent",
)
