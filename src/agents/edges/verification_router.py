from domain.states.supervisor.diagnose_graph_state import WMState

def route_after_verification(state: WMState) -> str:
    vr = state.verification_result

    if vr is None:
        return "supervisor"

    if vr.status == "pass":
        return "result"

    return "supervisor"