"""Health check and status monitoring for MCP server.

This module provides health check endpoints and status monitoring for the MCP server,
enabling integration with container orchestration systems and monitoring tools.
"""

import time
from typing import Any

from fastapi import APIRouter

from src.config import Config
from src.monitoring import get_logger, metrics
from src.openmetadata.openmetadata_client import OpenMetadataError, get_client

# Global server start time
SERVER_START_TIME = time.time()

# Create router
router = APIRouter(tags=["Health"])

# Configure logger
logger = get_logger("mcp.health")


def get_system_info() -> dict[str, Any]:
    """Get system information for status endpoint.

    Returns:
        Dictionary with system metrics and information
    """
    return {
        "uptime_seconds": int(time.time() - SERVER_START_TIME),
        "metrics": metrics.get_stats(),
    }


async def check_openmetadata_connection() -> dict[str, Any]:
    """Check connection to OpenMetadata server.

    Returns:
        Dictionary with connection status and details
    """
    try:
        # Try enhanced client first, fall back to standard client
        client = None
        try:
            from src.openmetadata.enhanced_client import get_enhanced_client

            client = get_enhanced_client()
            logger.debug("Using enhanced OpenMetadata client for health check")
        except (ImportError, RuntimeError, AttributeError) as e:
            # Fall back to standard client
            logger.debug("Enhanced client unavailable (%s), using standard client", str(e))
            client = get_client()

        if client is None:
            raise RuntimeError("No OpenMetadata client available")

        # Perform health check
        health_response = client.get("health")

        return {
            "status": "healthy" if health_response.get("healthy", False) else "unhealthy",
            "details": health_response,
            "client_type": "enhanced" if "enhanced_client" in str(type(client)) else "standard",
            "timestamp": time.time(),
        }
    except OpenMetadataError as e:
        logger.error("Failed to connect to OpenMetadata", error=str(e))
        return {"status": "unhealthy", "error": f"OpenMetadata error: {str(e)}", "timestamp": time.time()}
    except (ConnectionError, TimeoutError) as e:
        logger.error("Network error checking OpenMetadata", error=str(e))
        return {"status": "unhealthy", "error": f"Network error: {str(e)}", "timestamp": time.time()}
    except RuntimeError as e:
        logger.error("Runtime error checking OpenMetadata", error=str(e))
        return {"status": "unhealthy", "error": f"Runtime error: {str(e)}", "timestamp": time.time()}


@router.get("/health")
async def health_check() -> dict[str, Any]:
    """Health check endpoint for the MCP server.

    Returns:
        Dictionary with health status information
    """
    # Check OpenMetadata connection
    openmetadata_status = await check_openmetadata_connection()

    # Overall status is healthy only if OpenMetadata is healthy
    is_healthy = openmetadata_status["status"] == "healthy"

    return {
        "status": "healthy" if is_healthy else "unhealthy",
        "openmetadata": openmetadata_status,
        "uptime_seconds": int(time.time() - SERVER_START_TIME),
        "timestamp": time.time(),
    }


@router.get("/status")
async def status() -> dict[str, Any]:
    """Detailed status endpoint for the MCP server.

    Returns:
        Dictionary with detailed status information
    """
    # Get OpenMetadata status
    openmetadata_status = await check_openmetadata_connection()

    # Get system metrics
    system_info = get_system_info()

    # Get tool metrics from metrics object
    metrics_stats = metrics.get_stats()

    # Return comprehensive status
    return {
        "status": "healthy" if openmetadata_status["status"] == "healthy" else "unhealthy",
        "server": {
            "version": "0.3.0",  # Should match pyproject.toml version
            "uptime_seconds": int(time.time() - SERVER_START_TIME),
            "environment": Config.from_env().SENTRY_ENVIRONMENT,
        },
        "openmetadata": openmetadata_status,
        "tools": metrics_stats,
        "system": system_info,
        "timestamp": time.time(),
    }
