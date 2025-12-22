import json
from pathlib import Path
from typing import Optional, List
from datetime import datetime
from src.models.chat import ChatSession
from src.utils.config import config


class SessionManager:
    """Manage chat session persistence."""

    def __init__(self):
        self.storage_path = config.session_storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def save_session(self, session: ChatSession):
        """Save a chat session to disk."""
        file_path = self.storage_path / f"{session.session_id}.json"

        session_data = session.model_dump()
        # Convert datetime objects to ISO format strings
        session_data["created_at"] = session_data["created_at"].isoformat()
        session_data["updated_at"] = session_data["updated_at"].isoformat()

        for msg in session_data["messages"]:
            msg["timestamp"] = msg["timestamp"].isoformat()

        with open(file_path, "w") as f:
            json.dump(session_data, f, indent=2)

    def load_session(self, session_id: str) -> Optional[ChatSession]:
        """Load a chat session from disk."""
        file_path = self.storage_path / f"{session_id}.json"

        if not file_path.exists():
            return None

        with open(file_path, "r") as f:
            session_data = json.load(f)

        # Convert ISO format strings back to datetime objects
        session_data["created_at"] = datetime.fromisoformat(session_data["created_at"])
        session_data["updated_at"] = datetime.fromisoformat(session_data["updated_at"])

        for msg in session_data["messages"]:
            msg["timestamp"] = datetime.fromisoformat(msg["timestamp"])

        return ChatSession(**session_data)

    def list_sessions(self) -> List[Dict]:
        """List all saved sessions."""
        sessions = []

        for file_path in self.storage_path.glob("*.json"):
            try:
                with open(file_path, "r") as f:
                    session_data = json.load(f)

                sessions.append({
                    "session_id": session_data["session_id"],
                    "created_at": session_data["created_at"],
                    "updated_at": session_data["updated_at"],
                    "message_count": len(session_data["messages"]),
                })
            except (json.JSONDecodeError, KeyError):
                continue

        return sorted(sessions, key=lambda x: x["updated_at"], reverse=True)

    def delete_session(self, session_id: str):
        """Delete a saved session."""
        file_path = self.storage_path / f"{session_id}.json"
        if file_path.exists():
            file_path.unlink()

    def clear_all_sessions(self):
        """Delete all saved sessions."""
        for file_path in self.storage_path.glob("*.json"):
            file_path.unlink()


# Global session manager instance
session_manager = SessionManager()
