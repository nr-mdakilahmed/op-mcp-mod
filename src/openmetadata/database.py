"""Database container management for OpenMetadata.

This module provides database lifecycle operations, service connection management,
and schema relationship handling.
"""

from collections.abc import Callable
from typing import Any

import mcp.types as types

from src.openmetadata.openmetadata_client import get_client, format_response_as_raw_json


def get_all_functions() -> list[tuple[Callable, str, str]]:
    """Return list of (function, name, description) tuples for registration.

    Returns:
        List of tuples containing function reference, tool name, and description
    """
    return [
        (list_databases, "list_databases", "List databases from OpenMetadata with pagination and filtering"),
        (get_database, "get_database", "Get details of a specific database by ID"),
        (get_database_by_name, "get_database_by_name", "Get details of a specific database by fully qualified name"),
        (create_database, "create_database", "Create a new database in OpenMetadata"),
        (update_database, "update_database", "Update an existing database in OpenMetadata"),
        (delete_database, "delete_database", "Delete a database from OpenMetadata"),
    ]


async def list_databases(
    limit: int = 10,
    offset: int = 0,
    fields: str | None = None,
    service: str | None = None,
    include_deleted: bool = False,
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """List databases with pagination.

    Args:
        limit: Maximum number of databases to return
        offset: Number of databases to skip
        fields: Comma-separated list of fields to include
        service: Filter databases by service name
        include_deleted: Whether to include deleted databases

    Returns:
        List of MCP content types containing database list and metadata
    """
    client = get_client()
    params = {"limit": min(max(1, limit), 1000000), "offset": max(0, offset)}
    if fields:
        params["fields"] = fields
    if service:
        params["service"] = service
    if include_deleted:
        params["include"] = "all"

    result = client.get("databases", params=params)

    # Add UI URLs for web interface integration
    if "data" in result:
        for database in result["data"]:
            database_fqn = database.get("fullyQualifiedName", "")
            if database_fqn:
                database["ui_url"] = f"{client.host}/database/{database_fqn}"

    return [types.TextContent(type="text", text=format_response_as_raw_json(result))]


async def get_database(
    database_id: str,
    fields: str | None = None,
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Get details of a specific database by ID.

    Args:
        database_id: ID of the database
        fields: Comma-separated list of fields to include

    Returns:
        List of MCP content types containing database details
    """
    client = get_client()
    params = {}
    if fields:
        params["fields"] = fields

    result = client.get(f"databases/{database_id}", params=params)

    # Add UI URL for web interface integration
    database_fqn = result.get("fullyQualifiedName", "")
    if database_fqn:
        result["ui_url"] = f"{client.host}/database/{database_fqn}"

    return [types.TextContent(type="text", text=format_response_as_raw_json(result))]


async def get_database_by_name(
    fqn: str,
    fields: str | None = None,
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Get details of a specific database by fully qualified name.

    Args:
        fqn: Fully qualified name of the database
        fields: Comma-separated list of fields to include

    Returns:
        List of MCP content types containing database details
    """
    client = get_client()
    params = {}
    if fields:
        params["fields"] = fields

    result = client.get(f"databases/name/{fqn}", params=params)

    # Add UI URL for web interface integration
    database_fqn = result.get("fullyQualifiedName", "")
    if database_fqn:
        result["ui_url"] = f"{client.host}/database/{database_fqn}"

    return [types.TextContent(type="text", text=format_response_as_raw_json(result))]


async def create_database(
    database_data: dict[str, Any],
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Create a new database.

    Args:
        database_data: Database data including name, description, service, etc.

    Returns:
        List of MCP content types containing created database details
    """
    client = get_client()
    result = client.post("databases", json_data=database_data)

    # Add UI URL for web interface integration
    database_fqn = result.get("fullyQualifiedName", "")
    if database_fqn:
        result["ui_url"] = f"{client.host}/database/{database_fqn}"

    return [types.TextContent(type="text", text=format_response_as_raw_json(result))]


async def update_database(
    database_id: str,
    database_data: dict[str, Any],
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Update an existing database.

    Args:
        database_id: ID of the database to update
        database_data: Updated database data

    Returns:
        List of MCP content types containing updated database details
    """
    client = get_client()
    result = client.put(f"databases/{database_id}", json_data=database_data)

    # Add UI URL for web interface integration
    database_fqn = result.get("fullyQualifiedName", "")
    if database_fqn:
        result["ui_url"] = f"{client.host}/database/{database_fqn}"

    return [types.TextContent(type="text", text=format_response_as_raw_json(result))]


async def delete_database(
    database_id: str,
    hard_delete: bool = False,
    recursive: bool = False,
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Delete a database.

    Args:
        database_id: ID of the database to delete
        hard_delete: Whether to perform a hard delete
        recursive: Whether to recursively delete children

    Returns:
        List of MCP content types confirming deletion
    """
    client = get_client()
    params = {"hardDelete": hard_delete, "recursive": recursive}
    client.delete(f"databases/{database_id}", params=params)

    return [types.TextContent(type="text", text=f"Database {database_id} deleted successfully")]
