"""Schemas for log upload operations."""

from pydantic import BaseModel


class UploadResponse(BaseModel):
    """Response payload for file uploads."""

    id: int
    filename: str
    original_filename: str
    file_type: str | None = None
    size_bytes: int | None = None
    uploaded_at: str
    incident_id: int | None = None
