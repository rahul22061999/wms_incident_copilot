from agents.graph.sql_subgraph import sql_graph
from domain.states.sql_subgraph_state.sql_graph_state import SQLGraphState
from domain.states.supervisor.diagnose_graph_state import WMState


def sql_query_subgraph_node(state: WMState) -> dict:
    """
    Parent WMState -> SQLGraphState
    SQLGraphState result -> Parent WMState
    """
    decision = state.routing_decision or {}
    domain = decision.get("domain")

    sql_input=SQLGraphState(
            domain=domain,
            user_question=state.description,
            parent_session_id=state.session_id
    )

    result = sql_graph.invoke(sql_input.model_dump())

    payload = result.model_dump() if hasattr(result, "model_dump") else result

    return {"lookup_result": payload }