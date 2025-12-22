# DocAI System Architecture

## Table of Contents
1. [Overview](#overview)
2. [High-Level Architecture](#high-level-architecture)
3. [Component Architecture](#component-architecture)
4. [Data Flow](#data-flow)
5. [Module Breakdown](#module-breakdown)
6. [Deployment Architectures](#deployment-architectures)
7. [Technology Stack](#technology-stack)
8. [Sequence Diagrams](#sequence-diagrams)

---

## Overview

DocAI is an AI-powered document processing and chat CLI application that enables:
- Interactive chat with LLMs
- Document indexing and RAG-based querying
- Document summarization
- Entity and keyword extraction

**Core Technologies**: Python, LangChain, ChromaDB, Ollama

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        DocAI CLI Application                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌───────────────┐   ┌──────────────┐   ┌──────────────────┐   │
│  │  CLI Layer    │   │  Core Layer  │   │  Integration     │   │
│  │  (Click)      │──▶│  (Engines)   │──▶│  Layer           │   │
│  │  - Commands   │   │  - Chat      │   │  - Vector Store  │   │
│  │  - Prompts    │   │  - RAG       │   │  - LLM           │   │
│  │  - Formatters │   │  - Summarize │   │  - Embeddings    │   │
│  └───────────────┘   │  - Extract   │   └──────────────────┘   │
│                       └──────────────┘                           │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Data Processing Pipeline                     │   │
│  │  Document → Loader → Chunker → Embedder → Vector Store   │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
└───────────────────────────────────┬─────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
         ┌──────────▼──────────┐       ┌───────────▼──────────┐
         │   Vector Database   │       │    LLM Service       │
         │   (ChromaDB)        │       │    (Ollama)          │
         │                     │       │                      │
         │  • Embeddings       │       │  • Chat Model        │
         │  • Similarity       │       │  • Embedding Model   │
         │    Search           │       │  • Streaming         │
         └─────────────────────┘       └──────────────────────┘
```

---

## Component Architecture

### 1. CLI Layer (`src/cli/`)

**Responsibility**: User interaction and command handling

```
cli/
├── commands.py      → CLI command definitions
├── formatters.py    → Output formatting (Rich)
└── prompts.py       → User input handling
```

**Key Features**:
- Click-based command routing
- Rich terminal formatting
- Interactive prompts
- Error handling and user feedback

---

### 2. Core Processing Layer (`src/core/`)

**Responsibility**: Business logic and AI operations

```
core/
├── chat_engine.py         → General chat without context
├── rag_engine.py          → RAG query over documents
├── summarizer.py          → Document summarization
├── extractor.py           → Entity/keyword extraction
├── document_processor.py  → Document loading orchestration
└── session_manager.py     → Chat session persistence
```

**Architecture Pattern**: Engine-based services

```
┌──────────────────────────────────────────────────┐
│              Core Engines                         │
├──────────────────────────────────────────────────┤
│                                                   │
│  ChatEngine          RAGEngine                   │
│  ┌──────────┐       ┌──────────┐                │
│  │ Session  │       │ Retriever│                 │
│  │ History  │       │ Context  │                 │
│  │ LLM Call │       │ LLM Call │                 │
│  └──────────┘       └──────────┘                 │
│                                                   │
│  Summarizer         Extractor                    │
│  ┌──────────┐       ┌──────────┐                │
│  │ Load Doc │       │ Load Doc │                 │
│  │ Prompt   │       │ Prompt   │                 │
│  │ LLM Call │       │ Parse    │                 │
│  └──────────┘       └──────────┘                 │
└───────────────────────────────────────────────────┘
```

---

### 3. Document Loaders (`src/loaders/`)

**Responsibility**: Extract text from various file formats

```
loaders/
├── base_loader.py    → Abstract base class
├── pdf_loader.py     → PDF extraction (pdfplumber + pypdf)
├── text_loader.py    → TXT/MD files (multi-encoding)
└── docx_loader.py    → Word documents (python-docx)
```

**Pattern**: Strategy Pattern with polymorphic loaders

```
┌─────────────────────────────────────────┐
│         BaseLoader (Abstract)           │
│  + extract_text() → str                 │
│  + load() → Document                    │
└───────────┬─────────────────────────────┘
            │
    ┌───────┴───────┬─────────────┐
    │               │             │
┌───▼────┐   ┌──────▼───┐  ┌─────▼─────┐
│  PDF   │   │   Text   │  │   DOCX    │
│ Loader │   │  Loader  │  │  Loader   │
└────────┘   └──────────┘  └───────────┘
```

---

### 4. Vector Store Layer (`src/vector_store/`)

**Responsibility**: Embedding generation and vector search

```
vector_store/
├── chroma_store.py    → ChromaDB client wrapper
└── embeddings.py      → Ollama embedding service
```

**Dual-Mode Architecture**:

```
ChromaVectorStore
    │
    ├─ if CHROMA_HOST set:
    │     HttpClient (Server Mode)
    │     └─> ChromaDB Server (Docker)
    │
    └─ else:
          PersistentClient (Embedded Mode)
          └─> Local File Storage (./data/vector_db/)
```

---

### 5. Models (`src/models/`)

**Responsibility**: Data structures and domain models

```
models/
├── document.py      → Document, DocumentChunk
├── chat.py          → ChatSession, ChatMessage
└── extraction.py    → ExtractionResult, Entity
```

**Data Model Hierarchy**:

```
Document
├── doc_id: str
├── file_path: Path
├── content: str
├── metadata: dict
├── chunks: List[DocumentChunk]
└── word_count: int

DocumentChunk
├── chunk_id: str
├── text: str
├── chunk_index: int
└── source_file: str

ChatSession
├── session_id: str
├── messages: List[ChatMessage]
├── created_at: datetime
└── updated_at: datetime
```

---

### 6. Utilities (`src/utils/`)

**Responsibility**: Configuration, chunking, validation

```
utils/
├── config.py        → Environment-based configuration
├── chunking.py      → Text chunking with overlap
└── validators.py    → File validation
```

---

## Data Flow

### RAG Query Flow

```
1. User Query
   │
   ▼
2. Generate Query Embedding
   │  (nomic-embed-text via Ollama)
   ▼
3. Similarity Search in ChromaDB
   │  (returns top-K chunks)
   ▼
4. Build Context from Retrieved Chunks
   │
   ▼
5. Create RAG Prompt
   │  Context: [retrieved chunks]
   │  Question: [user query]
   ▼
6. LLM Generation
   │  (llama3.1:8b via Ollama)
   ▼
7. Stream Response to User
```

### Document Indexing Flow

```
1. User: docai add document.pdf
   │
   ▼
2. File Validation
   │  (size, format, existence)
   ▼
3. Select Loader (PDF/TXT/DOCX)
   │
   ▼
4. Extract Text
   │  (format-specific extraction)
   ▼
5. Text Chunking
   │  (800 tokens, 150 overlap)
   ▼
6. Generate Embeddings
   │  (batch embed via nomic-embed-text)
   ▼
7. Store in ChromaDB
   │  (vectors + metadata + text)
   ▼
8. Confirm to User
```

### Chat Flow

```
1. User Message
   │
   ▼
2. Add to Session History
   │
   ▼
3. Build Conversation Prompt
   │  (last N messages)
   ▼
4. LLM Streaming Call
   │  (llama3.1:8b)
   ▼
5. Stream Chunks to Terminal
   │  (yield each token)
   ▼
6. Save Assistant Response
   │
   ▼
7. Ready for Next Message
```

---

## Module Breakdown

### Directory Structure

```
llm-dir/
├── src/
│   ├── main.py                    # CLI entry point
│   │
│   ├── cli/                       # User Interface Layer
│   │   ├── commands.py            # Click command definitions
│   │   ├── formatters.py          # Rich formatting utilities
│   │   └── prompts.py             # Interactive input
│   │
│   ├── core/                      # Business Logic Layer
│   │   ├── chat_engine.py         # Stateful chat sessions
│   │   ├── rag_engine.py          # Retrieval augmented generation
│   │   ├── summarizer.py          # Document summarization
│   │   ├── extractor.py           # Entity extraction
│   │   ├── document_processor.py  # Document loading facade
│   │   └── session_manager.py     # Session persistence
│   │
│   ├── loaders/                   # Data Ingestion Layer
│   │   ├── base_loader.py         # Abstract loader interface
│   │   ├── pdf_loader.py          # PDF parsing
│   │   ├── text_loader.py         # TXT/MD parsing
│   │   └── docx_loader.py         # Word doc parsing
│   │
│   ├── models/                    # Domain Models
│   │   ├── document.py            # Document entities
│   │   ├── chat.py                # Chat entities
│   │   └── extraction.py          # Extraction entities
│   │
│   ├── vector_store/              # Data Persistence Layer
│   │   ├── chroma_store.py        # Vector DB client
│   │   └── embeddings.py          # Embedding service
│   │
│   └── utils/                     # Cross-Cutting Concerns
│       ├── config.py              # Configuration management
│       ├── chunking.py            # Text splitting
│       └── validators.py          # Input validation
│
├── data/                          # Runtime Data
│   ├── documents/                 # Cached documents
│   ├── vector_db/                 # ChromaDB (embedded mode)
│   └── sessions/                  # Chat sessions
│
├── tests/                         # Test Suite
├── test_docs/                     # Sample documents
│
├── docker-compose.yml             # Container orchestration
├── Dockerfile                     # App container definition
├── requirements.txt               # Python dependencies
├── .env                           # Local configuration
├── .env.docker                    # Docker configuration
└── Makefile                       # Build shortcuts
```

---

## Deployment Architectures

### Local Development Mode

```
┌──────────────────────────────────────────────┐
│          Local Machine                        │
│                                               │
│  ┌────────────────────────────────┐          │
│  │  DocAI Python Process          │          │
│  │                                 │          │
│  │  ┌──────────────────────────┐  │          │
│  │  │  Embedded ChromaDB       │  │          │
│  │  │  (PersistentClient)      │  │          │
│  │  │  ./data/vector_db/       │  │          │
│  │  └──────────────────────────┘  │          │
│  │                                 │          │
│  │  HTTP → http://localhost:11434 │          │
│  └───────────────┬─────────────────┘          │
│                  │                             │
│                  ▼                             │
│  ┌──────────────────────────────┐             │
│  │  Ollama Service              │             │
│  │  (Running locally)           │             │
│  │  • llama3.1:8b               │             │
│  │  • nomic-embed-text          │             │
│  └──────────────────────────────┘             │
└──────────────────────────────────────────────┘

Launch: python3 -m src.main chat
```

---

### Docker Deployment Mode

```
┌───────────────────────────────────────────────────────────┐
│                Docker Host (k8s01)                         │
│                                                            │
│  ┌────────────────────────────────────────────────────┐   │
│  │         docai-network (bridge)                     │   │
│  │                                                     │   │
│  │  ┌──────────────┐  ┌──────────────┐ ┌───────────┐ │   │
│  │  │   DocAI      │  │  ChromaDB    │ │  Ollama   │ │   │
│  │  │  Container   │  │   Server     │ │  Server   │ │   │
│  │  │              │  │              │ │           │ │   │
│  │  │  Python CLI  │→ │  Port: 8000  │ │Port:11434 │ │   │
│  │  │              │  │              │ │           │ │   │
│  │  │  Env:        │  │  HTTP API    │ │  HTTP API │ │   │
│  │  │  CHROMA_HOST │  │              │ │           │ │   │
│  │  │  =chromadb   │  │              │ │           │ │   │
│  │  └──────────────┘  └──────────────┘ └───────────┘ │   │
│  │         │                 │               │        │   │
│  └─────────┼─────────────────┼───────────────┼────────┘   │
│            │                 │               │            │
│  ┌─────────▼─────┐ ┌─────────▼─────┐ ┌──────▼────────┐   │
│  │ Volume:       │ │ Volume:       │ │ Volume:       │   │
│  │ ./data/docs   │ │ chroma_data   │ │ ollama_data   │   │
│  │ ./data/sess   │ │               │ │               │   │
│  └───────────────┘ └───────────────┘ └───────────────┘   │
└───────────────────────────────────────────────────────────┘

Launch: docker-compose run --rm docai chat
```

**Key Differences**:
- **Networking**: Service discovery via DNS (chromadb, ollama)
- **ChromaDB Mode**: HttpClient (server) vs PersistentClient (embedded)
- **Isolation**: Each service in separate container
- **Persistence**: Named volumes for DB, bind mounts for documents
- **Health Checks**: Automatic restart on failure

---

### Future: Kubernetes Deployment

```
┌────────────────────────────────────────────────────────┐
│              Kubernetes Cluster                         │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │          Namespace: docai                       │   │
│  │                                                  │   │
│  │  ┌──────────────────────────────────────────┐   │   │
│  │  │  Deployment: docai-app (replicas: 3)    │   │   │
│  │  │  ┌─────┐  ┌─────┐  ┌─────┐              │   │   │
│  │  │  │ Pod │  │ Pod │  │ Pod │              │   │   │
│  │  │  └──┬──┘  └──┬──┘  └──┬──┘              │   │   │
│  │  └─────┼────────┼────────┼─────────────────┘   │   │
│  │        └────────┴────────┘                      │   │
│  │                 │                               │   │
│  │  ┌──────────────▼───────────────────────────┐  │   │
│  │  │  Service: chromadb-service              │  │   │
│  │  │  ClusterIP: chromadb.docai.svc          │  │   │
│  │  └──────────────┬───────────────────────────┘  │   │
│  │                 │                               │   │
│  │  ┌──────────────▼───────────────────────────┐  │   │
│  │  │  StatefulSet: chromadb (replicas: 1)    │  │   │
│  │  │  ┌──────┐                                │  │   │
│  │  │  │ Pod  │ ← PVC (chroma-data)           │  │   │
│  │  │  └──────┘                                │  │   │
│  │  └──────────────────────────────────────────┘  │   │
│  │                                                 │   │
│  │  ┌──────────────────────────────────────────┐  │   │
│  │  │  Service: ollama-service                │  │   │
│  │  │  ClusterIP: ollama.docai.svc            │  │   │
│  │  └──────────────┬───────────────────────────┘  │   │
│  │                 │                               │   │
│  │  ┌──────────────▼───────────────────────────┐  │   │
│  │  │  Deployment: ollama (replicas: 1)       │  │   │
│  │  │  ┌──────┐                                │  │   │
│  │  │  │ Pod  │ ← PVC (ollama-models)         │  │   │
│  │  │  └──────┘                                │  │   │
│  │  └──────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────┘
```

---

## Technology Stack

### Core Technologies

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Runtime** | Python | 3.10+ | Application runtime |
| **LLM Framework** | LangChain | 0.1.0 | LLM orchestration |
| **Vector DB** | ChromaDB | 0.4.22 | Embedding storage |
| **LLM Server** | Ollama | Latest | Local LLM inference |
| **CLI Framework** | Click | 8.1.7 | Command-line interface |
| **UI Library** | Rich | 13.7.0 | Terminal formatting |

### Document Processing

| Library | Purpose |
|---------|---------|
| pypdf | PDF text extraction |
| pdfplumber | Enhanced PDF parsing |
| python-docx | Word document processing |
| tiktoken | Token counting |

### Data & Config

| Library | Purpose |
|---------|---------|
| pydantic | Data validation |
| python-dotenv | Environment config |
| sentence-transformers | Embedding support |

### Containerization

| Tool | Purpose |
|------|---------|
| Docker | Container runtime |
| Docker Compose | Multi-container orchestration |
| (Future) Kubernetes | Production orchestration |

---

## Sequence Diagrams

### 1. Document Addition

```
User          CLI         DocProcessor    Loader      Chunker     Embedder    ChromaDB
 │             │               │            │            │           │           │
 │─add file───▶│               │            │            │           │           │
 │             │──validate────▶│            │            │           │           │
 │             │               │──select────▶│           │           │           │
 │             │               │            │──extract──▶│           │           │
 │             │               │◀──text─────│            │           │           │
 │             │               │────chunk───────────────▶│           │           │
 │             │               │◀──chunks────────────────│           │           │
 │             │               │────embed─────────────────────────▶  │           │
 │             │               │◀──vectors────────────────────────── │           │
 │             │               │────store──────────────────────────────────────▶ │
 │             │◀──Document────│            │            │           │           │
 │◀─success────│               │            │            │           │           │
```

### 2. RAG Query

```
User        CLI       RAGEngine    Embedder    ChromaDB      LLM       Output
 │           │            │           │            │          │          │
 │──query───▶│            │           │            │          │          │
 │           │──execute──▶│           │            │          │          │
 │           │            │──embed───▶│            │          │          │
 │           │            │◀─vector───│            │          │          │
 │           │            │──search──────────────▶ │          │          │
 │           │            │◀─chunks────────────────│          │          │
 │           │            │──build context─────────│          │          │
 │           │            │──generate────────────────────────▶│          │
 │           │            │◀─stream tokens────────────────────│          │
 │           │            │──format──────────────────────────────────────▶│
 │◀──────────────────────────────────────────────────────────────────────│
```

### 3. Chat Session

```
User       CLI      ChatEngine    Session    LLM      Terminal
 │          │           │            │        │           │
 │─message─▶│           │            │        │           │
 │          │──chat────▶│            │        │           │
 │          │           │──save msg─▶│        │           │
 │          │           │◀──history──│        │           │
 │          │           │──build prompt       │           │
 │          │           │──invoke────────────▶│           │
 │          │           │◀──stream────────────│           │
 │          │           │──format─────────────────────────▶│
 │          │           │──save reply───────▶ │           │
 │◀─────────────────────────────────────────────────────── │
```

---

## Design Patterns Used

### 1. **Strategy Pattern**
- Document loaders (PDF, TXT, DOCX)
- Different loading strategies for different formats

### 2. **Factory Pattern**
- `DocumentProcessor.load_document()` selects appropriate loader
- Based on file extension

### 3. **Singleton Pattern**
- Global instances: `config`, `vector_store`, `embedding_service`
- Single shared instance across application

### 4. **Adapter Pattern**
- ChromaDB wrapper adapts HttpClient/PersistentClient
- Unified interface for different modes

### 5. **Template Method**
- BaseLoader defines extraction flow
- Subclasses implement `extract_text()`

### 6. **Repository Pattern**
- ChromaVectorStore abstracts vector database operations
- Clean separation from business logic

---

## Configuration Management

### Environment-Based Config

```python
# config.py - Single source of truth
config = Config.from_env()

# Automatically detects:
# - Local mode: No CHROMA_HOST → Embedded ChromaDB
# - Docker mode: CHROMA_HOST set → Server mode
```

### Config Hierarchy

```
1. Default values (in Config class)
   ↓
2. .env file (dotenv)
   ↓
3. Environment variables (highest priority)
   ↓
4. Docker Compose env section (Docker mode)
```

---

## Error Handling Strategy

### Layers of Error Handling

1. **Validation Layer** (utils/validators.py)
   - File existence, size, format
   - Fail fast before processing

2. **Business Logic Layer** (core/)
   - Try/except with specific exceptions
   - Graceful degradation

3. **CLI Layer** (cli/)
   - User-friendly error messages
   - Rich formatting for errors

4. **Integration Layer** (vector_store/, loaders/)
   - Handle external service failures
   - Retry logic for transient errors

---

## Performance Considerations

### Chunking Strategy
- **Size**: 800 tokens (balance between context and retrieval)
- **Overlap**: 150 tokens (prevent context loss at boundaries)

### Embedding Batch Processing
- Batch embed multiple chunks together
- Reduces API calls to Ollama

### Streaming Responses
- Stream LLM tokens as generated
- Better user experience (perceived performance)

### Connection Pooling
- Reuse HTTP connections to Ollama/ChromaDB
- Reduce connection overhead

---

## Security Considerations

### Current Implementation
- Local-only deployment (no external exposure)
- Environment-based secrets (.env)
- No authentication (single-user CLI)

### Production Recommendations
- Add API authentication
- Rate limiting
- Input sanitization
- Secrets management (Vault, K8s Secrets)
- Network policies (Kubernetes)
- TLS/SSL for inter-service communication

---

## Scalability

### Current Bottlenecks
1. **Ollama**: Single instance, GPU-bound
2. **ChromaDB**: Single instance in Docker
3. **CLI**: Single-user, not concurrent

### Scaling Options

#### Horizontal Scaling
```
┌──────────┐  ┌──────────┐  ┌──────────┐
│  DocAI   │  │  DocAI   │  │  DocAI   │
│Instance 1│  │Instance 2│  │Instance 3│
└────┬─────┘  └────┬─────┘  └────┬─────┘
     │             │             │
     └─────────────┼─────────────┘
                   │
        ┌──────────▼──────────┐
        │   Load Balancer     │
        └──────────┬──────────┘
                   │
     ┌─────────────┼─────────────┐
     │             │             │
┌────▼─────┐  ┌───▼──────┐  ┌───▼──────┐
│ChromaDB  │  │ Ollama   │  │  Cache   │
│ Cluster  │  │ Pool     │  │  (Redis) │
└──────────┘  └──────────┘  └──────────┘
```

#### Vertical Scaling
- Larger GPU for Ollama
- More RAM for ChromaDB
- SSD storage for vectors

---

## Future Enhancements

### Planned Features
1. **Multi-user Support**: Session management per user
2. **API Server**: REST API wrapper around CLI
3. **Web UI**: Browser-based interface
4. **Advanced RAG**: Re-ranking, hybrid search
5. **Model Fine-tuning**: Custom embeddings
6. **Monitoring**: Prometheus metrics, Grafana dashboards
7. **Kubernetes Manifests**: Production-ready deployment

### Architecture Evolution

```
Current: Monolithic CLI
         ↓
Phase 2: API + CLI + Web UI
         ↓
Phase 3: Microservices
         ↓
Phase 4: Multi-tenant SaaS
```

---

## Conclusion

DocAI demonstrates a well-structured, modular architecture suitable for:
- **Local development**: Embedded mode, fast iteration
- **Docker deployment**: Isolated services, easy distribution
- **Production scaling**: Ready for Kubernetes, horizontal scaling

The architecture emphasizes:
- **Separation of concerns**: Clear layer boundaries
- **Flexibility**: Multiple deployment modes
- **Extensibility**: Easy to add new document types, engines
- **Maintainability**: Clean code, type hints, documentation

---

## References

- **LangChain Docs**: https://python.langchain.com/
- **ChromaDB Docs**: https://docs.trychroma.com/
- **Ollama Docs**: https://ollama.ai/docs
- **Docker Compose**: https://docs.docker.com/compose/
- **Click Framework**: https://click.palletsprojects.com/
