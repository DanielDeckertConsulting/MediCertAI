#!/usr/bin/env bash
# Start all PraxisPilot components locally (API + Web).
# Run from project root. Requires: Postgres, pnpm, Python 3.11+

set -e
cd "$(dirname "$0")/.."

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

# Ensure API venv on PATH so "python3 -m uvicorn" in api dev uses venv
for d in /opt/homebrew/bin /usr/local/bin; do
  [ -d "$d" ] && PATH="$d:$PATH"
done
API_VENV="$(cd "$(dirname "$0")/.." && pwd)/services/api/.venv"
if [ -x "$API_VENV/bin/python" ]; then
  PATH="$API_VENV/bin:$PATH"
fi
export PATH

# Ensure deps
pnpm install
if [ -x "$API_VENV/bin/pip" ]; then
  "$API_VENV/bin/pip" install -q -r "$(dirname "$0")/../services/api/requirements.txt" 2>/dev/null || true
fi

# Kill existing processes on our ports
for port in 8000 5173; do
  lsof -ti :$port 2>/dev/null | xargs kill -9 2>/dev/null || true
done
sleep 2

echo "Starting API on http://localhost:8000 ..."
pnpm --filter api dev &
API_PID=$!
sleep 4

echo "Starting Web on http://localhost:5173 ..."
pnpm --filter web dev &
WEB_PID=$!
sleep 3

echo ""
echo "=== PraxisPilot running locally ==="
echo "  API:  http://localhost:8000"
echo "  Web:  http://localhost:5173"
echo "  Chat: http://localhost:5173/chat"
echo ""
echo "Press Ctrl+C to stop both servers."
wait $API_PID $WEB_PID
