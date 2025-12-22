from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """A single chat message."""

    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ChatSession(BaseModel):
    """A chat session with conversation history."""

    session_id: str
    messages: List[ChatMessage] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    context_documents: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def add_message(self, role: str, content: str, **metadata):
        """Add a message to the session."""
        message = ChatMessage(role=role, content=content, metadata=metadata)
        self.messages.append(message)
        self.updated_at = datetime.now()

    def get_history(self, max_messages: Optional[int] = None) -> List[ChatMessage]:
        """Get conversation history, optionally limited to recent messages."""
        if max_messages:
            return self.messages[-max_messages:]
        return self.messages

    def clear_history(self):
        """Clear all messages from the session."""
        self.messages = []
        self.updated_at = datetime.now()
