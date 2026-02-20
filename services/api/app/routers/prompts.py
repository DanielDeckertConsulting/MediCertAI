"""Prompt registry endpoints. Server-side only; client cannot override."""
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.dependencies import require_auth, get_tenant_id
from app.services.prompt_registry import ASSIST_KEYS

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

_ASSIST_DISPLAY = {
    "CHAT_WITH_AI": "Chat with AI",
    "SESSION_SUMMARY": "Session Summary",
    "STRUCTURED_DOC": "Structured Documentation",
    "THERAPY_PLAN": "Therapy Plan Draft",
    "RISK_ANALYSIS": "Risk Analysis",
    "CASE_REFLECTION": "Case Reflection",
}


class PromptSummary(BaseModel):
    key: str
    display_name: str
    version: int


class PromptDetail(BaseModel):
    key: str
    display_name: str
    version: int
    body: str


@router.get("", response_model=list[PromptSummary])
@limiter.limit("100/minute")
async def list_prompts(request: Request, _auth=Depends(require_auth)):
    """List available assist mode prompts."""
    return [
        PromptSummary(key=k, display_name=_ASSIST_DISPLAY.get(k, k), version=1)
        for k in ASSIST_KEYS
    ]


class PromptUpdate(BaseModel):
    body: str


@router.get("/{key}/latest", response_model=PromptDetail)
@limiter.limit("100/minute")
async def get_prompt_latest(
    request: Request,
    key: str,
    _auth=Depends(require_auth),
):
    """Get latest prompt body by key. Internal use; server injects into LLM."""
    from fastapi import HTTPException

    if key not in ASSIST_KEYS:
        raise HTTPException(status_code=404, detail="Not found")

    tenant_id = get_tenant_id(request)
    async for session in get_session(tenant_id=tenant_id):
        result = await session.execute(
            text("""
                SELECT pv.body, pv.version
                FROM prompts p
                JOIN prompt_versions pv ON pv.prompt_id = p.id
                WHERE p.key = :key AND (p.tenant_id IS NULL OR p.tenant_id = :tenant_id)
                ORDER BY pv.version DESC
                LIMIT 1
            """),
            {"key": key, "tenant_id": str(tenant_id) if tenant_id else None},
        )
        row = result.fetchone()
        body = row[0] if row else ""
        version = row[1] if row else 1
        return PromptDetail(
            key=key,
            display_name=_ASSIST_DISPLAY.get(key, key),
            version=version,
            body=body or "",
        )


@router.patch("/{key}", response_model=PromptDetail)
@limiter.limit("30/minute")
async def update_prompt(
    request: Request,
    key: str,
    payload: PromptUpdate,
    _auth=Depends(require_auth),
):
    """Update prompt body. Creates new version. Global prompts (tenant_id NULL) only for MVP."""
    from fastapi import HTTPException

    if key not in ASSIST_KEYS:
        raise HTTPException(status_code=404, detail="Not found")

    body = (payload.body or "").strip()
    if not body:
        raise HTTPException(status_code=400, detail="body cannot be empty")

    tenant_id = get_tenant_id(request)
    result: PromptDetail | None = None
    async for session in get_session(tenant_id=tenant_id):
        # Resolve prompt (global only for MVP)
        res = await session.execute(
            text("SELECT id FROM prompts WHERE key = :key AND tenant_id IS NULL"),
            {"key": key},
        )
        row = res.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Prompt not found")

        prompt_id = row[0]
        res = await session.execute(
            text(
                "SELECT COALESCE(MAX(version), 0) + 1 FROM prompt_versions WHERE prompt_id = :pid"
            ),
            {"pid": prompt_id},
        )
        new_version = res.scalar() or 1

        await session.execute(
            text(
                "INSERT INTO prompt_versions (prompt_id, version, body) VALUES (:pid, :ver, :body)"
            ),
            {"pid": prompt_id, "ver": new_version, "body": body},
        )

        result = PromptDetail(
            key=key,
            display_name=_ASSIST_DISPLAY.get(key, key),
            version=new_version,
            body=body,
        )
    assert result is not None
    return result
