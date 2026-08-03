"""Incident routes."""

import os

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth.service import get_current_user
from app.database.session import get_db
from app.incidents.schemas import IncidentCreate, IncidentListResponse, IncidentResponse, IncidentUpdate
from app.incidents.service import create_incident, delete_incident, get_incident, list_incidents, update_incident
from app.incidents.upload_schemas import UploadResponse
from app.incidents.upload_service import create_log_file, delete_incident_files
from app.models.log_file import LogFile
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


@router.post("/{incident_id}/upload", response_model=UploadResponse)
def upload_log_file_route(
    incident_id: int,
    file: UploadFile = File(...),
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> UploadResponse:
    """Upload a log file for an incident."""
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    get_current_user(db, credentials.credentials)
    get_incident(db, incident_id)
    try:
        log_file = create_log_file(db, incident_id=incident_id, file=file)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return UploadResponse(
        id=log_file.id,
        filename=log_file.filename,
        original_filename=log_file.original_filename,
        file_path=log_file.file_path,
        file_type=log_file.file_type,
        size_bytes=log_file.size_bytes,
        uploaded_at=log_file.uploaded_at.isoformat(),
        incident_id=log_file.incident_id,
    )


@router.get("/{incident_id}/download/{log_file_id}")
def download_log_file_route(
    incident_id: int,
    log_file_id: int,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> FileResponse:
    """Download an uploaded log file."""
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    get_current_user(db, credentials.credentials)
    get_incident(db, incident_id)
    log_file = db.query(LogFile).filter(
        LogFile.id == log_file_id, LogFile.incident_id == incident_id).first()
    if not log_file:
        raise HTTPException(status_code=404, detail="Log file not found")
    if not os.path.exists(log_file.file_path):
        raise HTTPException(status_code=404, detail="File no longer exists")

    return FileResponse(log_file.file_path, filename=log_file.original_filename)


@router.delete("/{incident_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_incident_route(
    incident_id: int,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> None:
    """Delete an incident and all uploaded files."""
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    get_current_user(db, credentials.credentials)
    delete_incident_files(db, incident_id)
    delete_incident(db, incident_id)
