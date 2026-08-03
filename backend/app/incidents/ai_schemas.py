"""Schemas for AI-generated incident analysis."""

from pydantic import BaseModel, Field


class AIReportPayload(BaseModel):
    """Structured JSON payload returned by the Gemini analysis."""

    summary: str = Field(min_length=1)
    findings: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    confidence_score: float | None = Field(default=None, ge=0.0, le=1.0)


class AIReportResponse(BaseModel):
    """Response payload for a stored AI report."""

    id: int
    incident_id: int
    model_name: str
    analysis_type: str
    summary: str
    findings: list[str]
    recommended_actions: list[str]
    confidence_score: float | None = None
    created_at: str
    created_by_id: int | None = None
