from dataclasses import dataclass

MAX_RUNS = 10
ACTIVE_STATUSES = {"active", "running"}


@dataclass
class MonitoringInput:
    job_id: str
    query: str
    interval_seconds: int
    ticket_number: str
    session_id: str
    user_id: str
    max_runs: int = MAX_RUNS