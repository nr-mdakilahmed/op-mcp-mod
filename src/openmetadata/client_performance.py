"""Performance utilities for OpenMetadata clients.

This module provides reusable performance enhancements like caching, retry logic,
and connection pooling that can be applied to any HTTP client or OpenMetadata client.

This is the foundational layer that enhanced_client.py builds upon.
"""

from collections.abc import Callable
from contextlib import contextmanager
import functools
import logging
import time
from typing import Any

from cachetools import TTLCache
import httpx

# Configure module logger
logger = logging.getLogger(__name__)

# Define caches with appropriate TTLs
# Short-lived cache for frequently accessed data that changes often
SHORT_CACHE = TTLCache(maxsize=100, ttl=60)  # 1 minute TTL
# Medium-lived cache for data that changes occasionally
MEDIUM_CACHE = TTLCache(maxsize=200, ttl=300)  # 5 minutes TTL
# Long-lived cache for relatively static data
LONG_CACHE = TTLCache(maxsize=500, ttl=3600)  # 1 hour TTL

# Define entity types and their cache durations
CACHE_POLICY = {
    # Long cache duration for relatively static data
    "classifications": LONG_CACHE,
    "teams": LONG_CACHE,
    "users": MEDIUM_CACHE,
    "roles": LONG_CACHE,
    "policies": LONG_CACHE,
    "glossaries": MEDIUM_CACHE,
    "glossaryTerms": MEDIUM_CACHE,
    "tags": LONG_CACHE,
    # Medium cache duration for semi-static data
    "databaseServices": MEDIUM_CACHE,
    "dashboardServices": MEDIUM_CACHE,
    "messagingServices": MEDIUM_CACHE,
    "pipelineServices": MEDIUM_CACHE,
    "mlmodelServices": MEDIUM_CACHE,
    "databases": MEDIUM_CACHE,
    "schemas": MEDIUM_CACHE,
    # Short cache duration for frequently changing data
    "tables": SHORT_CACHE,
    "dashboards": SHORT_CACHE,
    "topics": SHORT_CACHE,
    "pipelines": SHORT_CACHE,
    "charts": SHORT_CACHE,
    "mlmodels": SHORT_CACHE,
    # No caching for search and other dynamic operations
    "search": None,
    "lineage": None,
    "usage": None,
}


def generate_cache_key(endpoint: str, params: dict[str, Any] | None = None) -> str:
    """Generate a cache key from endpoint and params.

    Args:
        endpoint: API endpoint
        params: Request parameters

    Returns:
        String cache key
    """
    if params:
        # Convert params dict to sorted, stable string representation
        param_str = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
        return f"{endpoint}?{param_str}"
    return endpoint


def get_cache_for_endpoint(endpoint: str) -> TTLCache | None:
    """Get the appropriate cache for the given endpoint.

    Args:
        endpoint: API endpoint

    Returns:
        Cache instance or None if endpoint should not be cached
    """
    # Extract the entity type from the endpoint path
    parts = endpoint.strip("/").split("/")
    entity_type = parts[0] if parts else None

    # Return the appropriate cache based on entity type
    return CACHE_POLICY.get(entity_type)


def with_retry(max_retries: int = 3, backoff_factor: float = 0.5) -> Callable:
    """Decorator to retry API calls with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        backoff_factor: Backoff factor for retries

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            retries = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except (httpx.HTTPStatusError, httpx.NetworkError, httpx.TimeoutException) as e:
                    retries += 1
                    if retries > max_retries:
                        logger.error(
                            "Maximum retries exceeded for endpoint: %s - %s", kwargs.get("endpoint", "unknown"), str(e)
                        )
                        raise

                    # Calculate backoff time with exponential increase
                    backoff_time = backoff_factor * (2 ** (retries - 1))
                    logger.warning(
                        "Request failed, retrying in %.2fs",
                        backoff_time,
                        extra={"attempt": retries, "max_retries": max_retries, "error": str(e)},
                    )
                    time.sleep(backoff_time)

        return wrapper

    return decorator


def with_caching(func: Callable) -> Callable:
    """Decorator to add caching to API calls.

    Args:
        func: Function to decorate

    Returns:
        Decorated function with caching
    """

    @functools.wraps(func)
    def wrapper(self, endpoint: str, *args, **kwargs) -> Any:
        method = kwargs.get("method", "GET")

        # Only cache GET requests
        if method != "GET":
            return func(self, endpoint, *args, **kwargs)

        # Get the appropriate cache for this endpoint
        cache = get_cache_for_endpoint(endpoint)
        if cache is None:
            # No caching for this endpoint
            return func(self, endpoint, *args, **kwargs)

        # Generate cache key
        params = kwargs.get("params")
        cache_key = generate_cache_key(endpoint, params)

        # Check cache
        if cache_key in cache:
            logger.debug("Cache hit for endpoint: %s", endpoint, extra={"params": params})
            return cache[cache_key]

        # Execute request
        result = func(self, endpoint, *args, **kwargs)

        # Store in cache
        cache[cache_key] = result
        logger.debug("Cache miss - stored result for endpoint: %s", endpoint, extra={"params": params})

        return result

    return wrapper


@contextmanager
def connection_pool_context(max_connections: int = 20):
    """Context manager for HTTP connection pooling.

    Args:
        max_connections: Maximum number of connections in the pool

    Yields:
        Connection pool limits instance
    """
    limits = httpx.Limits(max_connections=max_connections)
    yield limits


def clear_cache(entity_type: str | None = None) -> None:
    """Clear cache for a specific entity type or all caches.

    Args:
        entity_type: Specific entity type to clear, or None for all caches
    """
    if entity_type:
        cache = CACHE_POLICY.get(entity_type)
        if cache:
            cache.clear()
            logger.info("Cleared cache for entity type: %s", entity_type)
    else:
        # Clear all caches
        SHORT_CACHE.clear()
        MEDIUM_CACHE.clear()
        LONG_CACHE.clear()
        logger.info("Cleared all caches")


def get_cache_stats() -> dict[str, dict[str, Any]]:
    """Get statistics for all caches.

    Returns:
        Dictionary containing cache statistics
    """
    return {
        "short_cache": {
            "size": len(SHORT_CACHE),
            "maxsize": SHORT_CACHE.maxsize,
            "ttl": SHORT_CACHE.ttl,
            "hits": getattr(SHORT_CACHE, "hits", 0),
            "misses": getattr(SHORT_CACHE, "misses", 0),
        },
        "medium_cache": {
            "size": len(MEDIUM_CACHE),
            "maxsize": MEDIUM_CACHE.maxsize,
            "ttl": MEDIUM_CACHE.ttl,
            "hits": getattr(MEDIUM_CACHE, "hits", 0),
            "misses": getattr(MEDIUM_CACHE, "misses", 0),
        },
        "long_cache": {
            "size": len(LONG_CACHE),
            "maxsize": LONG_CACHE.maxsize,
            "ttl": LONG_CACHE.ttl,
            "hits": getattr(LONG_CACHE, "hits", 0),
            "misses": getattr(LONG_CACHE, "misses", 0),
        },
    }


# Export the key components for use by enhanced_client.py
__all__ = [
    "SHORT_CACHE",
    "MEDIUM_CACHE",
    "LONG_CACHE",
    "CACHE_POLICY",
    "with_retry",
    "with_caching",
    "connection_pool_context",
    "generate_cache_key",
    "get_cache_for_endpoint",
    "clear_cache",
    "get_cache_stats",
]
