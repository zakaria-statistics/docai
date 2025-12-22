from prompt_toolkit import prompt
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory


def get_user_input(message: str = "You: ") -> str:
    """Get user input with history and auto-suggest."""
    history = InMemoryHistory()

    try:
        user_input = prompt(
            message,
            history=history,
            auto_suggest=AutoSuggestFromHistory(),
        )
        return user_input.strip()
    except (KeyboardInterrupt, EOFError):
        return ""


def confirm(message: str) -> bool:
    """Ask user for yes/no confirmation."""
    response = input(f"{message} (y/n): ").lower().strip()
    return response in ["y", "yes"]
