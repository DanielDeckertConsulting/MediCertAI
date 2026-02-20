"""Case summary across conversations. Draft support only; no diagnosis, no storage unless user saves."""
import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import text

from app.db import get_session
from app.dependencies import require_auth, get_tenant_id, get_user_uuid
from app.services.case_summary_service import generate_case_summary

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


# --- Schemas ---
class CaseSummaryRequest(BaseModel):
    conversation_ids: list[UUID]


class CaseSummaryResponse(BaseModel):
    case_summary: str
    trends: list[str]
    treatment_evolution: str


def _session_gen(tenant_id: UUID, user_uuid: UUID):
    return get_session(tenant_id=tenant_id, user_id=str(user_uuid))


@router.post("/summary", response_model=CaseSummaryResponse)
@limiter.limit("20/minute")
async def post_case_summary(
    request: Request,
    body: CaseSummaryRequest,
    _auth=Depends(require_auth),
):
    """
    Generate case summary across selected conversations.
    Draft support only. No automatic storage. No diagnosis. No treatment recommendation.
    Audit: cross_case_summary_generated.
    """
    tenant_id = get_tenant_id(request)
    user_uuid = get_user_uuid(request)
    if not tenant_id or not user_uuid:
        raise HTTPException(status_code=401, detail="Auth required")

    if not body.conversation_ids:
        raise HTTPException(status_code=400, detail="conversation_ids required")

    try:
        async for session in _session_gen(tenant_id, user_uuid):
            summary, usage = await generate_case_summary(
                session,
                body.conversation_ids,
                tenant_id,
                user_uuid,
            )

            # Audit: metadata only, no content
            await session.execute(
                text("""
                    INSERT INTO audit_logs
                    (tenant_id, actor_id, action, entity_type, entity_id,
                     assist_mode, model_name, model_version, input_tokens, output_tokens, metadata)
                    VALUES (:tenant_id, :actor_id, 'cross_case_summary_generated', 'case_summary', NULL,
                            'CASE_SUMMARY', 'gpt-4', NULL, :input_tokens, :output_tokens, CAST(:metadata AS jsonb))
                """),
                {
                    "tenant_id": str(tenant_id),
                    "actor_id": str(user_uuid),
                    "input_tokens": usage.get("prompt_tokens", 0),
                    "output_tokens": usage.get("completion_tokens", 0),
                    "metadata": json.dumps({
                        "conversation_count": len(body.conversation_ids),
                        "conversation_ids": [str(c) for c in body.conversation_ids],
                    }),
                },
            )
            await session.commit()

            return CaseSummaryResponse(
                case_summary=summary.get("case_summary", ""),
                trends=summary.get("trends", []),
                treatment_evolution=summary.get("treatment_evolution", ""),
            )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    raise HTTPException(status_code=500, detail="Unexpected error")
