from dataclasses import dataclass, field
from domain.states.supervisor.diagnose_graph_state import WMState
from datetime import datetime

@dataclass(frozen=True)
class StoredSession:
    session_id: str
    wm_state: WMState
    updated_at: datetime = field(default_factory=datetime.now)
    version: int = 1