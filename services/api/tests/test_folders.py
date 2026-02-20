"""Folder API tests. Requires DB; uses auth bypass."""
import uuid

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
async def test_create_folder(client):
    name = f"EMDR_{uuid.uuid4().hex[:8]}"
    r = await client.post("/folders", json={"name": name})
    assert r.status_code == 200, r.text
    data = r.json()
    assert "id" in data
    assert data["name"] == name
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_folder_empty_name_rejected(client):
    r = await client.post("/folders", json={"name": ""})
    assert r.status_code == 400
    r2 = await client.post("/folders", json={"name": "   "})
    assert r2.status_code == 400


@pytest.mark.asyncio
async def test_create_folder_duplicate_name_rejected(client):
    name = f"Duplicate_{uuid.uuid4().hex[:8]}"
    await client.post("/folders", json={"name": name})
    r = await client.post("/folders", json={"name": name})
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_list_folders(client):
    r = await client.get("/folders")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_patch_folder(client):
    name = f"RenameMe_{uuid.uuid4().hex[:8]}"
    create = await client.post("/folders", json={"name": name})
    assert create.status_code == 200
    folder_id = create.json()["id"]
    new_name = f"Renamed_{uuid.uuid4().hex[:8]}"

    r = await client.patch(f"/folders/{folder_id}", json={"name": new_name})
    assert r.status_code == 200
    assert r.json()["name"] == new_name


@pytest.mark.asyncio
async def test_delete_folder(client):
    name = f"ToDelete_{uuid.uuid4().hex[:8]}"
    create = await client.post("/folders", json={"name": name})
    assert create.status_code == 200
    folder_id = create.json()["id"]

    r = await client.delete(f"/folders/{folder_id}")
    assert r.status_code == 204


@pytest.mark.asyncio
async def test_assign_chat_to_folder(client):
    name = f"TestFolder_{uuid.uuid4().hex[:8]}"
    folder = await client.post("/folders", json={"name": name})
    assert folder.status_code == 200
    folder_id = folder.json()["id"]

    chat_title = f"Chat_{uuid.uuid4().hex[:8]}"
    chat = await client.post("/chats", json={"title": chat_title})
    assert chat.status_code == 200
    chat_id = chat.json()["id"]

    r = await client.patch(f"/chats/{chat_id}", json={"folder_id": folder_id})
    assert r.status_code == 200
    assert r.json().get("folder_id") == folder_id

    list_r = await client.get(f"/chats?folder_id={folder_id}")
    assert list_r.status_code == 200
    chats = list_r.json()
    assert any(c["id"] == chat_id for c in chats)


@pytest.mark.asyncio
async def test_list_chats_unfiled_only(client):
    r = await client.get("/chats?unfiled_only=true")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_unassign_chat_from_folder(client):
    """Unassign chat via folder_id empty string (sets folder to null)."""
    folder_name = f"UnassignFolder_{uuid.uuid4().hex[:8]}"
    folder = await client.post("/folders", json={"name": folder_name})
    assert folder.status_code == 200
    folder_id = folder.json()["id"]

    chat_title = f"UnassignChat_{uuid.uuid4().hex[:8]}"
    chat = await client.post("/chats", json={"title": chat_title})
    assert chat.status_code == 200
    chat_id = chat.json()["id"]

    assign = await client.patch(f"/chats/{chat_id}", json={"folder_id": folder_id})
    assert assign.status_code == 200
    assert assign.json().get("folder_id") == folder_id

    r = await client.patch(f"/chats/{chat_id}", json={"folder_id": ""})
    assert r.status_code == 200
    assert r.json().get("folder_id") is None

    list_r = await client.get("/chats?unfiled_only=true")
    assert list_r.status_code == 200
    assert any(c["id"] == chat_id for c in list_r.json())


@pytest.mark.asyncio
async def test_patch_chat_invalid_folder_id_returns_403(client):
    """Assign chat to non-existent folder returns 403."""
    chat_title = f"InvalidFolderChat_{uuid.uuid4().hex[:8]}"
    chat = await client.post("/chats", json={"title": chat_title})
    assert chat.status_code == 200
    chat_id = chat.json()["id"]

    fake_folder_id = str(uuid.uuid4())
    r = await client.patch(f"/chats/{chat_id}", json={"folder_id": fake_folder_id})
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_patch_folder_not_found_returns_404(client):
    """Patch non-existent folder returns 404."""
    fake_folder_id = str(uuid.uuid4())
    r = await client.patch(f"/folders/{fake_folder_id}", json={"name": "Any"})
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_delete_folder_not_found_returns_404(client):
    """Delete non-existent folder returns 404."""
    fake_folder_id = str(uuid.uuid4())
    r = await client.delete(f"/folders/{fake_folder_id}")
    assert r.status_code == 404
