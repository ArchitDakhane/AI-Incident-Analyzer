"""Upload service for incident log files."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models.log_file import LogFile
from app.utils.storage import save_upload


def create_log_file(db: Session, *, incident_id: int, file: UploadFile) -> LogFile:
    """Store a log file and persist its metadata to the database."""
    metadata = save_upload(file, incident_id)
    log_file = LogFile(
        filename=metadata["filename"],
        original_filename=metadata["original_filename"],
        file_path=metadata["file_path"],
        file_type=metadata["file_type"],
        size_bytes=metadata["size_bytes"],
        file_metadata=str({"saved": True}),
        incident_id=incident_id,
    )
    db.add(log_file)
    db.commit()
    db.refresh(log_file)
    return log_file


def delete_log_file(db: Session, log_file: LogFile) -> None:
    """Remove an uploaded file from disk and database."""
    if log_file.file_path and os.path.exists(log_file.file_path):
        os.remove(log_file.file_path)
    db.delete(log_file)
    db.commit()


def delete_incident_files(db: Session, incident_id: int) -> None:
    """Delete all log files associated with an incident."""
    log_files = db.query(LogFile).filter(
        LogFile.incident_id == incident_id).all()
    for log_file in log_files:
        delete_log_file(db, log_file)
