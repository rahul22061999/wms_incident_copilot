from domain.states.supervisor.diagnose_graph_state import WMState


def result_node(state: WMState):

    # api_response = {
    #         "session_id": state.session_id,
    #         "ticket_number": state.ticket_number,
    #         "answer": "",
    #     "supporting_data": {
    #         "sql_executed": state.lookup_result.get('validated_sql', ''),
    #         "data_rows": state.lookup_result.get('execution_result', ''),
    #         "diagnosis_result":""
    #         }
    #     }
    # return api_response

    return state


