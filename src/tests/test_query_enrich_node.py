import pytest
from unittest.mock import MagicMock, patch
from domain.states.supervisor.diagnose_graph_state import WMState
from workflows.nodes import query_enrich_node


def make_state(description):
    return WMState(
        description=description,
        session_id="example",
        ticket_number="INC",
        user_id="rahul",
    )


def make_mock_model(enriched_query="Enriched query", domain=None):
    if domain is None:
        domain = ["inbound"]

    response = MagicMock()
    response.enriched_query = enriched_query
    response.routing_decision = domain  # list, not a dict

    model = MagicMock()
    model.invoke.return_value = response
    return model


@patch("agents.nodes.query_enrich_node.get_google_llm")
@patch("agents.nodes.query_enrich_node.get_openai_fast_llm")
def test_happy_path(mock_openai, mock_google):
    mock_google.return_value.with_structured_output.return_value \
        .with_fallbacks.return_value = make_mock_model(
            enriched_query=(
                "Investigate why Purchase Order (PO) P07283 has not been confirmed "
                "as received in the WMS. Check the status of the associated Advanced "
                "Shipment Notice (ASN), verify if the inbound shipment has arrived at "
                "the dock, and identify any receiving discrepancies or missing Goods "
                "Receipt Note (GRN) records."
            ),
            domain=["inbound"],
        )

    result = query_enrich_node(make_state("Why is PO P07283 not received?"))

    assert "Purchase Order" in result["description"]
    assert "ASN" in result["description"]
    assert result["routing_decision"] == ["inbound"]


@patch("agents.nodes.query_enrich_node.get_google_llm")
@patch("agents.nodes.query_enrich_node.get_openai_fast_llm")
def test_empty_description_raises(mock_openai, mock_google):
    with pytest.raises(ValueError, match="state.description is empty"):
        query_enrich_node(make_state(""))


@patch("agents.nodes.query_enrich_node.get_google_llm")
@patch("agents.nodes.query_enrich_node.get_openai_fast_llm")
@pytest.mark.parametrize("query, domain", [
    ("Why is PO12345 not received?",        ["inbound"]),
    ("Carton C98765 is stuck not shipping", ["outbound"]),
    ("How much SKU0042 is in WH01?",        ["inventory"]),
])
def test_domain_routing(mock_openai, mock_google, query, domain):
    mock_google.return_value.with_structured_output.return_value \
        .with_fallbacks.return_value = make_mock_model(domain=domain)

    result = query_enrich_node(make_state(query))

    assert result["routing_decision"] == domain