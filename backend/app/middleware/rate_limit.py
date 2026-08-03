"""Simple IP-based request rate limiting middleware."""

from __future__ import annotations

from typing import Callable

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.cache import cache_service


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Limit repeated requests per IP address for a short window."""

    def __init__(self, app, *, max_requests: int = 60, window_seconds: int = 60) -> None:
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.method == "OPTIONS":
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        key = (
            f"ratelimit:{self.max_requests}:{self.window_seconds}:"
            f"{client_ip}:{request.method}:{request.url.path}"
        )
        current_count = cache_service.increment(
            key, ttl_seconds=self.window_seconds)
        remaining = max(self.max_requests - current_count, 0)

        headers = {
            "X-RateLimit-Limit": str(self.max_requests),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Window": str(self.window_seconds),
        }

        if current_count > self.max_requests:
            headers["Retry-After"] = str(self.window_seconds)
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
                headers=headers,
            )

        response = await call_next(request)
        response.headers.update(headers)
        return response
