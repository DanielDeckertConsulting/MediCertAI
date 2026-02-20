"""Chat CRUD and streaming messages. Tenant-isolated, RLS enforced."""
import io
import json
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse, Response, StreamingResponse
from pydantic import BaseModel
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import text
from app.config import settings
from app.db import get_session, session_scope
from app.dependencies import require_auth, get_tenant_id, get_user_uuid
from app.services.event_store import append_event
from app.services.anonymization import anonymize
from app.services.prompt_injection import sanitize_user_message
from app.services.prompt_registry import get_system_prompt, ASSIST_KEYS
from app.services.azure_openai import stream_chat
from app.services.structured_document_service import (
    get_by_conversation,
    create_or_update,
    generate_from_conversation,
    validate_structured_content,
)

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


# --- Schemas ---
class CreateChatBody(BaseModel):
    title: str | None = "New chat"


class ChatSummary(BaseModel):
    id: str
    title: str
    updated_at: str
    is_favorite: bool
    folder_id: str | None = None
    status: str = "active"


class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    created_at: str


class ChatDetail(BaseModel):
    id: str
    title: str
    is_favorite: bool
    folder_id: str | None = None
    status: str = "active"
    created_at: str
    updated_at: str
    messages: list[MessageOut]
    # Session context for Smart Context Banner
    last_message_at: str | None = None
    first_message_at: str | None = None
    total_tokens_in_session: int = 0
    # Conversation metadata (e.g. safe_mode)
    metadata: dict | None = None


class PatchChatBody(BaseModel):
    title: str | None = None
    is_favorite: bool | None = None
    folder_id: str | None = None
    metadata: dict | None = None


class SendMessageBody(BaseModel):
    assist_mode_key: str
    anonymization_enabled: bool = True
    safe_mode: bool = False
    user_message: str


class StructuredContentBody(BaseModel):
    content: dict


def _session_gen(tenant_id: UUID, user_uuid: UUID):
    return get_session(tenant_id=tenant_id, user_id=str(user_uuid))


FINALIZED_ERR = "Chat is finalized; no modifications allowed"


async def _get_chat_status(session, chat_id: UUID, tenant_id: UUID, owner_user_id: UUID) -> str | None:
    """Returns chat status or None if not found."""
    r = await session.execute(
        text("""
            SELECT COALESCE(status, 'active') FROM chats
            WHERE id = :cid AND tenant_id = :tid AND owner_user_id = :oid
        """),
        {"cid": str(chat_id), "tid": str(tenant_id), "oid": str(owner_user_id)},
    )
    row = r.fetchone()
    return row[0] if row else None


# --- CRUD ---
@router.post("", response_model=dict)
@limiter.limit("50/minute")
async def create_chat(
    request: Request,
    body: CreateChatBody | None = None,
    _auth=Depends(require_auth),
):
    tenant_id = get_tenant_id(request)
    user_uuid = get_user_uuid(request)
    if not tenant_id or not user_uuid:
        raise HTTPException(status_code=401, detail="Auth required")
    title = (body.title if body else None) or "New chat"

    created = None
    async for session in _session_gen(tenant_id, user_uuid):
        result = await session.execute(
            text("""
                INSERT INTO chats (tenant_id, owner_user_id, title)
                VALUES (:tenant_id, :owner_user_id, :title)
                RETURNING id, title, created_at, updated_at, is_favorite, folder_id, status
            """),
            {
                "tenant_id": str(tenant_id),
                "owner_user_id": str(user_uuid),
                "title": title,
            },
        )
        row = result.fetchone()
        created = {
            "id": str(row[0]),
            "title": row[1],
            "created_at": row[2].isoformat(),
            "updated_at": row[3].isoformat(),
            "is_favorite": row[4],
            "folder_id": str(row[5]) if row[5] else None,
            "status": row[6] or "active",
        }
    return created


@router.get("", response_model=list[ChatSummary])
@limiter.limit("100/minute")
async def list_chats(
    request: Request,
    folder_id: UUID | None = Query(None, description="Filter by folder; omit for all"),
    unfiled_only: bool = Query(False, description="If true, only chats with folder_id IS NULL"),
    _auth=Depends(require_auth),
):
    tenant_id = get_tenant_id(request)
    user_uuid = get_user_uuid(request)
    if not tenant_id or not user_uuid:
        raise HTTPException(status_code=401, detail="Auth required")
    if unfiled_only and folder_id is not None:
        raise HTTPException(status_code=400, detail="Use folder_id or unfiled_only, not both")

    async for session in _session_gen(tenant_id, user_uuid):
        params: dict = {"tenant_id": str(tenant_id), "owner_user_id": str(user_uuid)}
        if unfiled_only:
            sql = """
                SELECT id, title, updated_at, is_favorite, folder_id, COALESCE(status, 'active') AS status
                FROM chats
                WHERE tenant_id = :tenant_id AND owner_user_id = :owner_user_id
                AND folder_id IS NULL
                ORDER BY updated_at DESC
            """
        elif folder_id is None:
            sql = """
                SELECT id, title, updated_at, is_favorite, folder_id, COALESCE(status, 'active') AS status
                FROM chats
                WHERE tenant_id = :tenant_id AND owner_user_id = :owner_user_id
                ORDER BY updated_at DESC
            """
        else:
            sql = """
                SELECT id, title, updated_at, is_favorite, folder_id, COALESCE(status, 'active') AS status
                FROM chats
                WHERE tenant_id = :tenant_id AND owner_user_id = :owner_user_id
                AND folder_id = :folder_id
                ORDER BY updated_at DESC
            """
            params["folder_id"] = str(folder_id)

        result = await session.execute(text(sql), params)
        rows = result.fetchall()
        return [
            ChatSummary(
                id=str(r[0]),
                title=r[1],
                updated_at=r[2].isoformat(),
                is_favorite=r[3],
                folder_id=str(r[4]) if r[4] else None,
                status=r[5] if len(r) > 5 else "active",
            )
            for r in rows
        ]


@router.get("/{chat_id}", response_model=ChatDetail)
@limiter.limit("100/minute")
async def get_chat(
    request: Request,
    chat_id: UUID,
    _auth=Depends(require_auth),
):
    tenant_id = get_tenant_id(request)
    user_uuid = get_user_uuid(request)
    if not tenant_id or not user_uuid:
        raise HTTPException(status_code=401, detail="Auth required")

    async for session in _session_gen(tenant_id, user_uuid):
        chat = await session.execute(
            text("""
                SELECT id, title, is_favorite, folder_id, COALESCE(status, 'active') AS status, created_at, updated_at, metadata
                FROM chats WHERE id = :chat_id AND tenant_id = :tenant_id
                AND owner_user_id = :owner_user_id
            """),
            {
                "chat_id": str(chat_id),
                "tenant_id": str(tenant_id),
                "owner_user_id": str(user_uuid),
            },
        )
        row = chat.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Chat not found")

        msgs = await session.execute(
            text("""
                SELECT id, role, content, created_at
                FROM chat_messages WHERE chat_id = :chat_id
                ORDER BY created_at ASC
            """),
            {"chat_id": str(chat_id)},
        )
        msg_rows = msgs.fetchall()
        messages = [
            MessageOut(
                id=str(m[0]),
                role=m[1],
                content=m[2],
                created_at=m[3].isoformat(),
            )
            for m in msg_rows
            if m[1] != "system"
        ]  # hide system from client

        # Session context: first/last message timestamps (exclude system)
        first_at: str | None = None
        last_at: str | None = None
        non_system = [m for m in msg_rows if m[1] != "system"]
        if non_system:
            first_at = min(m[3] for m in non_system).isoformat()
            last_at = max(m[3] for m in non_system).isoformat()

        # Session context: total tokens from audit_logs for this chat's messages
        tok = await session.execute(
            text("""
                SELECT COALESCE(SUM(COALESCE(a.input_tokens, 0) + COALESCE(a.output_tokens, 0)), 0)
                FROM audit_logs a
                JOIN chat_messages cm ON cm.id = a.entity_id
                WHERE a.entity_type = 'chat_message' AND a.action = 'chat_message_sent'
                  AND cm.chat_id = :chat_id
                  AND a.tenant_id = :tenant_id
            """),
            {"chat_id": str(chat_id), "tenant_id": str(tenant_id)},
        )
        total_tokens = int(tok.fetchone()[0] or 0)

        meta = row[7] if len(row) > 7 and row[7] else None
        return ChatDetail(
            id=str(row[0]),
            title=row[1],
            is_favorite=row[2],
            folder_id=str(row[3]) if row[3] else None,
            status=row[4] if len(row) > 4 else "active",
            created_at=row[5].isoformat(),
            updated_at=row[6].isoformat(),
            messages=messages,
            last_message_at=last_at,
            first_message_at=first_at,
            total_tokens_in_session=total_tokens,
            metadata=meta,
        )


@router.patch("/{chat_id}", response_model=dict)
@limiter.limit("50/minute")
async def patch_chat(
    request: Request,
    chat_id: UUID,
    body: PatchChatBody,
    _auth=Depends(require_auth),
):
    tenant_id = get_tenant_id(request)
    user_uuid = get_user_uuid(request)
    if not tenant_id or not user_uuid:
        raise HTTPException(status_code=401, detail="Auth required")

    updates = []
    params = {"chat_id": str(chat_id), "tenant_id": str(tenant_id), "owner_user_id": str(user_uuid)}
    if body.title is not None:
        updates.append("title = :title")
        params["title"] = body.title
    if body.is_favorite is not None:
        updates.append("is_favorite = :is_favorite")
        params["is_favorite"] = body.is_favorite
    if body.folder_id is not None:
        updates.append("folder_id = :folder_id")
        fid = body.folder_id.strip() if isinstance(body.folder_id, str) else None
        params["folder_id"] = fid or None
    if body.metadata is not None:
        updates.append("metadata = :metadata")
        # Sanitize: only allow known keys (safe_mode); merged in loop with current metadata
        params["_metadata_patch"] = {k: v for k, v in body.metadata.items() if k in ("safe_mode",)}
    if not updates:
        raise HTTPException(status_code=400, detail="No updates provided")

    result_data = None
    async for session in _session_gen(tenant_id, user_uuid):
        if params.get("folder_id"):
            # Validate folder belongs to tenant (only when assigning to a folder, not when unassigning)
            folder_check = await session.execute(
                text("""
                    SELECT 1 FROM folders
                    WHERE id = :folder_id AND tenant_id = :tenant_id
                """),
                {"folder_id": params["folder_id"], "tenant_id": str(tenant_id)},
            )
            if not folder_check.fetchone():
                raise HTTPException(status_code=403, detail="Folder not found or access denied")

        # Get current state for event; block if finalized
        old_row = await session.execute(
            text("""
                SELECT folder_id, COALESCE(status, 'active'), metadata FROM chats
                WHERE id = :chat_id AND tenant_id = :tenant_id AND owner_user_id = :owner_user_id
            """),
            {"chat_id": str(chat_id), "tenant_id": str(tenant_id), "owner_user_id": str(user_uuid)},
        )
        prev = old_row.fetchone()
        if not prev:
            raise HTTPException(status_code=404, detail="Chat not found")
        if prev[1] == "finalized":
            raise HTTPException(status_code=409, detail=FINALIZED_ERR)
        old_folder_id = str(prev[0]) if prev[0] else None
        new_folder_id = params.get("folder_id")

        # Merge metadata if patching
        if "_metadata_patch" in params:
            current_meta = prev[2] or {}
            merged = {**current_meta, **params.pop("_metadata_patch")}
            params["metadata"] = json.dumps(merged) if merged else None

        result = await session.execute(
            text(f"""
                UPDATE chats SET {", ".join(updates)}, updated_at = now()
                WHERE id = :chat_id AND tenant_id = :tenant_id AND owner_user_id = :owner_user_id
                RETURNING id, title, is_favorite, folder_id, COALESCE(status, 'active'), updated_at
            """),
            params,
        )
        row = result.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Chat not found")

        if body.folder_id is not None and (old_folder_id != new_folder_id):
            await append_event(
                session,
                tenant_id,
                actor=str(user_uuid),
                entity_type="chat",
                entity_id=str(chat_id),
                event_type="chat.folder_changed",
                payload={
                    "chat_id": str(chat_id),
                    "old_folder_id": old_folder_id,
                    "new_folder_id": new_folder_id,
                },
            )
        await session.commit()

        result_data = {
            "id": str(row[0]),
            "title": row[1],
            "is_favorite": row[2],
            "folder_id": str(row[3]) if row[3] else None,
            "status": row[4] if len(row) > 4 else "active",
            "updated_at": row[5].isoformat(),
        }
    return result_data


@router.post("/{chat_id}/finalize", response_model=dict)
@limiter.limit("30/minute")
async def finalize_chat(
    request: Request,
    chat_id: UUID,
    _auth=Depends(require_auth),
):
    """Finalize chat for medico-legal documentation. No further modifications allowed; export remains available."""
    tenant_id = get_tenant_id(request)
    user_uuid = get_user_uuid(request)
    if not tenant_id or not user_uuid:
        raise HTTPException(status_code=401, detail="Auth required")

    result_data = None
    async for session in _session_gen(tenant_id, user_uuid):
        status = await _get_chat_status(session, chat_id, tenant_id, user_uuid)
        if status is None:
            raise HTTPException(status_code=404, detail="Chat not found")
        if status == "finalized":
            raise HTTPException(status_code=409, detail="Chat is already finalized")

        result = await session.execute(
            text("""
                UPDATE chats SET status = 'finalized', updated_at = now()
                WHERE id = :chat_id AND tenant_id = :tenant_id AND owner_user_id = :owner_user_id
                RETURNING id, title, is_favorite, folder_id, status, updated_at
            """),
            {"chat_id": str(chat_id), "tenant_id": str(tenant_id), "owner_user_id": str(user_uuid)},
        )
        row = result.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Chat not found")

        await append_event(
            session,
            tenant_id,
            actor=str(user_uuid),
            entity_type="chat",
            entity_id=str(chat_id),
            event_type="chat.finalized",
            payload={"chat_id": str(chat_id)},
        )
        await session.commit()

        result_data = {
            "id": str(row[0]),
            "title": row[1],
            "is_favorite": row[2],
            "folder_id": str(row[3]) if row[3] else None,
            "status": "finalized",
            "updated_at": row[5].isoformat(),
        }
    return result_data


@router.delete("/{chat_id}", status_code=204)
@limiter.limit("30/minute")
async def delete_chat(
    request: Request,
    chat_id: UUID,
    _auth=Depends(require_auth),
):
    tenant_id = get_tenant_id(request)
    user_uuid = get_user_uuid(request)
    if not tenant_id or not user_uuid:
        raise HTTPException(status_code=401, detail="Auth required")

    async for session in _session_gen(tenant_id, user_uuid):
        status = await _get_chat_status(session, chat_id, tenant_id, user_uuid)
        if status is None:
            raise HTTPException(status_code=404, detail="Chat not found")
        if status == "finalized":
            raise HTTPException(status_code=409, detail=FINALIZED_ERR)
        result = await session.execute(
            text("""
                DELETE FROM chats
                WHERE id = :chat_id AND tenant_id = :tenant_id AND owner_user_id = :owner_user_id
                RETURNING id
            """),
            {"chat_id": str(chat_id), "tenant_id": str(tenant_id), "owner_user_id": str(user_uuid)},
        )
        if not result.fetchone():
            raise HTTPException(status_code=404, detail="Chat not found")
    return None


# --- Structured Session Document (EPIC 14) ---
@router.get("/{chat_id}/structured-document", response_model=dict)
@limiter.limit("60/minute")
async def get_structured_document(
    request: Request,
    chat_id: UUID,
    _auth=Depends(require_auth),
):
    """Get latest structured document for conversation. 404 if none."""
    tenant_id = get_tenant_id(request)
    user_uuid = get_user_uuid(request)
    if not tenant_id or not user_uuid:
        raise HTTPException(status_code=401, detail="Auth required")

    async with session_scope(tenant_id, str(user_uuid)) as session:
        doc = await get_by_conversation(session, chat_id, tenant_id, user_uuid)
    if doc is None:
        raise HTTPException(status_code=404, detail="Structured document not found")
    return doc


@router.put("/{chat_id}/structured-document", response_model=dict)
@limiter.limit("60/minute")
async def put_structured_document(
    request: Request,
    chat_id: UUID,
    body: StructuredContentBody,
    _auth=Depends(require_auth),
):
    """Create or update structured document. Version increments on update. Blocks if chat finalized."""
    tenant_id = get_tenant_id(request)
    user_uuid = get_user_uuid(request)
    if not tenant_id or not user_uuid:
        raise HTTPException(status_code=401, detail="Auth required")

    async with session_scope(tenant_id, str(user_uuid)) as session:
        status = await _get_chat_status(session, chat_id, tenant_id, user_uuid)
        if status is None:
            raise HTTPException(status_code=404, detail="Chat not found")
        if status == "finalized":
            raise HTTPException(status_code=409, detail=FINALIZED_ERR)
        try:
            doc = await create_or_update(
                session, chat_id, tenant_id, user_uuid, str(user_uuid), body.content, is_manual_create=True
            )
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
    return doc


@router.post("/{chat_id}/structured-document/convert", response_model=dict)
@limiter.limit("20/minute")
async def convert_to_structured_document(
    request: Request,
    chat_id: UUID,
    _auth=Depends(require_auth),
):
    """Convert conversation to structured documentation via LLM. No diagnosis; documentation only."""
    tenant_id = get_tenant_id(request)
    user_uuid = get_user_uuid(request)
    if not tenant_id or not user_uuid:
        raise HTTPException(status_code=401, detail="Auth required")

    async with session_scope(tenant_id, str(user_uuid)) as session:
        status = await _get_chat_status(session, chat_id, tenant_id, user_uuid)
        if status is None:
            raise HTTPException(status_code=404, detail="Chat not found")
        if status == "finalized":
            raise HTTPException(status_code=409, detail=FINALIZED_ERR)
        try:
            doc, usage = await generate_from_conversation(
                session, chat_id, tenant_id, user_uuid, str(user_uuid)
            )
        except ValueError as e:
            if "valid JSON" in str(e):
                raise HTTPException(status_code=422, detail="Conversion failed: invalid structure from AI")
            raise HTTPException(status_code=400, detail=str(e))
    return {"document": doc, "usage": usage}


# Strict clinical mode modifier appended when safe_mode=True
_SAFE_MODE_MODIFIER = (
    "\n\nFormuliere konservativ. Gib keine absoluten Aussagen. "
    "Verweise darauf, dass fachliche Prüfung erforderlich ist. Keine spekulativen Annahmen."
)


# --- Streaming message ---
async def _sse_stream(
    chat_id: UUID,
    tenant_id: UUID,
    user_uuid: UUID,
    assist_mode_key: str,
    user_message: str,
    anonymization_enabled: bool,
    safe_mode: bool,
    correlation_id: str,
):
    """Generate SSE events for streaming response."""
    import json

    # 1. Resolve system prompt
    async for session in _session_gen(tenant_id, user_uuid):
        system_prompt = await get_system_prompt(session, assist_mode_key)
        if not system_prompt:
            yield f"event: error\ndata: {json.dumps({'message': 'Invalid assist mode'})}\n\n"
            return

        if safe_mode:
            system_prompt = system_prompt + _SAFE_MODE_MODIFIER

        # 2. Sanitize + check injection
        sanitized, refusal = sanitize_user_message(user_message)
        if refusal:
            yield f"event: error\ndata: {json.dumps({'message': refusal})}\n\n"
            return

        # 3. Anonymize if enabled (only for LLM; store original in DB)
        msg_for_llm = anonymize(sanitized) if anonymization_enabled else sanitized

        # 4. Save user message (original content)
        await session.execute(
            text("""
                INSERT INTO chat_messages (tenant_id, chat_id, role, content)
                VALUES (:tenant_id, :chat_id, 'user', :content)
            """),
            {"tenant_id": str(tenant_id), "chat_id": str(chat_id), "content": user_message},
        )
        await session.commit()

    # 5. Build history for LLM (fetch messages)
    async for session in _session_gen(tenant_id, user_uuid):
        hist = await session.execute(
            text("""
                SELECT role, content FROM chat_messages
                WHERE chat_id = :chat_id AND role != 'system'
                ORDER BY created_at ASC
            """),
            {"chat_id": str(chat_id)},
        )
        history = [{"role": r[0], "content": r[1]} for r in hist.fetchall()]
        # Last one is the user msg we just inserted; ensure we use msg_for_llm for this turn
        if history and history[-1]["role"] == "user":
            history[-1]["content"] = msg_for_llm

        if not settings.azure_openai_configured:
            yield f"event: error\ndata: {json.dumps({'message': 'Azure OpenAI not configured'})}\n\n"
            return

        try:
            buffer: list[str] = []
            async for chunk, usage in stream_chat(
                system_prompt=system_prompt,
                messages=history,
            ):
                if chunk:
                    buffer.append(chunk)
                    yield f"event: token\ndata: {json.dumps({'text': chunk})}\n\n"
                if usage is not None:
                    break

            full_content = "".join(buffer)

            # 6. Save assistant message
            async for session in _session_gen(tenant_id, user_uuid):
                result = await session.execute(
                    text("""
                        INSERT INTO chat_messages (tenant_id, chat_id, role, content)
                        VALUES (:tenant_id, :chat_id, 'assistant', :content)
                        RETURNING id
                    """),
                    {"tenant_id": str(tenant_id), "chat_id": str(chat_id), "content": full_content},
                )
                msg_id = str(result.fetchone()[0])

                prompt_tokens = usage.get("prompt_tokens", 0) if usage else 0
                completion_tokens = usage.get("completion_tokens", 0) if usage else 0

                # 7. Audit log (metadata only) — llm_audit_logs (legacy)
                await session.execute(
                    text("""
                        INSERT INTO llm_audit_logs
                        (tenant_id, user_id, assist_mode_key, model_name, model_version,
                         token_usage_prompt, token_usage_completion, correlation_id)
                        VALUES (:tenant_id, :user_id, :assist_mode_key, 'gpt-4', NULL,
                                :prompt_tokens, :completion_tokens, :correlation_id)
                    """),
                    {
                        "tenant_id": str(tenant_id),
                        "user_id": str(user_uuid),
                        "assist_mode_key": assist_mode_key,
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "correlation_id": correlation_id,
                    },
                )

                # 8. usage_records for KPI aggregation
                await session.execute(
                    text("""
                        INSERT INTO usage_records
                        (tenant_id, user_id, assist_mode, model_name, model_version,
                         input_tokens, output_tokens)
                        VALUES (:tenant_id, :user_id, :assist_mode, 'gpt-4', NULL,
                                :input_tokens, :output_tokens)
                    """),
                    {
                        "tenant_id": str(tenant_id),
                        "user_id": str(user_uuid),
                        "assist_mode": assist_mode_key,
                        "input_tokens": prompt_tokens,
                        "output_tokens": completion_tokens,
                    },
                )

                # 9. audit_logs for Admin Logs UI
                await session.execute(
                    text("""
                        INSERT INTO audit_logs
                        (tenant_id, actor_id, action, entity_type, entity_id,
                         assist_mode, model_name, model_version, input_tokens, output_tokens)
                        VALUES (:tenant_id, :actor_id, 'chat_message_sent', 'chat_message', :entity_id,
                                :assist_mode, 'gpt-4', NULL, :input_tokens, :output_tokens)
                    """),
                    {
                        "tenant_id": str(tenant_id),
                        "actor_id": str(user_uuid),
                        "entity_id": msg_id,
                        "assist_mode": assist_mode_key,
                        "input_tokens": prompt_tokens,
                        "output_tokens": completion_tokens,
                    },
                )
                await session.commit()

            yield f"event: done\ndata: {json.dumps({'message_id': msg_id, 'usage': usage or {}})}\n\n"
        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'message': str(e)})}\n\n"


@router.post("/{chat_id}/messages")
@limiter.limit("30/minute")
async def send_message(
    request: Request,
    chat_id: UUID,
    body: SendMessageBody,
    _auth=Depends(require_auth),
):
    tenant_id = get_tenant_id(request)
    user_uuid = get_user_uuid(request)
    if not tenant_id or not user_uuid:
        raise HTTPException(status_code=401, detail="Auth required")
    if body.assist_mode_key not in ASSIST_KEYS:
        raise HTTPException(status_code=400, detail="Invalid assist_mode_key")
    if not body.user_message.strip():
        raise HTTPException(status_code=400, detail="user_message required")

    # Verify chat exists, belongs to user, and is not finalized
    async for session in _session_gen(tenant_id, user_uuid):
        status = await _get_chat_status(session, chat_id, tenant_id, user_uuid)
        if status is None:
            raise HTTPException(status_code=404, detail="Chat not found")
        if status == "finalized":
            raise HTTPException(status_code=409, detail=FINALIZED_ERR)

    correlation_id = getattr(request.state, "request_id", None) or str(request.headers.get("X-Request-ID", ""))
    return StreamingResponse(
        _sse_stream(
            chat_id=chat_id,
            tenant_id=tenant_id,
            user_uuid=user_uuid,
            assist_mode_key=body.assist_mode_key,
            user_message=body.user_message,
            anonymization_enabled=body.anonymization_enabled,
            safe_mode=body.safe_mode,
            correlation_id=correlation_id,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# --- Export limits ---
EXPORT_MAX_MESSAGES = 2000
EXPORT_MAX_CHARS = 2_000_000  # ~2 MB


def _build_txt(chat_title: str, messages: list[tuple[str, str, datetime | None]]) -> str:
    """Build plain-text export content."""
    lines = [f"# {chat_title}\n"]
    for role, content, created_at in messages:
        ts = created_at.strftime("%Y-%m-%d %H:%M") if created_at else ""
        lines.append(f"\n[{ts}] {role.upper()}:\n{content}\n")
    return "\n".join(lines)


def _build_pdf(
    chat_title: str,
    messages: list[tuple[str, str, datetime | None]],
    structured_content: dict | None = None,
) -> bytes:
    """Build PDF export content. Minimal layout, UTF-8 safe. Optionally include structured document."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )
    styles = getSampleStyleSheet()
    body_style = ParagraphStyle(
        "ExportBody",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        wordWrap="CJK",
    )
    header_style = ParagraphStyle(
        "ExportHeader",
        parent=styles["Normal"],
        fontSize=8,
        textColor="gray",
    )
    role_style = ParagraphStyle(
        "ExportRole",
        parent=styles["Normal"],
        fontSize=9,
        fontName="Helvetica-Bold",
    )

    story = []

    # Header: ClinAI Export, title, export date
    story.append(Paragraph("ClinAI Export", header_style))
    story.append(Paragraph(chat_title or "Chat", body_style))
    export_ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    story.append(Paragraph(f"Export: {export_ts}", header_style))
    story.append(Spacer(1, 8 * mm))

    role_label = {"user": "Therapeut:in", "assistant": "KI"}

    for role, content, created_at in messages:
        ts = created_at.strftime("%Y-%m-%d %H:%M") if created_at else ""
        label = role_label.get(role, role)
        story.append(Paragraph(f"[{ts}] {label}", role_style))
        # Escape XML entities for Paragraph; wrap long lines
        safe_content = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        story.append(Paragraph(safe_content, body_style))
        story.append(Spacer(1, 4 * mm))

    if structured_content and any(str(v).strip() for v in structured_content.values()):
        story.append(Spacer(1, 8 * mm))
        story.append(Paragraph("Strukturierte Dokumentation", role_style))
        for key, val in structured_content.items():
            if not val or not str(val).strip():
                continue
            label = key.replace("_", " ").title()
            story.append(Paragraph(f"{label}:", header_style))
            safe_val = str(val).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            story.append(Paragraph(safe_val, body_style))
            story.append(Spacer(1, 2 * mm))

    doc.build(story)
    return buffer.getvalue()


# --- Export ---
@router.get("/{chat_id}/export", response_class=Response)
@router.get("/{chat_id}/export.txt", response_class=Response)  # backward compat
@limiter.limit("30/minute")
async def export_chat(
    request: Request,
    chat_id: UUID,
    format: str = Query("txt", description="Export format: txt or pdf"),
    _auth=Depends(require_auth),
):
    """Export chat as TXT or PDF. Audit: export_requested with metadata only (no content)."""
    tenant_id = get_tenant_id(request)
    user_uuid = get_user_uuid(request)
    if not tenant_id or not user_uuid:
        raise HTTPException(status_code=401, detail="Auth required")

    # Normalize format from path suffix (export.txt) or query param
    if request.url.path.endswith(".txt"):
        fmt = "txt"
    elif format and format.lower() in ("txt", "pdf"):
        fmt = format.lower()
    else:
        if format:
            raise HTTPException(status_code=400, detail="Format must be txt or pdf")
        fmt = "txt"

    async for session in _session_gen(tenant_id, user_uuid):
        chat = await session.execute(
            text("""
                SELECT id, title, created_at
                FROM chats
                WHERE id = :chat_id AND tenant_id = :tenant_id AND owner_user_id = :owner_user_id
            """),
            {"chat_id": str(chat_id), "tenant_id": str(tenant_id), "owner_user_id": str(user_uuid)},
        )
        row = chat.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Chat not found")

        chat_title = row[1]

        msgs_result = await session.execute(
            text("""
                SELECT role, content, created_at
                FROM chat_messages
                WHERE chat_id = :chat_id AND role != 'system'
                ORDER BY created_at ASC, id ASC
            """),
            {"chat_id": str(chat_id)},
        )
        messages = list(msgs_result.fetchall())

        if len(messages) > EXPORT_MAX_MESSAGES:
            raise HTTPException(
                status_code=413,
                detail="Export limit exceeded: too many messages. Maximum 2000.",
            )
        total_chars = sum(len(m[1]) for m in messages) + len(chat_title or "")
        if total_chars > EXPORT_MAX_CHARS:
            raise HTTPException(
                status_code=413,
                detail="Export limit exceeded: content too large.",
            )

        # Audit: metadata only, no content
        await session.execute(
            text("""
                INSERT INTO audit_logs
                (tenant_id, actor_id, action, entity_type, entity_id, assist_mode, model_name,
                 model_version, input_tokens, output_tokens, metadata)
                VALUES (:tenant_id, :actor_id, 'export_requested', 'chat', :entity_id,
                        NULL, NULL, NULL, 0, 0, CAST(:metadata AS jsonb))
            """),
            {
                "tenant_id": str(tenant_id),
                "actor_id": str(user_uuid),
                "entity_id": str(chat_id),
                "metadata": json.dumps({"format": fmt}),
            },
        )
        await session.commit()

        # Build and return response
        safe_title = (chat_title or str(chat_id))[:80].replace("/", "-")
        export_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        filename_base = f"clinai-chat-{safe_title}-{export_date}".replace(" ", "-")

        if fmt == "txt":
            content = _build_txt(chat_title or "Chat", messages)
            return PlainTextResponse(
                content,
                media_type="text/plain; charset=utf-8",
                headers={
                    "Content-Disposition": f'attachment; filename="{filename_base}.txt"',
                },
            )

        structured_content = None
        doc = await get_by_conversation(session, chat_id, tenant_id, user_uuid)
        if doc:
            structured_content = doc.get("content")
        pdf_bytes = _build_pdf(chat_title or "Chat", messages, structured_content)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename_base}.pdf"',
            },
        )
