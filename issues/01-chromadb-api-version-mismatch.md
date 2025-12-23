# Issue: ChromaDB API Version Mismatch (v1 vs v2)

## What Happened
docai-api container fails with error:
```
requests.exceptions.HTTPError: 410 Client Error: Gone for url: http://chromadb:8000/api/v1/tenants/default_tenant
Exception: {"error":"Unimplemented","message":"The v1 API is deprecated. Please use /v2 apis"}
```

## Root Cause
- ChromaDB server (latest) only supports v2 API
- ChromaDB Python client was version 0.4.22 (uses deprecated v1 API)
- Docker build cache may have kept old chromadb version despite requirements.txt update

## Resolution
1. Updated requirements.txt: chromadb from 0.4.22 to 0.5.23
2. Updated ollama from 0.1.6 to >=0.4.5 (to fix httpx dependency conflict)
3. Need to rebuild Docker images without cache to ensure new packages are installed

### Commands to Fix
```bash
# Stop all services
docker compose down

# Rebuild without cache
docker compose build --no-cache docai docai-api

# Start services
docker compose up -d

# Verify chromadb version in container
docker exec docai-api pip show chromadb | grep Version
```

Expected chromadb version: 0.5.23 or higher
