"""Case summary API tests. Azure OpenAI mocked."""
import pytest
from unittest.mock import AsyncMock, patch
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
def client():
    return AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        timeout=30.0,
    )


@pytest.mark.asyncio
async def test_case_summary_empty_ids_rejected(client):
    r = await client.post("/cases/summary", json={"conversation_ids": []})
    assert r.status_code == 400
    assert "conversation_ids" in r.json().get("detail", "").lower()


@pytest.mark.asyncio
async def test_case_summary_missing_ids_rejected(client):
    r = await client.post("/cases/summary", json={})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_case_summary_no_accessible_chats(client):
    """When no chats belong to user, returns 400."""
    import uuid

    fake_ids = [str(uuid.uuid4())]
    with patch(
        "app.services.case_summary_service.generate_case_summary",
        side_effect=ValueError("No accessible conversations found"),
    ):
        r = await client.post(
            "/cases/summary",
            json={"conversation_ids": fake_ids},
        )
    assert r.status_code == 400
    assert "No accessible" in r.json()["detail"]


@pytest.mark.asyncio
async def test_case_summary_returns_structured_output(client):
    """With mocked LLM, returns case_summary, trends, treatment_evolution."""
    create = await client.post("/chats", json={"title": "Summary Test"})
    assert create.status_code == 200
    chat_id = create.json()["id"]

    mock_summary = {
        "case_summary": "Testfall: dokumentierter Verlauf.",
        "trends": ["Thema A wiederholt", "Thema B erwähnt"],
        "treatment_evolution": "Dokumentierter Verlauf ohne Empfehlung.",
    }

    with patch(
        "app.routers.cases.generate_case_summary",
        new_callable=AsyncMock,
        return_value=(mock_summary, {"prompt_tokens": 100, "completion_tokens": 50}),
    ):
        r = await client.post(
            "/cases/summary",
            json={"conversation_ids": [chat_id]},
        )
    assert r.status_code == 200
    data = r.json()
    assert data["case_summary"] == mock_summary["case_summary"]
    assert data["trends"] == mock_summary["trends"]
    assert data["treatment_evolution"] == mock_summary["treatment_evolution"]
