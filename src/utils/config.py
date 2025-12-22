import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()


class Config(BaseModel):
    """Application configuration loaded from environment variables."""

    # Ollama settings
    ollama_base_url: str = Field(default="http://localhost:11434")
    ollama_chat_model: str = Field(default="llama3.1:8b")
    ollama_embedding_model: str = Field(default="nomic-embed-text")

    # Vector store settings
    vector_store_path: Path = Field(default=Path("./data/vector_db"))
    collection_name: str = Field(default="documents")

    # ChromaDB server settings (optional, for server mode)
    chroma_host: Optional[str] = Field(default=None)
    chroma_port: int = Field(default=8000)

    # Chunking settings
    chunk_size: int = Field(default=800)
    chunk_overlap: int = Field(default=150)

    # RAG settings
    retrieval_top_k: int = Field(default=5)
    similarity_threshold: float = Field(default=0.7)

    # Session settings
    session_storage_path: Path = Field(default=Path("./data/sessions"))
    max_session_history: int = Field(default=50)

    # Document processing
    max_file_size_mb: int = Field(default=100)

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        return cls(
            ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            ollama_chat_model=os.getenv("OLLAMA_CHAT_MODEL", "llama3.1:8b"),
            ollama_embedding_model=os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text"),
            vector_store_path=Path(os.getenv("VECTOR_STORE_PATH", "./data/vector_db")),
            collection_name=os.getenv("COLLECTION_NAME", "documents"),
            chroma_host=os.getenv("CHROMA_HOST"),
            chroma_port=int(os.getenv("CHROMA_PORT", "8000")),
            chunk_size=int(os.getenv("CHUNK_SIZE", "800")),
            chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "150")),
            retrieval_top_k=int(os.getenv("RETRIEVAL_TOP_K", "5")),
            similarity_threshold=float(os.getenv("SIMILARITY_THRESHOLD", "0.7")),
            session_storage_path=Path(os.getenv("SESSION_STORAGE_PATH", "./data/sessions")),
            max_session_history=int(os.getenv("MAX_SESSION_HISTORY", "50")),
            max_file_size_mb=int(os.getenv("MAX_FILE_SIZE_MB", "100")),
        )

    def ensure_directories(self):
        """Create necessary directories if they don't exist."""
        self.vector_store_path.mkdir(parents=True, exist_ok=True)
        self.session_storage_path.mkdir(parents=True, exist_ok=True)
        Path("./data/documents").mkdir(parents=True, exist_ok=True)


# Global configuration instance
config = Config.from_env()
config.ensure_directories()
