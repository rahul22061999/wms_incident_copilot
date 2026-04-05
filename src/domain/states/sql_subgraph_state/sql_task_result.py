from dataclasses import dataclass
from typing import Optional, List, Dict, Any


@dataclass
class SQLTaskResult:
    ok: bool
    generated_sql: Optional[str] = None
    validated_sql: Optional[str] = None
    rows: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None