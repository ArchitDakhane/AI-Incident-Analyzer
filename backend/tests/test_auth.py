"""Authentication module tests."""

import hashlib
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.database.session import get_db
from app.core.config import settings
from app.models.refresh_token import RefreshToken
from main import create_app


@pytest.fixture()
def client() -> TestClient:
    """Create a FastAPI test client backed by an in-memory SQLite database."""
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
    assert payload["refresh_token"] != refresh_token

    reused_response = client.post(
        "/api/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert reused_response.status_code == 401

    rotated_response = client.post(
        "/api/auth/refresh",
        json={"refresh_token": payload["refresh_token"]},
    )
    assert rotated_response.status_code == 200
    assert rotated_response.json()["refresh_token"] != payload["refresh_token"]

    profile_response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {refresh_token}"},
    )
    assert profile_response.status_code == 401


def test_duplicate_registration_and_invalid_login_return_client_errors(client: TestClient) -> None:
    payload = {
        "email": "duplicate@example.com",
        "username": "duplicate",
        "password": "secret123",
    }
    assert client.post("/api/auth/register", json=payload).status_code == 200
    assert client.post("/api/auth/register", json=payload).status_code == 409
    assert client.post(
        "/api/auth/login",
        json={"email": payload["email"], "password": "wrong-password"},
    ).status_code == 401


def test_expired_refresh_token_is_rejected(client: TestClient) -> None:
    expired_token = jwt.encode(
        {
            "sub": "1",
            "jti": "expired-test-token",
            "token_type": "refresh",
            "exp": datetime.now(timezone.utc) - timedelta(seconds=2),
        },
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    response = client.post(
        "/api/auth/refresh",
        json={"refresh_token": expired_token},
    )

    assert response.status_code == 401


def test_server_side_expired_refresh_token_record_is_rejected(client: TestClient) -> None:
    registration = client.post(
        "/api/auth/register",
        json={
            "email": "server-expired@example.com",
            "username": "serverexpired",
            "password": "secret123",
        },
    )
    refresh_token = registration.json()["refresh_token"]
    token_id = jwt.decode(
        refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
    )["jti"]

    db = client.app.state.testing_session()
    try:
        row = db.query(RefreshToken).filter(
            RefreshToken.token_hash == hashlib.sha256(
                token_id.encode("utf-8")).hexdigest()
        ).one()
        row.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        db.commit()
    finally:
        db.close()

    response = client.post(
        "/api/auth/refresh",
        json={"refresh_token": refresh_token},
    )

    assert response.status_code == 401


def test_logout_revokes_refresh_token_and_is_idempotent(client: TestClient) -> None:
    registration = client.post(
        "/api/auth/register",
        json={"email": "logout@example.com",
              "username": "logoutuser", "password": "secret123"},
    )
    refresh_token = registration.json()["refresh_token"]

    logout_response = client.post(
        "/api/auth/logout", json={"refresh_token": refresh_token})
    repeat_logout_response = client.post(
        "/api/auth/logout", json={"refresh_token": refresh_token})
    refresh_response = client.post(
        "/api/auth/refresh", json={"refresh_token": refresh_token})

    assert logout_response.status_code == 204
    assert repeat_logout_response.status_code == 204
    assert refresh_response.status_code == 401


def test_concurrent_refresh_reuse_allows_only_one_rotation(client: TestClient) -> None:
    registration = client.post(
        "/api/auth/register",
        json={"email": "race@example.com",
              "username": "raceuser", "password": "secret123"},
    )
    token = registration.json()["refresh_token"]

    def refresh_once():
        return client.post("/api/auth/refresh", json={"refresh_token": token})

    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(executor.map(lambda _: refresh_once(), range(2)))

    assert sorted(response.status_code for response in responses) == [200, 401]


def test_swagger_docs_are_available(client: TestClient) -> None:
    """Swagger UI should be available for interactive API testing."""
    response = client.get("/docs")

    assert response.status_code == 200
