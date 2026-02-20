"""FastAPI dependencies: auth, tenant context."""
from uuid import UUID

from fastapi import HTTPException, Request

from app.config import settings

# Dev bypass: matches seed_dev.py tenant and user
DEV_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")
DEV_USER_ID = "dev-user-1"
DEV_USER_UUID = UUID("00000000-0000-0000-0000-000000000002")


async def require_auth(request: Request) -> dict:
    """Require valid auth. Set tenant_id, user_id, user_uuid on request.state. Reject 401/403 if missing."""
    if settings.auth_bypass_local:
        request.state.tenant_id = DEV_TENANT_ID
        request.state.user_id = DEV_USER_ID
        request.state.user_uuid = DEV_USER_UUID
        request.state.roles = ["admin"]
        return {
            "tenant_id": str(request.state.tenant_id),
            "user_id": request.state.user_id,
            "user_uuid": str(request.state.user_uuid),
        }

    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization")

    # TODO: Validate JWT, extract claims, lookup tenant from users table
    raise HTTPException(status_code=501, detail="Auth not configured")


def get_tenant_id(request: Request) -> UUID | None:
    """Get tenant_id from request state (set by require_auth)."""
    return getattr(request.state, "tenant_id", None)


def get_user_id(request: Request) -> str | None:
    """Get user_id (b2c_sub) from request state."""
    return getattr(request.state, "user_id", None)


def get_user_uuid(request: Request) -> UUID | None:
    """Get user_uuid (users.id) from request state. Required for owner_user_id in chats."""
    return getattr(request.state, "user_uuid", None)
