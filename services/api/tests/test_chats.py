"""Chat API smoke tests. Requires DB; Azure OpenAI mocked or skipped."""
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.routers.chats import _SAFE_MODE_MODIFIER


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
    # Session context for Smart Context Banner (empty chat)
    assert "last_message_at" in data
    assert data["last_message_at"] is None
    assert "first_message_at" in data
    assert data["first_message_at"] is None
    assert "total_tokens_in_session" in data
    assert data["total_tokens_in_session"] == 0
    assert "metadata" in data


@pytest.mark.asyncio
async def test_patch_chat_metadata_persists(client):
    """Toggle safe_mode persists per conversation and is returned by GET."""
    create = await client.post("/chats", json={"title": "Safe Mode Test"})
    assert create.status_code == 200
    chat_id = create.json()["id"]

    # PATCH with safe_mode: true
    r = await client.patch(f"/chats/{chat_id}", json={"metadata": {"safe_mode": True}})
    assert r.status_code == 200

    get_r = await client.get(f"/chats/{chat_id}")
    assert get_r.status_code == 200
    assert get_r.json().get("metadata", {}).get("safe_mode") is True

    # PATCH to turn off
    await client.patch(f"/chats/{chat_id}", json={"metadata": {"safe_mode": False}})
    get_r2 = await client.get(f"/chats/{chat_id}")
    assert get_r2.json().get("metadata", {}).get("safe_mode") is False


@pytest.mark.asyncio
async def test_safe_mode_no_cross_conversation_effect(client):
    """Safe mode in chat A does not affect chat B."""
    a = await client.post("/chats", json={"title": "Chat A"})
    b = await client.post("/chats", json={"title": "Chat B"})
    assert a.status_code == 200 and b.status_code == 200
    chat_a_id = a.json()["id"]
    chat_b_id = b.json()["id"]

    await client.patch(f"/chats/{chat_a_id}", json={"metadata": {"safe_mode": True}})

    get_a = await client.get(f"/chats/{chat_a_id}")
    get_b = await client.get(f"/chats/{chat_b_id}")
    assert (get_a.json().get("metadata") or {}).get("safe_mode") is True
    assert (get_b.json().get("metadata") or {}).get("safe_mode") is not True


@pytest.mark.asyncio
async def test_export_txt(client):
    create = await client.post("/chats", json={"title": "Export TXT Test"})
    assert create.status_code == 200
    chat_id = create.json()["id"]

    r = await client.get(f"/chats/{chat_id}/export?format=txt")
    assert r.status_code == 200
    assert "text/plain" in r.headers.get("content-type", "")
    body = r.text
    assert "Export TXT Test" in body


@pytest.mark.asyncio
async def test_export_txt_backward_compat(client):
    create = await client.post("/chats", json={"title": "Export Legacy"})
    assert create.status_code == 200
    chat_id = create.json()["id"]

    r = await client.get(f"/chats/{chat_id}/export.txt")
    assert r.status_code == 200
    assert "text/plain" in r.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_export_pdf(client):
    create = await client.post("/chats", json={"title": "Export PDF Test"})
    assert create.status_code == 200
    chat_id = create.json()["id"]

    r = await client.get(f"/chats/{chat_id}/export?format=pdf")
    assert r.status_code == 200
    assert r.headers.get("content-type", "").startswith("application/pdf")
    assert len(r.content) > 100
    assert r.content[:4] == b"%PDF"


@pytest.mark.asyncio
async def test_export_chat_not_found(client):
    import uuid
    fake_id = str(uuid.uuid4())
    r = await client.get(f"/chats/{fake_id}/export?format=txt")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_export_invalid_format(client):
    create = await client.post("/chats", json={"title": "Export Invalid"})
    assert create.status_code == 200
    chat_id = create.json()["id"]

    r = await client.get(f"/chats/{chat_id}/export?format=docx")
    assert r.status_code == 400


# --- Conversation Lock / Finalize ---
@pytest.mark.asyncio
async def test_finalize_chat(client):
    create = await client.post("/chats", json={"title": "Finalize Test"})
    assert create.status_code == 200
    chat_id = create.json()["id"]
    assert create.json().get("status", "active") == "active"

    r = await client.post(f"/chats/{chat_id}/finalize")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "finalized"
    assert data["id"] == chat_id

    get_r = await client.get(f"/chats/{chat_id}")
    assert get_r.status_code == 200
    assert get_r.json()["status"] == "finalized"


@pytest.mark.asyncio
async def test_finalize_already_finalized(client):
    create = await client.post("/chats", json={"title": "Double Finalize"})
    assert create.status_code == 200
    chat_id = create.json()["id"]

    await client.post(f"/chats/{chat_id}/finalize")
    r = await client.post(f"/chats/{chat_id}/finalize")
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_patch_finalized_chat_rejected(client):
    create = await client.post("/chats", json={"title": "Patch Locked"})
    assert create.status_code == 200
    chat_id = create.json()["id"]
    await client.post(f"/chats/{chat_id}/finalize")

    r = await client.patch(f"/chats/{chat_id}", json={"title": "New Title"})
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_delete_finalized_chat_rejected(client):
    create = await client.post("/chats", json={"title": "Delete Locked"})
    assert create.status_code == 200
    chat_id = create.json()["id"]
    await client.post(f"/chats/{chat_id}/finalize")

    r = await client.delete(f"/chats/{chat_id}")
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_export_finalized_chat_allowed(client):
    create = await client.post("/chats", json={"title": "Export Finalized"})
    assert create.status_code == 200
    chat_id = create.json()["id"]
    await client.post(f"/chats/{chat_id}/finalize")

    r = await client.get(f"/chats/{chat_id}/export?format=txt")
    assert r.status_code == 200
    assert "Export Finalized" in r.text


def test_safe_mode_modifier_contains_required_phrases():
    """Safe mode modifier instructs conservative phrasing and no absolutes."""
    assert "konservativ" in _SAFE_MODE_MODIFIER.lower()
    assert "absoluten" in _SAFE_MODE_MODIFIER.lower() or "absolute" in _SAFE_MODE_MODIFIER.lower()
    assert "fachliche" in _SAFE_MODE_MODIFIER.lower()
    assert "spekulativen" in _SAFE_MODE_MODIFIER.lower() or "spekulativ" in _SAFE_MODE_MODIFIER.lower()


@pytest.mark.asyncio
async def test_send_message_finalized_chat_rejected(client):
    create = await client.post("/chats", json={"title": "Send Locked"})
    assert create.status_code == 200
    chat_id = create.json()["id"]
    await client.post(f"/chats/{chat_id}/finalize")

    r = await client.post(
        f"/chats/{chat_id}/messages",
        json={"assist_mode_key": "CHAT_WITH_AI", "user_message": "Hello"},
    )
    assert r.status_code == 409
