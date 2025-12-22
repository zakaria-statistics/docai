from pathlib import Path
from typing import Optional
import hashlib
from src.loaders.base_loader import BaseLoader
from src.loaders.pdf_loader import PDFLoader
from src.loaders.text_loader import TextLoader
from src.loaders.docx_loader import DOCXLoader
from src.models.document import Document, DocumentChunk
from src.utils.chunking import chunk_text
from src.utils.validators import validate_document


class DocumentProcessor:
    """Process documents with appropriate loaders and chunking."""

    LOADER_MAP = {
        ".pdf": PDFLoader,
        ".txt": TextLoader,
        ".md": TextLoader,
        ".docx": DOCXLoader,
    }

    @classmethod
    def get_loader(cls, file_path: Path) -> BaseLoader:
        """Get the appropriate loader for a file type."""
        ext = file_path.suffix.lower()
        loader_class = cls.LOADER_MAP.get(ext)

        if not loader_class:
            raise ValueError(f"Unsupported file type: {ext}")

        return loader_class(file_path)

    @classmethod
    def load_document(cls, file_path: str) -> Document:
        """Load a document from a file path."""
        path = validate_document(file_path)
        loader = cls.get_loader(path)
        document = loader.load()

        # Create chunks
        chunks = chunk_text(document.content)
        document.chunks = []

        for i, chunk_text_content in enumerate(chunks):
            chunk_id = hashlib.md5(f"{document.doc_id}_{i}".encode()).hexdigest()
            chunk = DocumentChunk(
                chunk_id=chunk_id,
                text=chunk_text_content,
                chunk_index=i,
                source_file=document.metadata.filename,
                metadata={"total_chunks": len(chunks)},
            )
            document.chunks.append(chunk)

        return document

    @classmethod
    def extract_text(cls, file_path: str) -> str:
        """Extract text from a document without full processing."""
        path = validate_document(file_path)
        loader = cls.get_loader(path)
        return loader.extract_text()
