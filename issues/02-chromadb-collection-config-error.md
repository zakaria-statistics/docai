# Issue: ChromaDB Collection Configuration Error

## What Happened
docai-api container fails with:
```
KeyError: '_type'
File "/usr/local/lib/python3.10/site-packages/chromadb/api/configuration.py", line 209, in from_json
```

## Root Cause
ChromaDB client (0.5.23) and server (latest from chromadb/chroma:latest image) may have incompatible collection configuration formats. The server is returning a different JSON structure than the client expects.

## Resolution Options

### Option 1: Pin ChromaDB Server Version (Recommended)
Update Dockerfile.chromadb to use a compatible version:
```dockerfile
FROM chromadb/chroma:0.5.23
```

### Option 2: Use Latest Client to Match Server
Update requirements.txt to use latest chromadb client (may require code changes).

### Option 3: Clear Old Collections
If collections were created with old version, clear the volume:
```bash
docker compose down -v
docker compose up -d
```

## Next Steps
1. Check ChromaDB server version: `docker exec docai-chromadb pip show chromadb | grep Version`
2. Ensure client and server versions are compatible
3. Clear volumes if needed
