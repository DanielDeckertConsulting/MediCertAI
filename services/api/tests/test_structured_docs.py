"""Structured session document and intervention library API tests. EPIC 14. Requires DB; auth bypass."""
import json
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.db import session_scope
from app.main import app

# Second tenant for RLS isolation tests (auth bypass uses DEV_TENANT_ID)
OTHER_TENANT_ID = UUID("00000000-0000-0000-0000-000000000011")

STRUCTURED_FIELDS = [
    "session_context",
    "presenting_symptoms",
    "resources",
    "interventions",
    "homework",
    "risk_assessment",
    "progress_evaluation",
]


@pytest.fixture
def client():
    return AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        timeout=30.0,
    )


@pytest.mark.asyncio
async def test_get_structured_document_404_when_none(client):
    create = await client.post("/chats", json={"title": "No Doc Chat"})
    assert create.status_code == 200
    cid = create.json()["id"]
    r = await client.get(f"/chats/{cid}/structured-document")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_put_structured_document_creates(client):
    create = await client.post("/chats", json={"title": "Create Doc Chat"})
    assert create.status_code == 200
    cid = create.json()["id"]
    content = {f: f"Sample {f}" for f in STRUCTURED_FIELDS}
    r = await client.put(f"/chats/{cid}/structured-document", json={"content": content})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["conversation_id"] == cid
    assert data["version"] == 1
    assert data["content"] == content


@pytest.mark.asyncio
async def test_get_structured_document_after_put(client):
    create = await client.post("/chats", json={"title": "Get Doc Chat"})
    assert create.status_code == 200
    cid = create.json()["id"]
    content = {f: f"Value {f}" for f in STRUCTURED_FIELDS}
    await client.put(f"/chats/{cid}/structured-document", json={"content": content})
    r = await client.get(f"/chats/{cid}/structured-document")
    assert r.status_code == 200
    data = r.json()
    assert data["content"] == content
    assert data["version"] == 1


@pytest.mark.asyncio
async def test_put_structured_document_increments_version(client):
    create = await client.post("/chats", json={"title": "Version Chat"})
    assert create.status_code == 200
    cid = create.json()["id"]
    content1 = {f: f"V1 {f}" for f in STRUCTURED_FIELDS}
    r1 = await client.put(f"/chats/{cid}/structured-document", json={"content": content1})
    assert r1.status_code == 200
    assert r1.json()["version"] == 1
    content2 = {f: f"V2 {f}" for f in STRUCTURED_FIELDS}
    r2 = await client.put(f"/chats/{cid}/structured-document", json={"content": content2})
    assert r2.status_code == 200
    assert r2.json()["version"] == 2
    get_r = await client.get(f"/chats/{cid}/structured-document")
    assert get_r.json()["content"] == content2
    assert get_r.json()["version"] == 2


@pytest.mark.asyncio
async def test_structured_document_schema_validates_extra_fields_ignored(client):
    """Backend normalizes to allowed fields only."""
    create = await client.post("/chats", json={"title": "Schema Chat"})
    assert create.status_code == 200
    cid = create.json()["id"]
    content = {f: "x" for f in STRUCTURED_FIELDS}
    content["extra_field"] = "ignored"
    r = await client.put(f"/chats/{cid}/structured-document", json={"content": content})
    assert r.status_code == 200
    data = r.json()
    for f in STRUCTURED_FIELDS:
        assert f in data["content"]
    assert "extra_field" not in data["content"]


@pytest.mark.asyncio
async def test_list_interventions(client):
    r = await client.get("/interventions")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    if data:
        item = data[0]
        assert "id" in item
        assert "category" in item
        assert "title" in item
        assert "description" in item


@pytest.mark.asyncio
async def test_convert_requires_existing_chat(client):
    """Convert on non-existent chat returns 404."""
    fake_id = str(uuid4())
    r = await client.post(f"/chats/{fake_id}/structured-document/convert")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_structured_document_rls_cross_tenant_isolation(client):
    """
    RLS: structured document for another tenant's chat is not visible to dev tenant.
    Create other tenant, user, chat, and structured doc; then GET as dev tenant must return 404.
    """
    other_chat_id = uuid4()
    other_user_id = uuid4()
    content = {f: f"Other tenant {f}" for f in STRUCTURED_FIELDS}
    other_b2c_sub = f"other-rls-{uuid4().hex}"

    async with session_scope(OTHER_TENANT_ID, str(other_user_id)) as session:
        await session.execute(
            text("""
                INSERT INTO tenants (id, name, settings)
                VALUES (:id, 'Other Tenant', '{}'::jsonb)
                ON CONFLICT (id) DO NOTHING
            """),
            {"id": str(OTHER_TENANT_ID)},
        )
        await session.execute(
            text("""
                INSERT INTO users (id, tenant_id, b2c_sub, email, role)
                VALUES (:id, :tenant_id, :b2c_sub, NULL, 'admin')
            """),
            {"id": str(other_user_id), "tenant_id": str(OTHER_TENANT_ID), "b2c_sub": other_b2c_sub},
        )
        await session.execute(
            text("""
                INSERT INTO chats (id, tenant_id, owner_user_id, title)
                VALUES (:id, :tenant_id, :owner_user_id, 'Other Tenant Chat')
            """),
            {
                "id": str(other_chat_id),
                "tenant_id": str(OTHER_TENANT_ID),
                "owner_user_id": str(other_user_id),
            },
        )
        await session.execute(
            text("""
                INSERT INTO structured_session_documents (tenant_id, conversation_id, version, content)
                VALUES (:tenant_id, :conversation_id, 1, CAST(:content AS jsonb))
            """),
            {
                "tenant_id": str(OTHER_TENANT_ID),
                "conversation_id": str(other_chat_id),
                "content": json.dumps(content),
            },
        )

    # API uses dev tenant (auth bypass). Must not see other tenant's structured doc.
    r = await client.get(f"/chats/{other_chat_id}/structured-document")
    assert r.status_code == 404, "RLS must prevent dev tenant from reading other tenant's structured document"
