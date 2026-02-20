"""AI Responses API integration tests. Requires DB; auth bypass for local."""
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


SAMPLE_MARKDOWN = """## Weekly Report Summary

This week showed **positive** trends.

### Key Points
- Session attendance improved
- Documentation at 94%

### Recommended Action
ACTION: open_queue_enterprise
LABEL: Review Enterprise Leads
CONFIDENCE: 0.91"""


@pytest.mark.asyncio
async def test_process_markdown(client):
    r = await client.post(
        "/ai-responses",
        json={
            "raw_markdown": SAMPLE_MARKDOWN,
            "entity_type": "weekly_report",
            "entity_id": "report_test_001",
            "model": "gpt-4",
            "confidence": 0.91,
        },
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert "id" in data
    assert data["entity_type"] == "weekly_report"
    assert data["entity_id"] == "report_test_001"
    assert "structured_blocks" in data
    assert len(data["structured_blocks"]) > 0
    assert data["confidence"] == 0.91
    assert "needs_review" in data
    # 0.91 >= 0.85 threshold, so no review needed
    assert data["needs_review"] is False


@pytest.mark.asyncio
async def test_process_markdown_rejects_script(client):
    r = await client.post(
        "/ai-responses",
        json={
            "raw_markdown": "Hello <script>alert(1)</script>",
            "entity_type": "test",
            "entity_id": "test_001",
        },
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_list_ai_responses(client):
    # Create then list in same test (self-contained)
    create = await client.post(
        "/ai-responses",
        json={
            "raw_markdown": "## List Test\nContent.",
            "entity_type": "weekly_report",
            "entity_id": "report_list_001",
        },
    )
    assert create.status_code == 200
    r = await client.get("/ai-responses?entity_id=report_list_001")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["entity_id"] == "report_list_001"


@pytest.mark.asyncio
async def test_get_ai_response(client):
    # Uses ID from test_process_markdown (runs first)
    create = await client.post(
        "/ai-responses",
        json={
            "raw_markdown": SAMPLE_MARKDOWN,
            "entity_type": "weekly_report",
            "entity_id": "report_test_001",
        },
    )
    assert create.status_code == 200
    resp_id = create.json()["id"]

    r = await client.get(f"/ai-responses/{resp_id}")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == resp_id
    assert "Weekly Report" in data["raw_markdown"]


@pytest.mark.asyncio
async def test_execute_action(client):
    r = await client.post(
        "/ai-responses/actions/execute",
        json={
            "command": "open_queue_enterprise",
            "label": "Review Enterprise Leads",
            "confidence": 0.91,
            "entity_type": "weekly_report",
            "entity_id": "report_action_001",
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["command"] == "open_queue_enterprise"
