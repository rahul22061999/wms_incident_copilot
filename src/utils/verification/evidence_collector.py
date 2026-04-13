from domain.states.supervisor.supervisor_evidence_states import EvidenceRecord


class EvidenceCollector:
    def __init__(self, existing: list[EvidenceRecord] | None = None):
        self.existing: list[EvidenceRecord] = existing or []
        self.collected: list[EvidenceRecord] = []

    def add(self, source: str, content: dict):
        version = (
            len([r for r in self.existing if r.source == source]) +
            len([r for r in self.collected if r.source == source])
        ) + 1

        record = EvidenceRecord(
            evidence_id=f"{source}:{version}",
            source=source,
            content=content,
        )

        self.collected.append(record)
        return record

    def flush(self) -> list[EvidenceRecord]:
        return self.collected