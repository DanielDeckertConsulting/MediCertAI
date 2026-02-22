# MentalCarePilot — Database Migrations

**Framework:** Alembic  
**Location:** `services/api/alembic/`

## Commands

```bash
cd services/api

# Upgrade to latest
alembic upgrade head

# Create new migration
alembic revision -m "description"

# Downgrade one revision
alembic downgrade -1
```

## Migrations

| Revision | Description |
|----------|-------------|
| 001 | Initial schema: tenants, users, prompts, prompt_versions, audit_logs, RLS |
| 002 | Chats, chat_messages, llm_audit_logs |
| ... | (003–009: AI responses, prompts, folders) |
| 010 | usage_records, extend audit_logs (assist_mode, model_name, tokens), indexes, RLS |

## Rules

- Additive-first; avoid destructive changes in MVP
- No PII in migration content
- RLS policies in migrations for tenant-scoped tables
