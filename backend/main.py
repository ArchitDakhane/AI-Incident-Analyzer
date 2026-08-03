"""Application entry point."""
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.auth import router as auth_router
from app.core import configure_logging, get_logger, settings
from app.database.session import get_db
from app.incidents import router as incidents_router
from app.middleware.rate_limit import RateLimitMiddleware
from app.services.dashboard import get_dashboard_stats

# Configure logging before anything else
configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore
    """Application lifespan context manager.

    Handles startup and shutdown events.
    """
    # Startup
    logger.info(f"Starting {settings.API_TITLE} v{settings.API_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug: {settings.DEBUG}")
    yield
    # Shutdown
    logger.info("Shutting down application")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        FastAPI application instance

    """
    app = FastAPI(
        title=settings.API_TITLE,
        version=settings.API_VERSION,
        description="AI-powered incident analysis system",
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RateLimitMiddleware, max_requests=60, window_seconds=60)

    app.include_router(auth_router)
    app.include_router(incidents_router)

    # Health check endpoint
    @app.get("/api/health", tags=["Health"])
    async def health_check() -> dict[str, str]:
        """Health check endpoint for monitoring."""
        return {"status": "healthy", "version": settings.API_VERSION}

    # API Info endpoint
    @app.get("/api/info", tags=["Info"])
    async def api_info() -> dict[str, str]:
        """Get API information."""
        return {
            "title": settings.API_TITLE,
            "version": settings.API_VERSION,
            "environment": settings.ENVIRONMENT,
        }

    @app.get("/api/dashboard/stats", tags=["Dashboard"])
    async def dashboard_stats(db: Session = Depends(get_db)) -> dict[str, int]:
        """Return cached dashboard statistics for the UI."""
        return get_dashboard_stats(db)

    logger.info("FastAPI application created successfully")
    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
