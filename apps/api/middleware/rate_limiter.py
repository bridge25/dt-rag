"""
Rate Limiting Middleware for DT-RAG API

Implements tiered rate limiting with Redis backend:
- Read operations (GET): 100 requests/minute
- Write operations (POST/PUT/DELETE): 50 requests/minute
- Admin operations: 200 requests/minute

Uses Fixed Window algorithm with Redis for distributed rate limiting.
"""

import os
import time
import logging
from typing import Callable, Optional
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

# Rate limit tiers (requests per window)
RATE_LIMIT_READ = int(os.getenv("RATE_LIMIT_READ", "100"))
RATE_LIMIT_WRITE = int(os.getenv("RATE_LIMIT_WRITE", "50"))
RATE_LIMIT_ADMIN = int(os.getenv("RATE_LIMIT_ADMIN", "200"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))  # seconds

# Redis configuration for rate limiting
REDIS_RATE_LIMIT_ENABLED = (
    os.getenv("REDIS_RATE_LIMIT_ENABLED", "true").lower() == "true"
)
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB_RATE_LIMIT", "1"))


class RedisRateLimiter:
    """
    Redis-based rate limiter using Fixed Window algorithm
    """

    def __init__(self):
        self.redis_client: Optional[aioredis.Redis] = None
        self.enabled = REDIS_RATE_LIMIT_ENABLED

    async def initialize(self):
        """Initialize Redis connection"""
        if not self.enabled:
            logger.info("Rate limiting disabled (REDIS_RATE_LIMIT_ENABLED=false)")
            return

        try:
            self.redis_client = await aioredis.from_url(
                f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}",
                encoding="utf-8",
                decode_responses=True,
            )
            await self.redis_client.ping()
            logger.info(
                f"Rate limiter initialized with Redis at {REDIS_HOST}:{REDIS_PORT}"
            )
        except Exception as e:
            logger.error(f"Failed to connect to Redis for rate limiting: {e}")
            self.enabled = False

    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()

    async def check_rate_limit(
        self, identifier: str, limit: int, window: int = RATE_LIMIT_WINDOW
    ) -> tuple[bool, int, int]:
        """
        Check if request is within rate limit

        Args:
            identifier: Unique identifier (API key or IP)
            limit: Maximum requests allowed in window
            window: Time window in seconds

        Returns:
            (is_allowed, current_count, remaining)
        """
        if not self.enabled or not self.redis_client:
            return True, 0, limit  # Allow all if disabled

        try:
            # Generate window-based key
            current_window = int(time.time()) // window
            key = f"ratelimit:{identifier}:{current_window}"

            # Increment counter
            current = await self.redis_client.incr(key)

            # Set expiry on first request in window
            if current == 1:
                await self.redis_client.expire(key, window)

            # Check if limit exceeded
            is_allowed = current <= limit
            remaining = max(0, limit - current)

            return is_allowed, current, remaining

        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            return True, 0, limit  # Fail open on error


# Global rate limiter instance
rate_limiter = RedisRateLimiter()


def get_client_identifier(request: Request) -> str:
    """
    Extract API key or IP address for rate limiting
    Priority: API Key > IP Address
    """
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return f"apikey:{api_key[:16]}"

    # Get client IP
    if request.client:
        return f"ip:{request.client.host}"

    return "ip:unknown"


def get_rate_limit_for_method(method: str) -> int:
    """
    Get rate limit based on HTTP method
    """
    if method == "GET":
        return RATE_LIMIT_READ
    elif method in ["POST", "PUT", "PATCH", "DELETE"]:
        return RATE_LIMIT_WRITE
    else:
        return RATE_LIMIT_READ


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware that applies different limits based on HTTP method
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Apply rate limiting based on HTTP method"""
        # Skip rate limiting for health check
        if request.url.path == "/health":
            return await call_next(request)

        # Get client identifier
        identifier = get_client_identifier(request)

        # Get rate limit for method
        limit = get_rate_limit_for_method(request.method)

        # Check rate limit
        is_allowed, current, remaining = await rate_limiter.check_rate_limit(
            identifier, limit, RATE_LIMIT_WINDOW
        )

        if not is_allowed:
            logger.warning(
                f"Rate limit exceeded for {identifier} "
                f"on {request.method} {request.url.path} "
                f"({current}/{limit} in {RATE_LIMIT_WINDOW}s window)"
            )
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "limit": limit,
                    "window": RATE_LIMIT_WINDOW,
                    "current": current,
                    "retry_after": RATE_LIMIT_WINDOW,
                },
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(
            (int(time.time()) // RATE_LIMIT_WINDOW + 1) * RATE_LIMIT_WINDOW
        )

        return response


__all__ = [
    "rate_limiter",
    "RateLimitMiddleware",
    "RATE_LIMIT_READ",
    "RATE_LIMIT_WRITE",
    "RATE_LIMIT_ADMIN",
]
