"""Tests for the database layer."""

from app.database import Base, SessionLocal
from app.database.session import create_database_engine
from app.models import AIReport, Comment, Incident, LogFile, User  # noqa: F401


def test_database_engine_is_configured() -> None:
    """The database engine should be created from the configured URL."""
    engine = create_database_engine("postgresql://user:password@localhost:5432/test_db")

    assert engine is not None
    assert engine.url.get_backend_name() == "postgresql"


def test_models_register_expected_tables() -> None:
    """The declarative metadata should include the expected tables."""
    table_names = set(Base.metadata.tables.keys())

    assert "users" in table_names
    assert "incidents" in table_names
    assert "log_files" in table_names
    assert "ai_reports" in table_names
    assert "comments" in table_names


def test_session_factory_is_configured() -> None:
    """The session factory should be available for dependency injection."""
    assert SessionLocal is not None
