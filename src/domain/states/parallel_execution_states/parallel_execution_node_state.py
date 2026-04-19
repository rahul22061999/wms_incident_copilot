from typing import List, Literal
from pydantic import BaseModel, Field


class SubTask(BaseModel):
    query: str= Field(description="List of subtasks")
    tool: Literal["sop_retrieval_node","sql_lookup_node"]
    domain: List[Literal["inbound", "outbound", "inventory", "none"]] = Field(
        default="none",
        description=(
            "WMS domain for SQL subtasks. Required for sql_lookup_tool. "
            "Use 'none' for rag_lookup_tool subtasks."
        ),
    )


class ParallelExecutionPlan(BaseModel):
    subtasks: List[SubTask] = Field(description="List of subtasks to run in parallel")




# {
#   "subtasks": [
#     {
#       "query": "What is the current stock level for SKU-009?",
#       "tool": "sql_lookup_tool"
#     },
#     {
#       "query": "What is the standard inbound receiving process?",
#       "tool": "sop_retrieval_tool"
#     }
#   ]
# }