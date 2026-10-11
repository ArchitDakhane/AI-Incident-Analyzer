"""Business logic for incident CRUD operations."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.exceptions import ResourceNotFoundException, ValidationException
from app.incidents.cache import invalidate_ai_report_cache
from app.models.incident import Incident
from app.models.user import User
from app.services.dashboard import invalidate_dashboard_cache


def create_incident(db: Session, *, user: User, payload: dict[str, Any]) -> Incident:
    """Create a new incident for the authenticated user."""
    title = payload.get("title")
    if not title or not str(title).strip():
        raise ValidationException("Title is required")

    incident = Incident(
        title=str(title).strip(),
        incident_type=payload.get("incident_type"),
        severity=payload.get("severity", "medium"),
        status=payload.get("status", "open"),
        description=payload.get("description"),
        summary=payload.get("summary"),
        created_by_id=user.id,
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)
    invalidate_dashboard_cache()
    return incident


def get_incident(
    db: Session,
    incident_id: int,
    *,
    created_by_id: int,
) -> Incident:
    """Fetch an incident owned by the specified user."""
    incident = (
        db.query(Incident)
        .filter(Incident.id == incident_id, Incident.created_by_id == created_by_id)
        .first()
    )
    if not incident:
        raise ResourceNotFoundException("incident", incident_id)
    return incident


def update_incident(
    db: Session,
    incident_id: int,
    payload: dict[str, Any],
    *,
    created_by_id: int,
) -> Incident:
    """Update an existing incident."""
    incident = get_incident(db, incident_id, created_by_id=created_by_id)
    for field in ["title", "incident_type", "severity", "status", "description", "summary"]:
        if field in payload and payload[field] is not None:
            setattr(incident, field, payload[field])
    incident.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(incident)
    invalidate_dashboard_cache()
    invalidate_ai_report_cache(incident.id)
    return incident


def delete_incident(
    db: Session,
    incident_id: int,
    *,
    created_by_id: int,
) -> None:
    """Delete an incident."""
    incident = get_incident(db, incident_id, created_by_id=created_by_id)
    db.delete(incident)
    db.commit()
    invalidate_dashboard_cache()
    invalidate_ai_report_cache(incident_id)


def list_incidents(
    db: Session,
    *,
    page: int = 1,
    size: int = 20,
    search: str | None = None,
    severity: str | None = None,
    status: str | None = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    created_by_id: int,
) -> tuple[list[Incident], int]:
    """Return incidents with pagination, search, filtering, and sorting."""
    query = db.query(Incident)
    query = query.filter(Incident.created_by_id == created_by_id)

    if search:
        search_term = f"%{search}%"
        query = query.filter(or_(Incident.title.ilike(
            search_term), Incident.description.ilike(search_term)))

    if severity:
        query = query.filter(Incident.severity == severity)

    if status:
        query = query.filter(Incident.status == status)

    allowed_sort_columns = {"created_at": Incident.created_at,
                            "updated_at": Incident.updated_at, "title": Incident.title}
    if sort_by not in allowed_sort_columns:
        raise ValidationException("Invalid sort field")

    sort_column = allowed_sort_columns[sort_by]
    if sort_order.lower() == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    total = query.count()
    items = query.offset((page - 1) * size).limit(size).all()
    return items, total
