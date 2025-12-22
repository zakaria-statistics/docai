# API Quick Start Guide

## How the Terminal/CLI Interaction Works

### CLI Mode (Direct I/O Piping)

When you run `docker-compose run --rm docai chat`, here's what happens:

```
Your Terminal
      │
      │ stdio pipes (NO network protocol)
      │ stdin/stdout/stderr directly connected
      │
      ▼
┌─────────────────────┐
│  Docker Container   │
│                     │
│  Python Process     │
│  ├─ stdin  ◄────────┼─── Your keyboard
│  ├─ stdout ─────────┼──► Your screen
│  └─ stderr ─────────┼──► Error messages
└─────────────────────┘
```

**Key Points**:
- **No HTTP/TCP** - Direct file descriptor mapping
- **TTY mode**: `tty: true` + `stdin_open: true` in docker-compose.yml
- **Interactive**: Docker transparently connects your terminal to the container
- **Feels local**: Exactly like running `python3 -m src.main chat` locally

### API Mode (HTTP Protocol)

When you access `http://localhost:8080/chat`:

```
Your Browser/curl
      │
      │ HTTP/TCP (network protocol)
      │ Port 8080
      │
      ▼
┌─────────────────────┐
│  Docker Container   │
│                     │
│  FastAPI Server     │
│  ├─ Port 8080       │
│  ├─ HTTP Handlers   │
│  └─ JSON Responses  │
└─────────────────────┘
```

**Key Points**:
- **HTTP protocol**: JSON requests/responses
- **Port exposed**: 8080:8080 in docker-compose.yml
- **Stateless**: Each request is independent
- **Multi-user**: Multiple clients can connect

---

## Quick Start

### 1. Start Services

```bash
# Build and start all services
docker-compose up -d

# Pull Ollama models (first time only)
docker exec docai-ollama ollama pull llama3.1:8b
docker exec docai-ollama ollama pull nomic-embed-text
```

### 2. Check API is Running

```bash
# Using Makefile
make api-health

# Or directly
curl http://localhost:8080/health
```

Expected output:
```json
{
  "status": "healthy",
  "vector_store": "connected",
  "documents_indexed": 0
}
```

### 3. Access Interactive Documentation

Open in your browser:
- **Swagger UI**: http://localhost:8080/docs
- **ReDoc**: http://localhost:8080/redoc

---

## Basic Usage Examples

### Upload a Document

```bash
curl -X POST http://localhost:8080/documents \
  -F "file=@test_docs/machine_learning_basics.md"
```

Response:
```json
{
  "doc_id": "doc-abc-123",
  "file_name": "machine_learning_basics.md",
  "chunks": 15
}
```

### Query Documents

```bash
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is supervised learning?",
    "stream": false
  }'
```

Response:
```json
{
  "answer": "Supervised learning is a type of machine learning...",
  "sources": [
    {
      "file": "machine_learning_basics.md",
      "chunk_index": 3
    }
  ]
}
```

### Chat

```bash
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Explain machine learning simply",
    "stream": false
  }'
```

Response:
```json
{
  "response": "Machine learning is a way for computers to learn...",
  "session_id": "session-xyz-789"
}
```

### List Documents

```bash
curl http://localhost:8080/documents
```

Response:
```json
{
  "total_chunks": 15,
  "unique_documents": 1,
  "document_files": [
    "machine_learning_basics.md"
  ]
}
```

---

## Architecture Comparison

### Services

```
docker-compose.yml defines 4 services:

1. ollama        - LLM server (port 11434)
2. chromadb      - Vector database (port 8000)
3. docai         - CLI interface (no port, profile: cli)
4. docai-api     - HTTP API (port 8080)
```

### Current Setup

```
┌──────────────────────────────────────────────┐
│         Docker Network (docai-network)        │
│                                               │
│  ┌──────────┐                                 │
│  │ Ollama   │◄───┐                           │
│  │:11434    │    │                           │
│  └──────────┘    │                           │
│                  │                           │
│  ┌──────────┐    │    ┌──────────────┐      │
│  │ChromaDB  │◄───┼────│  DocAI API   │      │
│  │:8000     │    │    │  :8080       │◄─────┼─── HTTP Clients
│  └──────────┘    │    └──────────────┘      │
│                  │                           │
│  ┌──────────┐    │                           │
│  │DocAI CLI │◄───┘                           │
│  │(profile) │        Terminal via            │
│  └──────────┘        stdio pipes             │
│                                               │
└──────────────────────────────────────────────┘
```

---

## CLI vs API Usage

| Task | CLI Command | API Endpoint |
|------|-------------|--------------|
| **Chat** | `docker-compose run --rm docai chat` | `POST /chat` |
| **Upload** | `docker-compose run --rm docai add file.pdf` | `POST /documents` |
| **Query** | `docker-compose run --rm docai query "..."` | `POST /query` |
| **List** | `docker-compose run --rm docai list` | `GET /documents` |

---

## Makefile Shortcuts

```bash
# Infrastructure
make up              # Start all services
make down            # Stop all services
make logs            # View all logs
make pull-models     # Download Ollama models

# CLI
make chat            # Interactive chat
make add FILE=/app/test_docs/file.md
make query Q="What is ML?"
make list            # List documents

# API
make api-health      # Check API status
make api-logs        # View API logs
make api-docs        # Open Swagger UI
make api-test        # Test API endpoints
```

---

## Testing the Complete Flow

### 1. Upload Documents (API)

```bash
curl -X POST http://localhost:8080/documents \
  -F "file=@test_docs/machine_learning_basics.md"

curl -X POST http://localhost:8080/documents \
  -F "file=@test_docs/python_best_practices.txt"

curl -X POST http://localhost:8080/documents \
  -F "file=@test_docs/kubernetes_guide.md"
```

### 2. Verify Upload (CLI)

```bash
docker-compose run --rm docai list
```

### 3. Query via API

```bash
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are Python naming conventions?",
    "stream": false
  }' | python3 -m json.tool
```

### 4. Query via CLI

```bash
docker-compose run --rm docai query "What is a Kubernetes Pod?"
```

**Both access the same ChromaDB!** Documents indexed via API are available in CLI and vice versa.

---

## Streaming Example

### CLI (Terminal Streaming)

```bash
docker-compose run --rm docai chat
# Type: "Tell me a story"
# Output appears token by token in real-time
```

### API (Server-Sent Events)

```python
import requests
import json

response = requests.post(
    'http://localhost:8080/chat',
    json={'message': 'Tell me a story', 'stream': True},
    stream=True
)

for line in response.iter_lines():
    if line:
        decoded = line.decode('utf-8')
        if decoded.startswith('data: '):
            data = json.loads(decoded[6:])
            if 'chunk' in data:
                print(data['chunk'], end='', flush=True)
            elif data.get('done'):
                print('\n[Complete]')
                break
```

---

## Next Steps

1. **Explore API Docs**: http://localhost:8080/docs
2. **Upload your documents**: Try PDFs, Word docs, text files
3. **Build a frontend**: React/Vue app consuming the API
4. **Check roadmap**: See `FUTURE_FEATURES.md`

---

## Troubleshooting

### API Not Responding

```bash
# Check if container is running
docker ps | grep docai-api

# View logs
docker-compose logs docai-api

# Restart
docker-compose restart docai-api
```

### Port 8080 Already in Use

Edit `docker-compose.yml`:
```yaml
docai-api:
  ports:
    - "8081:8080"  # Use 8081 instead
```

### CLI Terminal Not Interactive

Make sure docker-compose.yml has:
```yaml
docai:
  stdin_open: true
  tty: true
```

---

## Summary

✅ **CLI**: Direct I/O pipes, terminal interaction, single-user
✅ **API**: HTTP protocol, port 8080, multi-user, web/mobile ready
✅ **Both**: Share same backend (ChromaDB, Ollama, core engines)
✅ **Flexible**: Use whichever interface suits your needs!
