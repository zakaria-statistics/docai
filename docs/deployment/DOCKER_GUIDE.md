# Docker Deployment Guide

This guide covers running DocAI in Docker with ChromaDB server mode and Ollama containerized.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Network                        │
│  ┌──────────────┐  ┌───────────────┐  ┌──────────────┐ │
│  │    DocAI     │──│   ChromaDB    │  │    Ollama    │ │
│  │  Container   │  │    Server     │  │   Server     │ │
│  │ (Python CLI) │  │  (Port 8000)  │  │ (Port 11434) │ │
│  └──────────────┘  └───────────────┘  └──────────────┘ │
│         │                  │                  │          │
│    ┌────▼──────────────────▼──────────────────▼────┐    │
│    │          Persistent Volumes                   │    │
│    │  • ollama_data  • chroma_data  • local_data  │    │
│    └───────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

## Services

### 1. Ollama (LLM Server)
- **Image**: `ollama/ollama:latest`
- **Port**: 11434
- **Volume**: `ollama_data` (stores models)
- **Models**: llama3.1:8b, nomic-embed-text

### 2. ChromaDB (Vector Database Server)
- **Image**: `chromadb/chroma:latest`
- **Port**: 8000
- **Volume**: `chroma_data` (stores embeddings)
- **Mode**: Server mode (HTTP API)

### 3. DocAI (Application)
- **Build**: Custom Dockerfile
- **Depends on**: Ollama, ChromaDB
- **Volumes**: Local document and session storage

## Quick Start

### Step 1: Build and Start Services

```bash
docker-compose up -d
```

This will:
1. Pull Ollama and ChromaDB images
2. Build the DocAI application image
3. Create a Docker network
4. Start all services with health checks

### Step 2: Pull Ollama Models

The Ollama models need to be downloaded once:

```bash
# Pull the chat model (4.9GB)
docker exec docai-ollama ollama pull llama3.1:8b

# Pull the embedding model (274MB)
docker exec docai-ollama ollama pull nomic-embed-text
```

### Step 3: Verify Services Are Running

```bash
# Check all services are healthy
docker-compose ps

# Check Ollama models
docker exec docai-ollama ollama list

# Check ChromaDB is responding
curl http://localhost:8000/api/v1/heartbeat
```

### Step 4: Use DocAI

```bash
# Interactive mode (recommended)
docker-compose run --rm docai chat

# Add documents
docker-compose run --rm docai add /app/test_docs/machine_learning_basics.md

# Query documents
docker-compose run --rm docai query "What is supervised learning?"

# List indexed documents
docker-compose run --rm docai list

# Summarize a document
docker-compose run --rm docai summarize /app/test_docs/python_best_practices.txt --type bullet

# Extract entities
docker-compose run --rm docai extract /app/test_docs/kubernetes_guide.md
```

## Management Commands

### Start Services
```bash
docker-compose up -d
```

### Stop Services
```bash
docker-compose down
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f docai
docker-compose logs -f ollama
docker-compose logs -f chromadb
```

### Restart a Service
```bash
docker-compose restart docai
docker-compose restart chromadb
docker-compose restart ollama
```

### Rebuild DocAI After Code Changes
```bash
docker-compose build docai
docker-compose up -d docai
```

## Data Persistence

### Docker Volumes (Managed by Docker)
- `ollama_data`: Ollama models and configuration
- `chroma_data`: ChromaDB vector database

### Local Directories (Bind Mounts)
- `./data/documents`: Processed documents cache
- `./data/sessions`: Chat session history
- `./test_docs`: Sample documents (read-only)

### Backup Data
```bash
# Backup volumes
docker run --rm -v docai_ollama_data:/data -v $(pwd):/backup ubuntu tar czf /backup/ollama_backup.tar.gz /data
docker run --rm -v docai_chroma_data:/data -v $(pwd):/backup ubuntu tar czf /backup/chroma_backup.tar.gz /data

# Backup local data
tar czf data_backup.tar.gz ./data
```

### Restore Data
```bash
# Restore volumes
docker run --rm -v docai_ollama_data:/data -v $(pwd):/backup ubuntu tar xzf /backup/ollama_backup.tar.gz -C /
docker run --rm -v docai_chroma_data:/data -v $(pwd):/backup ubuntu tar xzf /backup/chroma_backup.tar.gz -C /
```

## Networking

All services are on the `docai-network` bridge network:
- Services communicate using service names as hostnames
- `docai` → `http://ollama:11434`
- `docai` → `http://chromadb:8000`

Exposed ports to host:
- `11434` → Ollama API
- `8000` → ChromaDB API

## Troubleshooting

### Services Won't Start
```bash
# Check service status
docker-compose ps

# View logs for errors
docker-compose logs

# Check health
docker inspect docai-ollama | grep Health
docker inspect docai-chromadb | grep Health
```

### Ollama Models Not Found
```bash
# Re-pull models
docker exec docai-ollama ollama pull llama3.1:8b
docker exec docai-ollama ollama pull nomic-embed-text

# Verify models
docker exec docai-ollama ollama list
```

### ChromaDB Connection Error
```bash
# Verify ChromaDB is running
curl http://localhost:8000/api/v1/heartbeat

# Check ChromaDB logs
docker-compose logs chromadb

# Restart ChromaDB
docker-compose restart chromadb
```

### DocAI Can't Connect to Services
```bash
# Verify network
docker network inspect docai_docai-network

# Test connectivity from docai container
docker-compose run --rm docai sh -c "curl http://ollama:11434/api/tags"
docker-compose run --rm docai sh -c "curl http://chromadb:8000/api/v1/heartbeat"
```

### Clear All Data and Start Fresh
```bash
# Stop services
docker-compose down

# Remove volumes
docker volume rm docai_ollama_data docai_chroma_data

# Remove local data
rm -rf ./data/vector_db ./data/documents ./data/sessions

# Start fresh
docker-compose up -d
docker exec docai-ollama ollama pull llama3.1:8b
docker exec docai-ollama ollama pull nomic-embed-text
```

## Environment Variables

Docker Compose sets these automatically (see `.env.docker`):

| Variable | Value | Description |
|----------|-------|-------------|
| `OLLAMA_BASE_URL` | `http://ollama:11434` | Ollama server URL |
| `CHROMA_HOST` | `chromadb` | ChromaDB server hostname |
| `CHROMA_PORT` | `8000` | ChromaDB server port |
| `OLLAMA_CHAT_MODEL` | `llama3.1:8b` | Chat model name |
| `OLLAMA_EMBEDDING_MODEL` | `nomic-embed-text` | Embedding model |

## Local Development vs Docker

### Run Locally (Embedded ChromaDB)
```bash
# Don't set CHROMA_HOST - uses embedded mode
python3 -m src.main chat
```

### Run in Docker (ChromaDB Server)
```bash
# CHROMA_HOST is set in docker-compose.yml
docker-compose run --rm docai chat
```

The code automatically detects the mode based on `CHROMA_HOST` environment variable.

## Resource Usage

Typical resource consumption:
- **Ollama**: 4-8 GB RAM (during inference)
- **ChromaDB**: 100-500 MB RAM
- **DocAI**: 100-200 MB RAM
- **Disk**: ~5 GB for models + vector data

## Advanced: Kubernetes Deployment

Want to deploy to Kubernetes? See `KUBERNETES_GUIDE.md` (coming soon).

## Tips

1. **First Time Setup**: Pulling Ollama models takes time (5-10 minutes)
2. **Development**: Rebuild only when you change Python code
3. **Performance**: ChromaDB server mode is faster than embedded for concurrent access
4. **Scaling**: Can run multiple DocAI instances sharing same ChromaDB/Ollama
5. **Production**: Add nginx reverse proxy, authentication, rate limiting

## Next Steps

1. Try adding your own documents
2. Experiment with different summary types
3. Test the RAG query system
4. Explore the ChromaDB API directly (http://localhost:8000/docs)
5. Monitor resource usage with `docker stats`
