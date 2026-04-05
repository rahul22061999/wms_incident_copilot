from src.session_store import (
    StoredAgentSession, save_agent_session,
    serialize_model_config, serialize_runtime_config
)
from pathlib import Path

def persist_wmstate(wm: WMState, model_config, runtime_config, usage: dict, total_cost_usd: float, directory: Path | None = None):
    # Build StoredAgentSession consistent with claw-code-agent shape
    stored = StoredAgentSession(
        session_id=wm.session_id,
        model_config=serialize_model_config(model_config),
        runtime_config=serialize_runtime_config(runtime_config),
        system_prompt_parts=(),                # if you build system prompt parts, put them here
        user_context={},                       # optional
        system_context={},                     # optional
        messages=tuple(wm.messages),
        turns=0,                               # supply a turns count if you track it
        tool_calls=0,                          # supply tool_calls if you track it
        usage=usage or {},
        total_cost_usd=float(total_cost_usd or 0.0),
        file_history=tuple(wm.file_history),
        budget_state=dict(wm.budget_state or {}),
        plugin_state=dict(wm.plugin_state or {}),
        scratchpad_directory=wm.scratchpad_directory,
    )
    path = save_agent_session(stored, directory=directory)
    return path