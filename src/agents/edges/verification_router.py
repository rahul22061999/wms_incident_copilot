from domain.states.supervisor.diagnose_graph_state import WMState

def route_after_verification(state: WMState) -> str:
    vr = state.verification_result

    if vr is None:
        return "result"

    if vr.status == "pass":
        return "result"

    if vr.status == "need_more_evidence":
        return "supervisor"

    return "result"