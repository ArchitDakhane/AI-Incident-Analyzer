"""Log upload tests."""

import io

import pytest
from fastapi import UploadFile
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.database.session import get_db
from app.core.config import settings
from app.utils.storage import save_upload
from app.models.log_file import LogFile
from main import create_app


@pytest.fixture()
def client() -> TestClient:
    """Create a FastAPI test client with a shared in-memory SQLite database."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(
        bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app = create_app()
    app.state.testing_session = TestingSessionLocal
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def create_user_token(client: TestClient) -> str:
    """Create a user and return an access token."""
    register_response = client.post(
        "/api/auth/register",
        json={"email": "upload@example.com",
              "username": "upload", "password": "secret123"},
    )
    return register_response.json()["access_token"]


def test_upload_download_and_delete_flow(client: TestClient) -> None:
    """Users can upload and download a TXT log, then delete it with the incident."""
    token = create_user_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    incident_response = client.post(
        "/api/incidents",
        json={"title": "Upload test", "severity": "medium"},
        headers=headers,
    )
    incident_id = incident_response.json()["id"]

    upload_response = client.post(
        f"/api/incidents/{incident_id}/upload",
        files={"file": ("sample.txt", io.BytesIO(
            b"line1\nline2\n"), "text/plain")},
        headers=headers,
    )
    assert upload_response.status_code == 200
    payload = upload_response.json()
    assert payload["original_filename"] == "sample.txt"

    duplicate_upload = client.post(
        f"/api/incidents/{incident_id}/upload",
        files={"file": ("sample.txt", io.BytesIO(
            b"replacement\n"), "text/plain")},
        headers=headers,
    )
    assert duplicate_upload.status_code == 200
    assert duplicate_upload.json()["filename"] != payload["filename"]

    download_response = client.get(
        f"/api/incidents/{incident_id}/download/{payload['id']}",
        headers=headers,
    )
    assert download_response.status_code == 200
    assert b"line1" in download_response.content

    delete_response = client.delete(
        f"/api/incidents/{incident_id}", headers=headers)
    assert delete_response.status_code == 204


def test_upload_limit_is_enforced_when_size_is_unknown(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE_MB", 1)
    monkeypatch.setattr(settings, "UPLOAD_DIRECTORY", str(tmp_path))
    upload = UploadFile(
        filename="large.txt",
        file=io.BytesIO(b"x" * (1024 * 1024 + 1)),
        size=None,
    )

    with pytest.raises(ValueError, match="File is too large"):
        save_upload(upload, incident_id=1)

    assert list(tmp_path.iterdir()) == []


def test_windows_path_in_upload_filename_is_reduced_to_basename(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "UPLOAD_DIRECTORY", str(tmp_path))
    upload = UploadFile(
        filename=r"..\..\private\audit.txt",
        file=io.BytesIO(b"safe content"),
        size=12,
    )

    metadata = save_upload(upload, incident_id=7)
    stored_path = tmp_path / metadata["filename"]

    assert metadata["original_filename"] == "audit.txt"
    assert stored_path.parent.resolve() == tmp_path.resolve()
    assert stored_path.read_bytes() == b"safe content"


def test_download_rejects_file_path_outside_upload_root(client: TestClient, tmp_path) -> None:
    token = create_user_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    incident = client.post(
        "/api/incidents",
        json={"title": "Path traversal check"},
        headers=headers,
    ).json()
    uploaded = client.post(
        f"/api/incidents/{incident['id']}/upload",
        files={"file": ("safe.txt", io.BytesIO(b"safe"), "text/plain")},
        headers=headers,
    ).json()
    secret_file = tmp_path / "outside.txt"
    secret_file.write_text("must not be served", encoding="utf-8")

    db = client.app.state.testing_session()
    try:
        row = db.query(LogFile).filter(LogFile.id == uploaded["id"]).one()
        row.file_path = str(secret_file)
        db.commit()
    finally:
        db.close()

    response = client.get(
        f"/api/incidents/{incident['id']}/download/{uploaded['id']}",
        headers=headers,
    )
    assert response.status_code == 404
