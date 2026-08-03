"""pytest configuration and fixtures."""
import os

import pytest

os.environ["DEBUG"] = "False"


@pytest.fixture(autouse=True)
def reset_cache_service():
    """Keep Redis-backed tests isolated from each other and local Redis state."""
    from app.core.cache import InMemoryCache, cache_service

    cache_service.fallback = InMemoryCache()
    cache_service.client = InMemoryCache()
    yield
    cache_service.fallback = InMemoryCache()
    cache_service.client = InMemoryCache()


@pytest.fixture
def app():
    """FastAPI application instance for testing."""
    from main import create_app

    return create_app()


@pytest.fixture
def client(app):  # type: ignore
    """FastAPI test client."""
    from fastapi.testclient import TestClient

    return TestClient(app)
