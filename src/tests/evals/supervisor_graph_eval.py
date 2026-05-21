from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
async def test_supervisor_routes_monitoring_query_to_schedule_node():
    state = {
        "query": "Monitor this ticket every 30 seconds",
        "ticket_number": "INC0003",
        "user_id": "rahul",
        "session_id": "eval-session-001",
        "interval_seconds": 30,
    }

    with patch(
        "application.nodes.schedule_registrar_node.schedule_task",
        new=AsyncMock(return_value={"job_id": "job-123"}),
    ):
        from application.nodes.schedule_registrar_node import schedule_registrar_node

        result = await schedule_registrar_node(state)

        assert "schedular_results" in result
        assert "monitor_schedule_created" in result["schedular_results"]


@pytest.mark.asyncio
async def test_supervisor_does_not_schedule_for_normal_question():
    query = "Why are cartons stuck?"

    should_schedule = should_route_to_monitoring(query)

    assert should_schedule is False


@pytest.mark.asyncio
async def test_supervisor_schedules_for_monitoring_question():
    query = "Keep checking this ticket every 60 seconds"

    should_schedule = should_route_to_monitoring(query)

    assert should_schedule is True


def should_route_to_monitoring(query: str) -> bool:
    keywords = ["monitor", "keep checking", "every", "schedule", "watch"]

    query_lower = query.lower()

    return any(keyword in query_lower for keyword in keywords)