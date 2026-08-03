"""Service layer for generating and storing AI incident reports."""

from __future__ import annotations

import json

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import ServiceException, ValidationException
from app.incidents.cache import (
    cache_ai_report,
    get_cached_ai_report,
    invalidate_ai_report_cache,
)
from app.incidents.vector_service import index_ai_report_embedding
from app.models.ai_report import AIReport
from app.models.incident import Incident
from app.models.user import User
from app.services.dashboard import invalidate_dashboard_cache

from .ai_schemas import AIReportPayload


def build_ai_report_prompt(incident: Incident) -> str:
    """Create a prompt for Gemini using the incident metadata."""
    title = incident.title or "Untitled incident"
    description = incident.description or "No additional details provided"
    severity = incident.severity or "unknown"
    status = incident.status or "unknown"
    return (
        "You are an incident analysis assistant. Analyze the incident and return JSON only.\n"
        f"Title: {title}\n"
        f"Description: {description}\n"
        f"Severity: {severity}\n"
        f"Status: {status}\n"
        "Return a JSON object with keys: summary, findings, recommended_actions, confidence_score."
    )


def call_gemini_api(prompt: str, api_key: str) -> str:
    """Call the Google Gemini API and return the raw response content."""
    if not api_key or api_key == "your-gemini-api-key-here":
        raise ServiceException("Gemini API key is not configured")

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        "gemini-1.5-flash:generateContent"
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json"},
    }

    response = httpx.post(
        url,
        params={"key": api_key},
        json=payload,
        timeout=20.0,
    )
    response.raise_for_status()

    data = response.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ServiceException("Invalid Gemini response format") from exc


def parse_ai_report_payload(raw_response: str) -> AIReportPayload:
    """Parse and validate the Gemini response as structured JSON."""
    try:
        payload = json.loads(raw_response)
    except json.JSONDecodeError as exc:
        raise ValidationException(
            "Gemini response was not valid JSON") from exc

    if not isinstance(payload, dict):
        raise ValidationException("Gemini response must be a JSON object")

    try:
        return AIReportPayload.model_validate(payload)
    except Exception as exc:  # pragma: no cover - defensive validation path
        raise ValidationException(
            "Gemini response did not match the expected schema") from exc


def _get_report_from_cache_marker(
    db: Session,
    incident_id: int,
    cached_payload: object,
) -> AIReport | None:
    """Resolve a cached AI report marker back to the persisted report."""
    query = db.query(AIReport).filter(AIReport.incident_id == incident_id)
    if isinstance(cached_payload, dict) and cached_payload.get("id"):
        query = query.filter(AIReport.id == int(cached_payload["id"]))

    return query.order_by(AIReport.created_at.desc()).first()


def create_ai_report(db: Session, *, incident: Incident, user: User | None = None) -> AIReport:
    """Generate a Gemini analysis for an incident and persist it."""
    cached = get_cached_ai_report(incident.id)
    if cached is not None:
        cached_report = _get_report_from_cache_marker(db, incident.id, cached)
        if cached_report is not None:
            return cached_report
        invalidate_ai_report_cache(incident.id)

    prompt = build_ai_report_prompt(incident)
    raw_response = call_gemini_api(prompt, settings.GEMINI_API_KEY)
    payload = parse_ai_report_payload(raw_response)

    ai_report = AIReport(
        model_name="gemini-1.5-flash",
        analysis_type="incident_summary",
        content=json.dumps(
            {
                "summary": payload.summary,
                "findings": payload.findings,
                "recommended_actions": payload.recommended_actions,
                "confidence_score": payload.confidence_score,
            }
        ),
        confidence_score=payload.confidence_score,
        incident_id=incident.id,
        created_by_id=user.id if user else None,
    )
    db.add(ai_report)
    db.commit()
    db.refresh(ai_report)
    index_ai_report_embedding(db, incident=incident, ai_report=ai_report)
    cache_ai_report(
        incident.id,
        {
            "id": ai_report.id,
            "incident_id": ai_report.incident_id,
            "model_name": ai_report.model_name,
            "analysis_type": ai_report.analysis_type,
            "content": ai_report.content,
            "confidence_score": ai_report.confidence_score,
            "embedding_id": ai_report.embedding_id,
            "created_by_id": ai_report.created_by_id,
        },
    )
    invalidate_dashboard_cache()
    return ai_report
