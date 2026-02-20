"""Chat API smoke tests. Requires DB; Azure OpenAI mocked or skipped."""
import pytest
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
async def test_create_chat(client):
    r = await client.post("/chats", json={"title": "Test Chat"})
    assert r.status_code == 200, r.text
    data = r.json()
    assert "id" in data
    assert data["title"] == "Test Chat"
    assert "created_at" in data


@pytest.mark.asyncio
async def test_list_chats(client):
    r = await client.get("/chats")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_create_and_get_chat(client):
    create = await client.post("/chats", json={"title": "Get Test"})
    assert create.status_code == 200
    chat_id = create.json()["id"]

    r = await client.get(f"/chats/{chat_id}")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == chat_id
    assert data["title"] == "Get Test"
    assert data["messages"] == []
