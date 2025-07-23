"""Centralized OpenMetadata REST API client configuration.

This module provides core OpenMetadata clients with authentication handling,
HTTP session management, and base methods for CRUD operations on metadata entities.

Both synchronous and asynchronous clients are provided:
- OpenMetadataClient: For synchronous (blocking) API calls
- AsyncOpenMetadataClient: For asynchronous (non-blocking) API calls

Examples:
    Synchronous usage:
    ```python
    from src.openmetadata.openmetadata_client import initialize_client, get_client

    # Initialize once at application startup
    initialize_client(host="http://localhost:8585", api_token="your-token")

    # Use anywhere in your application
    client = get_client()
    tables = client.get("tables")
    ```

    Asynchronous usage:
    ```python
    import asyncio
    from src.openmetadata.openmetadata_client import (
        initialize_async_client,
        get_async_client,
    )

    # Initialize once at application startup
    initialize_async_client(host="http://localhost:8585", api_token="your-token")

    # Use in async functions
    async def fetch_tables():
        client = get_async_client()
        tables = await client.get("tables")
        return tables

    # Run the async function
    tables = asyncio.run(fetch_tables())
    ```

Both clients support connection pooling for optimized performance and
include retry logic with exponential backoff for transient errors.
"""
# pylint: disable=global-statement

import asyncio
import json
import logging
import time
from typing import Any, Optional
from urllib.parse import urljoin

import httpx

# Global client instances
_client: Optional["OpenMetadataClient"] = None
_async_client: Optional["AsyncOpenMetadataClient"] = None

# Set up logger
logger = logging.getLogger(__name__)


def initialize_async_client(
    host: str,
    api_token: str | None = None,
    username: str | None = None,
    password: str | None = None,
) -> None:
    """Initialize the global async OpenMetadata client.

    Args:
        host: OpenMetadata host URL
        api_token: JWT token for API authentication
        username: Username for basic authentication
        password: Password for basic authentication

    Raises:
        OpenMetadataError: If neither API token nor username/password is provided
    """
    global _async_client
    _async_client = AsyncOpenMetadataClient(host, api_token, username, password)
    logger.info("Async OpenMetadata client initialized for host: %s", host)


class OpenMetadataError(Exception):
    """Base exception for OpenMetadata client errors."""


def get_client() -> "OpenMetadataClient":
    """Get the global OpenMetadata client instance.

    Returns:
        The initialized OpenMetadata client

    Raises:
        RuntimeError: If client has not been initialized
    """
    if _client is None:
        raise RuntimeError(
            "OpenMetadata client not initialized. Call initialize_client() first."
        )
    return _client


def get_async_client() -> "AsyncOpenMetadataClient":
    """Get the global async OpenMetadata client instance.

    Returns:
        The initialized async OpenMetadata client

    Raises:
        RuntimeError: If async client has not been initialized
    """
    if _async_client is None:
        raise RuntimeError(
            "Async OpenMetadata client not initialized. Call initialize_async_client() first."
        )
    return _async_client


def initialize_client(
    host: str,
    api_token: str | None = None,
    username: str | None = None,
    password: str | None = None,
) -> None:
    """Initialize the global OpenMetadata client.

    Args:
        host: OpenMetadata host URL
        api_token: JWT token for API authentication
        username: Username for basic authentication
        password: Password for basic authentication

    Raises:
        OpenMetadataError: If neither API token nor username/password is provided
    """
    global _client
    _client = OpenMetadataClient(host, api_token, username, password)
    logger.info("OpenMetadata client initialized for host: %s", host)


class OpenMetadataClient:
    """Client for interacting with OpenMetadata API.

    Provides centralized authentication handling, HTTP session management,
    and error handling for all OpenMetadata API operations.
    """

    def __init__(
        self,
        host: str,
        api_token: str | None = None,
        username: str | None = None,
        password: str | None = None,
    ):
        """Initialize OpenMetadata client.

        Args:
            host: OpenMetadata host URL
            api_token: JWT token for API authentication
            username: Username for basic authentication
            password: Password for basic authentication

        Raises:
            OpenMetadataError: If neither API token nor username/password is provided
        """
        self.host = host.rstrip("/")
        self.base_url = urljoin(self.host, "/api/v1/")

        # Configure HTTP client with optimized timeouts and connection pooling
        self.session = httpx.Client(
            timeout=httpx.Timeout(
                connect=5.0,  # Connection timeout
                read=30.0,  # Read timeout
                write=15.0,  # Write timeout
                pool=45.0,  # Pool timeout
            ),
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
            http2=True,  # Enable HTTP/2 for better performance
            transport=get_sync_connection_pool(),  # Use shared connection pool
        )

        # Set up authentication
        if api_token:
            self.session.headers["Authorization"] = f"Bearer {api_token}"
            logger.debug("Configured API token authentication")
        elif username and password:
            # Store credentials and perform login to get JWT token
            self._username = username
            self._password = password
            logger.debug("Performing login authentication")
            self._authenticate_with_login()
        else:
            raise OpenMetadataError(
                "Either API token or username/password must be provided"
            )

        # Set common headers
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })

    def _authenticate_with_login(self) -> None:
        """Authenticate using username/password to get JWT token."""
        import base64

        # Encode password in base64 as required by OpenMetadata
        encoded_password = base64.b64encode(self._password.encode()).decode()

        # Prepare login request
        login_data = {
            "email": self._username,
            "password": encoded_password
        }

        # Debug logging
        logger.debug("Attempting login with email: %s", self._username)
        logger.debug("Encoded password: %s", encoded_password)

        # Make login request to OpenMetadata
        login_url = urljoin(self.host, "/api/v1/users/login")

        try:
            response = self.session.post(login_url, json=login_data)
            response.raise_for_status()

            login_response = response.json()
            access_token = login_response.get("accessToken")

            if not access_token:
                raise OpenMetadataError(
                    "Login successful but no access token received"
                )

            # Set the authorization header with the JWT token
            self.session.headers["Authorization"] = f"Bearer {access_token}"
            logger.info(
                "Successfully authenticated with OpenMetadata using username/password"
            )

        except httpx.HTTPStatusError as e:
            error_msg = (
                f"Login failed: HTTP {e.response.status_code}: {e.response.text}"
            )
            logger.error(error_msg)
            raise OpenMetadataError(error_msg) from e
        except Exception as e:
            error_msg = f"Login failed: {e}"
            logger.error(error_msg)
            raise OpenMetadataError(error_msg) from e

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make HTTP request to OpenMetadata API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            params: Query parameters
            json_data: JSON payload for POST/PUT requests

        Returns:
            API response as dictionary

        Raises:
            OpenMetadataError: If the API request fails
        """
        url = urljoin(self.base_url, endpoint)

        logger.debug("Making %s request to %s", method, url)

        # Apply retry logic for transient failures
        retry_count = 0
        max_retries = 3
        backoff = 0.5  # Start with 0.5s backoff

        while retry_count <= max_retries:
            try:
                response = self.session.request(
                    method=method, url=url, params=params, json=json_data
                )
                response.raise_for_status()

                result = response.json() if response.content else {}
                logger.debug(
                    "Request successful, response size: %d bytes", len(response.content)
                )
                return result

            except httpx.HTTPStatusError as e:
                # Don't retry client errors (4xx)
                if 400 <= e.response.status_code < 500:
                    error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
                    logger.error("API request failed: %s", error_msg)
                    raise OpenMetadataError(error_msg) from e

                # Server errors (5xx) may be retried
                if retry_count < max_retries:
                    retry_count += 1
                    logger.warning(
                        "Server error (HTTP %d), retrying %d/%d after %.1fs",
                        e.response.status_code,
                        retry_count,
                        max_retries,
                        backoff,
                    )
                    time.sleep(backoff)
                    backoff *= 2  # Exponential backoff
                    continue

                # Max retries exceeded
                error_msg = f"HTTP {e.response.status_code} after {max_retries} retries: {e.response.text}"
                logger.error("API request failed: %s", error_msg)
                raise OpenMetadataError(error_msg) from e

            except httpx.RequestError as e:
                # Network errors may be retried
                if retry_count < max_retries:
                    retry_count += 1
                    logger.warning(
                        "Network error, retrying %d/%d after %.1fs: %s", retry_count, max_retries, backoff, str(e)
                    )
                    time.sleep(backoff)
                    backoff *= 2  # Exponential backoff
                    continue

                # Max retries exceeded
                error_msg = f"Request failed after {max_retries} retries: {str(e)}"
                logger.error("Network error: %s", error_msg)
                raise OpenMetadataError(error_msg) from e

            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
                logger.error("Unexpected error in API request: %s", error_msg)
                raise OpenMetadataError(error_msg) from e

        # This should never be reached due to the raised exceptions above,
        # but we need it to satisfy the type checker
        raise OpenMetadataError("Maximum retries exceeded")

    def get(
        self, endpoint: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Make GET request to OpenMetadata API."""
        return self._make_request("GET", endpoint, params=params)

    def post(self, endpoint: str, json_data: dict[str, Any]) -> dict[str, Any]:
        """Make POST request to OpenMetadata API."""
        return self._make_request("POST", endpoint, json_data=json_data)

    def put(self, endpoint: str, json_data: dict[str, Any]) -> dict[str, Any]:
        """Make PUT request to OpenMetadata API."""
        return self._make_request("PUT", endpoint, json_data=json_data)

    def delete(self, endpoint: str, params: dict[str, Any] | None = None) -> None:
        """Make DELETE request to OpenMetadata API."""
        self._make_request("DELETE", endpoint, params=params)

    def close(self) -> None:
        """Close the HTTP session."""
        self.session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Shared connection pools for better performance
_SYNC_CONNECTION_POOL = None
_ASYNC_CONNECTION_POOL = None


def get_sync_connection_pool():
    """Get or create a shared connection pool for synchronous HTTP requests.

    This reduces the overhead of creating new connections for each request
    and improves performance.

    Returns:
        httpx sync connection pool object
    """
    global _SYNC_CONNECTION_POOL
    if _SYNC_CONNECTION_POOL is None:
        _SYNC_CONNECTION_POOL = httpx.HTTPTransport(
            limits=httpx.Limits(max_keepalive_connections=50, max_connections=200)
        )
    return _SYNC_CONNECTION_POOL


def get_async_connection_pool():
    """Get or create a shared connection pool for asynchronous HTTP requests.

    This reduces the overhead of creating new connections for each request
    and improves performance in async contexts.

    Returns:
        httpx async connection pool object
    """
    global _ASYNC_CONNECTION_POOL
    if _ASYNC_CONNECTION_POOL is None:
        _ASYNC_CONNECTION_POOL = httpx.AsyncHTTPTransport(
            limits=httpx.Limits(max_keepalive_connections=50, max_connections=200)
        )
    return _ASYNC_CONNECTION_POOL


class AsyncOpenMetadataClient:
    """Async client for interacting with OpenMetadata API.

    Provides centralized authentication handling, HTTP session management,
    and error handling for all OpenMetadata API operations using async I/O.
    """

    def __init__(
        self,
        host: str,
        api_token: str | None = None,
        username: str | None = None,
        password: str | None = None,
    ):
        """Initialize async OpenMetadata client.

        Args:
            host: OpenMetadata host URL
            api_token: JWT token for API authentication
            username: Username for basic authentication
            password: Password for basic authentication

        Raises:
            OpenMetadataError: If neither API token nor username/password is provided
        """
        self.host = host.rstrip("/")
        self.base_url = urljoin(self.host, "/api/v1/")

        # Configure async HTTP client with optimized timeouts and connection pooling
        self.session = httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=5.0,  # Connection timeout
                read=30.0,  # Read timeout
                write=15.0,  # Write timeout
                pool=45.0,  # Pool timeout
            ),
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
            http2=True,  # Enable HTTP/2 for better performance
            transport=get_async_connection_pool(),  # Use shared connection pool
        )

        # Set up authentication
        if api_token:
            self.session.headers["Authorization"] = f"Bearer {api_token}"
            logger.debug("Configured API token authentication for async client")
        elif username and password:
            # Store credentials and perform login to get JWT token
            self._username = username
            self._password = password
            logger.debug("Performing async login authentication")
            # For async client, we'll need to handle authentication on first request
            self._needs_authentication = True
        else:
            raise OpenMetadataError(
                "Either API token or username/password must be provided"
            )

        # Set common headers
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })

    async def _authenticate_with_login(self) -> None:
        """Authenticate using username/password to get JWT token (async)."""
        import base64

        # Encode password in base64 as required by OpenMetadata
        encoded_password = base64.b64encode(self._password.encode()).decode()

        # Prepare login request
        login_data = {
            "email": self._username,
            "password": encoded_password
        }

        # Make login request to OpenMetadata
        login_url = urljoin(self.host, "/api/v1/users/login")

        try:
            response = await self.session.post(login_url, json=login_data)
            response.raise_for_status()

            login_response = response.json()
            access_token = login_response.get("accessToken")

            if not access_token:
                raise OpenMetadataError(
                    "Login successful but no access token received"
                )

            # Set the authorization header with the JWT token
            self.session.headers["Authorization"] = f"Bearer {access_token}"
            self._needs_authentication = False
            logger.info(
                "Successfully authenticated with OpenMetadata using username/password (async)"
            )

        except httpx.HTTPStatusError as e:
            error_msg = f"Async login failed: HTTP {e.response.status_code}: {e.response.text}"
            logger.error(error_msg)
            raise OpenMetadataError(error_msg) from e
        except Exception as e:
            error_msg = f"Async login failed: {e}"
            logger.error(error_msg)
            raise OpenMetadataError(error_msg) from e

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make async HTTP request to OpenMetadata API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            params: Query parameters
            json_data: JSON payload for POST/PUT requests

        Returns:
            API response as dictionary

        Raises:
            OpenMetadataError: If the API request fails
        """
        # Perform authentication if needed
        if hasattr(self, '_needs_authentication') and self._needs_authentication:
            await self._authenticate_with_login()

        url = urljoin(self.base_url, endpoint)

        logger.debug("Making async %s request to %s", method, url)

        # Apply retry logic for transient failures
        retry_count = 0
        max_retries = 3
        backoff = 0.5  # Start with 0.5s backoff

        while retry_count <= max_retries:
            try:
                response = await self.session.request(method=method, url=url, params=params, json=json_data)
                response.raise_for_status()

                result = response.json() if response.content else {}
                logger.debug("Async request successful, response size: %d bytes", len(response.content))
                return result

            except httpx.HTTPStatusError as e:
                # Don't retry client errors (4xx)
                if 400 <= e.response.status_code < 500:
                    error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
                    logger.error("Async API request failed: %s", error_msg)
                    raise OpenMetadataError(error_msg) from e

                # Server errors (5xx) may be retried
                if retry_count < max_retries:
                    retry_count += 1
                    logger.warning(
                        "Server error (HTTP %d), retrying %d/%d after %.1fs",
                        e.response.status_code,
                        retry_count,
                        max_retries,
                        backoff,
                    )
                    await asyncio.sleep(backoff)
                    backoff *= 2  # Exponential backoff
                    continue

                # Max retries exceeded
                error_msg = f"HTTP {e.response.status_code} after {max_retries} retries: {e.response.text}"
                logger.error("Async API request failed: %s", error_msg)
                raise OpenMetadataError(error_msg) from e

            except httpx.RequestError as e:
                # Network errors may be retried
                if retry_count < max_retries:
                    retry_count += 1
                    logger.warning(
                        "Network error, retrying %d/%d after %.1fs: %s", retry_count, max_retries, backoff, str(e)
                    )
                    await asyncio.sleep(backoff)
                    backoff *= 2  # Exponential backoff
                    continue

                # Max retries exceeded
                error_msg = f"Request failed after {max_retries} retries: {str(e)}"
                logger.error("Async network error: %s", error_msg)
                raise OpenMetadataError(error_msg) from e

            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
                logger.error("Unexpected error in async API request: %s", error_msg)
                raise OpenMetadataError(error_msg) from e

        # This should never be reached due to the raised exceptions above,
        # but we need it to satisfy the type checker
        raise OpenMetadataError("Maximum retries exceeded")

    async def get(
        self, endpoint: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Make async GET request to OpenMetadata API."""
        return await self._make_request("GET", endpoint, params=params)

    async def post(self, endpoint: str, json_data: dict[str, Any]) -> dict[str, Any]:
        """Make async POST request to OpenMetadata API."""
        return await self._make_request("POST", endpoint, json_data=json_data)

    async def put(self, endpoint: str, json_data: dict[str, Any]) -> dict[str, Any]:
        """Make async PUT request to OpenMetadata API."""
        return await self._make_request("PUT", endpoint, json_data=json_data)

    async def delete(
        self, endpoint: str, params: dict[str, Any] | None = None
    ) -> None:
        """Make async DELETE request to OpenMetadata API."""
        await self._make_request("DELETE", endpoint, params=params)

    async def close(self) -> None:
        """Close the async HTTP session."""
        await self.session.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


def format_response_as_json(data: Any) -> str:
    """Convert response data to properly formatted JSON string.

    Args:
        data: The response data to convert to JSON

    Returns:
        JSON formatted string
    """
    return json.dumps(data, indent=2, ensure_ascii=False)


def format_response_as_raw_json(data: Any) -> str:
    """Convert response data to compact JSON string for single Inspector response.

    This function returns JSON without extra formatting to prevent duplicate
    responses in MCP Inspector - the Inspector will format it naturally.

    Args:
        data: The response data to convert to JSON

    Returns:
        Compact JSON string
    """
    return json.dumps(data, ensure_ascii=False, separators=(',', ':'))
