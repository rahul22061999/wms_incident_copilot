"""
SQL subgraph state definitions — merged from three single-file folders.
All SQL pipeline shapes live here: subquery generation, graph state, task result.
"""

from dataclasses import dataclass, field
from typing import Literal, Optional, List, Annotated, Any, Dict
import operator

from pydantic import BaseModel, Field


# ---------- Subquery generation ----------

class Subquery(BaseModel):
    domain: str = Field(description="One of: inbound, outbound, inventory")
    query: str = Field(description="The self-contained subquery for this domain")


class GenerateSubqueries(BaseModel):
    subqueries: List[Subquery] = Field(default_factory=list)


# ---------- SQL graph state ----------

@dataclass
class SQLGraphState:
    domain: Optional[List[Literal["inbound", "outbound", "inventory"]]] = None
    parent_session_id: Optional[str] = None
    user_question: str = ""

    skill_context: List[Dict[str, str]] = field(default_factory=list)

    subqueries: GenerateSubqueries = field(default_factory=GenerateSubqueries)
    generated_sql: Dict[str, str] = field(default_factory=dict)
    validated_sql: Dict[str, str] = field(default_factory=dict)
    execution_result: Optional[Dict[str, Any]] = None
    errors: List[str] = field(default_factory=list)

    source: Literal["sql", "log", "sop", "ticket"] = None
    content: Annotated[dict, operator.or_] = field(default_factory=dict)


# ---------- Task result ----------

@dataclass
class SQLTaskResult:
    ok: bool
    generated_sql: Optional[str] = None
    validated_sql: Optional[str] = None
    rows: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
