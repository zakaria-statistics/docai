from typing import Generator, List, Optional
from langchain_community.llms import Ollama
from src.models.chat import ChatSession, ChatMessage
from src.utils.config import config
import uuid


class ChatEngine:
    """Engine for general chat without document context."""

    def __init__(self):
        self.llm = Ollama(
            base_url=config.ollama_base_url,
            model=config.ollama_chat_model,
        )
        self.current_session: Optional[ChatSession] = None

    def create_session(self) -> ChatSession:
        """Create a new chat session."""
        session_id = str(uuid.uuid4())
        self.current_session = ChatSession(session_id=session_id)
        return self.current_session

    def chat(self, message: str, stream: bool = True) -> str:
        """Send a message and get a response."""
        if not self.current_session:
            self.create_session()

        # Add user message to history
        self.current_session.add_message("user", message)

        # Build prompt with conversation history
        prompt = self._build_prompt()

        # Get response
        if stream:
            response = ""
            for chunk in self.llm.stream(prompt):
                response += chunk
                yield chunk
            self.current_session.add_message("assistant", response)
        else:
            response = self.llm.invoke(prompt)
            self.current_session.add_message("assistant", response)
            return response

    def _build_prompt(self) -> str:
        """Build prompt from conversation history."""
        if not self.current_session or not self.current_session.messages:
            return ""

        # Get recent history
        recent_messages = self.current_session.get_history(
            max_messages=config.max_session_history
        )

        # Format messages
        prompt_parts = []
        for msg in recent_messages:
            role_label = "User" if msg.role == "user" else "Assistant"
            prompt_parts.append(f"{role_label}: {msg.content}")

        return "\n\n".join(prompt_parts)

    def clear_history(self):
        """Clear conversation history."""
        if self.current_session:
            self.current_session.clear_history()

    def get_session(self) -> Optional[ChatSession]:
        """Get current chat session."""
        return self.current_session
