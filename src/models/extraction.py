from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class Entity(BaseModel):
    """An extracted named entity."""

    text: str
    type: str  # person, organization, location, date, etc.
    confidence: Optional[float] = None


class Keyword(BaseModel):
    """An extracted keyword or key phrase."""

    text: str
    relevance: Optional[float] = None


class ExtractionResult(BaseModel):
    """Results from document information extraction."""

    source_file: str
    entities: List[Entity] = Field(default_factory=list)
    keywords: List[Keyword] = Field(default_factory=list)
    summary: Optional[str] = None
    key_points: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "source_file": self.source_file,
            "entities": [{"text": e.text, "type": e.type} for e in self.entities],
            "keywords": [{"text": k.text} for k in self.keywords],
            "summary": self.summary,
            "key_points": self.key_points,
            "metadata": self.metadata,
        }
