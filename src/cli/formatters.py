from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn
from typing import List, Dict, Any

console = Console()


def print_success(message: str):
    """Print a success message."""
    console.print(f"[green]✓[/green] {message}")


def print_error(message: str):
    """Print an error message."""
    console.print(f"[red]✗[/red] {message}")


def print_info(message: str):
    """Print an info message."""
    console.print(f"[blue]ℹ[/blue] {message}")


def print_warning(message: str):
    """Print a warning message."""
    console.print(f"[yellow]⚠[/yellow] {message}")


def print_header(title: str):
    """Print a header."""
    console.print(f"\n[bold cyan]{title}[/bold cyan]\n")


def print_document_list(documents: List[str]):
    """Print a list of indexed documents."""
    if not documents:
        print_info("No documents indexed yet.")
        return

    table = Table(title="Indexed Documents")
    table.add_column("Filename", style="cyan")

    for doc in documents:
        table.add_row(doc)

    console.print(table)


def print_extraction_result(result: Dict[str, Any]):
    """Print extraction results."""
    console.print(Panel(f"[bold]Extraction Results: {result['source_file']}[/bold]"))

    if result.get("entities"):
        console.print("\n[bold]Entities:[/bold]")
        for entity in result["entities"]:
            console.print(f"  • {entity['text']} ({entity['type']})")

    if result.get("keywords"):
        console.print("\n[bold]Keywords:[/bold]")
        for keyword in result["keywords"]:
            console.print(f"  • {keyword['text']}")

    if result.get("key_points"):
        console.print("\n[bold]Key Points:[/bold]")
        for i, point in enumerate(result["key_points"], 1):
            console.print(f"  {i}. {point}")


def print_summary(summary: str, filename: str):
    """Print a document summary."""
    console.print(Panel(
        summary,
        title=f"[bold]Summary: {filename}[/bold]",
        border_style="green"
    ))


def print_chat_message(role: str, content: str):
    """Print a chat message."""
    if role == "user":
        console.print(f"\n[bold blue]You:[/bold blue] {content}")
    else:
        console.print(f"\n[bold green]Assistant:[/bold green] {content}")


def stream_chat_response(chunks):
    """Stream chat response chunks."""
    console.print("\n[bold green]Assistant:[/bold green] ", end="")
    for chunk in chunks:
        console.print(chunk, end="")
    console.print()  # New line after streaming


def create_progress():
    """Create a progress indicator."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    )
