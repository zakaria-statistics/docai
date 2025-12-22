from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from src.models.document import Document, DocumentChunk
from src.vector_store.embeddings import embedding_service
from src.utils.config import config


class ChromaVectorStore:
    """Vector store using ChromaDB for document retrieval."""

    def __init__(self):
        # Check if we should use server mode or embedded mode
        if config.chroma_host:
            # Server mode (Docker/production)
            self.client = chromadb.HttpClient(
                host=config.chroma_host,
                port=config.chroma_port,
                settings=Settings(anonymized_telemetry=False),
            )
        else:
            # Embedded mode (local development)
            self.client = chromadb.PersistentClient(
                path=str(config.vector_store_path),
                settings=Settings(anonymized_telemetry=False),
            )

        self.collection = self.client.get_or_create_collection(
            name=config.collection_name,
            metadata={"description": "Document chunks for RAG"},
        )

    def add_document(self, document: Document):
        """Add a document's chunks to the vector store."""
        if not document.chunks:
            raise ValueError("Document has no chunks to add")

        texts = [chunk.text for chunk in document.chunks]
        ids = [chunk.chunk_id for chunk in document.chunks]
        metadatas = [
            {
                "source_file": chunk.source_file,
                "chunk_index": chunk.chunk_index,
                "doc_id": document.doc_id,
            }
            for chunk in document.chunks
        ]

        # Generate embeddings
        embeddings = embedding_service.embed_documents(texts)

        # Add to ChromaDB
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )

    def query(
        self,
        query_text: str,
        top_k: Optional[int] = None,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Query the vector store for similar documents."""
        k = top_k or config.retrieval_top_k

        # Generate query embedding
        query_embedding = embedding_service.embed_text(query_text)

        # Query ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            where=filter_dict,
        )

        # Format results
        formatted_results = []
        if results["ids"] and len(results["ids"]) > 0:
            for i in range(len(results["ids"][0])):
                result = {
                    "id": results["ids"][0][i],
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i] if "distances" in results else None,
                }
                formatted_results.append(result)

        return formatted_results

    def delete_document(self, doc_id: str):
        """Delete all chunks of a document from the vector store."""
        self.collection.delete(where={"doc_id": doc_id})

    def clear_all(self):
        """Clear all documents from the vector store."""
        self.client.delete_collection(config.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=config.collection_name,
            metadata={"description": "Document chunks for RAG"},
        )

    def list_documents(self) -> List[str]:
        """List all unique document IDs in the store."""
        results = self.collection.get()
        if not results["metadatas"]:
            return []

        doc_ids = set()
        for metadata in results["metadatas"]:
            if "doc_id" in metadata:
                doc_ids.add(metadata["doc_id"])

        return list(doc_ids)

    def get_document_info(self) -> Dict[str, Any]:
        """Get information about stored documents."""
        results = self.collection.get()
        doc_files = set()
        chunk_count = 0

        if results["metadatas"]:
            chunk_count = len(results["metadatas"])
            for metadata in results["metadatas"]:
                if "source_file" in metadata:
                    doc_files.add(metadata["source_file"])

        return {
            "total_chunks": chunk_count,
            "unique_documents": len(doc_files),
            "document_files": list(doc_files),
        }


# Global vector store instance
vector_store = ChromaVectorStore()
