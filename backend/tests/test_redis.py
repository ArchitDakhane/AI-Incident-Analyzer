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
from app.services.dashboard import DASHBOARD_STATS_CACHE_KEY
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


def test_dashboard_stats_are_cached_and_invalidated(client: TestClient) -> None:
    """Dashboard stats should be cached and invalidated when dependent data changes."""
    initial_response = client.get("/api/dashboard/stats")
    assert initial_response.status_code == 200
    assert initial_response.json()["active_users"] == 0
    assert cache_service.get(DASHBOARD_STATS_CACHE_KEY) is not None

    register_response = client.post(
        "/api/auth/register",
        json={
            "email": "cache@example.com",
            "username": "cacheuser",
            "password": "secret123",
        },
    )
    assert register_response.status_code == 200

    refreshed_response = client.get("/api/dashboard/stats")
    assert refreshed_response.status_code == 200
    assert refreshed_response.json()["active_users"] == 1
