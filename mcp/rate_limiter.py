"""
Rate limiting middleware for MCP server using Redis.
Implements distributed rate limiting across Railway containers.
"""

import os
import logging
from typing import Optional
from datetime import datetime
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.requests import Request
from starlette.responses import JSONResponse
import redis

logger = logging.getLogger(__name__)

# Rate limiting configuration
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "10"))
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Global rate limiter instance
limiter: Optional[Limiter] = None
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
    return get_remote_address(request)

def init_redis_connection() -> Optional[redis.Redis]:
    """
    Initialize Redis connection for distributed rate limiting.
    Returns None if Redis unavailable (will fallback to in-memory).
    """
    try:
        logger.info(f"[RATE_LIMIT_INIT] Attempting Redis connection: {REDIS_URL.split('@')[-1]}")  # Hide password

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
        logger.warning(f"[RATE_LIMIT_INIT] ⚠️ Redis connection failed: {e}")
        logger.warning("[RATE_LIMIT_INIT] Falling back to in-memory rate limiting (per-container)")
        return None
    except Exception as e:
        logger.error(f"[RATE_LIMIT_INIT] ❌ Unexpected Redis error: {e}")
        return None

def init_rate_limiter() -> Limiter:
    """
    Initialize SlowAPI rate limiter with Redis backend (or in-memory fallback).

    Returns configured Limiter instance ready for use as decorator.
    """
    global limiter, redis_client

    if not RATE_LIMIT_ENABLED:
        logger.info("[RATE_LIMIT_INIT] Rate limiting DISABLED via environment variable")
        # Return a no-op limiter
        return Limiter(key_func=get_real_client_ip, enabled=False)

    # Try to connect to Redis
    redis_client = init_redis_connection()

    if redis_client:
        # Use Redis for distributed rate limiting
        logger.info(f"[RATE_LIMIT_INIT] Configuring distributed rate limiting: {RATE_LIMIT_PER_MINUTE} req/min per IP")

        limiter = Limiter(
            key_func=get_real_client_ip,
            storage_uri=REDIS_URL,
            default_limits=[],  # No default limits, we'll use decorators
            enabled=True,
            headers_enabled=True,  # Add X-RateLimit-* headers
            swallow_errors=True  # Don't crash if Redis fails mid-request
        )
    else:
        # Fallback to in-memory (per-container)
        logger.warning(f"[RATE_LIMIT_INIT] Using in-memory rate limiting: {RATE_LIMIT_PER_MINUTE} req/min per IP (per container)")
        logger.warning("[RATE_LIMIT_INIT] ⚠️ WARNING: Multiple Railway containers will have separate limits!")

        limiter = Limiter(
            key_func=get_real_client_ip,
            default_limits=[],
            enabled=True,
            headers_enabled=True
        )

    logger.info("[RATE_LIMIT_INIT] Rate limiter initialized successfully")
    return limiter

def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """
    Custom error handler for rate limit exceeded (429).
    Returns helpful JSON response with retry information.
    """
    client_ip = get_real_client_ip(request)
    endpoint = request.url.path

    # Extract retry_after from exception (seconds until reset)
    retry_after = int(exc.detail.split("Retry after ")[1].split(" seconds")[0]) if "Retry after" in exc.detail else 60

    logger.warning(f"[RATE_LIMIT] IP {client_ip} exceeded {RATE_LIMIT_PER_MINUTE}/min on {endpoint}")

    error_response = {
        "error": "Rate limit exceeded",
        "message": f"You have exceeded {RATE_LIMIT_PER_MINUTE} requests per minute. Please try again in {retry_after} seconds.",
        "retry_after": retry_after,
        "limit": f"{RATE_LIMIT_PER_MINUTE} per minute",
        "ip": client_ip,
        "endpoint": endpoint,
        "timestamp": datetime.now().isoformat()
    }

    return JSONResponse(
        status_code=429,
        content=error_response,
        headers={
            "Retry-After": str(retry_after),
            "X-RateLimit-Limit": str(RATE_LIMIT_PER_MINUTE),
            "X-RateLimit-Remaining": "0",
        }
    )

def get_rate_limit_stats() -> dict:
    """
    Get current rate limiting statistics for monitoring.
    Returns info about backend, tracked IPs, violations, etc.
    """
    try:
        stats = {
            "enabled": RATE_LIMIT_ENABLED,
            "limit": f"{RATE_LIMIT_PER_MINUTE} per minute",
            "backend": "redis" if redis_client else "in-memory",
            "redis_connected": False,
            "total_keys": 0,
            "violations_tracked": 0
        }

        if redis_client:
            # Test Redis connection
            redis_client.ping()
            stats["redis_connected"] = True

            # Count rate limit keys in Redis
            slowapi_keys = redis_client.keys("slowapi:*")
            stats["total_keys"] = len(slowapi_keys) if slowapi_keys else 0

            # Count IPs being tracked (unique prefixes)
            if slowapi_keys:
                unique_ips = set()
                for key in slowapi_keys:
                    # Key format: slowapi:{ip}:{endpoint}
                    parts = key.split(":")
                    if len(parts) >= 2:
                        unique_ips.add(parts[1])
                stats["unique_ips_tracked"] = len(unique_ips)

        return stats

    except Exception as e:
        logger.error(f"[RATE_LIMIT] Error getting stats: {e}")
        return {
            "enabled": RATE_LIMIT_ENABLED,
            "error": str(e)
        }

# Initialize on module import
logger.info("[RATE_LIMIT_INIT] Initializing rate limiting module...")
limiter = init_rate_limiter()
