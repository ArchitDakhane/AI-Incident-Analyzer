"""Local file storage helpers for uploaded log files."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4
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

    safe_original_name = Path(file.filename.replace("\\", "/")).name
    if safe_original_name in {"", ".", ".."}:
        raise ValueError("File name is invalid")

    allowed_extensions = {".txt", ".log", ".out"}
    file_extension = Path(safe_original_name).suffix.lower()
    if file_extension not in allowed_extensions:
        raise ValueError("Only .txt, .log, and .out files are supported")

    if file.size is not None and file.size > settings.max_upload_size_bytes:
        raise ValueError("File is too large")


def save_upload(file: UploadFile, incident_id: int) -> dict[str, Any]:
    """Persist an uploaded file to disk and return metadata."""
    validate_upload(file)
    upload_dir = ensure_upload_directory()
    original_name = Path(file.filename.replace("\\", "/")).name
    if len(original_name) > 180:
        suffix = Path(original_name).suffix
        original_name = f"{original_name[: 180 - len(suffix)]}{suffix}"
    safe_name = (
        f"incident_{incident_id}_{uuid4().hex}_{original_name}"
    )
    target_path = upload_dir / safe_name
    size_bytes = 0
    try:
        with target_path.open("xb") as destination:
            while chunk := file.file.read(64 * 1024):
                size_bytes += len(chunk)
                if size_bytes > settings.max_upload_size_bytes:
                    raise ValueError("File is too large")
                destination.write(chunk)
    except Exception:
        target_path.unlink(missing_ok=True)
        raise

    return {
        "filename": safe_name,
        "original_filename": original_name,
        "file_path": str(target_path),
        "file_type": Path(original_name).suffix.lower().lstrip("."),
        "size_bytes": size_bytes,
    }
