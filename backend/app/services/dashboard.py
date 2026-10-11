"""Dashboard statistics service with Redis caching."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.cache import cache_service
from app.models.ai_report import AIReport
from app.models.incident import Incident
from app.models.user import User

DASHBOARD_CACHE_PREFIX = "dashboard:"
DASHBOARD_STATS_TTL_SECONDS = 120


def dashboard_stats_cache_key(user_id: int) -> str:
    """Build a user-isolated dashboard stats cache key."""
    return f"{DASHBOARD_CACHE_PREFIX}{user_id}:stats"


def invalidate_dashboard_cache() -> None:
    """Invalidate cached dashboard data after incident or report changes."""
    cache_service.invalidate_prefix(DASHBOARD_CACHE_PREFIX)


def get_dashboard_stats(db: Session, *, user_id: int) -> dict[str, int]:
    """Return statistics for one user, using Redis as a short-lived cache."""
    cache_key = dashboard_stats_cache_key(user_id)
    cached_stats = cache_service.get(cache_key)
    if isinstance(cached_stats, dict):
        return {key: int(value) for key, value in cached_stats.items()}

    stats = {
        "total_incidents": db.query(Incident).filter(Incident.created_by_id == user_id).count(),
        "open_incidents": db.query(Incident)
        .filter(Incident.created_by_id == user_id, Incident.status == "open")
        .count(),
        "critical_incidents": db.query(Incident)
        .filter(Incident.created_by_id == user_id, Incident.severity == "critical")
        .count(),
        "resolved_incidents": db.query(Incident)
        .filter(Incident.created_by_id == user_id, Incident.status == "resolved")
        .count(),
        "total_ai_reports": db.query(AIReport).filter(AIReport.created_by_id == user_id).count(),
        "active_users": (
            db.query(User)
            .filter(User.id == user_id, User.is_active.is_(True))
            .count()
        ),
    }
    cache_service.set(cache_key, stats,
                      ttl_seconds=DASHBOARD_STATS_TTL_SECONDS)
    return stats
