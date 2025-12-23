# Issue: Missing wait-for-it.sh Script

## What Happened
When running `docker compose up -d`, the docai-api container failed to start with error:
```
exec: "./wait-for-it.sh": stat ./wait-for-it.sh: no such file or directory
```

## Root Cause
The docker-compose.yml references `./wait-for-it.sh` in the entrypoint, but this script doesn't exist in the Docker image.

## Resolution
Remove the wait-for-it.sh entrypoint from docker-compose.yml since `depends_on: service_healthy` already handles waiting for ChromaDB to be ready.

### Fix Applied
In `docker-compose.yml` line 95, remove:
```yaml
entrypoint: ["./wait-for-it.sh", "chromadb:8000", "--"]
```

The `depends_on: chromadb: condition: service_healthy` configuration is sufficient to ensure ChromaDB is ready before docai-api starts.
