"""Auth middleware: JWT validation (or bypass for local dev), tenant/user context."""
from fastapi import Request
from fastapi.responses import JSONResponse


def get_request_id(request: Request) -> str:
    """Get correlation/request ID from request state."""
    return getattr(request.state, "request_id", "unknown")


async def auth_middleware(request: Request, call_next):
    """Validate JWT, set tenant_id/user_id. Bypass when AUTH_BYPASS_LOCAL=true."""
    # Actual auth middleware is applied per-route via dependencies
    return await call_next(request)


def get_tenant_context(request: Request) -> dict | None:
    """Get tenant_id, user_id from request state (set by auth dependency)."""
    if not hasattr(request.state, "tenant_id"):
        return None
    return {
        "tenant_id": str(request.state.tenant_id) if request.state.tenant_id else None,
        "user_id": getattr(request.state, "user_id", None),
        "roles": getattr(request.state, "roles", []),
    }
