"""
DocAI REST API Server

Provides HTTP endpoints for document processing and chat functionality.
Run with: uvicorn src.api:app --host 0.0.0.0 --port 8080
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from pathlib import Path
import tempfile
import shutil
import json

from src.core.chat_engine import ChatEngine
from src.core.rag_engine import rag_engine
from src.core.summarizer import summarizer
from src.core.extractor import extractor
from src.core.document_processor import DocumentProcessor
from src.vector_store.chroma_store import vector_store


# Pydantic Models for API
class ChatRequest(BaseModel):
    message: str = Field(..., description="User message")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    stream: bool = Field(False, description="Enable streaming response")


class ChatResponse(BaseModel):
    response: str
    session_id: str


class QueryRequest(BaseModel):
    question: str = Field(..., description="Question to ask about documents")
    stream: bool = Field(False, description="Enable streaming response")


class QueryResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]


class SummarizeRequest(BaseModel):
    summary_type: str = Field("concise", description="Type: concise, detailed, or bullet")


class DocumentInfo(BaseModel):
    doc_id: str
    file_name: str
    chunks: int


class VectorStoreInfo(BaseModel):
    total_chunks: int
    unique_documents: int
    document_files: List[str]


# Initialize FastAPI app
app = FastAPI(
    title="DocAI API",
    description="AI-powered document processing and chat API",
    version="1.0.0",
)

# CORS middleware for web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session storage (use Redis in production)
chat_sessions: Dict[str, ChatEngine] = {}


# Helper functions
def get_or_create_session(session_id: Optional[str] = None) -> tuple[str, ChatEngine]:
    """Get existing session or create new one."""
    if session_id and session_id in chat_sessions:
        return session_id, chat_sessions[session_id]

    engine = ChatEngine()
    session = engine.create_session()
    chat_sessions[session.session_id] = engine
    return session.session_id, engine


# API Endpoints

@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "name": "DocAI API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "chat": "/chat",
            "query": "/query",
            "documents": "/documents",
            "summarize": "/summarize/{file_name}",
            "extract": "/extract/{file_name}",
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Test vector store connection
        info = vector_store.get_document_info()
        return {
            "status": "healthy",
            "vector_store": "connected",
            "documents_indexed": info["unique_documents"]
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat with AI without document context.

    - **message**: User message
    - **session_id**: Optional session ID for conversation continuity
    - **stream**: Enable streaming (returns text/event-stream)
    """
    try:
        session_id, engine = get_or_create_session(request.session_id)

        if request.stream:
            async def generate():
                response_text = ""
                for chunk in engine.chat(request.message, stream=True):
                    response_text += chunk
                    yield f"data: {json.dumps({'chunk': chunk, 'session_id': session_id})}\n\n"
                yield f"data: {json.dumps({'done': True, 'session_id': session_id})}\n\n"

            return StreamingResponse(generate(), media_type="text/event-stream")
        else:
            response = engine.chat(request.message, stream=False)
            return ChatResponse(response=response, session_id=session_id)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """
    Query indexed documents using RAG.

    - **question**: Question to ask about your documents
    - **stream**: Enable streaming response
    """
    try:
        # Check if documents are indexed
        info = vector_store.get_document_info()
        if info["total_chunks"] == 0:
            raise HTTPException(
                status_code=400,
                detail="No documents indexed. Upload documents first using POST /documents"
            )

        if request.stream:
            async def generate():
                for chunk in rag_engine.query(request.question, stream=True):
                    yield f"data: {json.dumps({'chunk': chunk})}\n\n"
                yield f"data: {json.dumps({'done': True})}\n\n"

            return StreamingResponse(generate(), media_type="text/event-stream")
        else:
            # For non-streaming, we need to consume the generator
            answer = ""
            for chunk in rag_engine.query(request.question, stream=True):
                answer += chunk

            # Get source information
            retrieved = vector_store.query(request.question, top_k=5)
            sources = [
                {
                    "file": r["metadata"].get("source_file", "unknown"),
                    "chunk_index": r["metadata"].get("chunk_index", 0)
                }
                for r in retrieved
            ]

            return QueryResponse(answer=answer, sources=sources)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/documents", response_model=DocumentInfo)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Upload and index a document.

    Supported formats: PDF, TXT, MD, DOCX
    """
    try:
        # Save uploaded file to temp location
        suffix = Path(file.filename).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name

        # Process document
        document = DocumentProcessor.load_document(tmp_path)

        # Add to vector store
        vector_store.add_document(document)

        # Clean up temp file in background
        background_tasks.add_task(lambda: Path(tmp_path).unlink(missing_ok=True))

        return DocumentInfo(
            doc_id=document.doc_id,
            file_name=file.filename,
            chunks=len(document.chunks)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")


@app.get("/documents", response_model=VectorStoreInfo)
async def list_documents():
    """List all indexed documents."""
    try:
        info = vector_store.get_document_info()
        return VectorStoreInfo(**info)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/documents")
async def clear_documents():
    """Clear all indexed documents."""
    try:
        vector_store.clear_all()
        return {"message": "All documents cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/summarize/{file_name}")
async def summarize_document(file_name: str, request: SummarizeRequest):
    """
    Summarize an uploaded document.

    - **file_name**: Name of previously uploaded file
    - **summary_type**: concise, detailed, or bullet
    """
    try:
        # This would need document storage tracking
        # For now, return error indicating feature needs document management
        raise HTTPException(
            status_code=501,
            detail="Summarize endpoint requires persistent document storage. Use CLI for now."
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/extract/{file_name}")
async def extract_entities(file_name: str):
    """
    Extract entities and keywords from a document.

    - **file_name**: Name of previously uploaded file
    """
    try:
        # This would need document storage tracking
        raise HTTPException(
            status_code=501,
            detail="Extract endpoint requires persistent document storage. Use CLI for now."
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a chat session."""
    if session_id in chat_sessions:
        del chat_sessions[session_id]
        return {"message": f"Session {session_id} deleted"}
    raise HTTPException(status_code=404, detail="Session not found")


# Run with: uvicorn src.api:app --host 0.0.0.0 --port 8080 --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
