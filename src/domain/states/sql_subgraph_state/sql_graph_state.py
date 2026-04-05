from dataclasses import dataclass, field
from typing import Literal, Optional, List
from typing_extensions import Any, Dict
from domain.states.sql_generate_subquery.sql_generate_subqueries_state import GenerateSubqueries

@dataclass
class SQLGraphState:
    # input
    domain: Optional[List[Literal["inbound", "outbound", "inventory"]]] = None
    parent_session_id: Optional[str] = None
    user_question: str = ""

    # context / scratch
    skill_context: List[Dict[str, str]] = field(default_factory=list)
    scratch: Dict[str, Any] = field(default_factory=dict)

    # intermediate outputsre
    subqueries: GenerateSubqueries = field(default_factory=GenerateSubqueries)
    generated_sql: Dict[str, str] = field(default_factory=dict)
    validated_sql: Dict[str, str] = field(default_factory=dict)
    execution_result: Optional[Dict[str, Any]] = None
    errors: List[str] = field(default_factory=list)
