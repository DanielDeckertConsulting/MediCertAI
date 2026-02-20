"""Intervention suggestion library. EPIC 14. Evidence-informed, non-prescriptive. RLS: global + tenant."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy import text

from app.db import get_session
from app.dependencies import require_auth, get_tenant_id, get_user_uuid
from app.services.event_store import append_event

router = APIRouter()


class InterventionOut(BaseModel):
    id: str
    category: str
    title: str
    description: str
    evidence_level: str | None
    references: list[str] | None


def _session_gen(tenant_id: UUID, user_uuid: UUID):
    return get_session(tenant_id=tenant_id, user_id=str(user_uuid))


@router.get("", response_model=list[InterventionOut])
async def list_interventions(
    request: Request,
    category: str | None = Query(None, description="Filter by category (e.g. anxiety, depression)"),
    _auth=Depends(require_auth),
):
    """
    List intervention library entries. Global (tenant_id NULL) + tenant-specific.
    RLS: tenant_id IS NULL OR tenant_id = current tenant.
    """
    tenant_id = get_tenant_id(request)
    user_uuid = get_user_uuid(request)
    if not tenant_id or not user_uuid:
        raise HTTPException(status_code=401, detail="Auth required")

    async for session in _session_gen(tenant_id, user_uuid):
        if category:
            result = await session.execute(
                text("""
                    SELECT id, category, title, description, evidence_level, "references"
                    FROM intervention_library
                    WHERE (tenant_id IS NULL OR tenant_id = :tid) AND category = :category
                    ORDER BY category, title
                """),
                {"tid": str(tenant_id), "category": category},
            )
        else:
            result = await session.execute(
                text("""
                    SELECT id, category, title, description, evidence_level, "references"
                    FROM intervention_library
                    WHERE tenant_id IS NULL OR tenant_id = :tid
                    ORDER BY category, title
                """),
                {"tid": str(tenant_id)},
            )
        rows = result.fetchall()
        return [
            InterventionOut(
                id=str(r[0]),
                category=r[1],
                title=r[2],
                description=r[3],
                evidence_level=r[4],
                references=list(r[5]) if r[5] else None,
            )
            for r in rows
        ]
    return []


@router.post("/{intervention_id}/viewed")
async def record_intervention_viewed(
    request: Request,
    intervention_id: UUID,
    _auth=Depends(require_auth),
):
    """Record that user viewed an intervention (no PII). Optional analytics."""
    tenant_id = get_tenant_id(request)
    user_uuid = get_user_uuid(request)
    if not tenant_id or not user_uuid:
        raise HTTPException(status_code=401, detail="Auth required")

    async for session in _session_gen(tenant_id, user_uuid):
        row = await session.execute(
            text("""
                SELECT id, category FROM intervention_library
                WHERE id = :iid AND (tenant_id IS NULL OR tenant_id = :tid)
            """),
            {"iid": str(intervention_id), "tid": str(tenant_id)},
        )
        r = row.fetchone()
        if not r:
            raise HTTPException(status_code=404, detail="Intervention not found")
        await append_event(
            session,
            tenant_id,
            actor=str(user_uuid),
            entity_type="intervention",
            entity_id=str(intervention_id),
            event_type="intervention_viewed",
            payload={"intervention_id": str(intervention_id), "category": r[1]},
        )
        return {}
    return {}
