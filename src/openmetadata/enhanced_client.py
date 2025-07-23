"""Enhanced OpenMetadata client with improved performance.

This module provides the primary interface for performance-enhanced OpenMetadata clients.
It builds upon the foundational performance utilities in client_performance.py to provide
OpenMetadata-specific optimizations including:

- Intelligent caching based on entity types
- Connection pooling with configurable limits
- Automatic retry with exponential backoff
- Comprehensive error handling and logging
- Both synchronous and asynchronous client support

This is the recommended client for production use.
"""

import logging
from typing import Any

import httpx

from src.openmetadata.client_performance import (
    clear_cache,
    connection_pool_context,
    get_cache_stats,
    with_caching,
    with_retry,
)
from src.openmetadata.openmetadata_client import AsyncOpenMetadataClient, OpenMetadataClient

# Configure module logger
logger = logging.getLogger(__name__)


class EnhancedOpenMetadataClient(OpenMetadataClient):
    """OpenMetadata client with enhanced performance features."""

    def __init__(
        self,
        host: str,
        api_token: str | None = None,
        username: str | None = None,
        password: str | None = None,
        max_connections: int = 20,
        retry_max_attempts: int = 3,
        retry_backoff_factor: float = 0.5,
    ):
        """Initialize enhanced OpenMetadata client.

        Args:
            host: OpenMetadata host URL
            api_token: JWT token for API authentication
            username: Username for basic authentication
            password: Password for basic authentication
            max_connections: Maximum number of connections in the pool
            retry_max_attempts: Maximum number of retry attempts
            retry_backoff_factor: Backoff factor for retries
        """
        # Store retry configuration for decorators
        self.retry_max_attempts = retry_max_attempts
        self.retry_backoff_factor = retry_backoff_factor

        # Initialize the parent class with connection details
        super().__init__(host, api_token, username, password)

        # Initialize connection pool
        with connection_pool_context(max_connections) as limits:
            transport = httpx.HTTPTransport(limits=limits)
            timeout = httpx.Timeout(10.0, connect=5.0)

            # Initialize client with connection pool
            self._client = httpx.Client(base_url=host, transport=transport, timeout=timeout, follow_redirects=True)

        # Configure authentication
        if api_token:
            self._client.headers.update({"Authorization": f"Bearer {api_token}"})
        elif username and password:
            # Handle basic auth
            self._client.auth = (username, password)
        else:
            # Anonymous access
            pass

        # Set common headers
        self._client.headers.update(
            {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "EnhancedOpenMetadataClient/1.0",
            }
        )

        self.host = host
        logger.info("Enhanced OpenMetadata client initialized for host: %s", host)

    @with_caching
    @with_retry(max_retries=3, backoff_factor=0.5)
    def get(self, endpoint: str, params: dict[str, Any] | None = None, **kwargs) -> dict[str, Any]:
        """Send a GET request to the OpenMetadata API with caching and retries.

        Args:
            endpoint: API endpoint
            params: Query parameters
            **kwargs: Additional arguments to pass to httpx

        Returns:
            Response JSON

        Raises:
            OpenMetadataError: If the request fails
        """
        return super().get(endpoint, params, **kwargs)

    def clear_cache(self, entity_type: str | None = None) -> None:
        """Clear the cache for the given entity type or all caches.

        Args:
            entity_type: Entity type to clear cache for, or None to clear all
        """
        clear_cache(entity_type)

    def get_cache_statistics(self) -> dict[str, Any]:
        """Get cache statistics for monitoring and debugging.

        Returns:
            Dictionary containing cache statistics
        """
        return get_cache_stats()


class EnhancedAsyncOpenMetadataClient(AsyncOpenMetadataClient):
    """Async OpenMetadata client with enhanced performance features."""

    def __init__(
        self,
        host: str,
        api_token: str | None = None,
        username: str | None = None,
        password: str | None = None,
        max_connections: int = 20,
    ):
        """Initialize enhanced async OpenMetadata client.

        Args:
            host: OpenMetadata host URL
            api_token: JWT token for API authentication
            username: Username for basic authentication
            password: Password for basic authentication
            max_connections: Maximum number of connections in the pool
        """
        # Initialize the parent class with connection details
        super().__init__(host, api_token, username, password)

        # Initialize with connection pool
        with connection_pool_context(max_connections) as limits:
            timeout = httpx.Timeout(10.0, connect=5.0)

            # Initialize async client with connection pool
            self._client = httpx.AsyncClient(base_url=host, limits=limits, timeout=timeout, follow_redirects=True)

        # Configure authentication
        if api_token:
            self._client.headers.update({"Authorization": f"Bearer {api_token}"})
        elif username and password:
            self._client.auth = (username, password)

        self._client.headers.update(
            {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "EnhancedAsyncOpenMetadataClient/1.0",
            }
        )

        self.host = host
        logger.info("Enhanced Async OpenMetadata client initialized for host: %s", host)

    def clear_cache(self, entity_type: str | None = None) -> None:
        """Clear the cache for the given entity type or all caches."""
        clear_cache(entity_type)

    def get_cache_statistics(self) -> dict[str, Any]:
        """Get cache statistics for monitoring and debugging."""
        return get_cache_stats()


# Initialize and get client functions
_enhanced_client: EnhancedOpenMetadataClient | None = None
_enhanced_async_client: EnhancedAsyncOpenMetadataClient | None = None


def initialize_enhanced_client(
    host: str,
    api_token: str | None = None,
    username: str | None = None,
    password: str | None = None,
    max_connections: int = 20,
) -> None:
    """Initialize the global enhanced OpenMetadata client.

    Args:
        host: OpenMetadata host URL
        api_token: JWT token for API authentication
        username: Username for basic authentication
        password: Password for basic authentication
        max_connections: Maximum number of connections in the pool
    """
    global _enhanced_client  # pylint: disable=global-statement
    _enhanced_client = EnhancedOpenMetadataClient(host, api_token, username, password, max_connections)
    logger.info("Enhanced OpenMetadata client initialized for host: %s", host)


def get_enhanced_client() -> EnhancedOpenMetadataClient:
    """Get the global enhanced OpenMetadata client instance.

    Returns:
        The initialized enhanced OpenMetadata client

    Raises:
        RuntimeError: If client has not been initialized
    """
    if _enhanced_client is None:
        raise RuntimeError("Enhanced OpenMetadata client not initialized. Call initialize_enhanced_client() first.")
    return _enhanced_client
