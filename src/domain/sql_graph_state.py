from typing import Literal, Optional
from pydantic import BaseModel, Field


class SQLGraphState(BaseModel):
    domain: Optional[Literal["inbound", "outbound", "inventory"]] = Field(
        default=None,
        description="Business domain for the request"
    )
    description: str = Field(description="User request or ticket description")

    # SQL lookup node
    skill_context: Optional[str] = Field(default=None, description="Relevant skill context")
    table_names: Optional[str] = Field(default=None, description="Relevant database tables")

    # Generate SQL node
    generated_sql: Optional[str] = Field(default=None, description="Generated SQL statement")

    # SQL check node
    validated_sql: Optional[str] = Field(default=None, description="Validated SQL statement")

    # Run SQL node
    query_rows: Optional[str] = Field(default=None, description="Query result rows")

    # Result node
    final_response: Optional[str] = Field(default=None, description="Final user-facing response")