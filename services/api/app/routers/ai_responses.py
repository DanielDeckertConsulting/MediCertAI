"""AI Response API. Process markdown, fetch responses, execute actions."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.db import get_session
from app.dependencies import require_auth, get_tenant_id, get_user_uuid
from app.services.ai_rendering_service import AIRenderingService
from app.services.event_store import append_event

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


# --- Schemas ---
class ProcessMarkdownBody(BaseModel):
    raw_markdown: str
    entity_type: str
    entity_id: str
    model: str = "gpt-4"
    confidence: float = 1.0


class ExecuteActionBody(BaseModel):
    command: str
    label: str
    confidence: float
    entity_type: str
    entity_id: str


def _session_gen(tenant_id: UUID, user_uuid: UUID):
    return get_session(tenant_id=tenant_id, user_id=str(user_uuid))


@router.post("", response_model=dict)
@limiter.limit("30/minute")
async def process_markdown(
    request: Request,
    body: ProcessMarkdownBody,
    _auth=Depends(require_auth),
):
    """Process AI markdown: sanitize, extract blocks, store event + ai_response."""
    tenant_id = get_tenant_id(request)
    user_uuid = get_user_uuid(request)
    if not tenant_id or not user_uuid:
        raise HTTPException(status_code=401, detail="Auth required")
    if not body.raw_markdown.strip():
        raise HTTPException(status_code=400, detail="raw_markdown required")
    if not body.entity_type or not body.entity_id:
        raise HTTPException(status_code=400, detail="entity_type and entity_id required")

    result = None
    async for session in _session_gen(tenant_id, user_uuid):
        service = AIRenderingService(session, tenant_id, str(user_uuid))
        try:
            result = await service.process_markdown(
                raw_markdown=body.raw_markdown,
                entity_type=body.entity_type,
                entity_id=body.entity_id,
                model=body.model,
                confidence=body.confidence,
            )
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
    return result


@router.get("", response_model=list)
@limiter.limit("100/minute")
async def list_ai_responses(
    request: Request,
    entity_id: str,
    _auth=Depends(require_auth),
):
    """List AI responses for an entity. Latest first."""
    tenant_id = get_tenant_id(request)
    user_uuid = get_user_uuid(request)
    if not tenant_id or not user_uuid:
        raise HTTPException(status_code=401, detail="Auth required")

    from sqlalchemy import text

    async for session in _session_gen(tenant_id, user_uuid):
        result = await session.execute(
            text("""
                SELECT id, entity_type, entity_id, raw_markdown, structured_blocks, model, confidence, version, created_at
                FROM ai_responses
                WHERE tenant_id = :tenant_id AND entity_id = :entity_id
                ORDER BY version DESC
            """),
            {"tenant_id": str(tenant_id), "entity_id": entity_id},
        )
        rows = result.fetchall()
        return [
            {
                "id": str(r[0]),
                "entity_type": r[1],
                "entity_id": r[2],
                "raw_markdown": r[3],
                "structured_blocks": r[4],
                "model": r[5],
                "confidence": r[6],
                "version": r[7],
                "created_at": r[8].isoformat() if r[8] else "",
            }
            for r in rows
        ]


@router.get("/{response_id}", response_model=dict)
@limiter.limit("100/minute")
async def get_ai_response(
    request: Request,
    response_id: UUID,
    _auth=Depends(require_auth),
):
    """Get single AI response by id."""
    tenant_id = get_tenant_id(request)
    user_uuid = get_user_uuid(request)
    if not tenant_id or not user_uuid:
        raise HTTPException(status_code=401, detail="Auth required")

    from sqlalchemy import text

    async for session in _session_gen(tenant_id, user_uuid):
        result = await session.execute(
            text("""
                SELECT id, entity_type, entity_id, raw_markdown, structured_blocks, model, confidence, version, created_at
                FROM ai_responses
                WHERE id = :id AND tenant_id = :tenant_id
            """),
            {"id": str(response_id), "tenant_id": str(tenant_id)},
        )
        row = result.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="AI response not found")
        return {
            "id": str(row[0]),
            "entity_type": row[1],
            "entity_id": row[2],
            "raw_markdown": row[3],
            "structured_blocks": row[4],
            "model": row[5],
            "confidence": row[6],
            "version": row[7],
            "created_at": row[8].isoformat() if row[8] else "",
        }


@router.post("/actions/execute", response_model=dict)
@limiter.limit("50/minute")
async def execute_action(
    request: Request,
    body: ExecuteActionBody,
    _auth=Depends(require_auth),
):
    """Log AI_ACTION_EXECUTED event. Frontend handles actual command routing."""
    tenant_id = get_tenant_id(request)
    user_uuid = get_user_uuid(request)
    if not tenant_id or not user_uuid:
        raise HTTPException(status_code=401, detail="Auth required")

    async for session in _session_gen(tenant_id, user_uuid):
        await append_event(
            session,
            tenant_id,
            actor=str(user_uuid),
            entity_type=body.entity_type,
            entity_id=body.entity_id,
            event_type="ai_response.action_executed",
            payload={
                "command": body.command,
                "label": body.label,
                "confidence": body.confidence,
            },
            source="praxis-pilot-api",
        )
    return {"ok": True, "command": body.command}
