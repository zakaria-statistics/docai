# AI Document Processing CLI - Implementation Plan

## Overview
Build a CLI application for chatting with AI and processing documents (PDF, TXT/MD, DOCX) using Ollama running locally. Features include RAG-based Q&A, summarization, general chat, and entity extraction.

## Technology Stack
- **Framework**: LangChain
- **Vector Store**: ChromaDB
- **CLI**: Click + Rich
- **Ollama Models**:
  - Chat: `llama3.1:8b`
  - Embeddings: `nomic-embed-text`

## CLI Commands
```bash
docai chat                    # General chat mode
docai add <file>              # Index document
docai query <question>        # RAG query over all docs
docai summarize <file>        # Summarize document
docai extract <file>          # Extract entities/keywords
docai list                    # List indexed documents
docai remove <file>           # Remove from index
docai clear                   # Clear all documents
```

## Project Structure
See directory structure for organized modules including cli/, core/, loaders/, models/, utils/, and vector_store/.

## Implementation Phases
1. Foundation & Setup (config, models, dependencies)
2. Document Loading (PDF, TXT/MD, DOCX loaders)
3. Vector Store & Embeddings (ChromaDB integration)
4. Core AI Engines (chat, RAG, summarization, extraction)
5. CLI Interface (commands, prompts, formatters)
6. Polish & Documentation

## Usage
```bash
pip install -r requirements.txt
python -m src.main chat
```
