"""Incident CRUD tests."""

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
        json={"email": "incident@example.com",
              "username": "incident", "password": "secret123"},
    )
    return register_response.json()["access_token"]


def test_incident_crud_flow_and_pagination(client: TestClient) -> None:
    """Users should be able to create, read, update, delete, and list incidents."""
    token = create_user_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    create_response = client.post(
        "/api/incidents",
        json={"title": "Database latency spike",
              "severity": "high", "status": "open"},
        headers=headers,
    )
    assert create_response.status_code == 201
    incident_id = create_response.json()["id"]

    list_response = client.get(
        "/api/incidents?page=1&size=10", headers=headers)
    assert list_response.status_code == 200
    payload = list_response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["title"] == "Database latency spike"

    search_response = client.get(
        "/api/incidents?search=latency", headers=headers)
    assert search_response.status_code == 200
    assert search_response.json()["total"] == 1

    filter_response = client.get(
        "/api/incidents?severity=high", headers=headers)
    assert filter_response.status_code == 200
    assert filter_response.json()["total"] == 1

    update_response = client.put(
        f"/api/incidents/{incident_id}",
        json={"status": "resolved"},
        headers=headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "resolved"

    get_response = client.get(f"/api/incidents/{incident_id}", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["title"] == "Database latency spike"

    delete_response = client.delete(
        f"/api/incidents/{incident_id}", headers=headers)
    assert delete_response.status_code == 204

    after_delete = client.get("/api/incidents", headers=headers)
    assert after_delete.status_code == 200
    assert after_delete.json()["total"] == 0
