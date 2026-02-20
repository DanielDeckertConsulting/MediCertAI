# ClinAI MVP — Tech Stack Recommendation

**Version:** 0.1  
**Date:** 2025-02-19

---

## 1. Frontend

### Framework

| Option | Recommendation | Rationale |
|--------|----------------|-----------|
| **Vite + React** | ✅ Recommended | Fast DX, small bundle, streaming-friendly |
| Next.js | Alternative | SSR not required for SPA; adds complexity |
| Vue | Alternative | Less common for streaming chat patterns |

**Choice:** Vite + React. MVP is a SPA; no SEO/server-render needs. Vite has excellent HMR and build speed.

### Execution

```bash
# Example
npm create vite@latest clinai-ui -- --template react-ts
```

---

### UI System

| Option | Recommendation | Rationale |
|--------|----------------|-----------|
| **Radix UI + Tailwind** | ✅ Recommended | Accessible, medical-clean aesthetic, no heavy design system |
| MUI | Alternative | Heavier; good if strict Material Design needed |
| Shadcn/ui | Alternative | Similar to Radix; good defaults |
| Chakra | Alternative | Good DX but larger bundle |

**Choice:** Radix UI primitives + Tailwind. Medical/clean look; WCAG-compliant; customizable.

---

### State Management

| Option | Recommendation | Rationale |
|--------|----------------|-----------|
| **React Query (TanStack Query) + Zustand** | ✅ Recommended | Server state (Query) + minimal client state (Zustand) |
| Redux | Alternative | Overkill for MVP |
| Context only | Alternative | Fine for small apps; Query simplifies caching |

**Choice:** TanStack Query for API/chat data; Zustand for UI state (sidebar, modals, toggles).

---

### Streaming Support

- **fetch + ReadableStream** or **EventSource** for SSE
- **React:** Render streaming tokens incrementally via `useState` + chunk append
- **Libraries:** No heavy deps; native streaming sufficient for MVP

---

## 2. Backend

### Language & Framework

| Option | Recommendation | Rationale |
|--------|----------------|-----------|
| **Python + FastAPI** | ✅ Recommended | Async, streaming, Pydantic validation, good Azure SDK support |
| Node + NestJS | Alternative | Good for JS teams; Python stronger for ML/LLM ecosystems |
| Node + Express | Alternative | Less structure; more manual work |

**Choice:** Python + FastAPI. Async streaming, strong validation, native Azure OpenAI SDK.

---

### Background Job Framework

| Option | Recommendation | Rationale |
|--------|----------------|-----------|
| **None (in-request)** | MVP default | Deletion/export in request; simple |
| **Celery + Redis** | Phase 2 | Adds Redis; overkill for MVP |
| **Azure Functions + Queue** | Phase 2 | When async deletion/export needed |

**Choice:** Start without background jobs. Add Azure Functions + Queue when deletion or export becomes heavy.

---

### Migration Framework

- **Alembic** — Standard for SQLAlchemy/Postgres
- Migrations in `backend/migrations/`
- No destructive migrations in MVP; additive first

---

### OpenAPI Strategy

- FastAPI auto-generates OpenAPI 3.0
- Expose `/openapi.json` for frontend codegen
- Optional: `openapi-typescript-codegen` for type-safe API client

---

## 3. Database

### Postgres

- **ORM:** SQLAlchemy 2.0 (async)
- **Driver:** asyncpg
- **Extensions:** `uuid-ossp`, optionally `pgcrypto`
- **RLS:** Used on tenant-scoped tables (see MULTI_TENANCY_DESIGN.md)

---

## 4. Async / Queue

| Need | MVP | Phase 2 |
|------|-----|---------|
| Deletion workflow | In-request | Azure Queue + Function |
| Export generation | In-request | Queue + Function |
| Usage aggregation | In-request write | Nightly Function |

**Decision:** No queue in MVP. Add Azure Queue Storage when justified.

---

## 5. Observability

| Component | Technology |
|-----------|------------|
| **Tracing** | OpenTelemetry → Application Insights |
| **Logging** | `structlog` (JSON), no PII |
| **Metrics** | App Insights custom metrics (token usage, request count) |
| **Errors** | App Insights exceptions; optional Sentry later |

---

## 6. Summary Table

| Layer | Technology | Notes |
|-------|------------|-------|
| Frontend | Vite + React + TypeScript | SPA |
| UI | Radix UI + Tailwind | Medical, accessible |
| State | TanStack Query + Zustand | Server + client state |
| Backend | Python + FastAPI | Async, streaming |
| DB | PostgreSQL + SQLAlchemy + Alembic | RLS for tenants |
| Auth | Azure B2C | JWT validation |
| LLM | Azure OpenAI SDK | Streaming |
| Secrets | Azure Key Vault | Managed Identity |
| Logs | structlog → App Insights | No PII |
| Queue | None (MVP) | Add when needed |
