"""
Rate limiting middleware for MCP server using Redis.
Implements distributed rate limiting at the HTTP layer before FastMCP.
"""

import os
import logging
import time
from typing import Optional
from datetime import datetime
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
import redis

logger = logging.getLogger(__name__)

# Rate limiting configuration
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "10"))
RATE_LIMIT_WINDOW = 60  # seconds
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Global Redis client
redis_client: Optional[redis.Redis] = None

def get_real_client_ip(request: Request) -> str:
    """
    Extract real client IP from request, handling Railway proxy headers.

    Railway uses X-Forwarded-For header with format: "client_ip, proxy1_ip, proxy2_ip"
    We take the first IP which is the real client IP.
    """
    # Check for X-Forwarded-For header (Railway proxy)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take first IP in comma-separated list
        client_ip = forwarded_for.split(",")[0].strip()
        return client_ip

    # Check for X-Real-IP header (alternative proxy header)
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    # Fallback to direct connection IP
    if request.client:
        return request.client.host

    return "unknown"

def init_redis_connection() -> Optional[redis.Redis]:
    """
    Initialize Redis connection for distributed rate limiting.
    Returns None if Redis unavailable (will disable rate limiting).
    """
    try:
        logger.info(f"[RATE_LIMIT_INIT] Attempting Redis connection...")

        # Parse Redis URL and create client
        client = redis.from_url(
            REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30
        )

        # Test connection
        client.ping()
        logger.info("[RATE_LIMIT_INIT] ✅ Redis connected successfully")
        return client

    except redis.ConnectionError as e:
        logger.warning(f"[RATE_LIMIT_INIT] ⚠️  Redis connection failed: {e}")
        logger.warning("[RATE_LIMIT_INIT] Rate limiting DISABLED (no Redis)")
        return None
    except Exception as e:
        logger.error(f"[RATE_LIMIT_INIT] ❌ Unexpected Redis error: {e}")
        return None

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Starlette middleware for rate limiting at HTTP layer.
    Intercepts requests before they reach FastMCP.
    """

    def __init__(self, app):
        super().__init__(app)
        global redis_client

        # Initialize Redis connection
        if not redis_client and RATE_LIMIT_ENABLED:
            redis_client = init_redis_connection()

            if redis_client:
                logger.info(f"[RATE_LIMIT_INIT] Middleware active: {RATE_LIMIT_PER_MINUTE} req/min per IP")
            else:
                logger.warning("[RATE_LIMIT_INIT] Middleware running without Redis (rate limiting disabled)")

        self.redis = redis_client

    async def dispatch(self, request: Request, call_next):
        """
        Intercept all HTTP requests and apply rate limiting.
        """
        # Exempt health and SSE endpoints from rate limiting
        if request.url.path in ["/health", "/sse"]:
            return await call_next(request)

        # Only rate limit MCP endpoint
        if not request.url.path.startswith("/mcp") and request.url.path != "/":
            return await call_next(request)

        # If Redis not available or rate limiting disabled, allow all requests
        if not self.redis or not RATE_LIMIT_ENABLED:
            return await call_next(request)

        # Extract client IP
        client_ip = get_real_client_ip(request)

        # Check rate limit
        try:
            is_allowed, retry_after = self._check_rate_limit(client_ip)

            if not is_allowed:
                # Rate limit exceeded
                logger.warning(f"[RATE_LIMIT] IP {client_ip} exceeded {RATE_LIMIT_PER_MINUTE}/min on {request.url.path}")

                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "Rate limit exceeded",
                        "message": f"You have exceeded {RATE_LIMIT_PER_MINUTE} requests per minute. Please try again in {retry_after} seconds.",
                        "retry_after": retry_after,
                        "limit": f"{RATE_LIMIT_PER_MINUTE} per minute",
                        "ip": client_ip,
                        "endpoint": request.url.path,
                        "timestamp": datetime.now().isoformat()
                    },
                    headers={
                        "Retry-After": str(retry_after),
                        "X-RateLimit-Limit": str(RATE_LIMIT_PER_MINUTE),
                        "X-RateLimit-Remaining": "0",
                    }
                )

            # Request allowed - continue to FastMCP
            response = await call_next(request)

            # Add rate limit headers to successful responses
            remaining = self._get_remaining_requests(client_ip)
            response.headers["X-RateLimit-Limit"] = str(RATE_LIMIT_PER_MINUTE)
            response.headers["X-RateLimit-Remaining"] = str(remaining)

            return response

        except Exception as e:
            logger.error(f"[RATE_LIMIT] Error checking rate limit: {e}")
            # On error, allow request (fail open)
            return await call_next(request)

    def _check_rate_limit(self, client_ip: str) -> tuple[bool, int]:
        """
        Check if client IP is within rate limit using Redis.

        Returns:
            (is_allowed, retry_after_seconds)
        """
        try:
            key = f"rate_limit:{client_ip}"

            # Get current count
            current_count = self.redis.get(key)

            if current_count is None:
                # First request in window - initialize
                self.redis.setex(key, RATE_LIMIT_WINDOW, 1)
                return (True, 0)

            current_count = int(current_count)

            if current_count >= RATE_LIMIT_PER_MINUTE:
                # Limit exceeded
                ttl = self.redis.ttl(key)
                retry_after = max(ttl, 1) if ttl > 0 else RATE_LIMIT_WINDOW
                return (False, retry_after)

            # Increment counter
            self.redis.incr(key)
            return (True, 0)

        except Exception as e:
            logger.error(f"[RATE_LIMIT] Redis error: {e}")
            # On Redis error, allow request (fail open)
            return (True, 0)

    def _get_remaining_requests(self, client_ip: str) -> int:
        """Get remaining requests in current window for client IP."""
        try:
            key = f"rate_limit:{client_ip}"
            current_count = self.redis.get(key)

            if current_count is None:
                return RATE_LIMIT_PER_MINUTE

            remaining = RATE_LIMIT_PER_MINUTE - int(current_count)
            return max(remaining, 0)

        except Exception as e:
            logger.error(f"[RATE_LIMIT] Error getting remaining requests: {e}")
            return RATE_LIMIT_PER_MINUTE

def get_rate_limit_stats() -> dict:
    """
    Get current rate limiting statistics for monitoring.
    Returns info about backend, tracked IPs, violations, etc.
    """
    try:
        stats = {
            "enabled": RATE_LIMIT_ENABLED,
            "limit": f"{RATE_LIMIT_PER_MINUTE} per minute",
            "backend": "redis" if redis_client else "disabled",
            "redis_connected": False,
            "total_keys": 0
        }

        if redis_client:
            # Test Redis connection
            redis_client.ping()
            stats["redis_connected"] = True

            # Count rate limit keys in Redis
            rate_limit_keys = redis_client.keys("rate_limit:*")
            stats["total_keys"] = len(rate_limit_keys) if rate_limit_keys else 0

            # Count unique IPs being tracked
            if rate_limit_keys:
                unique_ips = set()
                for key in rate_limit_keys:
                    # Key format: rate_limit:{ip}
                    ip = key.replace("rate_limit:", "")
                    unique_ips.add(ip)
                stats["unique_ips_tracked"] = len(unique_ips)

        return stats

    except Exception as e:
        logger.error(f"[RATE_LIMIT] Error getting stats: {e}")
        return {
            "enabled": RATE_LIMIT_ENABLED,
            "error": str(e)
        }

# Log initialization
logger.info("[RATE_LIMIT_INIT] Rate limiter module loaded")
