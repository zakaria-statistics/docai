import os
from pathlib import Path
from typing import Optional
from src.utils.config import config


SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".docx"}


def validate_file_path(file_path: str) -> Path:
    """Validate that a file exists and is accessible."""
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if not path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")

    return path


def validate_file_extension(file_path: Path) -> bool:
    """Check if file extension is supported."""
    return file_path.suffix.lower() in SUPPORTED_EXTENSIONS


def validate_file_size(file_path: Path) -> bool:
    """Check if file size is within limits."""
    size_mb = file_path.stat().st_size / (1024 * 1024)
    return size_mb <= config.max_file_size_mb


def validate_document(file_path: str) -> Path:
    """Perform all validations on a document file."""
    path = validate_file_path(file_path)

    if not validate_file_extension(path):
        raise ValueError(
            f"Unsupported file extension: {path.suffix}. "
            f"Supported extensions: {', '.join(SUPPORTED_EXTENSIONS)}"
        )

    if not validate_file_size(path):
        raise ValueError(
            f"File too large: {path.stat().st_size / (1024 * 1024):.2f}MB. "
            f"Maximum size: {config.max_file_size_mb}MB"
        )

    return path
