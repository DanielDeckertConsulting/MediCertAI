# ClinAI — Database Migrations

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

## Rules

- Additive-first; avoid destructive changes in MVP
- No PII in migration content
- RLS policies in migrations for tenant-scoped tables
