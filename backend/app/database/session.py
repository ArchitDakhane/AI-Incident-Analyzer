"""Database session management and engine configuration."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.database.base import Base


def create_database_engine(database_url: str | None = None):
    """Create a SQLAlchemy engine for the configured database URL."""
    url = database_url or settings.DATABASE_URL
    return create_engine(url, pool_pre_ping=True, echo=settings.SQLALCHEMY_ECHO)


engine = create_database_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Yield a database session for dependency injection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables for the current metadata."""
    Base.metadata.create_all(bind=engine)
