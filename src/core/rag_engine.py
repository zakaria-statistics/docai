from typing import List, Dict, Any, Optional, Generator
from langchain_community.llms import Ollama
from src.vector_store.chroma_store import vector_store
from src.utils.config import config


class RAGEngine:
    """Retrieval Augmented Generation engine for Q&A over documents."""

    def __init__(self):
        self.llm = Ollama(
            base_url=config.ollama_base_url,
            model=config.ollama_chat_model,
        )
        self.vector_store = vector_store

    def query(
        self,
        question: str,
        top_k: Optional[int] = None,
        stream: bool = True,
    ) -> Generator[str, None, None]:
        """Query documents and generate an answer."""
        # Retrieve relevant chunks
        results = self.vector_store.query(question, top_k=top_k)

        if not results:
            yield "I couldn't find any relevant information in the documents to answer your question."
            return

        # Build context from retrieved chunks
        context = self._build_context(results)

        # Build prompt
        prompt = self._build_prompt(question, context, results)

        # Generate answer
        if stream:
            for chunk in self.llm.stream(prompt):
                yield chunk
        else:
            response = self.llm.invoke(prompt)
            yield response

    def _build_context(self, results: List[Dict[str, Any]]) -> str:
        """Build context string from retrieved chunks."""
        context_parts = []

        for i, result in enumerate(results, 1):
            text = result["text"]
            source = result["metadata"].get("source_file", "Unknown")
            chunk_idx = result["metadata"].get("chunk_index", 0)

            context_parts.append(
                f"[Source {i}: {source}, chunk {chunk_idx}]\n{text}"
            )

        return "\n\n".join(context_parts)

    def _build_prompt(
        self,
        question: str,
        context: str,
        results: List[Dict[str, Any]]
    ) -> str:
        """Build the RAG prompt with context and question."""
        sources = set()
        for result in results:
            source = result["metadata"].get("source_file", "Unknown")
            sources.add(source)

        sources_list = ", ".join(sources)

        prompt = f"""You are a helpful AI assistant. Answer the question based on the provided context from the documents.

Context from documents ({sources_list}):
{context}

Question: {question}

Instructions:
- Answer based only on the information provided in the context above
- If the context doesn't contain enough information to answer the question, say so clearly
- Be concise but thorough
- Cite which source(s) you're using in your answer when relevant

Answer:"""

        return prompt

    def get_relevant_chunks(
        self,
        question: str,
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get relevant document chunks without generating an answer."""
        return self.vector_store.query(question, top_k=top_k)


# Global RAG engine instance
rag_engine = RAGEngine()
