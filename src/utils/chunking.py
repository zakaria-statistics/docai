from typing import List
from langchain.text_splitter import RecursiveCharacterTextSplitter
from src.utils.config import config


def create_text_splitter() -> RecursiveCharacterTextSplitter:
    """Create a text splitter with configured chunk size and overlap."""
    return RecursiveCharacterTextSplitter(
        chunk_size=config.chunk_size,
        chunk_overlap=config.chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
        is_separator_regex=False,
    )


def chunk_text(text: str) -> List[str]:
    """Split text into chunks using the configured splitter."""
    splitter = create_text_splitter()
    return splitter.split_text(text)


def chunk_documents(documents: List[str]) -> List[str]:
    """Split multiple documents into chunks."""
    splitter = create_text_splitter()
    all_chunks = []
    for doc in documents:
        chunks = splitter.split_text(doc)
        all_chunks.extend(chunks)
    return all_chunks
