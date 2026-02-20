# ClinAI MVP

AI-powered documentation assistant for psychotherapists. Azure-native, GDPR-ready, multi-tenant SaaS.

## Prerequisites

- Node.js 20+
- Python 3.11+
- pnpm
- Postgres 14+ (via Docker or local install)

## Quick Start (< 15 min)

### 1. Install dependencies

```bash
pnpm install
cd services/api && pip install -r requirements.txt && cd ../..
```

### 2. Configure environment

```bash
cp apps/web/.env.example apps/web/.env
cp services/api/.env.example services/api/.env
```

### 3. Start Postgres (Docker)

Ensure Docker is running, then:

```bash
docker-compose up -d postgres
```

If Docker is not available, see [Postgres without Docker](#postgres-without-docker) below.

### 4. Azure OpenAI (required for chat streaming)

Add to `services/api/.env`:

```
AZURE_OPENAI_ENDPOINT=https://<your-deployment>.openai.azure.com/
AZURE_OPENAI_API_KEY=<your-key>
AZURE_OPENAI_DEPLOYMENT=gpt-4
AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

See [Azure OpenAI setup](https://learn.microsoft.com/en-us/azure/ai-services/openai/quickstart) for creating a deployment.

### 5. Run migrations & seed

```bash
cd services/api
alembic upgrade head
python scripts/seed_dev.py
cd ../..
```

### 6. Run backend and frontend

**Option A — one command (recommended):**

```bash
./scripts/start-local.sh
```

**Option B — two terminals:**

```bash
# Terminal 1
pnpm --filter api dev
```

```bash
# Terminal 2
pnpm --filter web dev
```

- **API:** http://localhost:8000  
- **Web:** http://localhost:5173  
- **Health:** http://localhost:8000/health  
- **Chat:** http://localhost:5173/chat

---

## Postgres without Docker

If Docker is not running, use a local Postgres instance. Create the role and database:

```bash
psql -U postgres -c "CREATE USER clinai WITH PASSWORD 'clinai';"
psql -U postgres -c "CREATE DATABASE clinai OWNER clinai;"
```

Then run migrations and seed as in step 5 above. Ensure `DATABASE_URL` in `services/api/.env` is:

```
DATABASE_URL=postgresql+asyncpg://clinai:clinai@localhost:5432/clinai
```

## Troubleshooting

| Error | Fix |
|-------|-----|
| `role "clinai" does not exist` | Use [Postgres without Docker](#postgres-without-docker) to create the role, or start Postgres via Docker. |
| `Cannot connect to the Docker daemon` | Start Docker Desktop (or your Docker daemon) and run `docker-compose up -d postgres` again. |
| `vite: command not found` / `node_modules missing` | Run `pnpm install` from the project root. |
| `Got unexpected extra arguments (# terminal 1)` | Run backend and frontend in separate terminals; don't copy-paste both commands at once. |

## How to test streaming

1. Ensure Azure OpenAI is configured in `services/api/.env`.
2. Start backend and frontend.
3. Open http://localhost:5173/chat, click "Neuer Chat".
4. Select an assist mode (e.g. Session Summary), ensure "Anonymisieren" is ON.
5. Send a message; tokens should stream in real time.
6. Use export (download icon) to get a `.txt` transcript.

## Project Structure

```
├── apps/
│   └── web/              # Vite + React frontend
├── services/
│   └── api/              # FastAPI backend
├── packages/
│   └── shared/           # Shared types
├── docs/                 # Architecture, ADRs, diagrams
├── infra/                # IaC (optional)
└── docker-compose.yml    # Local Postgres
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Tech Stack](docs/TECHSTACK.md)
- [MVP Feature List](docs/MVP_FEATURE_LIST.md)
- [Migrations](docs/MIGRATIONS.md)
- [RLS](docs/RLS.md)
- [ADR: Anonymization Storage](docs/adr/ADR-0002-anonymization-storage.md)

## CI

GitHub Actions: build + test on push/PR. See `.github/workflows/ci.yml`.
