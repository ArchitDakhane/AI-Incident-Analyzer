"""AI report generation tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.database.session import get_db
from app.models.ai_report import AIReport
from main import create_app


@pytest.fixture()
def client_and_db():
    """Create a FastAPI test client with a shared in-memory SQLite database."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(
        bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield {"client": test_client, "db": db}

    app.dependency_overrides.clear()
    db.close()


def create_user_token(client: TestClient) -> str:
    """Create a user and return an access token."""
    register_response = client.post(
        "/api/auth/register",
        json={"email": "ai@example.com",
              "username": "aiuser", "password": "secret123"},
    )
    return register_response.json()["access_token"]


def test_generate_ai_report_success_and_store(client_and_db, monkeypatch) -> None:
    """A successful Gemini response should be validated, stored, and returned."""
    client = client_and_db["client"]
    db = client_and_db["db"]
    token = create_user_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    incident_response = client.post(
        "/api/incidents",
        json={"title": "API outage", "severity": "high",
              "description": "Payments are failing"},
        headers=headers,
    )
    incident_id = incident_response.json()["id"]

    def fake_call_gemini_api(prompt: str, api_key: str) -> str:
        assert "API outage" in prompt
        return (
            '{"summary": "Detected a backend outage", '
            '"findings": ["Payments failing"], '
            '"recommended_actions": ["Restart the services"], '
            '"confidence_score": 0.91}'
        )

    monkeypatch.setattr(
        "app.incidents.ai_service.call_gemini_api", fake_call_gemini_api)

    response = client.post(
        f"/api/incidents/{incident_id}/ai-report",
        headers=headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"] == "Detected a backend outage"
    assert payload["confidence_score"] == 0.91
    assert db.query(AIReport).count() == 1


def test_generate_ai_report_uses_cached_analysis(client_and_db, monkeypatch) -> None:
    """Repeated analysis requests should return the cached report without calling Gemini again."""
    client = client_and_db["client"]
    db = client_and_db["db"]
    token = create_user_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    incident_response = client.post(
        "/api/incidents",
        json={"title": "Cacheable outage", "severity": "critical"},
        headers=headers,
    )
    incident_id = incident_response.json()["id"]
    call_count = 0

    def fake_call_gemini_api(prompt: str, api_key: str) -> str:
        nonlocal call_count
        call_count += 1
        return (
            '{"summary": "Cached analysis", '
            '"findings": ["One finding"], '
            '"recommended_actions": ["One action"], '
            '"confidence_score": 0.87}'
        )

    monkeypatch.setattr(
        "app.incidents.ai_service.call_gemini_api", fake_call_gemini_api)

    first_response = client.post(
        f"/api/incidents/{incident_id}/ai-report",
        headers=headers,
    )
    second_response = client.post(
        f"/api/incidents/{incident_id}/ai-report",
        headers=headers,
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert second_response.json()["summary"] == "Cached analysis"
    assert call_count == 1
    assert db.query(AIReport).count() == 1


def test_incident_update_invalidates_cached_ai_analysis(client_and_db, monkeypatch) -> None:
    """Changing an incident should invalidate cached AI analysis for that incident."""
    client = client_and_db["client"]
    db = client_and_db["db"]
    token = create_user_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    incident_response = client.post(
        "/api/incidents",
        json={"title": "Stale cache outage", "severity": "high"},
        headers=headers,
    )
    incident_id = incident_response.json()["id"]
    responses = [
        (
            '{"summary": "First analysis", '
            '"findings": [], '
            '"recommended_actions": [], '
            '"confidence_score": 0.8}'
        ),
        (
            '{"summary": "Second analysis", '
            '"findings": [], '
            '"recommended_actions": [], '
            '"confidence_score": 0.9}'
        ),
    ]

    def fake_call_gemini_api(prompt: str, api_key: str) -> str:
        return responses.pop(0)

    monkeypatch.setattr(
        "app.incidents.ai_service.call_gemini_api", fake_call_gemini_api)

    first_response = client.post(
        f"/api/incidents/{incident_id}/ai-report",
        headers=headers,
    )
    update_response = client.put(
        f"/api/incidents/{incident_id}",
        json={"summary": "Operator added details"},
        headers=headers,
    )
    second_response = client.post(
        f"/api/incidents/{incident_id}/ai-report",
        headers=headers,
    )

    assert first_response.status_code == 200
    assert update_response.status_code == 200
    assert second_response.status_code == 200
    assert second_response.json()["summary"] == "Second analysis"
    assert len(responses) == 0
    assert db.query(AIReport).count() == 2


def test_generate_ai_report_handles_api_errors(client_and_db, monkeypatch) -> None:
    """Gemini API failures should return a handled error without storing a report."""
    client = client_and_db["client"]
    db = client_and_db["db"]
    token = create_user_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    incident_response = client.post(
        "/api/incidents",
        json={"title": "DB latency", "severity": "medium"},
        headers=headers,
    )
    incident_id = incident_response.json()["id"]

    def fake_call_gemini_api(prompt: str, api_key: str) -> str:
        raise RuntimeError("Gemini unavailable")

    monkeypatch.setattr(
        "app.incidents.ai_service.call_gemini_api", fake_call_gemini_api)

    response = client.post(
        f"/api/incidents/{incident_id}/ai-report",
        headers=headers,
    )

    assert response.status_code == 503
    assert db.query(AIReport).count() == 0
