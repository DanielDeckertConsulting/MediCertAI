#!/usr/bin/env bash
# Bootstrap local dev: deps, env, Postgres, migrations, seed.
# Run from project root. After this, run: ./scripts/start-local.sh

set -e
cd "$(dirname "$0")/.."
ROOT="$PWD"

# Ensure pnpm on PATH (version managers often not loaded in script subshell)
for d in "$HOME/.local/share/pnpm" "$HOME/.volta/bin" "$HOME/.fnm/current/bin"; do
  [ -d "$d" ] && PATH="$d:$PATH"
done
# Load nvm if present (adds node/npm/pnpm to PATH)
export NVM_DIR="${NVM_DIR:-$HOME/.nvm}"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
if ! command -v pnpm >/dev/null 2>&1; then
  if command -v corepack >/dev/null 2>&1; then
    corepack enable && corepack prepare pnpm@latest --activate
  elif command -v npm >/dev/null 2>&1; then
    npm install -g pnpm
  fi
fi
if ! command -v pnpm >/dev/null 2>&1; then
  echo "pnpm not found. Install Node 20+, then run: corepack enable && corepack prepare pnpm@latest --activate"
  exit 1
fi

# Ensure Homebrew on PATH (Apple Silicon / Intel)
for d in /opt/homebrew/bin /usr/local/bin; do
  [ -d "$d" ] && PATH="$d:$PATH"
done
if ! command -v brew >/dev/null 2>&1; then
  echo "=== Homebrew not found. Installing Homebrew (non-interactive) ==="
  NONINTERACTIVE=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  [ -x /opt/homebrew/bin/brew ] && eval "$(/opt/homebrew/bin/brew shellenv)"
  [ -x /usr/local/bin/brew ] && eval "$(/usr/local/bin/brew shellenv)"
fi
if ! command -v brew >/dev/null 2>&1; then
  echo "Could not install or find Homebrew. Install from https://brew.sh and re-run."
  exit 1
fi

# Ensure Python 3.11+ (for API and uvicorn)
if ! command -v python3 >/dev/null 2>&1; then
  echo "=== Python 3 not found. Installing via Homebrew ==="
  brew install python@3.12
  PATH="$(brew --prefix python@3.12)/bin:$PATH"
fi

echo "=== 1. Install dependencies ==="
pnpm install
# API: use venv (PEP 668 — Homebrew Python is externally managed)
API_VENV="$ROOT/services/api/.venv"
if ! command -v python3 >/dev/null 2>&1; then
  echo "Warning: python3 not found. Install Python 3.11+ (e.g. brew install python@3.12)."
else
  if [ ! -d "$API_VENV" ]; then
    echo "Creating API venv at services/api/.venv ..."
    python3 -m venv "$API_VENV"
  fi
  echo "Installing API Python deps into venv ..."
  "$API_VENV/bin/pip" install -q -r "$ROOT/services/api/requirements.txt"
fi

echo ""
echo "=== 2. Configure environment ==="
for pair in "apps/web/.env.example:apps/web/.env" "services/api/.env.example:services/api/.env"; do
  src="${pair%%:*}"
  dst="${pair##*:}"
  if [ ! -f "$dst" ]; then
    cp "$src" "$dst"
    echo "Created $dst from $src"
  else
    echo "Already exists: $dst"
  fi
done

echo ""
echo "=== 3. Start Postgres ==="
POSTGRES_READY=0
if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
  docker compose up -d postgres
  echo "Waiting for Postgres (Docker) to be ready..."
  for i in $(seq 1 30); do
    if docker compose exec -T postgres pg_isready -U clinai 2>/dev/null; then
      POSTGRES_READY=1
      break
    fi
    [ "$i" -eq 30 ] && { echo "Postgres did not become ready in time."; exit 1; }
    sleep 1
  done
  echo "Postgres is ready."
fi

if [ "$POSTGRES_READY" -eq 0 ] && command -v brew >/dev/null 2>&1; then
  echo "Using Homebrew for Postgres."
  if ! brew list postgresql@16 &>/dev/null && ! brew list postgresql &>/dev/null; then
    echo "Installing PostgreSQL via Homebrew..."
    brew install postgresql@16
  fi
  # Prefer postgresql@16; fallback to postgresql (e.g. postgresql@17)
  if brew list postgresql@16 &>/dev/null; then
    brew services start postgresql@16
    PG_BIN="$(brew --prefix postgresql@16)/bin"
  else
    brew services start postgresql
    PG_BIN="$(brew --prefix postgresql)/bin"
  fi
  export PATH="$PG_BIN:$PATH"
  echo "Waiting for Postgres (Homebrew) to be ready..."
  for i in $(seq 1 30); do
    if pg_isready -h localhost -p 5432 2>/dev/null; then
      POSTGRES_READY=1
      break
    fi
    [ "$i" -eq 30 ] && { echo "Postgres did not become ready in time."; exit 1; }
    sleep 1
  done
  # Create clinai user and database (match docker-compose)
  psql -h localhost -p 5432 -d postgres -tAc "SELECT 1 FROM pg_roles WHERE rolname='clinai'" 2>/dev/null | grep -q 1 || \
    psql -h localhost -p 5432 -d postgres -c "CREATE USER clinai WITH PASSWORD 'clinai';" 2>/dev/null || true
  psql -h localhost -p 5432 -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='clinai'" 2>/dev/null | grep -q 1 || \
    psql -h localhost -p 5432 -d postgres -c "CREATE DATABASE clinai OWNER clinai;" 2>/dev/null || true
  echo "Postgres is ready (user clinai, database clinai)."
fi

if [ "$POSTGRES_READY" -eq 0 ]; then
  echo "Postgres not started (no Docker, or Homebrew Postgres failed). Set DATABASE_URL in services/api/.env, then run:"
  echo "  cd services/api && .venv/bin/python -m alembic upgrade head && .venv/bin/python scripts/seed_dev.py && cd ../.."
  exit 1
fi

echo ""
echo "=== 4. Run migrations & seed ==="
cd "$ROOT/services/api"
API_VENV="$ROOT/services/api/.venv"
if [ ! -x "$API_VENV/bin/python" ]; then
  echo "API venv missing. Re-run bootstrap to create it and install deps."
  exit 1
fi
"$API_VENV/bin/python" -m alembic upgrade head
"$API_VENV/bin/python" scripts/seed_dev.py
cd "$ROOT"

echo ""
echo "=== Bootstrap complete ==="
echo "Start backend and frontend with:"
echo "  ./scripts/start-local.sh"
echo ""
echo "Or in two terminals:"
echo "  pnpm --filter api dev"
echo "  pnpm --filter web dev"
