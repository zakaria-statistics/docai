# Docker Volumes Deep Dive

## Storage Fundamentals

### Container Filesystem Problem

**Containers are ephemeral** - when removed, all data inside is lost:

```bash
docker run -it ubuntu bash
# Inside container:
echo "important data" > /data.txt
exit

docker rm <container-id>
# /data.txt is GONE forever!
```

**Solution**: Docker volumes persist data outside containers.

---

## Volume Types

Docker provides 3 ways to persist data:

| Type | Managed By | Location | Use Case |
|------|-----------|----------|----------|
| **Named Volume** | Docker | `/var/lib/docker/volumes/` | Production databases, app data |
| **Bind Mount** | You | Any host path | Development, config files |
| **tmpfs** | Memory | RAM only | Sensitive temporary data |

---

## Named Volumes

### Definition

**File**: `docker-compose.yml`

```yaml
volumes:
  ollama_data:
    driver: local
  chroma_data:
    driver: local
```

### Usage

```yaml
services:
  ollama:
    volumes:
      - ollama_data:/root/.ollama
        #     ▲            ▲
        #     │            └─ Path inside container
        #     └────────────── Volume name

  chromadb:
    volumes:
      - chroma_data:/chroma/chroma
```

### How It Works

```
┌──────────────────────────────────────────────┐
│           Docker Host                         │
│                                               │
│  /var/lib/docker/volumes/                    │
│  ├─ docai_ollama_data/                       │
│  │  └─ _data/                                │
│  │     ├─ models/                            │
│  │     │  └─ llama3.1-8b (4.9GB)            │
│  │     └─ manifests/                         │
│  │                                           │
│  └─ docai_chroma_data/                       │
│     └─ _data/                                │
│        └─ chroma.sqlite3                     │
│                                               │
│          ▲           ▲                        │
│          │           │                        │
│  ┌───────┴───┐  ┌───┴────────┐              │
│  │  ollama   │  │  chromadb  │              │
│  │ container │  │  container │              │
│  │           │  │            │              │
│  │ /root/    │  │ /chroma/   │              │
│  │ .ollama ──┘  │ chroma ────┘              │
│  └───────────┘  └────────────┘              │
└──────────────────────────────────────────────┘
```

**Key Features**:
- Docker manages location
- Survives container deletion
- Can be shared between containers
- Backed up by Docker

---

## Bind Mounts

### Definition

```yaml
services:
  docai-api:
    volumes:
      - ./data/documents:/app/data/documents
      #   ▲                 ▲
      #   │                 └─ Container path
      #   └─────────────────── Host path (relative or absolute)

      - ./test_docs:/app/test_docs:ro
      #                                ▲
      #                                └─ Read-only flag
```

### How It Works

```
┌──────────────────────────────────────────────┐
│           Docker Host                         │
│                                               │
│  /home/zack/llm-dir/                         │
│  ├─ data/                                    │
│  │  ├─ documents/                            │
│  │  │  └─ uploaded_file.pdf                  │
│  │  └─ sessions/                             │
│  │     └─ session-123.json                   │
│  │                                           │
│  └─ test_docs/                               │
│     ├─ machine_learning_basics.md            │
│     └─ python_best_practices.txt             │
│                                               │
│          ▲           ▲                        │
│          │           │                        │
│  ┌───────┴───────────┴─────────┐            │
│  │     docai-api container      │            │
│  │                               │            │
│  │  /app/data/documents/   ◄────┼─── Same files!
│  │  /app/test_docs/        ◄────┼─── (read-only)
│  │                               │            │
│  └───────────────────────────────┘            │
└──────────────────────────────────────────────┘
```

**Key Features**:
- You control exact location
- Changes in container → visible on host
- Changes on host → visible in container
- Good for development (edit files locally)

---

## DocAI Volume Strategy

### Named Volumes (Persistent Data)

```yaml
volumes:
  ollama_data:    # Ollama models (4-5 GB)
  chroma_data:    # Vector embeddings
```

**Why named volumes**:
- Large binary data (models)
- Don't need direct host access
- Let Docker manage backups
- Better performance on Mac/Windows

### Bind Mounts (Development Data)

```yaml
volumes:
  - ./data/documents:/app/data/documents    # Document cache
  - ./data/sessions:/app/data/sessions      # Chat sessions
  - ./test_docs:/app/test_docs:ro          # Sample docs (read-only)
```

**Why bind mounts**:
- Easy to inspect from host
- Can edit/add files directly
- Survives `docker-compose down`
- Good for development

---

## Volume Lifecycle

### Creation

```bash
# Automatically created on first run
docker-compose up -d

# Manually create
docker volume create my-volume
```

### Inspection

```bash
# List volumes
docker volume ls

# Inspect specific volume
docker volume inspect docai_ollama_data

# Output shows:
{
  "Name": "docai_ollama_data",
  "Mountpoint": "/var/lib/docker/volumes/docai_ollama_data/_data",
  "Driver": "local"
}
```

### Accessing Data

```bash
# Named volume (need root)
sudo ls /var/lib/docker/volumes/docai_ollama_data/_data/

# Bind mount (normal access)
ls ./data/documents/
```

### Backup

```bash
# Named volume - backup to tar
docker run --rm \
  -v docai_ollama_data:/data \
  -v $(pwd):/backup \
  ubuntu tar czf /backup/ollama-backup.tar.gz /data

# Bind mount - just copy
cp -r ./data/ ./backup/
```

### Restore

```bash
# Named volume - restore from tar
docker run --rm \
  -v docai_ollama_data:/data \
  -v $(pwd):/backup \
  ubuntu tar xzf /backup/ollama-backup.tar.gz -C /

# Bind mount - just copy back
cp -r ./backup/data/ ./
```

### Deletion

```bash
# Remove with containers
docker-compose down -v  # WARNING: Deletes ALL volumes!

# Remove specific volume (manual)
docker volume rm docai_ollama_data

# Prune unused volumes
docker volume prune
```

---

## Read-Only Volumes

### Why Use Read-Only?

```yaml
docai-api:
  volumes:
    - ./test_docs:/app/test_docs:ro
    #                              ▲
    #                              └─ Read-only
```

**Benefits**:
- Prevent accidental modification
- Security (container can't write)
- Clearly communicate intent

**When to use**:
- Configuration files
- Static data (test documents)
- Shared resources between containers

---

## Volume Drivers

### Local Driver (Default)

```yaml
volumes:
  ollama_data:
    driver: local  # Stores on local disk
```

### Cloud Drivers

```yaml
volumes:
  shared_data:
    driver: nfs  # Network File System
    driver_opts:
      share: "nfs-server:/path"

  aws_data:
    driver: rexray/ebs  # AWS Elastic Block Store
```

**Use cases**:
- Multi-host deployments
- Shared storage across cluster
- Cloud-native applications

---

## Performance Considerations

### Named Volumes vs Bind Mounts

| Metric | Named Volume | Bind Mount |
|--------|-------------|-----------|
| **Linux** | Native speed | Native speed |
| **Mac** | ~2x faster | Slow (OSXFS overhead) |
| **Windows** | ~2x faster | Slow (file sharing overhead) |
| **Docker Desktop** | Optimized | Unoptimized |

**Recommendation**: Use named volumes for performance-critical data (databases, models).

### Volume Mount Options

```yaml
volumes:
  - type: volume
    source: ollama_data
    target: /root/.ollama
    volume:
      nocopy: true  # Don't copy initial container contents

  - type: bind
    source: ./data
    target: /app/data
    bind:
      propagation: rshared  # Mount propagation mode
```

---

## Common Patterns

### 1. Data Containers (Legacy)

```yaml
# Old way (deprecated)
data:
  image: busybox
  volumes:
    - /data

app:
  volumes_from:
    - data
```

**Modern alternative**: Use named volumes directly.

### 2. Shared Volumes

```yaml
services:
  app1:
    volumes:
      - shared:/data

  app2:
    volumes:
      - shared:/data  # Both access same volume

volumes:
  shared:
```

### 3. Volume Initialization

```yaml
services:
  init:
    image: busybox
    volumes:
      - data:/data
    command: sh -c "echo 'initialized' > /data/ready.txt"

  app:
    depends_on:
      - init
    volumes:
      - data:/data
```

---

## Inspecting Volume Usage

### Check Volume Size

```bash
# Named volume
sudo du -sh /var/lib/docker/volumes/docai_ollama_data/

# Bind mount
du -sh ./data/
```

### List Files in Volume

```bash
# From container
docker exec docai-ollama ls -lah /root/.ollama/models/

# From host (named volume)
sudo ls -lah /var/lib/docker/volumes/docai_ollama_data/_data/models/

# From host (bind mount)
ls -lah ./data/documents/
```

### Monitor Volume I/O

```bash
# Real-time stats
docker stats docai-ollama

# Shows:
# CONTAINER     CPU %   MEM USAGE   BLOCK I/O
# docai-ollama  5%      2.1GB       100MB / 50MB
#                                   ▲       ▲
#                                   read    write
```

---

## Troubleshooting

### Volume Not Found

```bash
# Error: volume "docai_ollama_data" not found

# Solution: Create it
docker volume create docai_ollama_data

# Or let compose create it
docker-compose up -d
```

### Permission Denied

```bash
# Error: permission denied writing to /app/data

# Check ownership inside container
docker exec docai-api ls -l /app/data

# Fix: Change ownership
docker exec docai-api chown -R $(id -u):$(id -g) /app/data

# Or in Dockerfile:
RUN mkdir -p /app/data && chown app:app /app/data
```

### Volume Not Persisting

```bash
# Make sure you're not using anonymous volumes
# Bad:
volumes:
  - /app/data  # Anonymous - gets deleted!

# Good:
volumes:
  - app_data:/app/data  # Named - persists

volumes:
  app_data:
```

### Bind Mount Not Updating

```bash
# On Mac/Windows, file watching might be slow
# Force refresh:
docker-compose restart

# Or use polling in your app instead of file watchers
```

---

## Security Best Practices

### 1. Principle of Least Privilege

```yaml
# Bad: Full read-write access
volumes:
  - ./sensitive:/app/data

# Good: Read-only when possible
volumes:
  - ./config:/app/config:ro
```

### 2. Avoid Mounting Sensitive Directories

```yaml
# Never do this!
volumes:
  - /:/host  # Mounts entire host filesystem
  - /var/run/docker.sock:/var/run/docker.sock  # Docker control
```

### 3. Use Secrets for Sensitive Data

```yaml
# Bad: Mount secrets as files
volumes:
  - ./secrets:/secrets

# Good: Use Docker secrets (Swarm) or env vars
secrets:
  db_password:
    external: true

services:
  app:
    secrets:
      - db_password
```

---

## Volume Commands Reference

```bash
# Create
docker volume create my-volume

# List
docker volume ls

# Inspect
docker volume inspect my-volume

# Remove
docker volume rm my-volume

# Prune unused
docker volume prune

# Copy data from volume
docker run --rm -v my-volume:/data -v $(pwd):/backup \
  ubuntu cp -r /data /backup

# Copy data to volume
docker run --rm -v my-volume:/data -v $(pwd):/backup \
  ubuntu cp -r /backup/data/* /data/
```

---

## Summary: DocAI Volumes

| Volume | Type | Purpose | Size |
|--------|------|---------|------|
| `ollama_data` | Named | Ollama models | ~5 GB |
| `chroma_data` | Named | Vector embeddings | ~100 MB |
| `./data/documents` | Bind | Document cache | Variable |
| `./data/sessions` | Bind | Chat sessions | ~1 MB |
| `./test_docs` | Bind (ro) | Sample docs | ~15 KB |

**Key Takeaway**: Named volumes for Docker-managed data (models, databases), bind mounts for development convenience (documents, configs).
