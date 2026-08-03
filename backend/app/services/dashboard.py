"""Dashboard statistics service with Redis caching."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.cache import cache_service
from app.models.ai_report import AIReport
from app.models.incident import Incident
from app.models.user import User

DASHBOARD_CACHE_PREFIX = "dashboard:"
DASHBOARD_STATS_CACHE_KEY = f"{DASHBOARD_CACHE_PREFIX}stats"
DASHBOARD_STATS_TTL_SECONDS = 120


def invalidate_dashboard_cache() -> None:
    """Invalidate cached dashboard data after incident or report changes."""
    cache_service.invalidate_prefix(DASHBOARD_CACHE_PREFIX)


def get_dashboard_stats(db: Session) -> dict[str, int]:
    """Return dashboard statistics, using Redis as a short-lived cache."""
    cached_stats = cache_service.get(DASHBOARD_STATS_CACHE_KEY)
    if isinstance(cached_stats, dict):
        return {key: int(value) for key, value in cached_stats.items()}

    stats = {
        "total_incidents": db.query(Incident).count(),
        "open_incidents": db.query(Incident).filter(Incident.status == "open").count(),
        "critical_incidents": db.query(Incident).filter(Incident.severity == "critical").count(),
        "resolved_incidents": db.query(Incident).filter(Incident.status == "resolved").count(),
        "total_ai_reports": db.query(AIReport).count(),
        "active_users": db.query(User).filter(User.is_active.is_(True)).count(),
    }
    cache_service.set(DASHBOARD_STATS_CACHE_KEY, stats, ttl_seconds=DASHBOARD_STATS_TTL_SECONDS)
    return stats
