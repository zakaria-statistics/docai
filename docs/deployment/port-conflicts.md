# Handling Port Conflicts

## Quick Check

Before starting Docker containers, check if ports are available:

```bash
make check-ports
# or
./check-ports.sh
```

---

## Current Status

**Port 11434 (Ollama) is OCCUPIED** - Ollama is already running on the host.

```
Process: ollama (PID 1071)
Command: /usr/local/bin/ollama serve
Status: Running since Dec 19
```

---

## Solutions

### Option 1: Use Host Ollama (Recommended for You)

Since Ollama is already running and has models downloaded, use it instead of Docker Ollama.

#### Update docker-compose.yml

**Remove Ollama service**:

```yaml
services:
  # Comment out or remove Ollama
  # ollama:
  #   image: ollama/ollama:latest
  #   ...

  docai-api:
    environment:
      - OLLAMA_BASE_URL=http://host.docker.internal:11434  # Use host Ollama
```

**On Linux**, use host network mode or `host.docker.internal`:

```yaml
docai-api:
  environment:
    - OLLAMA_BASE_URL=http://172.17.0.1:11434  # Docker bridge gateway
    # or add extra_hosts:
  extra_hosts:
    - "host.docker.internal:host-gateway"
  environment:
    - OLLAMA_BASE_URL=http://host.docker.internal:11434
```

---

### Option 2: Stop Host Ollama (Use Docker Ollama)

Stop the host Ollama to free port 11434 for Docker container.

```bash
# Check if Ollama is a systemd service
sudo systemctl status ollama

# If yes, stop it
sudo systemctl stop ollama

# Disable auto-start
sudo systemctl disable ollama

# Or kill the process directly
sudo killall ollama
```

**Then start Docker stack**:
```bash
docker-compose up -d
docker exec docai-ollama ollama pull llama3.1:8b
docker exec docai-ollama ollama pull nomic-embed-text
```

---

### Option 3: Change Docker Ports

Modify docker-compose.yml to use different host ports.

```yaml
services:
  ollama:
    ports:
      - "11435:11434"  # Host port 11435 → Container port 11434

  chromadb:
    ports:
      - "8001:8000"    # Host port 8001 → Container port 8000

  docai-api:
    ports:
      - "8081:8080"    # Host port 8081 → Container port 8080
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434  # Internal communication unchanged
```

**Access API**:
```bash
curl http://localhost:8081/health  # Changed from 8080
```

---

## Comparison: Host vs Docker Ollama

| Aspect | Host Ollama | Docker Ollama |
|--------|-------------|---------------|
| **Models** | Already downloaded (~5GB) | Need to download again |
| **Port** | Uses 11434 (conflicts) | Can use any port |
| **Updates** | System package manager | Docker image updates |
| **Isolation** | Shared with system | Isolated in container |
| **Performance** | Slightly faster (no Docker overhead) | Negligible difference |
| **Docker access** | Need network bridge | Direct service communication |

---

## Recommended Approach

Given that:
- ✅ Ollama already running on host
- ✅ Models already downloaded (saves ~5GB download)
- ✅ Working properly

**Recommendation**: **Use host Ollama** with updated docker-compose.yml

---

## Implementation: Use Host Ollama

### Step 1: Update docker-compose.yml

```yaml
version: '3.8'

services:
  # Remove or comment out Ollama service
  # ollama:
  #   ...

  chromadb:
    image: chromadb/chroma:latest
    container_name: docai-chromadb
    ports:
      - "8000:8000"
    volumes:
      - chroma_data:/chroma/chroma
    environment:
      - IS_PERSISTENT=TRUE
      - ANONYMIZED_TELEMETRY=FALSE
    networks:
      - docai-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/heartbeat"]
      interval: 30s
      timeout: 10s
      retries: 5
    restart: unless-stopped

  docai:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: docai-app
    depends_on:
      chromadb:
        condition: service_healthy
    volumes:
      - ./data/documents:/app/data/documents
      - ./data/sessions:/app/data/sessions
      - ./test_docs:/app/test_docs:ro
    environment:
      - OLLAMA_BASE_URL=http://host.docker.internal:11434  # Use host Ollama
      - OLLAMA_CHAT_MODEL=llama3.1:8b
      - OLLAMA_EMBEDDING_MODEL=nomic-embed-text
      - CHROMA_HOST=chromadb
      - CHROMA_PORT=8000
      - VECTOR_STORE_PATH=/app/data/vector_db
      - CHUNK_SIZE=800
      - CHUNK_OVERLAP=150
      - RETRIEVAL_TOP_K=5
    networks:
      - docai-network
    extra_hosts:
      - "host.docker.internal:host-gateway"  # Enable host access
    stdin_open: true
    tty: true
    restart: unless-stopped
    profiles:
      - cli

  docai-api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: docai-api
    depends_on:
      chromadb:
        condition: service_healthy
    ports:
      - "8080:8080"
    volumes:
      - ./data/documents:/app/data/documents
      - ./data/sessions:/app/data/sessions
      - ./test_docs:/app/test_docs:ro
    environment:
      - OLLAMA_BASE_URL=http://host.docker.internal:11434  # Use host Ollama
      - OLLAMA_CHAT_MODEL=llama3.1:8b
      - OLLAMA_EMBEDDING_MODEL=nomic-embed-text
      - CHROMA_HOST=chromadb
      - CHROMA_PORT=8000
      - VECTOR_STORE_PATH=/app/data/vector_db
      - CHUNK_SIZE=800
      - CHUNK_OVERLAP=150
      - RETRIEVAL_TOP_K=5
    networks:
      - docai-network
    extra_hosts:
      - "host.docker.internal:host-gateway"  # Enable host access
    command: ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8080"]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 5
    restart: unless-stopped

networks:
  docai-network:
    driver: bridge

volumes:
  # Removed ollama_data volume
  chroma_data:
    driver: local
```

### Step 2: Verify Host Ollama

```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Should return: {"models": [...]}
```

### Step 3: Start Docker Services

```bash
# Check ports
make check-ports

# Start services (no Ollama container)
docker-compose up -d

# Test API can reach host Ollama
docker exec docai-api curl http://host.docker.internal:11434/api/tags
```

### Step 4: Test Everything

```bash
# API health check
make api-health

# Test chat
docker-compose run --rm docai chat

# Test API
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "stream": false}'
```

---

## Troubleshooting

### Container Can't Reach Host Ollama

**Error**: `Connection refused to host.docker.internal:11434`

**Solutions**:

1. **Check host.docker.internal works**:
   ```bash
   docker run --rm --add-host host.docker.internal:host-gateway \
     alpine ping -c 2 host.docker.internal
   ```

2. **Use Docker bridge gateway IP instead**:
   ```bash
   # Find Docker bridge IP
   ip addr show docker0 | grep inet
   # Usually: 172.17.0.1

   # Update docker-compose.yml:
   environment:
     - OLLAMA_BASE_URL=http://172.17.0.1:11434
   ```

3. **Check firewall allows Docker access**:
   ```bash
   sudo iptables -L | grep 11434
   ```

### Host Ollama Not Responding

```bash
# Check if running
ps aux | grep ollama

# Check logs
journalctl -u ollama -f

# Restart
sudo systemctl restart ollama
```

---

## Port Check Reference

### Check Specific Port

```bash
# Method 1: netstat
netstat -tlnp | grep :11434

# Method 2: ss
ss -tlnp | grep :11434

# Method 3: lsof
lsof -i :11434

# Method 4: nc (netcat)
nc -zv localhost 11434
```

### Kill Process on Port

```bash
# Find PID
lsof -ti :11434

# Kill it
kill -9 $(lsof -ti :11434)

# For Ollama specifically
sudo systemctl stop ollama
# or
sudo killall ollama
```

---

## Summary

**Current State**:
- Port 11434: ❌ Occupied by host Ollama
- Port 8000: ✅ Available
- Port 8080: ✅ Available

**Recommended Action**:
1. Keep host Ollama running
2. Update docker-compose.yml to use `host.docker.internal`
3. Remove Ollama service from docker-compose.yml
4. Start remaining services

**Benefits**:
- ✅ No port conflicts
- ✅ Models already downloaded
- ✅ Faster startup
- ✅ Simpler setup
