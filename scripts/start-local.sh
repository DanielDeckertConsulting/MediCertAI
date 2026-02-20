#!/usr/bin/env bash
# Start all PraxisPilot components locally (API + Web).
# Run from project root. Requires: Postgres, pnpm, Python 3.11+

set -e
cd "$(dirname "$0")/.."

# Ensure deps
pnpm install
cd services/api && pip install -q -r requirements.txt 2>/dev/null || true && cd ../..

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
