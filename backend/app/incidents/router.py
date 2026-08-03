"""Incident routes."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth.service import get_current_user
from app.database.session import get_db
from app.incidents.schemas import IncidentCreate, IncidentListResponse, IncidentResponse, IncidentUpdate
from app.incidents.service import create_incident, delete_incident, get_incident, list_incidents, update_incident
from app.models.user import User

router = APIRouter(prefix="/api/incidents", tags=["Incidents"])
security = HTTPBearer(auto_error=False)


@router.post("", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED)
def create_incident_route(
    payload: IncidentCreate,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> IncidentResponse:
    """Create a new incident."""
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = get_current_user(db, credentials.credentials)
    incident = create_incident(db, user=user, payload=payload.model_dump())
    return IncidentResponse(
        id=incident.id,
        title=incident.title,
        incident_type=incident.incident_type,
        severity=incident.severity,
        status=incident.status,
        description=incident.description,
        summary=incident.summary,
        created_at=incident.created_at.isoformat(),
        updated_at=incident.updated_at.isoformat(),
        created_by_id=incident.created_by_id,
    )


@router.get("", response_model=IncidentListResponse)
def list_incidents_route(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    search: str | None = None,
    severity: str | None = None,
    status: str | None = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> IncidentListResponse:
    """List incidents with pagination, search, filtering, and sorting."""
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    get_current_user(db, credentials.credentials)
    items, total = list_incidents(
        db,
        page=page,
        size=size,
        search=search,
        severity=severity,
        status=status,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return IncidentListResponse(
        items=[
            IncidentResponse(
                id=item.id,
                title=item.title,
                incident_type=item.incident_type,
                severity=item.severity,
                status=item.status,
                description=item.description,
                summary=item.summary,
                created_at=item.created_at.isoformat(),
                updated_at=item.updated_at.isoformat(),
                created_by_id=item.created_by_id,
            )
            for item in items
        ],
        total=total,
        page=page,
        size=size,
    )


@router.get("/{incident_id}", response_model=IncidentResponse)
def get_incident_route(
    incident_id: int,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> IncidentResponse:
    """Fetch a single incident."""
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    get_current_user(db, credentials.credentials)
    incident = get_incident(db, incident_id)
    return IncidentResponse(
        id=incident.id,
        title=incident.title,
        incident_type=incident.incident_type,
        severity=incident.severity,
        status=incident.status,
        description=incident.description,
        summary=incident.summary,
        created_at=incident.created_at.isoformat(),
        updated_at=incident.updated_at.isoformat(),
        created_by_id=incident.created_by_id,
    )


@router.put("/{incident_id}", response_model=IncidentResponse)
def update_incident_route(
    incident_id: int,
    payload: IncidentUpdate,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> IncidentResponse:
    """Update an incident."""
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    get_current_user(db, credentials.credentials)
    incident = update_incident(
        db, incident_id, payload.model_dump(exclude_unset=True))
    return IncidentResponse(
        id=incident.id,
        title=incident.title,
        incident_type=incident.incident_type,
        severity=incident.severity,
        status=incident.status,
        description=incident.description,
        summary=incident.summary,
        created_at=incident.created_at.isoformat(),
        updated_at=incident.updated_at.isoformat(),
        created_by_id=incident.created_by_id,
    )


@router.delete("/{incident_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_incident_route(
    incident_id: int,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> None:
    """Delete an incident."""
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    get_current_user(db, credentials.credentials)
    delete_incident(db, incident_id)
