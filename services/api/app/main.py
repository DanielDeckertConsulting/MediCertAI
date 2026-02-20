"""ClinAI API — FastAPI application."""
import uuid

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

from app.config import settings
from app.routers import health, prompts, chats, ai_responses, folders, admin, cases, interventions
from app.middleware.auth import auth_middleware, get_request_id

structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ]
)
log = structlog.get_logger()

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(
    title="ClinAI API",
    description="AI-powered documentation assistant for psychotherapists",
    version="0.1.0",
    openapi_url="/openapi.json",
    docs_url="/docs" if settings.auth_bypass_local else None,
)

app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    """Add correlation/request ID to all requests."""
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Structured logging. No PII, no content."""
    rid = get_request_id(request)
    log.info("request_start", request_id=rid, path=request.url.path, method=request.method)
    response = await call_next(request)
    log.info("request_end", request_id=rid, status_code=response.status_code)
    return response


@app.on_event("startup")
async def startup():
    log.info("startup", auth_bypass=settings.auth_bypass_local)


app.include_router(health.router, tags=["health"])
app.include_router(prompts.router, prefix="/prompts", tags=["prompts"])
app.include_router(chats.router, prefix="/chats", tags=["chats"])
app.include_router(folders.router, prefix="/folders", tags=["folders"])
app.include_router(ai_responses.router, prefix="/ai-responses", tags=["ai-responses"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(cases.router, prefix="/cases", tags=["cases"])
app.include_router(interventions.router, prefix="/interventions", tags=["interventions"])
