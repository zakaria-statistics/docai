# DocAI - AI-Powered Document Processing CLI

A command-line tool for chatting with AI and processing documents using Ollama running locally. Built with Python, LangChain, and ChromaDB.

## Features

- **Chat Mode**: Interactive AI chat without document context
- **RAG Q&A**: Ask questions over your indexed documents
- **Document Summarization**: Generate concise or detailed summaries
- **Information Extraction**: Extract entities, keywords, and key points
- **Multiple Format Support**: PDF, TXT, MD, and DOCX files

## Technology Stack

- **LLM**: Ollama (llama3.1:8b)
- **Embeddings**: nomic-embed-text
- **Vector Store**: ChromaDB
- **Framework**: LangChain
- **CLI**: Click + Rich

## Prerequisites

- Python 3.10+
- Ollama installed and running
- Required Ollama models:
  - `llama3.1:8b` (chat model)
  - `nomic-embed-text` (embedding model)

## Installation

### 1. Clone or navigate to the project directory

```bash
cd /home/zack/llm-dir
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Verify Ollama models are installed

```bash
ollama list
```

If the models aren't installed, pull them:

```bash
ollama pull llama3.1:8b
ollama pull nomic-embed-text
```

### 4. Configuration

The `.env` file is already configured with default settings. You can modify it if needed:

```bash
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_CHAT_MODEL=llama3.1:8b
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
CHUNK_SIZE=800
CHUNK_OVERLAP=150
RETRIEVAL_TOP_K=5
```

## Usage

### General Chat

Start an interactive chat session without document context:

```bash
python -m src.main chat
```

Commands in chat mode:
- Type your message and press Enter
- Type `clear` to clear conversation history
- Type `exit` or `quit` to end the session

### Add Documents

Index a document to the knowledge base:

```bash
python -m src.main add /path/to/document.pdf
python -m src.main add /path/to/notes.md
python -m src.main add /path/to/report.docx
```

### Query Documents (RAG)

Ask questions about your indexed documents:

```bash
python -m src.main query "What are the main findings?"
python -m src.main query "Summarize the key points about machine learning"
```

### Summarize Documents

Generate a summary of a document:

```bash
# Concise summary (default)
python -m src.main summarize document.pdf

# Detailed summary
python -m src.main summarize document.pdf --type detailed

# Bullet-point summary
python -m src.main summarize document.pdf --type bullet
```

### Extract Information

Extract entities, keywords, and key points:

```bash
python -m src.main extract document.pdf
```

### List Indexed Documents

View all documents in the knowledge base:

```bash
python -m src.main list
```

### Clear Knowledge Base

Remove all indexed documents:

```bash
python -m src.main clear
```

## Project Structure

```
llm-dir/
├── src/
│   ├── main.py                    # CLI entry point
│   ├── cli/                       # CLI interface
│   │   ├── commands.py
│   │   ├── formatters.py
│   │   └── prompts.py
│   ├── core/                      # Core engines
│   │   ├── chat_engine.py
│   │   ├── rag_engine.py
│   │   ├── summarizer.py
│   │   ├── extractor.py
│   │   ├── document_processor.py
│   │   └── session_manager.py
│   ├── loaders/                   # Document loaders
│   │   ├── base_loader.py
│   │   ├── pdf_loader.py
│   │   ├── text_loader.py
│   │   └── docx_loader.py
│   ├── models/                    # Data models
│   │   ├── document.py
│   │   ├── chat.py
│   │   └── extraction.py
│   ├── vector_store/             # Vector database
│   │   ├── chroma_store.py
│   │   └── embeddings.py
│   └── utils/                    # Utilities
│       ├── config.py
│       ├── chunking.py
│       └── validators.py
├── data/                         # Runtime data
│   ├── documents/                # Document cache
│   ├── vector_db/                # ChromaDB data
│   └── sessions/                 # Chat sessions
├── requirements.txt              # Python dependencies
├── .env                          # Configuration
└── README.md                     # This file
```

## How It Works

### RAG Pipeline

1. **Document Indexing**:
   - Documents are loaded and parsed
   - Text is split into 800-token chunks with 150-token overlap
   - Chunks are embedded using `nomic-embed-text`
   - Embeddings are stored in ChromaDB

2. **Query Processing**:
   - User question is embedded
   - Top-5 similar chunks are retrieved
   - Context is assembled from chunks
   - LLM generates answer with source citations

### Supported File Formats

- **PDF**: Extracted using pdfplumber and pypdf
- **TXT/MD**: Plain text and Markdown files
- **DOCX**: Microsoft Word documents

## Configuration Options

Edit `.env` to customize:

| Variable | Description | Default |
|----------|-------------|---------|
| `OLLAMA_BASE_URL` | Ollama server URL | http://localhost:11434 |
| `OLLAMA_CHAT_MODEL` | Chat model name | llama3.1:8b |
| `OLLAMA_EMBEDDING_MODEL` | Embedding model | nomic-embed-text |
| `CHUNK_SIZE` | Text chunk size (tokens) | 800 |
| `CHUNK_OVERLAP` | Chunk overlap (tokens) | 150 |
| `RETRIEVAL_TOP_K` | Number of chunks to retrieve | 5 |
| `MAX_FILE_SIZE_MB` | Maximum file size | 100 |

## Troubleshooting

### Ollama Connection Error

Ensure Ollama is running:
```bash
ollama serve
```

### Model Not Found

Pull the required models:
```bash
ollama pull llama3.1:8b
ollama pull nomic-embed-text
```

### Import Errors

Install all dependencies:
```bash
pip install -r requirements.txt
```

### Performance Issues

- Use smaller chunk sizes for faster processing
- Reduce `RETRIEVAL_TOP_K` for quicker queries
- Consider using a smaller model (e.g., mistral:7b)

## Examples

### Example Workflow

```bash
# 1. Add some documents
python -m src.main add research_paper.pdf
python -m src.main add notes.md
python -m src.main add report.docx

# 2. List indexed documents
python -m src.main list

# 3. Ask questions about the documents
python -m src.main query "What are the main conclusions?"

# 4. Summarize a specific document
python -m src.main summarize research_paper.pdf --type bullet

# 5. Extract key information
python -m src.main extract report.docx

# 6. Start a general chat
python -m src.main chat
```

## Documentation

Comprehensive documentation is available in the `docs/` directory:

### Architecture
- [System Architecture](docs/architecture/ARCHITECTURE.md) - Complete system design and component breakdown

### Deployment
- [Docker Guide](docs/deployment/DOCKER_GUIDE.md) - Docker deployment with docker-compose
- [Docker Networking](docs/deployment/docker-networking.md) - Container networking deep dive
- [Docker Volumes](docs/deployment/docker-volumes.md) - Data persistence and volumes
- [API Quick Start](docs/deployment/QUICKSTART_API.md) - CLI vs API usage comparison

### API
- [API Guide](docs/api/API_GUIDE.md) - Complete REST API reference

### Guides
- [I/O Explained](docs/guides/IO_EXPLAINED.md) - How stdin/stdout works in Docker
- [Interactive Mode](docs/guides/interactive-mode-io.md) - TTY and interactive containers
- [Future Features](docs/guides/FUTURE_FEATURES.md) - Roadmap and planned enhancements

## License

This project is open source and available for educational and personal use.

## Contributing

Feel free to submit issues and enhancement requests!
