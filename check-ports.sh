#!/bin/bash

echo "========================================"
echo "DocAI Port Availability Check"
echo "========================================"
echo ""

# Ports used by DocAI
PORTS=(8080 8000 11434)
PORT_NAMES=("DocAI API" "ChromaDB" "Ollama")

ALL_AVAILABLE=true

for i in ${!PORTS[@]}; do
    PORT=${PORTS[$i]}
    NAME=${PORT_NAMES[$i]}

    echo "Checking port $PORT ($NAME)..."

    # Check if port is in use
    if ss -tlnp 2>/dev/null | grep -q ":$PORT " || netstat -tlnp 2>/dev/null | grep -q ":$PORT "; then
        echo "  ❌ Port $PORT is OCCUPIED"

        # Try to find what's using it
        PROCESS=$(lsof -i :$PORT 2>/dev/null | grep LISTEN | awk '{print $1, $2}' | head -1)
        if [ -n "$PROCESS" ]; then
            echo "     Process: $PROCESS"
        else
            PROCESS=$(ss -tlnp 2>/dev/null | grep ":$PORT " | sed 's/.*users:((\(.*\)).*/\1/' | head -1)
            if [ -n "$PROCESS" ]; then
                echo "     Process: $PROCESS"
            fi
        fi

        ALL_AVAILABLE=false
    else
        echo "  ✅ Port $PORT is available"
    fi
    echo ""
done

echo "========================================"
if [ "$ALL_AVAILABLE" = true ]; then
    echo "✅ All ports are available!"
    echo "You can safely run: docker-compose up -d"
else
    echo "⚠️  Some ports are occupied"
    echo ""
    echo "Solutions:"
    echo "1. Stop conflicting services:"
    echo "   - Ollama: sudo systemctl stop ollama"
    echo "   - Or: sudo killall ollama"
    echo ""
    echo "2. Change ports in docker-compose.yml:"
    echo "   ports:"
    echo "     - \"8081:8080\"  # Use 8081 instead of 8080"
    echo "     - \"8001:8000\"  # Use 8001 instead of 8000"
    echo "     - \"11435:11434\" # Use 11435 instead of 11434"
    echo ""
    echo "3. Use Docker Ollama instead of host Ollama"
    echo "   (Recommended for containerized setup)"
fi
echo "========================================"
