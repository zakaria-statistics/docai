import click
from pathlib import Path
from src.core.chat_engine import ChatEngine
from src.core.rag_engine import rag_engine
from src.core.summarizer import summarizer
from src.core.extractor import extractor
from src.core.document_processor import DocumentProcessor
from src.vector_store.chroma_store import vector_store
from src.cli import formatters as fmt
from src.cli.prompts import get_user_input, confirm


@click.group()
def cli():
    """DocAI - AI-powered document processing and chat CLI."""
    pass


@cli.command()
def chat():
    """Start an interactive chat session."""
    fmt.print_header("DocAI Chat Mode")
    fmt.print_info("Type 'exit' or 'quit' to end the conversation.\n")

    engine = ChatEngine()
    engine.create_session()

    while True:
        user_message = get_user_input("You: ")

        if not user_message:
            continue

        if user_message.lower() in ["exit", "quit"]:
            fmt.print_info("Goodbye!")
            break

        if user_message.lower() == "clear":
            engine.clear_history()
            fmt.print_success("Conversation history cleared.")
            continue

        # Stream response
        try:
            fmt.stream_chat_response(engine.chat(user_message, stream=True))
        except Exception as e:
            fmt.print_error(f"Error: {e}")


@cli.command()
@click.argument("file_path", type=click.Path(exists=True))
def add(file_path):
    """Add a document to the vector store."""
    try:
        with fmt.create_progress() as progress:
            task = progress.add_task("Processing document...", total=None)

            # Load and process document
            document = DocumentProcessor.load_document(file_path)

            # Add to vector store
            vector_store.add_document(document)

        fmt.print_success(f"Added '{Path(file_path).name}' to the knowledge base.")
        fmt.print_info(f"Document ID: {document.doc_id}")
        fmt.print_info(f"Chunks created: {len(document.chunks)}")

    except Exception as e:
        fmt.print_error(f"Failed to add document: {e}")


@cli.command()
@click.argument("question")
def query(question):
    """Query the knowledge base using RAG."""
    try:
        # Check if any documents are indexed
        info = vector_store.get_document_info()
        if info["total_chunks"] == 0:
            fmt.print_warning("No documents indexed. Use 'docai add <file>' first.")
            return

        fmt.print_header("RAG Query")
        fmt.print_info(f"Searching across {info['unique_documents']} document(s)...\n")

        # Stream response
        fmt.stream_chat_response(rag_engine.query(question, stream=True))

    except Exception as e:
        fmt.print_error(f"Query failed: {e}")


@cli.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--type", default="concise", help="Summary type: concise, detailed, or bullet")
def summarize(file_path, type):
    """Summarize a document."""
    try:
        with fmt.create_progress() as progress:
            task = progress.add_task("Summarizing document...", total=None)
            summary = summarizer.summarize_file(file_path, summary_type=type)

        fmt.print_summary(summary, Path(file_path).name)

    except Exception as e:
        fmt.print_error(f"Summarization failed: {e}")


@cli.command()
@click.argument("file_path", type=click.Path(exists=True))
def extract(file_path):
    """Extract entities and keywords from a document."""
    try:
        with fmt.create_progress() as progress:
            task = progress.add_task("Extracting information...", total=None)
            result = extractor.extract_from_file(file_path)

        fmt.print_extraction_result(result.to_dict())

    except Exception as e:
        fmt.print_error(f"Extraction failed: {e}")


@cli.command()
def list():
    """List all indexed documents."""
    try:
        info = vector_store.get_document_info()

        fmt.print_header("Indexed Documents")
        fmt.print_info(f"Total documents: {info['unique_documents']}")
        fmt.print_info(f"Total chunks: {info['total_chunks']}\n")

        if info["document_files"]:
            fmt.print_document_list(info["document_files"])
        else:
            fmt.print_warning("No documents indexed yet.")

    except Exception as e:
        fmt.print_error(f"Failed to list documents: {e}")


@cli.command()
def clear():
    """Clear all documents from the vector store."""
    if confirm("Are you sure you want to clear all indexed documents?"):
        try:
            vector_store.clear_all()
            fmt.print_success("All documents cleared from the knowledge base.")
        except Exception as e:
            fmt.print_error(f"Failed to clear documents: {e}")
    else:
        fmt.print_info("Operation cancelled.")


if __name__ == "__main__":
    cli()
