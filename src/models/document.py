from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    """Metadata for a document."""

    filename: str
    file_path: str
    file_type: str
    file_size: int
    created_at: datetime = Field(default_factory=datetime.now)
    page_count: Optional[int] = None
    word_count: Optional[int] = None
    extra: Dict[str, Any] = Field(default_factory=dict)


class DocumentChunk(BaseModel):
    """A chunk of document text with metadata."""

    chunk_id: str
    text: str
    chunk_index: int
    source_file: str
    page_number: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Document(BaseModel):
    """Represents a processed document."""

    doc_id: str
    content: str
    metadata: DocumentMetadata
    chunks: List[DocumentChunk] = Field(default_factory=list)
    processed_at: datetime = Field(default_factory=datetime.now)

    @classmethod
    def from_file(cls, file_path: Path, content: str, **kwargs) -> "Document":
        """Create a Document from a file path and content."""
        import hashlib

        doc_id = hashlib.md5(str(file_path).encode()).hexdigest()
        metadata = DocumentMetadata(
            filename=file_path.name,
            file_path=str(file_path),
            file_type=file_path.suffix,
            file_size=file_path.stat().st_size,
            **kwargs,
        )
        return cls(doc_id=doc_id, content=content, metadata=metadata)
