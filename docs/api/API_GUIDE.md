# DocAI REST API Guide

## Overview

The DocAI API provides HTTP endpoints for document processing and AI chat functionality. It runs alongside the CLI and provides the same features via REST API.

## Architecture: CLI vs API

```
┌─────────────────────────────────────────────────────┐
│                 Docker Compose                       │
│                                                      │
│  ┌──────────────┐          ┌──────────────────┐    │
│  │   CLI Mode   │          │    API Mode      │    │
│  │  (Profile)   │          │   (Always On)    │    │
│  │              │          │                  │    │
│  │  Terminal    │          │  HTTP Server     │    │
│  │  I/O Pipes   │          │  Port 8080       │    │
│  │  Interactive │          │  REST Endpoints  │    │
│  └──────────────┘          └──────────────────┘    │
│        │                          │                 │
│        └──────────┬───────────────┘                 │
│                   │                                 │
│         ┌─────────▼─────────┐                       │
│         │  Shared Backend   │                       │
│         │  • ChromaDB       │                       │
│         │  • Ollama         │                       │
│         │  • Core Engines   │                       │
│         └───────────────────┘                       │
└─────────────────────────────────────────────────────┘
```

**Key Difference**:
- **CLI**: Uses stdin/stdout pipes, TTY for terminal interaction
- **API**: Uses HTTP protocol, JSON requests/responses, exposed port 8080

## Quick Start

### 1. Start API Server

```bash
# Start all services including API
docker-compose up -d

# Check API is running
curl http://localhost:8080/health
```

### 2. Access API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8080/docs
- **ReDoc**: http://localhost:8080/redoc
- **OpenAPI JSON**: http://localhost:8080/openapi.json

## API Endpoints

### Health & Info

#### GET /
Root endpoint with API information.

**Response**:
```json
{
  "name": "DocAI API",
  "version": "1.0.0",
  "docs": "/docs",
  "endpoints": {
    "chat": "/chat",
    "query": "/query",
    "documents": "/documents"
  }
}
```

#### GET /health
Health check endpoint.

**Response**:
```json
{
  "status": "healthy",
  "vector_store": "connected",
  "documents_indexed": 3
}
```

---

### Chat Endpoints

#### POST /chat
Chat with AI without document context.

**Request**:
```json
{
  "message": "Hello, how are you?",
  "session_id": "optional-session-id",
  "stream": false
}
```

**Response**:
```json
{
  "response": "Hello! I'm doing well, thank you for asking...",
  "session_id": "abc-123-def"
}
```

**Streaming** (set `stream: true`):
```bash
curl -N -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Tell me a story", "stream": true}'

# Returns Server-Sent Events:
data: {"chunk": "Once", "session_id": "abc-123"}
data: {"chunk": " upon", "session_id": "abc-123"}
data: {"chunk": " a", "session_id": "abc-123"}
...
data: {"done": true, "session_id": "abc-123"}
```

---

### Document Management

#### POST /documents
Upload and index a document.

**Request** (multipart/form-data):
```bash
curl -X POST http://localhost:8080/documents \
  -F "file=@/path/to/document.pdf"
```

**Response**:
```json
{
  "doc_id": "doc-123-456",
  "file_name": "document.pdf",
  "chunks": 42
}
```

**Supported Formats**: PDF, TXT, MD, DOCX

#### GET /documents
List all indexed documents.

**Response**:
```json
{
  "total_chunks": 156,
  "unique_documents": 3,
  "document_files": [
    "machine_learning_basics.md",
    "python_best_practices.txt",
    "kubernetes_guide.md"
  ]
}
```

#### DELETE /documents
Clear all indexed documents.

**Response**:
```json
{
  "message": "All documents cleared successfully"
}
```

---

### RAG Query

#### POST /query
Query indexed documents using RAG.

**Request**:
```json
{
  "question": "What is supervised learning?",
  "stream": false
}
```

**Response**:
```json
{
  "answer": "Supervised learning is a type of machine learning...",
  "sources": [
    {
      "file": "machine_learning_basics.md",
      "chunk_index": 3
    },
    {
      "file": "machine_learning_basics.md",
      "chunk_index": 5
    }
  ]
}
```

**Streaming** (set `stream: true`):
```bash
curl -N -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Kubernetes?", "stream": true}'

# Returns Server-Sent Events
data: {"chunk": "Kubernetes"}
data: {"chunk": " is"}
data: {"chunk": " an"}
...
data: {"done": true}
```

---

### Session Management

#### DELETE /sessions/{session_id}
Delete a chat session.

**Request**:
```bash
curl -X DELETE http://localhost:8080/sessions/abc-123-def
```

**Response**:
```json
{
  "message": "Session abc-123-def deleted"
}
```

---

## Usage Examples

### Python (requests)

```python
import requests

# Upload document
with open('document.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:8080/documents',
        files={'file': f}
    )
print(response.json())

# Query documents
response = requests.post(
    'http://localhost:8080/query',
    json={'question': 'What are the main topics?', 'stream': False}
)
print(response.json()['answer'])

# Chat
response = requests.post(
    'http://localhost:8080/chat',
    json={'message': 'Hello!', 'stream': False}
)
print(response.json()['response'])
```

### JavaScript (fetch)

```javascript
// Upload document
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const uploadResponse = await fetch('http://localhost:8080/documents', {
  method: 'POST',
  body: formData
});
const docInfo = await uploadResponse.json();
console.log(docInfo);

// Query documents
const queryResponse = await fetch('http://localhost:8080/query', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    question: 'What is machine learning?',
    stream: false
  })
});
const result = await queryResponse.json();
console.log(result.answer);

// Chat
const chatResponse = await fetch('http://localhost:8080/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    message: 'Hello AI!',
    stream: false
  })
});
const chat = await chatResponse.json();
console.log(chat.response);
```

### cURL Examples

```bash
# Health check
curl http://localhost:8080/health

# Upload document
curl -X POST http://localhost:8080/documents \
  -F "file=@test_docs/machine_learning_basics.md"

# List documents
curl http://localhost:8080/documents

# Query documents
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is supervised learning?", "stream": false}'

# Chat
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Explain machine learning", "stream": false}'

# Clear all documents
curl -X DELETE http://localhost:8080/documents
```

---

## Streaming Responses

The API supports **Server-Sent Events (SSE)** for streaming responses.

### Why Streaming?

- **Better UX**: See results as they're generated
- **Lower latency**: Don't wait for complete response
- **Real-time feedback**: Know the AI is working

### How to Use

Set `"stream": true` in your request:

```python
import requests

response = requests.post(
    'http://localhost:8080/chat',
    json={'message': 'Tell me a long story', 'stream': True},
    stream=True  # Important for SSE
)

for line in response.iter_lines():
    if line:
        decoded = line.decode('utf-8')
        if decoded.startswith('data: '):
            data = json.loads(decoded[6:])
            if 'chunk' in data:
                print(data['chunk'], end='', flush=True)
            elif data.get('done'):
                print('\n[Stream complete]')
                break
```

---

## Error Handling

### HTTP Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | Success | Request completed successfully |
| 400 | Bad Request | Missing required field |
| 404 | Not Found | Session ID doesn't exist |
| 500 | Server Error | Internal processing error |
| 503 | Service Unavailable | ChromaDB not connected |

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

**Example**:
```bash
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{"question": "test"}'

# Response (400 Bad Request):
{
  "detail": "No documents indexed. Upload documents first using POST /documents"
}
```

---

## CORS Configuration

The API includes CORS middleware configured to accept all origins by default.

**For Production**, update `src/api.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specific domains
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)
```

---

## Running the API

### Option 1: Docker Compose (Recommended)

```bash
# Start API server
docker-compose up -d

# View logs
docker-compose logs -f docai-api

# Stop
docker-compose down
```

**Access**: http://localhost:8080

### Option 2: Local Development

```bash
# Install dependencies (including FastAPI)
pip install -r requirements.txt

# Run API server
uvicorn src.api:app --host 0.0.0.0 --port 8080 --reload

# With auto-reload on code changes
uvicorn src.api:app --reload
```

**Access**: http://localhost:8080

---

## CLI vs API Comparison

| Feature | CLI | API |
|---------|-----|-----|
| **Access** | Terminal only | HTTP (any client) |
| **Concurrency** | Single user | Multiple concurrent users |
| **Integration** | Scripts, automation | Web apps, mobile apps |
| **Session** | In-memory | HTTP stateless + session IDs |
| **Streaming** | Terminal output | Server-Sent Events |
| **Auth** | None | Can add JWT/API keys |
| **Use Case** | Interactive, dev | Production, integrations |

---

## Production Considerations

### 1. Authentication

Add API key or JWT authentication:

```python
from fastapi import Security, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.post("/chat")
async def chat(request: ChatRequest, token: str = Security(security)):
    # Verify token
    if not verify_token(token):
        raise HTTPException(status_code=401, detail="Invalid token")
    # ... rest of endpoint
```

### 2. Rate Limiting

Add rate limiting to prevent abuse:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/query")
@limiter.limit("10/minute")
async def query_documents(request: QueryRequest):
    # ...
```

### 3. Monitoring

Add Prometheus metrics:

```python
from prometheus_fastapi_instrumentator import Instrumentator

Instrumentator().instrument(app).expose(app)
```

### 4. Logging

Configure structured logging:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### 5. Session Storage

Replace in-memory sessions with Redis:

```python
import redis

redis_client = redis.Redis(host='redis', port=6379, db=0)

def get_session(session_id):
    data = redis_client.get(f"session:{session_id}")
    return json.loads(data) if data else None
```

---

## Testing the API

### Manual Testing

Use the interactive Swagger UI:
1. Open http://localhost:8080/docs
2. Click "Try it out" on any endpoint
3. Fill in parameters
4. Execute and see results

### Automated Testing

```bash
# Install pytest-async
pip install pytest-asyncio httpx

# Run tests
pytest tests/test_api.py
```

Example test:

```python
import pytest
from httpx import AsyncClient
from src.api import app

@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
```

---

## Future API Enhancements

See `FUTURE_FEATURES.md` for planned additions:
- WebSocket support for bi-directional streaming
- Batch document upload
- Document management (update, delete specific docs)
- Custom prompt templates
- Model selection per request
- API versioning (v2, v3)

---

## Troubleshooting

### API Not Responding

```bash
# Check if container is running
docker ps | grep docai-api

# Check logs
docker-compose logs docai-api

# Check health endpoint
curl http://localhost:8080/health
```

### Port Already in Use

```bash
# Change port in docker-compose.yml
ports:
  - "8081:8080"  # Use 8081 on host instead
```

### CORS Errors in Browser

Update CORS origins in `src/api.py`:

```python
allow_origins=["http://localhost:3000"]  # Your frontend URL
```

---

## Summary

The DocAI API provides a REST interface to all core functionality:
- ✅ Document upload and indexing
- ✅ RAG-based querying with sources
- ✅ AI chat with session management
- ✅ Streaming support via SSE
- ✅ Automatic OpenAPI documentation
- ✅ Health checks and monitoring

**Next Steps**:
1. Start the API: `docker-compose up -d`
2. Explore Swagger UI: http://localhost:8080/docs
3. Upload a document and test queries
4. Build a frontend or integrate with your apps!
