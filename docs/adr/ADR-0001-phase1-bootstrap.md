# ADR-0001: Phase 1 Bootstrap

## Context

Initialize MentalCarePilot MVP foundation from Phase 0 docs: monorepo, backend skeleton, frontend skeleton, DB + RLS, prompt scaffold.

## Decision

- **Structure:** `apps/web`, `services/api`, `packages/shared` (optional), `docs`, `infra` (optional)
- **Backend:** FastAPI, SQLAlchemy async, Alembic, structlog, slowapi
- **Frontend:** Vite + React + TypeScript, TanStack Query, Zustand, Tailwind, Radix (minimal)
- **Auth:** Config-driven bypass for local dev (`AUTH_BYPASS_LOCAL=true`); JWT validation stubbed
- **DB:** Single Postgres, RLS on tenant-scoped tables, `app.tenant_id` session variable
- **CI:** GitHub Actions; build web + run API tests with Postgres service

## Consequences

- Single-command local setup possible once Docker + pnpm available
- Auth bypass must never be enabled in production
- Prompt system loads from DB; API returns placeholders until prompt_versions populated
