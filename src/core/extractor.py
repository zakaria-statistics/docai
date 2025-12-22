import json
from typing import List, Dict, Any
from langchain_community.llms import Ollama
from src.core.document_processor import DocumentProcessor
from src.models.extraction import ExtractionResult, Entity, Keyword
from src.utils.config import config


class Extractor:
    """Extract structured information from documents."""

    def __init__(self):
        self.llm = Ollama(
            base_url=config.ollama_base_url,
            model=config.ollama_chat_model,
        )

    def extract_from_file(self, file_path: str) -> ExtractionResult:
        """Extract information from a document file."""
        text = DocumentProcessor.extract_text(file_path)
        return self.extract_from_text(text, source_file=file_path)

    def extract_from_text(
        self,
        text: str,
        source_file: str = "unknown"
    ) -> ExtractionResult:
        """Extract entities, keywords, and key points from text."""
        # Extract entities
        entities = self._extract_entities(text)

        # Extract keywords
        keywords = self._extract_keywords(text)

        # Extract key points
        key_points = self._extract_key_points(text)

        return ExtractionResult(
            source_file=source_file,
            entities=entities,
            keywords=keywords,
            key_points=key_points,
        )

    def _extract_entities(self, text: str) -> List[Entity]:
        """Extract named entities from text."""
        prompt = f"""Extract named entities from the following text.
Identify: people, organizations, locations, dates, and other important entities.

Format your response as a JSON array of objects with "text" and "type" fields.
Example: [{{"text": "John Doe", "type": "person"}}, {{"text": "Microsoft", "type": "organization"}}]

Text:
{text[:2000]}

Entities (JSON):"""

        response = self.llm.invoke(prompt)

        # Parse JSON response
        try:
            # Extract JSON from response
            json_start = response.find("[")
            json_end = response.rfind("]") + 1
            if json_start != -1 and json_end > json_start:
                json_str = response[json_start:json_end]
                entities_data = json.loads(json_str)
                return [Entity(**e) for e in entities_data]
        except (json.JSONDecodeError, ValueError):
            pass

        return []

    def _extract_keywords(self, text: str) -> List[Keyword]:
        """Extract important keywords from text."""
        prompt = f"""Extract the 10 most important keywords or key phrases from the following text.

Format your response as a JSON array of objects with a "text" field.
Example: [{{"text": "machine learning"}}, {{"text": "artificial intelligence"}}]

Text:
{text[:2000]}

Keywords (JSON):"""

        response = self.llm.invoke(prompt)

        # Parse JSON response
        try:
            json_start = response.find("[")
            json_end = response.rfind("]") + 1
            if json_start != -1 and json_end > json_start:
                json_str = response[json_start:json_end]
                keywords_data = json.loads(json_str)
                return [Keyword(**k) for k in keywords_data]
        except (json.JSONDecodeError, ValueError):
            pass

        return []

    def _extract_key_points(self, text: str) -> List[str]:
        """Extract key points from text."""
        prompt = f"""Extract 5-7 key points from the following text.
Format as a simple list, one point per line, without numbering or bullets.

Text:
{text[:2000]}

Key points:"""

        response = self.llm.invoke(prompt)

        # Split response into lines and clean
        points = []
        for line in response.split("\n"):
            line = line.strip()
            # Remove numbering and bullets
            line = line.lstrip("0123456789.-•* ")
            if line and len(line) > 10:
                points.append(line)

        return points[:7]


# Global extractor instance
extractor = Extractor()
