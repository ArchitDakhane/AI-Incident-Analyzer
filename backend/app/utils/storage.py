"""Local file storage helpers for uploaded log files."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import UploadFile

from app.core.config import settings


def ensure_upload_directory() -> Path:
    """Create the configured upload directory if it does not already exist."""
    upload_dir = Path(settings.UPLOAD_DIRECTORY)
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


def validate_upload(file: UploadFile) -> None:
    """Validate upload size and extension before storing the file."""
    if not file.filename:
        raise ValueError("File name is required")

    allowed_extensions = {".txt", ".log", ".out"}
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in allowed_extensions:
        raise ValueError("Only .txt, .log, and .out files are supported")

    if file.size and file.size > settings.max_upload_size_bytes:
        raise ValueError("File is too large")


def save_upload(file: UploadFile, incident_id: int) -> dict[str, Any]:
    """Persist an uploaded file to disk and return metadata."""
    validate_upload(file)
    upload_dir = ensure_upload_directory()
    safe_name = f"incident_{incident_id}_{Path(file.filename or 'upload').name}"
    target_path = upload_dir / safe_name
    contents = file.file.read()
    target_path.write_bytes(contents)

    return {
        "filename": safe_name,
        "original_filename": file.filename,
        "file_path": str(target_path),
        "file_type": Path(file.filename or "").suffix.lower().lstrip("."),
        "size_bytes": len(contents),
    }
