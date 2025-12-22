from typing import Optional
from langchain_community.llms import Ollama
from langchain.chains.summarize import load_summarize_chain
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document as LangchainDocument
from src.core.document_processor import DocumentProcessor
from src.utils.config import config


class Summarizer:
    """Document summarization engine."""

    def __init__(self):
        self.llm = Ollama(
            base_url=config.ollama_base_url,
            model=config.ollama_chat_model,
        )

    def summarize_file(self, file_path: str, summary_type: str = "concise") -> str:
        """Summarize a document file."""
        # Extract text from document
        text = DocumentProcessor.extract_text(file_path)
        return self.summarize_text(text, summary_type)

    def summarize_text(self, text: str, summary_type: str = "concise") -> str:
        """Summarize text content."""
        # Determine if text is short enough for direct summarization
        word_count = len(text.split())

        if word_count < 1000:
            # Short document - direct summarization
            return self._summarize_short(text, summary_type)
        else:
            # Long document - use map-reduce strategy
            return self._summarize_long(text, summary_type)

    def _summarize_short(self, text: str, summary_type: str) -> str:
        """Summarize short text directly."""
        prompt = self._get_summary_prompt(text, summary_type)
        return self.llm.invoke(prompt)

    def _summarize_long(self, text: str, summary_type: str) -> str:
        """Summarize long text using map-reduce."""
        # Split text into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=200,
        )
        chunks = text_splitter.split_text(text)

        # Summarize each chunk
        chunk_summaries = []
        for chunk in chunks:
            prompt = f"""Summarize the following text concisely:

{chunk}

Summary:"""
            summary = self.llm.invoke(prompt)
            chunk_summaries.append(summary)

        # Combine summaries
        combined_summary = "\n\n".join(chunk_summaries)

        # Final summarization
        final_prompt = self._get_summary_prompt(combined_summary, summary_type)
        return self.llm.invoke(final_prompt)

    def _get_summary_prompt(self, text: str, summary_type: str) -> str:
        """Get the appropriate summary prompt based on type."""
        if summary_type == "concise":
            instruction = "Provide a concise summary in 2-3 paragraphs."
        elif summary_type == "detailed":
            instruction = "Provide a detailed summary covering all major points."
        elif summary_type == "bullet":
            instruction = "Provide a summary as a bullet-point list of key points."
        else:
            instruction = "Provide a concise summary."

        return f"""Summarize the following text. {instruction}

Text:
{text}

Summary:"""

    def extract_key_points(self, text: str, num_points: int = 5) -> str:
        """Extract key points from text."""
        prompt = f"""Extract the {num_points} most important key points from the following text.
Format your response as a numbered list.

Text:
{text}

Key Points:"""

        return self.llm.invoke(prompt)


# Global summarizer instance
summarizer = Summarizer()
