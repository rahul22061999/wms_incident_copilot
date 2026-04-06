import json
from pathlib import Path
from typing import Optional

from config import settings, BASE_DIR


class SessionStore:
    def __init__(self, session_dir= settings.SESSION_STORE_DIR):
        self.session_dir = BASE_DIR / session_dir
        self.session_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, session_id: str) -> Path:
        return self.session_dir/ f"{session_id}.json"

    def load(self, session_id: str) -> Optional[dict]:
        path = self._path(session_id)
        if path.exists():
            try:
                content = path.read_text()
                if content.strip():
                    return json.loads(content)
            except (json.JSONDecodeError, Exception):
                return None
        return None

    def save(self, session_id: str, state: dict) -> None:
        serialized={}
        for key, value in state.items():
            if key == "messages":
                serialized[key] = [
                    {
                        "type": type(msg).__name__,
                        "content":msg.content if hasattr(msg, "content") else str(msg),
                        "name": getattr(msg, "name", None),
                    }

                for msg in value
                ]
            else:
                serialized[key] = value

        self._path(session_id).write_text(json.dumps(serialized, indent=4, default=str))


    def exists(self, session_id: str) -> bool:
        return self._path(session_id).exists()

    def delete(self, session_id: str) -> None:
        path = self._path(session_id)
        if path.exists():
            path.unlink()


