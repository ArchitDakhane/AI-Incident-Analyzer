"""Incident schemas for request and response validation."""

from pydantic import BaseModel, Field


class IncidentCreate(BaseModel):
    """Payload for creating a new incident."""

    title: str = Field(min_length=3, max_length=255)
    incident_type: str | None = Field(default=None, max_length=100)
    severity: str = Field(default="medium", max_length=50)
    status: str = Field(default="open", max_length=50)
    description: str | None = None
    summary: str | None = None


class IncidentUpdate(BaseModel):
    """Payload for updating an existing incident."""

    title: str | None = Field(default=None, min_length=3, max_length=255)
    incident_type: str | None = Field(default=None, max_length=100)
    severity: str | None = Field(default=None, max_length=50)
    status: str | None = Field(default=None, max_length=50)
    description: str | None = None
    summary: str | None = None


class IncidentResponse(BaseModel):
    """Incident response payload."""

    id: int
    title: str
    incident_type: str | None = None
    severity: str
    status: str
    description: str | None = None
    summary: str | None = None
    created_at: str
    updated_at: str
    created_by_id: int | None = None


class IncidentListResponse(BaseModel):
    """Paginated incident list response."""

    items: list[IncidentResponse]
    total: int
    page: int
    size: int
