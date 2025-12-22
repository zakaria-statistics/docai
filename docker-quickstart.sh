#!/bin/bash
set -e

echo "================================="
echo "DocAI Docker Quick Start"
echo "================================="
echo ""

# Check if docker compose is installed
if ! command -v docker compose &> /dev/null; then
    echo "Error: docker compose not found. Please install Docker Compose first."
    exit 1
fi

# Build and start services
echo "Step 1: Building Docker images..."
docker compose build

echo ""
echo "Step 2: Starting services..."
docker compose up -d

echo ""
echo "Step 3: Waiting for services to be healthy..."
sleep 10

# Check if services are running
if ! docker compose ps | grep -q "Up"; then
    echo "Error: Services failed to start. Check logs with: docker compose logs"
    exit 1
fi

echo ""
echo "Step 4: Pulling Ollama models (this may take 5-10 minutes)..."
docker exec docai-ollama ollama pull llama3.1:8b
docker exec docai-ollama ollama pull nomic-embed-text

echo ""
echo "================================="
echo "Setup Complete!"
echo "================================="
echo ""
echo "Services running:"
docker compose ps
echo ""
echo "Try these commands:"
echo "  docker compose run --rm docai chat"
echo "  docker compose run --rm docai add /app/test_docs/machine_learning_basics.md"
echo "  docker compose run --rm docai list"
echo "  docker compose run --rm docai query 'What is machine learning?'"
echo ""
echo "Or use the Makefile:"
echo "  make chat"
echo "  make add FILE=/app/test_docs/file.md"
echo "  make query Q='Your question'"
echo ""
echo "View logs: docker compose logs -f"
echo "Stop services: docker compose down"
echo ""
