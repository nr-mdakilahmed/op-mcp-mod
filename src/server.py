"""Server initialization module for MCP OpenMetadata.

This module initializes the FastMCP server with proper configuration.
It serves as the central point for MCP server instance creation,
providing a consistent reference to the FastMCP app throughout the codebase.
"""

from collections.abc import Callable
import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

# Initialize the FastMCP server with descriptive name
app = FastMCP("OpenMetadata MCP Server")

# Store registered tools for reporting
_registered_tools: list[tuple[Callable, str, str]] = []


def register_tool(func: Callable, name: str, description: str) -> None:
    """Register a tool with the MCP server.

    Args:
        func: The function to register as a tool
        name: The name of the tool
        description: A description of what the tool does
    """
    app.add_tool(func, name=name, description=description)
    _registered_tools.append((func, name, description))
    logging.debug("Registered tool: %s", name)


def get_registered_tools() -> list[tuple[Callable, str, str]]:
    """Get a list of all registered tools.

    Returns:
        List of tuples containing (function, name, description)
    """
    return _registered_tools


def configure_server_metadata(
    title: str = "OpenMetadata MCP Server",
    description: str = "MCP server for accessing OpenMetadata platform",
    version: str = "1.0.0",
) -> None:
    """Configure server metadata.

    Args:
        title: Server title
        description: Server description
        version: Server version
    """
    # FastMCP doesn't seem to have this config option based on usage
    # This is a placeholder for future FastMCP versions that might support it
    logging.info("Server metadata configured: %s v%s", title, version)

    # Store metadata for reference
    # Use the module-level variable directly
    _server_metadata["title"] = title
    _server_metadata["description"] = description
    _server_metadata["version"] = version


# Server metadata storage
_server_metadata: dict[str, str] = {
    "title": "OpenMetadata MCP Server",
    "description": "MCP server for accessing OpenMetadata platform",
    "version": "1.0.0",
}


def get_server_metadata() -> dict[str, str]:
    """Get server metadata.

    Returns:
        Dictionary with server metadata
    """
    return _server_metadata.copy()


def get_server_status() -> dict[str, Any]:
    """Get current server status including registered tools.

    Returns:
        Dictionary with server status information
    """
    return {
        "metadata": get_server_metadata(),
        "registered_tools_count": len(_registered_tools),
        "registered_tools": [{"name": name, "description": description} for _, name, description in _registered_tools],
        "status": "running",
    }
