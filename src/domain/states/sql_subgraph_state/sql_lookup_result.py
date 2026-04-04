from dataclasses import dataclass, field

@dataclass
class LookupResult:
    answer: str
    evidence: list[dict] = field(default_factory=list[dict])
    sql: str = field(default_factory=str)