from pathlib import Path
from src.loaders.base_loader import BaseLoader
from src.models.document import Document


class TextLoader(BaseLoader):
    """Loader for text files (.txt, .md)."""

    def __init__(self, file_path: Path):
        super().__init__(file_path)

    def extract_text(self) -> str:
        """Extract text from text file."""
        encodings = ["utf-8", "ascii", "latin-1", "cp1252"]

        for encoding in encodings:
            try:
                with open(self.file_path, "r", encoding=encoding) as f:
                    return f.read()
            except (UnicodeDecodeError, UnicodeError):
                continue

        raise ValueError(
            f"Could not decode file {self.file_path} with any of the attempted encodings: {encodings}"
        )

    def load(self) -> Document:
        """Load the text document."""
        content = self.extract_text()

        return Document.from_file(
            self.file_path,
            content,
            word_count=len(content.split()),
        )
