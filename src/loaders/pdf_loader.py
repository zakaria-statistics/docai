from pathlib import Path
import pdfplumber
from pypdf import PdfReader
from src.loaders.base_loader import BaseLoader
from src.models.document import Document


class PDFLoader(BaseLoader):
    """Loader for PDF documents."""

    def __init__(self, file_path: Path):
        super().__init__(file_path)

    def extract_text(self) -> str:
        """Extract text from PDF using pdfplumber (better for complex layouts)."""
        text_content = []

        try:
            with pdfplumber.open(self.file_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_content.append(text)
        except Exception as e:
            # Fallback to pypdf if pdfplumber fails
            try:
                reader = PdfReader(self.file_path)
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        text_content.append(text)
            except Exception as fallback_error:
                raise Exception(
                    f"Failed to extract text from PDF: {e}. Fallback also failed: {fallback_error}"
                )

        return "\n\n".join(text_content)

    def get_page_count(self) -> int:
        """Get the number of pages in the PDF."""
        try:
            with pdfplumber.open(self.file_path) as pdf:
                return len(pdf.pages)
        except:
            reader = PdfReader(self.file_path)
            return len(reader.pages)

    def load(self) -> Document:
        """Load the PDF document."""
        content = self.extract_text()
        page_count = self.get_page_count()

        return Document.from_file(
            self.file_path,
            content,
            page_count=page_count,
            word_count=len(content.split()),
        )
