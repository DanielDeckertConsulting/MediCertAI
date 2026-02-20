"""Chat CRUD and streaming messages. Tenant-isolated, RLS enforced."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import text
from app.config import settings
from app.db import get_session
from app.dependencies import require_auth, get_tenant_id, get_user_uuid
from app.services.anonymization import anonymize
from app.services.prompt_injection import sanitize_user_message
from app.services.prompt_registry import get_system_prompt, ASSIST_KEYS
from app.services.azure_openai import stream_chat

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


class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    created_at: str


class ChatDetail(BaseModel):
    id: str
    title: str
    is_favorite: bool
    created_at: str
    updated_at: str
    messages: list[MessageOut]


class PatchChatBody(BaseModel):
    title: str | None = None
    is_favorite: bool | None = None


class SendMessageBody(BaseModel):
    assist_mode_key: str
    anonymization_enabled: bool = True
    user_message: str


def _session_gen(tenant_id: UUID, user_uuid: UUID):
    return get_session(tenant_id=tenant_id, user_id=str(user_uuid))


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
                RETURNING id, title, created_at, updated_at, is_favorite
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
        }
    return created


@router.get("", response_model=list[ChatSummary])
@limiter.limit("100/minute")
async def list_chats(
    request: Request,
    _auth=Depends(require_auth),
):
    tenant_id = get_tenant_id(request)
    user_uuid = get_user_uuid(request)
    if not tenant_id or not user_uuid:
        raise HTTPException(status_code=401, detail="Auth required")

    async for session in _session_gen(tenant_id, user_uuid):
        result = await session.execute(
            text("""
                SELECT id, title, updated_at, is_favorite
                FROM chats
                WHERE tenant_id = :tenant_id AND owner_user_id = :owner_user_id
                ORDER BY updated_at DESC
            """),
            {"tenant_id": str(tenant_id), "owner_user_id": str(user_uuid)},
        )
        rows = result.fetchall()
        return [
            ChatSummary(
                id=str(r[0]),
                title=r[1],
                updated_at=r[2].isoformat(),
                is_favorite=r[3],
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
                SELECT id, title, is_favorite, created_at, updated_at
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
        messages = [
            MessageOut(
                id=str(m[0]),
                role=m[1],
                content=m[2],
                created_at=m[3].isoformat(),
            )
            for m in msgs.fetchall()
            if m[1] != "system"
        ]  # hide system from client
        return ChatDetail(
            id=str(row[0]),
            title=row[1],
            is_favorite=row[2],
            created_at=row[3].isoformat(),
            updated_at=row[4].isoformat(),
            messages=messages,
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
    if not updates:
        raise HTTPException(status_code=400, detail="No updates provided")

    result_data = None
    async for session in _session_gen(tenant_id, user_uuid):
        result = await session.execute(
            text(f"""
                UPDATE chats SET {", ".join(updates)}, updated_at = now()
                WHERE id = :chat_id AND tenant_id = :tenant_id AND owner_user_id = :owner_user_id
                RETURNING id, title, is_favorite, updated_at
            """),
            params,
        )
        row = result.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Chat not found")
        result_data = {"id": str(row[0]), "title": row[1], "is_favorite": row[2], "updated_at": row[3].isoformat()}
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


# --- Streaming message ---
async def _sse_stream(
    chat_id: UUID,
    tenant_id: UUID,
    user_uuid: UUID,
    assist_mode_key: str,
    user_message: str,
    anonymization_enabled: bool,
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

                # 7. Audit log (metadata only)
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
                        "prompt_tokens": usage.get("prompt_tokens", 0) if usage else 0,
                        "completion_tokens": usage.get("completion_tokens", 0) if usage else 0,
                        "correlation_id": correlation_id,
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

    # Verify chat exists and belongs to user
    async for session in _session_gen(tenant_id, user_uuid):
        check = await session.execute(
            text("""
                SELECT 1 FROM chats
                WHERE id = :chat_id AND tenant_id = :tenant_id AND owner_user_id = :owner_user_id
            """),
            {"chat_id": str(chat_id), "tenant_id": str(tenant_id), "owner_user_id": str(user_uuid)},
        )
        if not check.fetchone():
            raise HTTPException(status_code=404, detail="Chat not found")

    correlation_id = getattr(request.state, "request_id", None) or str(request.headers.get("X-Request-ID", ""))
    return StreamingResponse(
        _sse_stream(
            chat_id=chat_id,
            tenant_id=tenant_id,
            user_uuid=user_uuid,
            assist_mode_key=body.assist_mode_key,
            user_message=body.user_message,
            anonymization_enabled=body.anonymization_enabled,
            correlation_id=correlation_id,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# --- Export ---
@router.get("/{chat_id}/export.txt")
@limiter.limit("30/minute")
async def export_chat(
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
                SELECT id, title FROM chats
                WHERE id = :chat_id AND tenant_id = :tenant_id AND owner_user_id = :owner_user_id
            """),
            {"chat_id": str(chat_id), "tenant_id": str(tenant_id), "owner_user_id": str(user_uuid)},
        )
        row = chat.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Chat not found")

        msgs = await session.execute(
            text("""
                SELECT role, content, created_at
                FROM chat_messages WHERE chat_id = :chat_id AND role != 'system'
                ORDER BY created_at ASC
            """),
            {"chat_id": str(chat_id)},
        )
        lines = [f"# {row[1]}\n"]
        for role, content, created_at in msgs.fetchall():
            ts = created_at.strftime("%Y-%m-%d %H:%M") if created_at else ""
            lines.append(f"\n[{ts}] {role.upper()}:\n{content}\n")
        from fastapi.responses import PlainTextResponse
        return PlainTextResponse("\n".join(lines), media_type="text/plain")
