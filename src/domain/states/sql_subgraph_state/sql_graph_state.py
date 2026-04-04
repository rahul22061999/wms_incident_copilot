from dataclasses import dataclass, field
from typing import Literal, Optional
from typing_extensions import TypedDict, Any


# class SQLGraphState(TypedDict):
#     domain: Optional[Literal["inbound", "outbound", "inventory"]]
#     description: str
#     # SQL lookup node
#     skill_context: str | None
#     table_names: str | None
#     generated_sql: str | None
#     validated_sql: str | None
#     query_rows: str | None
#     final_responses: str | None

@dataclass
class SQLGraphState:
    domain: Optional[Literal["inbound", "outbound", "inventory"]]
    parent_session_id: str
    user_question: str
    skill_context: str
    scratch: dict[str, Any] = field(default_factory=dict)
    generated_sql: str = field(default=None)
    execution_result: dict = field(default=None)
    errors: list[str] = field(default_factory=list)
