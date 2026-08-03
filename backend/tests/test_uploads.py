"""Log upload tests."""

import io

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.database.session import get_db
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
    """Users should be able to upload a TXT log, download it, and have it removed with the incident."""
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

    download_response = client.get(
        f"/api/incidents/{incident_id}/download/{payload['id']}",
        headers=headers,
    )
    assert download_response.status_code == 200
    assert b"line1" in download_response.content

    delete_response = client.delete(
        f"/api/incidents/{incident_id}", headers=headers)
    assert delete_response.status_code == 204
