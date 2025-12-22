# Docker Setup Notes

## Configuration: Using Host Ollama

The docker compose.yml has been configured to use your existing Ollama installation instead of running Ollama in a container.

### What Changed

✅ **Ollama service** - Commented out (not needed)
✅ **OLLAMA_BASE_URL** - Changed to `http://host.docker.internal:11434`
✅ **extra_hosts** - Added `host.docker.internal:host-gateway` for Linux
✅ **Dependencies** - Removed Ollama health check dependency
✅ **Volumes** - Removed `ollama_data` volume

### Why This Setup?

- ✅ Ollama already running on host (PID 1071)
- ✅ Models already downloaded (~5GB saved)
- ✅ No port conflicts
- ✅ Simpler stack

### Services Running

```
┌─────────────────────────────────────┐
│  Host System                        │
│  ├─ Ollama (localhost:11434)        │
│  │  └─ Models: llama3.1:8b          │
│  │             nomic-embed-text     │
│  └─ Docker Containers:              │
│     ├─ ChromaDB (port 8000)         │
│     └─ DocAI API (port 8080)        │
└─────────────────────────────────────┘
```

### Quick Start

```bash
# 1. Check ports (8080 and 8000 should be available)
make check-ports

# 2. Start services
docker compose up -d

# 3. Verify API can reach host Ollama
docker exec docai-api curl -s http://host.docker.internal:11434/api/tags

# 4. Test API
make api-health

# 5. Test CLI
docker compose run --rm docai list
```

### Verification Steps

1. **Check host Ollama is running:**
   ```bash
   curl http://localhost:11434/api/tags
   ```

2. **Check container can reach host:**
   ```bash
   docker exec docai-api curl http://host.docker.internal:11434/api/tags
   ```

3. **Test chat:**
   ```bash
   docker compose run --rm docai chat
   ```

### Troubleshooting

#### Container can't reach host Ollama

**Symptom**: Connection refused to `host.docker.internal:11434`

**Solution 1**: Verify extra_hosts is set
```yaml
extra_hosts:
  - "host.docker.internal:host-gateway"
```

**Solution 2**: Use bridge gateway IP instead
```bash
# Find Docker bridge IP
ip addr show docker0 | grep inet
# Usually: 172.17.0.1

# Update .env or docker compose.yml:
OLLAMA_BASE_URL=http://172.17.0.1:11434
```

**Solution 3**: Check host Ollama is listening
```bash
# Should show 127.0.0.1:11434 or 0.0.0.0:11434
ss -tlnp | grep 11434
```

#### Switch back to Docker Ollama

If you want to run Ollama in Docker instead:

1. Uncomment the Ollama service in docker compose.yml
2. Uncomment ollama_data volume
3. Change `OLLAMA_BASE_URL=http://ollama:11434`
4. Add back Ollama dependency in docai/docai-api
5. Remove `extra_hosts`
6. Pull models: `docker exec docai-ollama ollama pull llama3.1:8b`

### Port Summary

| Service | Host Port | Container Port | Status |
|---------|-----------|----------------|--------|
| Ollama | 11434 | - | Host (not Docker) |
| ChromaDB | 8000 | 8000 | Docker |
| DocAI API | 8080 | 8080 | Docker |

### Network Flow

```
API Request → DocAI API (port 8080)
    ↓
    ├─→ ChromaDB (chromadb:8000) - Internal network
    └─→ Ollama (host.docker.internal:11434) - Host bridge
```

### Files Modified

- `docker compose.yml` - Main configuration
- `check-ports.sh` - Port availability checker
- `Makefile` - Added `make check-ports`

### Next Steps

1. Run `make check-ports` to verify ports
2. Run `docker compose up -d` to start
3. Test with `make api-health`
4. See `docs/deployment/port-conflicts.md` for more details
