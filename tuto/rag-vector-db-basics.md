# RAG & Vector DB Basics

## The Flow (30-second version)

```
Document → Chunks → Embeddings → Vector DB → Query → Similar Chunks → LLM → Answer
```

---

## Step-by-Step

### 1. Document Ingestion
```
PDF/TXT/MD → Parse text → Split into chunks (800 tokens each)
```
**Why split?** LLMs have context limits. Smaller chunks = precise retrieval.

### 2. Embedding (Text → Numbers)
```
"Kubernetes is a container orchestrator"
        ↓ (Ollama: nomic-embed-text)
[0.23, -0.45, 0.67, 0.12, ...] (768 numbers)
```
**What is embedding?** Text converted to a vector (list of numbers). Similar texts = similar vectors.

### 3. Storage (Vector DB)
```
ChromaDB stores:
├── Chunk ID: abc123
├── Text: "Kubernetes is a container..."
├── Vector: [0.23, -0.45, ...]
└── Metadata: {source: "k8s_guide.md", page: 1}
```

### 4. Query (User asks question)
```
"What is K8s?" → embed → [0.21, -0.44, ...] → search similar vectors
```

### 5. Retrieval (Find similar chunks)
```
Query vector ←→ Compare all stored vectors
        ↓
Top 5 most similar chunks returned
```
**How?** Cosine similarity (angle between vectors).

### 6. Generation (LLM answers)
```
Prompt = "Answer based on this context: [retrieved chunks]"
        ↓
LLM (llama3.1:8b) generates answer
```

---

## Key Components

| Component | Role | In DocAI |
|-----------|------|----------|
| **Embedder** | Text → Vectors | Ollama (nomic-embed-text) |
| **Vector DB** | Store & search vectors | ChromaDB |
| **LLM** | Generate answers | Ollama (llama3.1:8b) |
| **Chunker** | Split documents | LangChain (800 tokens) |

---

## ChromaDB Structure

```
ChromaDB Server
└── Tenant: default_tenant
    └── Collection: docai_documents
        ├── Document 1
        │   ├── Chunk 1 (text + vector + metadata)
        │   ├── Chunk 2
        │   └── Chunk N
        └── Document 2
            └── ...
```

**Tenant**: Namespace for isolation (multi-user scenarios)
**Collection**: Group of related documents
**Chunk**: Single searchable unit with embedding

---

## RAG vs Fine-tuning

| RAG | Fine-tuning |
|-----|-------------|
| Add docs anytime | Retrain model |
| No GPU needed | Expensive |
| Dynamic knowledge | Static after training |
| DocAI uses this | Not used here |

---

## Visual Flow

```
┌─────────────┐
│   User      │
│  uploads    │
│   PDF       │
└──────┬──────┘
       ▼
┌─────────────┐
│   Chunk     │  "Split into 10 pieces"
│   Text      │
└──────┬──────┘
       ▼
┌─────────────┐
│   Ollama    │  "Convert to vectors"
│  Embedding  │
└──────┬──────┘
       ▼
┌─────────────┐
│  ChromaDB   │  "Store vectors"
│   Store     │
└─────────────┘

       ... later ...

┌─────────────┐
│   User      │
│   asks      │  "What is K8s?"
│  question   │
└──────┬──────┘
       ▼
┌─────────────┐
│   Ollama    │  "Embed question"
│  Embedding  │
└──────┬──────┘
       ▼
┌─────────────┐
│  ChromaDB   │  "Find similar chunks"
│   Search    │
└──────┬──────┘
       ▼
┌─────────────┐
│   Ollama    │  "Generate answer from chunks"
│    LLM      │
└──────┬──────┘
       ▼
┌─────────────┐
│   Answer    │  "Kubernetes is..."
└─────────────┘
```

---

## Quick Commands

```bash
# Add document (creates chunks + embeddings)
docker compose --profile cli run --rm docai add /app/test_docs/file.md

# List indexed documents
docker compose --profile cli run --rm docai list

# Query (search + LLM answer)
docker compose --profile cli run --rm docai query "your question"

# Check ChromaDB collections
curl http://localhost:8000/api/v1/collections
```

---

## TL;DR

1. **Chunk** your docs
2. **Embed** chunks to vectors
3. **Store** in vector DB
4. **Search** by similarity when queried
5. **Generate** answer with retrieved context

That's RAG.
