from dataclasses import field, dataclass

@dataclass
class DiagnosisResult:
    answer: str
    causes: list[str] = field(default_factory=list)
    sql: str = field(default_factory=str)