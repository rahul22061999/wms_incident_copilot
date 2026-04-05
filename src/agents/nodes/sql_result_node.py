from domain.states.sql_subgraph_state.sql_graph_state import SQLGraphState
from domain.states.sql_subgraph_state.sql_task_result import SQLTaskResult


def sql_result_node(state: SQLGraphState) -> SQLGraphState:

    rows = state.execution_result.get("rows") for

    state.result = SQLTaskResult(
        ok= rows is not None,
        generated_sql=state.generated_sql,
        validated_sql=state.validated_sql,
        rows=rows,
        error=state.execution_result.get("error")
    )

    return state