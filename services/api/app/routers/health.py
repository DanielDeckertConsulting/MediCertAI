"""Health endpoints."""
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.get("/health")
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def health(request: Request):
    """Liveness probe. Always returns 200 if process is up."""
    return {"status": "ok", "version": "0.1.0"}


@router.get("/ready")
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def ready(request: Request):
    """Readiness probe. Checks DB connectivity."""
    try:
        from app.db import async_session_factory
        from sqlalchemy import text

        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
        return {"status": "ready", "database": "ok"}
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "database": "error", "detail": str(e)},
        )
