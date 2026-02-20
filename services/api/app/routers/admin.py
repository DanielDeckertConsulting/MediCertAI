"""Admin KPIs and audit logs. Role-scoped: admin sees tenant, user sees own."""
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import text

from app.db import get_session
from app.dependencies import require_auth, get_tenant_id, get_user_uuid

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


def _is_admin(request: Request) -> bool:
    roles = getattr(request.state, "roles", None) or []
    return "admin" in roles


def _session_gen(tenant_id: UUID, user_id: str | None = None):
    from app.db import get_session

    return get_session(tenant_id=tenant_id, user_id=user_id)


# --- Schemas ---


class KPISummary(BaseModel):
    input_tokens: int
    output_tokens: int
    total_tokens: int
    request_count: int
    chats_created_count: int


class TokenBucket(BaseModel):
    bucket_start: str
    input_tokens: int
    output_tokens: int
    total_tokens: int


class ChatsBucket(BaseModel):
    bucket_start: str
    chats_created: int


class AssistModeRow(BaseModel):
    assist_mode: str | None
    request_count: int
    total_tokens: int


class ModelRow(BaseModel):
    model_config = {"protected_namespaces": ()}
    model_name: str
    model_version: str | None
    request_count: int
    total_tokens: int


class ActivitySummary(BaseModel):
    active_days_count: int
    current_streak_days: int
    avg_tokens_per_request: float


class AuditLogRow(BaseModel):
    model_config = {"protected_namespaces": ()}
    id: str
    user_id: str
    tenant_id: str
    timestamp: str
    action: str
    assist_mode: str | None
    input_tokens: int
    output_tokens: int
    total_tokens: int
    model_name: str | None
    model_version: str | None
    entity_type: str | None
    entity_id: str | None


class AuditLogsResponse(BaseModel):
    items: list[AuditLogRow]
    next_cursor: str | None


def _parse_range(range_val: str) -> tuple[datetime, datetime]:
    """Parse range into (from_ts, to_ts)."""
    now = datetime.utcnow().replace(tzinfo=None)
    if range_val == "last30d" or range_val == "month":
        from_ts = now - timedelta(days=30)
    elif range_val == "last12w":
        from_ts = now - timedelta(weeks=12)
    elif range_val == "last12m":
        from_ts = now - timedelta(days=365)
    else:
        from_ts = now - timedelta(days=30)
    return (from_ts, now)


def _parse_granularity(gran: str) -> str:
    if gran in ("day", "week", "month", "year"):
        return gran
    return "day"


# --- KPI Endpoints ---


@router.get("/kpis/summary", response_model=KPISummary)
@limiter.limit("60/minute")
async def get_kpis_summary(
    request: Request,
    range_val: str = Query("month", alias="range"),
    scope: str = Query("me", description="tenant (admin) or me"),
    _auth=Depends(require_auth),
):
    tenant_id = get_tenant_id(request)
    user_uuid = get_user_uuid(request)
    if not tenant_id or not user_uuid:
        raise HTTPException(status_code=401, detail="Auth required")

    if scope == "tenant" and not _is_admin(request):
        raise HTTPException(status_code=403, detail="Admin role required for tenant scope")

    from_ts, to_ts = _parse_range(range_val if range_val in ("last30d", "last12w", "last12m") else "last30d")

    async for session in _session_gen(tenant_id):
        user_filter = "" if scope == "tenant" else "AND user_id = :user_id"
        params = {
            "tenant_id": str(tenant_id),
            "from_ts": from_ts,
            "to_ts": to_ts,
        }
        if scope == "me":
            params["user_id"] = str(user_uuid)

        sql_usage = f"""
            SELECT COALESCE(SUM(input_tokens), 0), COALESCE(SUM(output_tokens), 0), COUNT(*)
            FROM usage_records
            WHERE tenant_id = :tenant_id AND ts >= :from_ts AND ts <= :to_ts {user_filter}
        """
        res = await session.execute(text(sql_usage), params)
        row = res.fetchone()
        input_tok = row[0] or 0
        output_tok = row[1] or 0
        request_count = row[2] or 0

        user_filter_chats = "" if scope == "tenant" else "AND owner_user_id = :owner_user_id"
        params_chats = {
            "tenant_id": str(tenant_id),
            "from_ts": from_ts,
            "to_ts": to_ts,
        }
        if scope == "me":
            params_chats["owner_user_id"] = str(user_uuid)

        sql_chats = f"""
            SELECT COUNT(*) FROM chats
            WHERE tenant_id = :tenant_id AND created_at >= :from_ts AND created_at <= :to_ts {user_filter_chats}
        """
        res_chats = await session.execute(text(sql_chats), params_chats)
        chats_count = res_chats.fetchone()[0] or 0

    return KPISummary(
        input_tokens=input_tok,
        output_tokens=output_tok,
        total_tokens=input_tok + output_tok,
        request_count=request_count,
        chats_created_count=chats_count,
    )


@router.get("/kpis/tokens", response_model=list[TokenBucket])
@limiter.limit("60/minute")
async def get_kpis_tokens(
    request: Request,
    granularity: str = Query("day"),
    range_val: str = Query("last30d", alias="range"),
    scope: str = Query("me"),
    _auth=Depends(require_auth),
):
    tenant_id = get_tenant_id(request)
    user_uuid = get_user_uuid(request)
    if not tenant_id or not user_uuid:
        raise HTTPException(status_code=401, detail="Auth required")
    if scope == "tenant" and not _is_admin(request):
        raise HTTPException(status_code=403, detail="Admin role required for tenant scope")

    from_ts, to_ts = _parse_range(range_val)
    gran = _parse_granularity(granularity)
    date_trunc = {"day": "day", "week": "week", "month": "month", "year": "year"}.get(gran, "day")
    user_filter = "" if scope == "tenant" else "AND user_id = :user_id"
    params = {"tenant_id": str(tenant_id), "from_ts": from_ts, "to_ts": to_ts}
    if scope == "me":
        params["user_id"] = str(user_uuid)

    async for session in _session_gen(tenant_id):
        sql = f"""
            SELECT date_trunc(:date_trunc, ts) AS bucket_start,
                   COALESCE(SUM(input_tokens), 0), COALESCE(SUM(output_tokens), 0)
            FROM usage_records
            WHERE tenant_id = :tenant_id AND ts >= :from_ts AND ts <= :to_ts {user_filter}
            GROUP BY date_trunc(:date_trunc, ts)
            ORDER BY bucket_start
        """
        params["date_trunc"] = date_trunc
        res = await session.execute(text(sql), params)
        rows = res.fetchall()

    return [
        TokenBucket(
            bucket_start=r[0].isoformat() if r[0] else "",
            input_tokens=r[1] or 0,
            output_tokens=r[2] or 0,
            total_tokens=(r[1] or 0) + (r[2] or 0),
        )
        for r in rows
    ]


@router.get("/kpis/chats-created", response_model=list[ChatsBucket])
@limiter.limit("60/minute")
async def get_kpis_chats_created(
    request: Request,
    granularity: str = Query("day"),
    range_val: str = Query("last30d", alias="range"),
    scope: str = Query("me"),
    _auth=Depends(require_auth),
):
    tenant_id = get_tenant_id(request)
    user_uuid = get_user_uuid(request)
    if not tenant_id or not user_uuid:
        raise HTTPException(status_code=401, detail="Auth required")
    if scope == "tenant" and not _is_admin(request):
        raise HTTPException(status_code=403, detail="Admin role required for tenant scope")

    from_ts, to_ts = _parse_range(range_val)
    gran = _parse_granularity(granularity)
    date_trunc = {"day": "day", "week": "week", "month": "month", "year": "year"}.get(gran, "day")
    user_filter = "" if scope == "tenant" else "AND owner_user_id = :owner_user_id"
    params = {"tenant_id": str(tenant_id), "from_ts": from_ts, "to_ts": to_ts, "date_trunc": date_trunc}
    if scope == "me":
        params["owner_user_id"] = str(user_uuid)

    async for session in _session_gen(tenant_id):
        sql = f"""
            SELECT date_trunc(:date_trunc, created_at) AS bucket_start, COUNT(*)
            FROM chats
            WHERE tenant_id = :tenant_id AND created_at >= :from_ts AND created_at <= :to_ts {user_filter}
            GROUP BY date_trunc(:date_trunc, created_at)
            ORDER BY bucket_start
        """
        res = await session.execute(text(sql), params)
        rows = res.fetchall()

    return [
        ChatsBucket(bucket_start=r[0].isoformat() if r[0] else "", chats_created=r[1] or 0)
        for r in rows
    ]


@router.get("/kpis/assist-modes", response_model=list[AssistModeRow])
@limiter.limit("60/minute")
async def get_kpis_assist_modes(
    request: Request,
    range_val: str = Query("month", alias="range"),
    scope: str = Query("me"),
    _auth=Depends(require_auth),
):
    tenant_id = get_tenant_id(request)
    user_uuid = get_user_uuid(request)
    if not tenant_id or not user_uuid:
        raise HTTPException(status_code=401, detail="Auth required")
    if scope == "tenant" and not _is_admin(request):
        raise HTTPException(status_code=403, detail="Admin role required for tenant scope")

    from_ts, to_ts = _parse_range(range_val)
    user_filter = "" if scope == "tenant" else "AND user_id = :user_id"
    params = {"tenant_id": str(tenant_id), "from_ts": from_ts, "to_ts": to_ts}
    if scope == "me":
        params["user_id"] = str(user_uuid)

    async for session in _session_gen(tenant_id):
        sql = f"""
            SELECT assist_mode, COUNT(*), COALESCE(SUM(input_tokens + output_tokens), 0)
            FROM usage_records
            WHERE tenant_id = :tenant_id AND ts >= :from_ts AND ts <= :to_ts {user_filter}
            GROUP BY assist_mode
            ORDER BY COUNT(*) DESC
        """
        res = await session.execute(text(sql), params)
        rows = res.fetchall()

    return [
        AssistModeRow(assist_mode=r[0], request_count=r[1] or 0, total_tokens=r[2] or 0)
        for r in rows
    ]


@router.get("/kpis/models", response_model=list[ModelRow])
@limiter.limit("60/minute")
async def get_kpis_models(
    request: Request,
    range_val: str = Query("month", alias="range"),
    scope: str = Query("me"),
    _auth=Depends(require_auth),
):
    tenant_id = get_tenant_id(request)
    user_uuid = get_user_uuid(request)
    if not tenant_id or not user_uuid:
        raise HTTPException(status_code=401, detail="Auth required")
    if scope == "tenant" and not _is_admin(request):
        raise HTTPException(status_code=403, detail="Admin role required for tenant scope")

    from_ts, to_ts = _parse_range(range_val)
    user_filter = "" if scope == "tenant" else "AND user_id = :user_id"
    params = {"tenant_id": str(tenant_id), "from_ts": from_ts, "to_ts": to_ts}
    if scope == "me":
        params["user_id"] = str(user_uuid)

    async for session in _session_gen(tenant_id):
        sql = f"""
            SELECT model_name, model_version, COUNT(*), COALESCE(SUM(input_tokens + output_tokens), 0)
            FROM usage_records
            WHERE tenant_id = :tenant_id AND ts >= :from_ts AND ts <= :to_ts {user_filter}
            GROUP BY model_name, model_version
            ORDER BY COUNT(*) DESC
        """
        res = await session.execute(text(sql), params)
        rows = res.fetchall()

    return [
        ModelRow(
            model_name=r[0] or "unknown",
            model_version=r[1],
            request_count=r[2] or 0,
            total_tokens=r[3] or 0,
        )
        for r in rows
    ]


@router.get("/kpis/activity", response_model=ActivitySummary)
@limiter.limit("60/minute")
async def get_kpis_activity(
    request: Request,
    range_val: str = Query("month", alias="range"),
    scope: str = Query("me"),
    _auth=Depends(require_auth),
):
    tenant_id = get_tenant_id(request)
    user_uuid = get_user_uuid(request)
    if not tenant_id or not user_uuid:
        raise HTTPException(status_code=401, detail="Auth required")
    if scope == "tenant" and not _is_admin(request):
        raise HTTPException(status_code=403, detail="Admin role required for tenant scope")

    from_ts, to_ts = _parse_range(range_val)
    user_filter = "" if scope == "tenant" else "AND user_id = :user_id"
    params = {"tenant_id": str(tenant_id), "from_ts": from_ts, "to_ts": to_ts}
    if scope == "me":
        params["user_id"] = str(user_uuid)

    async for session in _session_gen(tenant_id):
        sql = f"""
            SELECT COUNT(DISTINCT date_trunc('day', ts)::date) AS active_days,
                   COALESCE(SUM(input_tokens + output_tokens), 0) / NULLIF(COUNT(*), 0) AS avg_tokens
            FROM usage_records
            WHERE tenant_id = :tenant_id AND ts >= :from_ts AND ts <= :to_ts {user_filter}
        """
        res = await session.execute(text(sql), params)
        row = res.fetchone()
        active_days = row[0] or 0
        avg_tokens = float(row[1] or 0)

        sql_streak = f"""
            WITH days AS (
                SELECT DISTINCT date_trunc('day', ts)::date AS d
                FROM usage_records
                WHERE tenant_id = :tenant_id AND ts >= :from_ts AND ts <= :to_ts {user_filter}
                ORDER BY d DESC
            ),
            ranked AS (
                SELECT d, d - ROW_NUMBER() OVER (ORDER BY d)::int AS grp FROM days
            ),
            streaks AS (
                SELECT grp, COUNT(*) AS cnt FROM ranked GROUP BY grp
            )
            SELECT COALESCE((SELECT cnt FROM streaks ORDER BY grp DESC LIMIT 1), 0)
        """
        res_streak = await session.execute(text(sql_streak), params)
        streak = res_streak.fetchone()[0] or 0

    return ActivitySummary(
        active_days_count=active_days,
        current_streak_days=streak,
        avg_tokens_per_request=round(avg_tokens, 1),
    )


# --- Audit Logs ---


@router.get("/audit-logs", response_model=AuditLogsResponse)
@limiter.limit("100/minute")
async def get_audit_logs(
    request: Request,
    from_ts: datetime | None = Query(None, description="From timestamp (ISO)"),
    to_ts: datetime | None = Query(None, description="To timestamp (ISO)"),
    assist_mode: str | None = Query(None),
    action: str | None = Query(None),
    model_name: str | None = Query(None),
    user_id_param: str | None = Query(None, alias="user_id"),
    q: str | None = Query(None, description="Search safe fields"),
    limit: int = Query(50, ge=1, le=200),
    cursor: str | None = Query(None),
    scope: str = Query("me"),
    _auth=Depends(require_auth),
):
    tenant_id = get_tenant_id(request)
    user_uuid = get_user_uuid(request)
    if not tenant_id or not user_uuid:
        raise HTTPException(status_code=401, detail="Auth required")

    if scope == "tenant":
        if not _is_admin(request):
            raise HTTPException(status_code=403, detail="Admin role required for tenant scope")
        actor_filter = ""
        params_user = {}
    else:
        scope = "me"
        actor_filter = "AND actor_id = :actor_id"
        user_id_param = None
        params_user = {"actor_id": str(user_uuid)}

    params: dict = {
        "tenant_id": str(tenant_id),
        "limit": limit + 1,
    }
    params.update(params_user)

    filters = ["tenant_id = :tenant_id", actor_filter.lstrip("AND ") if actor_filter else "1=1"]
    if from_ts:
        filters.append("ts >= :from_ts")
        params["from_ts"] = from_ts
    if to_ts:
        filters.append("ts <= :to_ts")
        params["to_ts"] = to_ts
    if assist_mode:
        filters.append("assist_mode = :assist_mode")
        params["assist_mode"] = assist_mode
    if action:
        filters.append("action = :action")
        params["action"] = action
    if model_name:
        filters.append("model_name = :model_name")
        params["model_name"] = model_name
    if user_id_param and scope == "tenant":
        filters.append("actor_id = :filter_user_id")
        params["filter_user_id"] = user_id_param

    q_filter = ""
    if q and q.strip():
        safe_q = q.strip().replace("%", "\\%").replace("_", "\\_")
        params["q_pattern"] = f"%{safe_q}%"
        q_filter = """
            AND (
                action ILIKE :q_pattern
                OR COALESCE(assist_mode, '') ILIKE :q_pattern
                OR COALESCE(model_name, '') ILIKE :q_pattern
                OR COALESCE(model_version, '') ILIKE :q_pattern
                OR COALESCE(entity_type, '') ILIKE :q_pattern
                OR COALESCE(entity_id::text, '') ILIKE :q_pattern
            )
        """

    cursor_clause = ""
    if cursor:
        parts = cursor.split("|")
        if len(parts) == 2:
            try:
                cursor_ts = parts[0]
                cursor_id = parts[1]
                cursor_clause = "AND (ts, id) < (:cursor_ts::timestamptz, :cursor_id::uuid)"
                params["cursor_ts"] = cursor_ts
                params["cursor_id"] = cursor_id
            except Exception:
                pass

    where_clause = " AND ".join(filters)

    sql = f"""
        SELECT id, actor_id, tenant_id, ts, action, assist_mode,
               COALESCE(input_tokens, 0), COALESCE(output_tokens, 0),
               model_name, model_version, entity_type, entity_id
        FROM audit_logs
        WHERE {where_clause} {q_filter}
        ORDER BY ts DESC, id DESC
        LIMIT :limit
    """

    async for session in _session_gen(tenant_id):
        res = await session.execute(text(sql), params)
        rows = res.fetchall()

    items = []
    next_cursor = None
    for i, r in enumerate(rows):
        if i == limit:
            next_cursor = f"{r[3].isoformat()}|{r[0]}"
            break
        items.append(
            AuditLogRow(
                id=str(r[0]),
                user_id=str(r[1]),
                tenant_id=str(r[2]),
                timestamp=r[3].isoformat() if r[3] else "",
                action=r[4] or "",
                assist_mode=r[5],
                input_tokens=r[6] or 0,
                output_tokens=r[7] or 0,
                total_tokens=(r[6] or 0) + (r[7] or 0),
                model_name=r[8],
                model_version=r[9],
                entity_type=r[10],
                entity_id=str(r[11]) if r[11] else None,
            )
        )

    return AuditLogsResponse(items=items, next_cursor=next_cursor)
