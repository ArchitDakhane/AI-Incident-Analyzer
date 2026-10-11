"""Incident cache keys and invalidation helpers."""

from __future__ import annotations

from typing import Any

from app.core.cache import cache_service

AI_REPORT_CACHE_PREFIX = "ai_report:"
AI_REPORT_CACHE_TTL_SECONDS = 600


def ai_report_cache_key(incident_id: int, log_file_id: int | None = None) -> str:
    """Return a report cache key scoped to the incident and selected log."""
    if log_file_id is None:
        return f"{AI_REPORT_CACHE_PREFIX}{incident_id}"
    return f"{AI_REPORT_CACHE_PREFIX}{incident_id}:log:{log_file_id}"


def get_cached_ai_report(incident_id: int, log_file_id: int | None = None) -> Any | None:
    """Return a cached AI analysis payload for an incident, if present."""
    return cache_service.get(ai_report_cache_key(incident_id, log_file_id))


def cache_ai_report(
    incident_id: int,
    payload: dict[str, Any],
    *,
    log_file_id: int | None = None,
) -> None:
    """Cache an AI analysis payload for an incident."""
    cache_service.set(
        ai_report_cache_key(incident_id, log_file_id),
        payload,
        ttl_seconds=AI_REPORT_CACHE_TTL_SECONDS,
    )


def invalidate_ai_report_cache(incident_id: int) -> None:
    """Remove cached AI analysis for an incident."""
    cache_service.delete(ai_report_cache_key(incident_id))
    cache_service.invalidate_prefix(
        f"{AI_REPORT_CACHE_PREFIX}{incident_id}:log:")
