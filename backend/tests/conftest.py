"""pytest configuration and fixtures."""
import pytest


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
