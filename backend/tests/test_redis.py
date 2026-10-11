"""Redis and rate-limit regression tests."""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.cache import CacheService, InMemoryCache, cache_service
from app.database.base import Base
from app.database.session import get_db
from app.services.dashboard import dashboard_stats_cache_key
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
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_cache_service_round_trip() -> None:
    """The cache service should store and retrieve values."""
    service = CacheService(redis_client=InMemoryCache())

    service.set("demo", {"value": 1}, ttl_seconds=30)

    assert service.get("demo") == {"value": 1}
    service.delete("demo")
    assert service.get("demo") is None


def test_cache_service_prefix_invalidation_and_increment() -> None:
    """The cache service should delete cache groups and increment counters."""
    service = CacheService(redis_client=InMemoryCache())

    service.set("dashboard:stats", {"total": 1}, ttl_seconds=30)
    service.set("dashboard:recent", [1, 2], ttl_seconds=30)
    service.set("ai_report:1", {"id": 1}, ttl_seconds=30)

    assert service.increment("ratelimit:test", ttl_seconds=60) == 1
    assert service.increment("ratelimit:test", ttl_seconds=60) == 2

    service.invalidate_prefix("dashboard:")

    assert service.get("dashboard:stats") is None
    assert service.get("dashboard:recent") is None
    assert service.get("ai_report:1") == {"id": 1}


def test_rate_limit_middleware_blocks_excess_requests() -> None:
    """The middleware should block traffic once the request limit is reached."""
    from app.middleware.rate_limit import RateLimitMiddleware

    app = FastAPI()
    app.add_middleware(RateLimitMiddleware, max_requests=1, window_seconds=60)

    @app.get("/ping")
    def ping() -> dict[str, str]:
        return {"status": "ok"}

    with TestClient(app) as client:
        first_response = client.get("/ping")
        second_response = client.get("/ping")

    assert first_response.status_code == 200
    assert first_response.headers["X-RateLimit-Limit"] == "1"
    assert first_response.headers["X-RateLimit-Remaining"] == "0"
    assert second_response.status_code == 429
    assert second_response.headers["Retry-After"] == "60"


def test_rate_limit_groups_numeric_resource_paths() -> None:
    from app.middleware.rate_limit import RateLimitMiddleware

    app = FastAPI()
    app.add_middleware(RateLimitMiddleware, max_requests=1, window_seconds=60)

    @app.get("/incidents/{incident_id}")
    def get_incident(incident_id: int) -> dict[str, int]:
        return {"id": incident_id}

    with TestClient(app) as test_client:
        first = test_client.get("/incidents/101")
        second = test_client.get("/incidents/202")

    assert first.status_code == 200
    assert second.status_code == 429


def test_dashboard_stats_are_cached_and_invalidated(client: TestClient) -> None:
    """Dashboard stats should be authorized, owner-scoped, cached, and invalidated."""
    assert client.get("/api/dashboard/stats").status_code == 401
    register_response = client.post(
        "/api/auth/register",
        json={
            "email": "cache@example.com",
            "username": "cacheuser",
            "password": "secret123",
        },
    )
    assert register_response.status_code == 200
    owner_token = register_response.json()["access_token"]
    owner_headers = {"Authorization": f"Bearer {owner_token}"}

    initial_response = client.get(
        "/api/dashboard/stats", headers=owner_headers)
    assert initial_response.status_code == 200
    assert initial_response.json()["active_users"] == 1
    owner_id = register_response.json()["user"]["id"]
    owner_cache_key = dashboard_stats_cache_key(owner_id)
    assert cache_service.get(owner_cache_key) is not None

    incident_response = client.post(
        "/api/incidents",
        json={"title": "Dashboard cache invalidation"},
        headers=owner_headers,
    )
    assert incident_response.status_code == 201
    assert cache_service.get(owner_cache_key) is None
    refreshed_response = client.get(
        "/api/dashboard/stats", headers=owner_headers)
    assert refreshed_response.json()["total_incidents"] == 1

    other_response = client.post(
        "/api/auth/register",
        json={"email": "other-cache@example.com",
              "username": "other-cache", "password": "secret123"},
    )
    other_headers = {
        "Authorization": f"Bearer {other_response.json()['access_token']}"}
    other_stats = client.get("/api/dashboard/stats", headers=other_headers)
    assert other_stats.json()["total_incidents"] == 0
    assert other_stats.json()["active_users"] == 1
