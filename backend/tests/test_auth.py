"""Authentication module tests."""

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
    """Create a FastAPI test client backed by an in-memory SQLite database."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
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


def test_register_login_and_profile_flow(client: TestClient) -> None:
    """Users should be able to register, log in, and access their profile."""
    register_response = client.post(
        "/api/auth/register",
        json={
            "email": "demo@example.com",
            "username": "demo",
            "password": "secret123",
            "full_name": "Demo User",
        },
    )

    assert register_response.status_code == 200
    register_payload = register_response.json()
    assert register_payload["user"]["email"] == "demo@example.com"
    assert register_payload["access_token"]
    assert register_payload["refresh_token"]

    login_response = client.post(
        "/api/auth/login",
        json={"email": "demo@example.com", "password": "secret123"},
    )

    assert login_response.status_code == 200
    login_payload = login_response.json()
    assert login_payload["access_token"]
    assert login_payload["refresh_token"]

    profile_response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {login_payload['access_token']}"},
    )

    assert profile_response.status_code == 200
    assert profile_response.json()["email"] == "demo@example.com"


def test_refresh_token_rotation(client: TestClient) -> None:
    """Refresh tokens should issue a new access token and rotate the refresh token."""
    register_response = client.post(
        "/api/auth/register",
        json={
            "email": "refresh@example.com",
            "username": "refresh",
            "password": "secret123",
        },
    )

    refresh_token = register_response.json()["refresh_token"]
    refresh_response = client.post(
        "/api/auth/refresh",
        json={"refresh_token": refresh_token},
    )

    assert refresh_response.status_code == 200
    payload = refresh_response.json()
    assert payload["access_token"]
    assert payload["refresh_token"]


def test_swagger_docs_are_available(client: TestClient) -> None:
    """Swagger UI should be available for interactive API testing."""
    response = client.get("/docs")

    assert response.status_code == 200
