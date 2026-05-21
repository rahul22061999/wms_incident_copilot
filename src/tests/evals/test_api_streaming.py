from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from api.app import app


@pytest.mark.asyncio
async def test_stream_ticket_job_returns_sse_response():
    async def fake_generator():
        yield "data: monitor_schedule_created\n\n"

    with patch(
        "application.stream_job_updates.stream_ticket_jobs_service",
        return_value=fake_generator(),
    ):
        client = TestClient(app)

        response = client.get(
            "/monitoring/INC0003/jobs/stream",
            params={"user_id": "rahul"},
        )

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")


def test_stream_ticket_job_requires_user_id():
    client = TestClient(app)

    response = client.get("/monitoring/INC0003/jobs/stream")

    assert response.status_code == 422