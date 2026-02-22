# MentalCarePilot MVP

AI-powered documentation assistant for psychotherapists. Azure-native, GDPR-ready, multi-tenant SaaS.

## Prerequisites

- **Node.js 20+** (script can enable pnpm via corepack if missing)
- **Python 3.11+** (on macOS without Docker, the script can install via Homebrew)
- **Postgres 14+** — via Docker, or the bootstrap script can install and start Postgres via Homebrew on macOS

You do **not** need to install pnpm or Python packages yourself; the bootstrap script sets up the API virtualenv and deps.

---

## Quick Start (recommended)

Two commands from the project root:

### Step 1 — Bootstrap (first time or after clone)

Installs Node deps (pnpm), creates the API Python venv, installs API deps, copies env files, starts Postgres (Docker or Homebrew), runs migrations and seed.

```bash
./scripts/bootstrap-local.sh
```

- If **Docker** is running: Postgres is started via `docker compose`.
- If **Docker is not** running (e.g. on macOS): the script uses **Homebrew** to install/start Postgres and creates the `clinai` user and database.
- The API uses a **virtualenv** at `services/api/.venv` (PEP 668–friendly; no system Python install).

### Step 2 — Start the app

```bash
./scripts/start-local.sh
```

This starts the API (port 8000) and the web app (port 5173) in one terminal.

- **API:** http://localhost:8000  
- **Web:** http://localhost:5173  
- **Health:** http://localhost:8000/health  
- **Chat:** http://localhost:5173/chat  

### Optional — Azure OpenAI (for chat streaming)

To use the chat with AI, add to `services/api/.env`:

```
AZURE_OPENAI_ENDPOINT=https://<your-deployment>.openai.azure.com/
AZURE_OPENAI_API_KEY=<your-key>
AZURE_OPENAI_DEPLOYMENT=gpt-4
AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

See [Azure OpenAI setup](https://learn.microsoft.com/en-us/azure/ai-services/openai/quickstart).

---

## Manual setup (if you prefer)

Use this if you don’t want to run the bootstrap script.

### 1. Install dependencies

```bash
pnpm install
cd services/api && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt && cd ../..
```

### 2. Configure environment

```bash
cp apps/web/.env.example apps/web/.env
cp services/api/.env.example services/api/.env
```

### 3. Start Postgres

**Option A — Docker**

```bash
docker compose up -d postgres
```

**Option B — Homebrew (macOS)**

```bash
brew install postgresql@16
brew services start postgresql@16
# Create user and DB (once):
psql -h localhost -d postgres -c "CREATE USER clinai WITH PASSWORD 'clinai';"
psql -h localhost -d postgres -c "CREATE DATABASE clinai OWNER clinai;"
```

Ensure `DATABASE_URL` in `services/api/.env` is:

```
DATABASE_URL=postgresql+asyncpg://clinai:clinai@localhost:5432/clinai
```

### 4. Run migrations & seed

```bash
cd services/api
.venv/bin/python -m alembic upgrade head
.venv/bin/python scripts/seed_dev.py
cd ../..
```

### 5. Run backend and frontend

**One command:** `./scripts/start-local.sh`

**Or two terminals:**

```bash
# Terminal 1
pnpm --filter api dev
```

```bash
# Terminal 2
pnpm --filter web dev
```

---

## Troubleshooting

| Error | Fix |
|-------|-----|
| `pnpm not found` | Run from a terminal where Node is available, or let bootstrap run (it enables pnpm via corepack). Install Node 20+ from [nodejs.org](https://nodejs.org/) if needed. |
| `pip: externally-managed-environment` | Use the bootstrap script; it creates `services/api/.venv` and installs deps there. Do not install API packages into the system Python. |
| `alembic: command not found` | Run migrations with the venv: `cd services/api && .venv/bin/python -m alembic upgrade head`. Ensure you ran `./scripts/bootstrap-local.sh` first. |
| `uvicorn: command not found` / `spawn ENOENT` | The API dev script uses `services/api/.venv`. Run `./scripts/bootstrap-local.sh` once to create the venv, then `./scripts/start-local.sh`. |
| `role "clinai" does not exist` | If using Homebrew Postgres, create user/DB (see [Manual setup](#manual-setup) step 3). Or run `./scripts/bootstrap-local.sh`; it creates them when using Homebrew. |
| `Cannot connect to the Docker daemon` | Start Docker Desktop, or run without Docker — bootstrap will use Homebrew for Postgres on macOS. |
| `vite: command not found` / `node_modules missing` | Run `pnpm install` from the project root. |
| `Got unexpected extra arguments` | Run backend and frontend in separate terminals; don’t paste both commands in one. |

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
