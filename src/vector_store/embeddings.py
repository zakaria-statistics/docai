from typing import List
from langchain_community.embeddings import OllamaEmbeddings
from src.utils.config import config


class EmbeddingService:
    """Service for generating embeddings using Ollama."""

    def __init__(self):
        self.embeddings = OllamaEmbeddings(
            base_url=config.ollama_base_url,
            model=config.ollama_embedding_model,
        )

    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        return self.embeddings.embed_query(text)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        return self.embeddings.embed_documents(texts)


# Global embedding service instance
embedding_service = EmbeddingService()
