from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
from src.models.document import Document


class BaseLoader(ABC):
    """Abstract base class for document loaders."""

    def __init__(self, file_path: Path):
        self.file_path = file_path

    @abstractmethod
    def load(self) -> Document:
        """Load and process the document."""
        pass

    @abstractmethod
    def extract_text(self) -> str:
        """Extract text content from the document."""
        pass

    def get_metadata(self) -> dict:
        """Get basic metadata for the document."""
        return {
            "filename": self.file_path.name,
            "file_type": self.file_path.suffix,
            "file_size": self.file_path.stat().st_size,
        }
