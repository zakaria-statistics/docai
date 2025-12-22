#!/usr/bin/env python3
"""
DocAI - AI-powered document processing and chat CLI

A command-line tool for:
- Chatting with AI using Ollama
- Processing documents (PDF, TXT, MD, DOCX)
- RAG-based Q&A over documents
- Document summarization
- Entity and keyword extraction
"""

import sys
from src.cli.commands import cli


def main():
    """Main entry point for the DocAI CLI."""
    try:
        cli()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
