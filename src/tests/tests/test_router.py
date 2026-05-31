import pytest

from workflows.nodes.router_node import router_node


@pytest.mark.parametrize(
    "query, expected_route",
    [
        ("Monitor order 123 every 5 minutes", "schedule"),
        ("Cancel monitoring for order 123", "cancel_schedule"),
        ("Check why order 123 is stuck", "sequential"),
        ("Check inventory, shipment, and allocation for order 123", "parallel"),
    ],
)
def test_router_route(query, expected_route):
    result = router_node({"query": query})
    assert result["route"] == expected_route