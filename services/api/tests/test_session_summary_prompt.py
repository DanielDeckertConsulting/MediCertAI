"""Verify SESSION_SUMMARY and STRUCTURED_DOC system prompts."""
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
async def test_chat_with_ai_prompt_exists(client):
    """CHAT_WITH_AI prompt exists and is general conversational."""
    r = await client.get("/prompts/CHAT_WITH_AI/latest")
    assert r.status_code == 200
    data = r.json()
    assert data["key"] == "CHAT_WITH_AI"
    assert "Chat with AI" in data["body"] or "helpful" in data["body"].lower()
    assert "German" in data["body"] or "de-DE" in data["body"]


@pytest.mark.asyncio
async def test_risk_analysis_prompt_contains_expected_structure(client):
    """RISK_ANALYSIS prompt must include risk reflection structure and cautious language."""
    r = await client.get("/prompts/RISK_ANALYSIS/latest")
    assert r.status_code == 200
    data = r.json()
    assert data["key"] == "RISK_ANALYSIS"
    body = data["body"]

    # Constraints
    assert "NOT performing diagnosis" in body
    assert "NOT give emergency instructions" in body
    assert "German (de-DE)" in body
    assert "Im Text finden sich Hinweise" in body or "weiter zu explorieren" in body

    # Output structure
    assert "Risikoanalyse" in body
    assert "Explizit genannte Hinweise" in body
    assert "Implizite Risikosignale" in body
    assert "Schutzfaktoren" in body
    assert "Offene Fragen" in body
    assert "Gesamteindruck" in body


@pytest.mark.asyncio
async def test_therapy_plan_prompt_contains_expected_structure(client):
    """THERAPY_PLAN prompt must include draft structure and cautious wording."""
    r = await client.get("/prompts/THERAPY_PLAN/latest")
    assert r.status_code == 200
    data = r.json()
    assert data["key"] == "THERAPY_PLAN"
    body = data["body"]

    # Constraints
    assert "Do NOT provide diagnosis" in body
    assert "Do NOT recommend medication" in body
    assert "könnte" in body or "möglicherweise" in body
    assert "German (de-DE)" in body

    # Output structure
    assert "Therapieplan-Entwurf" in body
    assert "Ausgangssituation" in body
    assert "Mögliche Therapieziele" in body
    assert "Potenzielle Interventionen" in body
    assert "Ressourcen" in body
    assert "Risiken" in body or "Belastungsfaktoren" in body
    assert "Evaluationskriterien" in body


@pytest.mark.asyncio
async def test_structured_doc_prompt_contains_expected_structure(client):
    """STRUCTURED_DOC prompt must include guideline-based structure."""
    r = await client.get("/prompts/STRUCTURED_DOC/latest")
    assert r.status_code == 200
    data = r.json()
    assert data["key"] == "STRUCTURED_DOC"
    body = data["body"]

    # Constraints
    assert "No diagnosis generation" in body
    assert "No legal assessment" in body
    assert "German (de-DE)" in body
    assert "Keine ausreichenden Angaben im vorliegenden Text" in body

    # Output structure
    assert "Strukturierte Dokumentation" in body
    assert "Sitzungsrahmen" in body
    assert "Subjektiver Bericht" in body
    assert "Objektive Beobachtungen" in body
    assert "Psychischer Befund" in body
    assert "Interventionen" in body
    assert "Therapieverlauf" in body


@pytest.mark.asyncio
async def test_session_summary_prompt_contains_expected_structure(client):
    """SESSION_SUMMARY prompt must include clinical constraints and output format."""
    r = await client.get("/prompts/SESSION_SUMMARY/latest")
    assert r.status_code == 200
    data = r.json()
    assert data["key"] == "SESSION_SUMMARY"
    body = data["body"]

    # Clinical constraints
    assert "Do NOT provide diagnosis" in body
    assert "Do NOT provide treatment advice" in body
    assert "Do NOT invent information" in body
    assert "German (de-DE)" in body

    # Output structure
    assert "Sitzungszusammenfassung" in body
    assert "Anlass / Thema" in body
    assert "Zentrale Inhalte" in body
    assert "Emotionale Dynamik" in body
    assert "Interventionen / Methoden" in body
    assert "Vereinbarungen / Nächste Schritte" in body


@pytest.mark.asyncio
async def test_update_prompt_creates_new_version(client):
    """PATCH /prompts/{key} creates new version and returns updated prompt."""
    r = await client.get("/prompts/SESSION_SUMMARY/latest")
    assert r.status_code == 200
    original = r.json()
    body_before = original["body"]
    version_before = original["version"]

    new_body = body_before + "\n\n<!-- test append -->"
    patch_r = await client.patch(
        "/prompts/SESSION_SUMMARY",
        json={"body": new_body},
    )
    assert patch_r.status_code == 200
    updated = patch_r.json()
    assert updated["key"] == "SESSION_SUMMARY"
    assert updated["body"] == new_body
    assert updated["version"] == version_before + 1


@pytest.mark.asyncio
async def test_update_prompt_rejects_empty_body(client):
    """PATCH /prompts/{key} with empty body returns 400."""
    r = await client.patch("/prompts/SESSION_SUMMARY", json={"body": "   "})
    assert r.status_code == 400
