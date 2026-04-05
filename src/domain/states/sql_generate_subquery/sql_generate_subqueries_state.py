from pydantic import BaseModel, Field
from typing import List

class Subquery(BaseModel):
    domain: str = Field(description="One of: inbound, outbound, inventory")
    query: str = Field(description="The self-contained subquery for this domain")

class GenerateSubqueries(BaseModel):
    subqueries: List[Subquery] = Field(default_factory=list)