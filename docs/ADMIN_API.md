# Admin API Reference

**Base path:** `/admin`  
**Auth:** Bearer JWT required  
**Date:** 2025-02-20

---

## Scope & Roles

| Scope   | Role     | Description                                              |
|---------|----------|----------------------------------------------------------|
| `me`    | Any user | Own KPIs and own audit logs only                         |
| `tenant`| Admin    | Tenant-wide KPIs and audit logs; returns 403 for non-admin |

---

## KPI Endpoints

### GET /admin/kpis/summary

Aggregated token usage, request count, and chats created.

| Param  | Type   | Default | Description                    |
|--------|--------|---------|--------------------------------|
| `range`| string | `month` | `last30d`, `last12w`, `last12m`, `month` |
| `scope`| string | `me`    | `me` or `tenant`               |

**Response:**
```json
{
  "input_tokens": 1234,
  "output_tokens": 5678,
  "total_tokens": 6912,
  "request_count": 42,
  "chats_created_count": 5
}
```

---

### GET /admin/kpis/tokens

Token usage over time (time series).

| Param         | Type   | Default   | Description                    |
|---------------|--------|-----------|--------------------------------|
| `granularity` | string | `day`     | `day`, `week`, `month`, `year` |
| `range`       | string | `last30d` | `last30d`, `last12w`, `last12m`|
| `scope`       | string | `me`      | `me` or `tenant`               |

**Response:**
```json
[
  {
    "bucket_start": "2025-02-19T00:00:00",
    "input_tokens": 100,
    "output_tokens": 200,
    "total_tokens": 300
  }
]
```

---

### GET /admin/kpis/chats-created

Chats created over time (time series).

| Param         | Type   | Default   | Description                    |
|---------------|--------|-----------|--------------------------------|
| `granularity` | string | `day`     | `day`, `week`, `month`, `year` |
| `range`       | string | `last30d` | `last30d`, `last12w`, `last12m`|
| `scope`       | string | `me`      | `me` or `tenant`               |

**Response:**
```json
[
  {
    "bucket_start": "2025-02-19T00:00:00",
    "chats_created": 3
  }
]
```

---

### GET /admin/kpis/assist-modes

Assist mode usage distribution.

| Param  | Type   | Default | Description      |
|--------|--------|---------|------------------|
| `range`| string | `month` | `last30d`, `last12w`, `last12m`, `month` |
| `scope`| string | `me`    | `me` or `tenant` |

**Response:**
```json
[
  {
    "assist_mode": "session_summary",
    "request_count": 10,
    "total_tokens": 5000
  }
]
```

---

### GET /admin/kpis/models

Model usage distribution.

| Param  | Type   | Default | Description      |
|--------|--------|---------|------------------|
| `range`| string | `month` | `last30d`, `last12w`, `last12m`, `month` |
| `scope`| string | `me`    | `me` or `tenant` |

**Response:**
```json
[
  {
    "model_name": "gpt-4",
    "model_version": null,
    "request_count": 25,
    "total_tokens": 12000
  }
]
```

---

### GET /admin/kpis/activity

Activity summary: active days, streak, avg tokens per request.

| Param  | Type   | Default | Description      |
|--------|--------|---------|------------------|
| `range`| string | `month` | `last30d`, `last12w`, `last12m`, `month` |
| `scope`| string | `me`    | `me` or `tenant` |

**Response:**
```json
{
  "active_days_count": 7,
  "current_streak_days": 3,
  "avg_tokens_per_request": 245.5
}
```

---

## Audit Logs

### GET /admin/audit-logs

Searchable, filterable audit logs. Sorted by `ts` DESC, `id` DESC. Paginated via cursor.

| Param         | Type   | Default | Description                                                  |
|---------------|--------|---------|--------------------------------------------------------------|
| `from_ts`     | string | —       | From timestamp (ISO 8601)                                    |
| `to_ts`       | string | —       | To timestamp (ISO 8601)                                     |
| `assist_mode` | string | —       | Filter by assist_mode                                        |
| `action`      | string | —       | Filter by action (e.g. `chat_message_sent`, `folder.deleted`) |
| `model_name`  | string | —       | Filter by model_name                                         |
| `user_id`     | string | —       | Filter by actor_id (admin scope only)                        |
| `q`           | string | —       | Search safe fields: action, assist_mode, model_name, model_version, entity_type, entity_id |
| `limit`       | int    | 50      | Page size (1–200)                                            |
| `cursor`      | string | —       | Opaque cursor for next page (`ts|id`)                        |
| `scope`       | string | `me`    | `me` or `tenant`                                             |

**Response:**
```json
{
  "items": [
    {
      "id": "uuid",
      "user_id": "actor-uuid",
      "tenant_id": "tenant-uuid",
      "timestamp": "2025-02-20T12:00:00",
      "action": "chat_message_sent",
      "assist_mode": "session_summary",
      "input_tokens": 100,
      "output_tokens": 200,
      "total_tokens": 300,
      "model_name": "gpt-4",
      "model_version": null,
      "entity_type": "chat_message",
      "entity_id": "message-uuid"
    }
  ],
  "next_cursor": "2025-02-20T11:00:00|previous-id"
}
```

**Search `q`:** ILIKE against action, assist_mode, model_name, model_version, entity_type, entity_id. Does NOT search metadata JSON (PII risk).
