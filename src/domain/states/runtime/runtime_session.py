from domain.states.supervisor.diagnose_graph_state import WMState


class SessionRuntime:
    def __init__(self, store, graph, sql_graph):
        self.store = store
        self.graph = graph
        self.sql_graph = sql_graph

    def run(self, session_id: str, prompt: str) -> WMState:
        state = self.store.load(session_id) or WMState(session_id=session_id, messages=[])
        state.messages.append(UserMessag(content=prompt))
        updated = self.graph.invoke(state.model_dump())
        final_state = WMState.model_validate(updated)
        self.store.save(final_state)
        return final_state