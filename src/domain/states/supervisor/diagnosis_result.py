from dataclasses import dataclass, field


@dataclass
class DiagnosisResult:
    answer: str
    causes: list[str] = field(default_factory=list)
    sql: str = field(default_factory=str)
