from dataclasses import dataclass, field
from datetime import datetime
from typing_extensions import Any


@dataclass
class Event:
    type: str
    node: str
    ts: datetime
    detail: dict[str, Any] = field(default_factory=dict)