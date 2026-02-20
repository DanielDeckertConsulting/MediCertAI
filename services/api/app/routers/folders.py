"""Folder CRUD. Tenant-isolated, RLS enforced. Emits domain events."""
import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import text

from app.db import get_session
from app.dependencies import require_auth, get_tenant_id, get_user_uuid
from app.services.event_store import append_event

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


# --- Schemas ---
class CreateFolderBody(BaseModel):
    name: str


class FolderOut(BaseModel):
    id: str
    name: str
    created_at: str


class PatchFolderBody(BaseModel):
    name: str


def _session_gen(tenant_id: UUID, user_uuid: UUID):
    return get_session(tenant_id=tenant_id, user_id=str(user_uuid))


# --- CRUD ---
@router.post("", response_model=FolderOut)
@limiter.limit("50/minute")
async def create_folder(
    request: Request,
    body: CreateFolderBody,
    _auth=Depends(require_auth),
):
    tenant_id = get_tenant_id(request)
    user_uuid = get_user_uuid(request)
    if not tenant_id or not user_uuid:
        raise HTTPException(status_code=401, detail="Auth required")

    name = (body.name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Folder name required")

    async for session in _session_gen(tenant_id, user_uuid):
        # Check duplicate (unique per tenant)
        dup = await session.execute(
            text("""
                SELECT 1 FROM folders
                WHERE tenant_id = :tenant_id AND name = :name
            """),
            {"tenant_id": str(tenant_id), "name": name},
        )
        if dup.fetchone():
            raise HTTPException(status_code=409, detail="Folder with this name already exists")

        result = await session.execute(
            text("""
                INSERT INTO folders (tenant_id, name)
                VALUES (:tenant_id, :name)
                RETURNING id, name, created_at
            """),
            {"tenant_id": str(tenant_id), "name": name},
        )
        row = result.fetchone()
        folder_id = row[0]

        await append_event(
            session,
            tenant_id,
            actor=str(user_uuid),
            entity_type="folder",
            entity_id=str(folder_id),
            event_type="folder.created",
            payload={"folder_id": str(folder_id), "name": name},
        )
        await session.commit()

        return FolderOut(
            id=str(folder_id),
            name=row[1],
            created_at=row[2].isoformat(),
        )

    raise HTTPException(status_code=500, detail="Unexpected error")


@router.get("", response_model=list[FolderOut])
@limiter.limit("100/minute")
async def list_folders(
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
                SELECT id, name, created_at
                FROM folders
                WHERE tenant_id = :tenant_id
                ORDER BY name ASC
            """),
            {"tenant_id": str(tenant_id)},
        )
        rows = result.fetchall()
        return [
            FolderOut(id=str(r[0]), name=r[1], created_at=r[2].isoformat())
            for r in rows
        ]

    return []


@router.patch("/{folder_id}", response_model=FolderOut)
@limiter.limit("50/minute")
async def patch_folder(
    request: Request,
    folder_id: UUID,
    body: PatchFolderBody,
    _auth=Depends(require_auth),
):
    tenant_id = get_tenant_id(request)
    user_uuid = get_user_uuid(request)
    if not tenant_id or not user_uuid:
        raise HTTPException(status_code=401, detail="Auth required")

    name = (body.name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Folder name required")

    async for session in _session_gen(tenant_id, user_uuid):
        # Check duplicate (excluding self)
        dup = await session.execute(
            text("""
                SELECT 1 FROM folders
                WHERE tenant_id = :tenant_id AND name = :name AND id != :folder_id
            """),
            {
                "tenant_id": str(tenant_id),
                "name": name,
                "folder_id": str(folder_id),
            },
        )
        if dup.fetchone():
            raise HTTPException(status_code=409, detail="Folder with this name already exists")

        result = await session.execute(
            text("""
                UPDATE folders SET name = :name
                WHERE id = :folder_id AND tenant_id = :tenant_id
                RETURNING id, name, created_at
            """),
            {
                "folder_id": str(folder_id),
                "tenant_id": str(tenant_id),
                "name": name,
            },
        )
        row = result.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Folder not found")

        await append_event(
            session,
            tenant_id,
            actor=str(user_uuid),
            entity_type="folder",
            entity_id=str(folder_id),
            event_type="folder.renamed",
            payload={"folder_id": str(folder_id)},
        )
        await session.commit()

        return FolderOut(
            id=str(row[0]),
            name=row[1],
            created_at=row[2].isoformat(),
        )

    raise HTTPException(status_code=500, detail="Unexpected error")


@router.delete("/{folder_id}", status_code=204)
@limiter.limit("30/minute")
async def delete_folder(
    request: Request,
    folder_id: UUID,
    _auth=Depends(require_auth),
):
    tenant_id = get_tenant_id(request)
    user_uuid = get_user_uuid(request)
    if not tenant_id or not user_uuid:
        raise HTTPException(status_code=401, detail="Auth required")

    async for session in _session_gen(tenant_id, user_uuid):
        # Count chats before delete (for event payload)
        count_result = await session.execute(
            text("""
                SELECT COUNT(*) FROM chats
                WHERE folder_id = :folder_id AND tenant_id = :tenant_id
            """),
            {"folder_id": str(folder_id), "tenant_id": str(tenant_id)},
        )
        chats_moved = count_result.scalar() or 0

        result = await session.execute(
            text("""
                DELETE FROM folders
                WHERE id = :folder_id AND tenant_id = :tenant_id
                RETURNING id
            """),
            {"folder_id": str(folder_id), "tenant_id": str(tenant_id)},
        )
        if not result.fetchone():
            raise HTTPException(status_code=404, detail="Folder not found")

        await append_event(
            session,
            tenant_id,
            actor=str(user_uuid),
            entity_type="folder",
            entity_id=str(folder_id),
            event_type="folder.deleted",
            payload={"folder_id": str(folder_id), "chats_moved": chats_moved},
        )

        # Audit log (folder_id only, no name — no PII)
        await session.execute(
            text("""
                INSERT INTO audit_logs (tenant_id, actor_id, action, entity_type, entity_id, metadata)
                VALUES (:tenant_id, :actor_id, 'folder.deleted', 'folder', :entity_id, CAST(:metadata AS jsonb))
            """),
            {
                "tenant_id": str(tenant_id),
                "actor_id": str(user_uuid),
                "entity_id": str(folder_id),
                "metadata": json.dumps({"chats_moved": chats_moved}),
            },
        )
        await session.commit()

    return None
