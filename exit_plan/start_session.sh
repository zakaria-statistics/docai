#!/bin/bash

# exit_plan/start_session.sh
# Quick session startup: show context, start services

set -e

EXIT_PLAN_DIR="exit_plan"
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

echo "========================================="
echo "  DocAI Session Start"
echo "========================================="
echo ""

# 1. Show last session context
echo "[1/4] Previous session context:"
if [ -f "$EXIT_PLAN_DIR/handoff_to_claude.md" ]; then
    echo "---"
    head -50 "$EXIT_PLAN_DIR/handoff_to_claude.md"
    echo "---"
    echo "(Full context: cat $EXIT_PLAN_DIR/handoff_to_claude.md)"
else
    echo "No previous handoff found."
fi
echo ""

# 2. Git status
echo "[2/4] Git status:"
git status --short
git log -3 --oneline
echo ""

# 3. Start Docker services
echo "[3/4] Starting Docker services..."
if ! docker compose ps -q 2>/dev/null | grep -q .; then
    docker compose up -d 2>&1 | grep -v "^WARN" || true
    echo "Waiting for services to be healthy..."
    sleep 5
fi
docker compose ps 2>&1 | grep -v "^WARN"
echo ""

# 4. Health check
echo "[4/4] Service health:"
API_HEALTH=$(curl -s http://localhost:8080/health 2>/dev/null || echo '{"status":"unavailable"}')
echo "API: $API_HEALTH"

CHROMA_HEALTH=$(curl -s http://localhost:8000/api/v1/heartbeat 2>/dev/null && echo "healthy" || echo "unavailable")
echo "ChromaDB: $CHROMA_HEALTH"

OLLAMA_HEALTH=$(curl -s http://localhost:11434/api/tags 2>/dev/null | jq -r '.models | length' 2>/dev/null || echo "0")
echo "Ollama: $OLLAMA_HEALTH models available"

echo ""
echo "========================================="
echo "  Ready to work!"
echo "========================================="
echo ""
echo "Quick commands:"
echo "  docker compose --profile cli run --rm docai list"
echo "  docker compose --profile cli run --rm docai query 'your question'"
echo ""
