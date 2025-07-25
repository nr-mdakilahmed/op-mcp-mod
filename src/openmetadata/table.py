"""Table entity management for OpenMetadata.

This module provides comprehensive table management operations including
CRUD operations, field filtering, pagination support, and FQN-based lookups.
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
        (list_tables, "list_tables", "List tables from OpenMetadata with pagination and filtering"),
        (get_table, "get_table", "Get details of a specific table by ID"),
        (get_table_by_name, "get_table_by_name", "Get details of a specific table by fully qualified name"),
        (create_table, "create_table", "Create a new table in OpenMetadata"),
        (update_table, "update_table", "Update an existing table in OpenMetadata"),
        (delete_table, "delete_table", "Delete a table from OpenMetadata"),
    ]


async def list_tables(
    limit: int = 10,
    offset: int = 0,
    fields: str | None = None,
    database: str | None = None,
    include_deleted: bool = False,
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """List tables with pagination.

    Args:
        limit: Maximum number of tables to return (1 to 1000000)
        offset: Number of tables to skip
        fields: Comma-separated list of fields to include
        database: Filter tables by database fully qualified name
        include_deleted: Whether to include deleted tables

    Returns:
        List of MCP content types containing table list and metadata
    """
    client = get_client()
    params = {"limit": min(max(1, limit), 1000000), "offset": max(0, offset)}
    if fields:
        params["fields"] = fields
    if database:
        params["database"] = database
    if include_deleted:
        params["include"] = "all"

    result = client.get("tables", params=params)

    # Add UI URL for web interface integration
    if "data" in result:
        for table in result["data"]:
            table_fqn = table.get("fullyQualifiedName", "")
            if table_fqn:
                table["ui_url"] = f"{client.host}/table/{table_fqn}"

    return [types.TextContent(type="text", text=format_response_as_raw_json(result))]


async def get_table(
    table_id: str,
    fields: str | None = None,
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Get details of a specific table by ID.

    Args:
        table_id: ID of the table
        fields: Comma-separated list of fields to include

    Returns:
        List of MCP content types containing table details
    """
    client = get_client()
    params = {}
    if fields:
        params["fields"] = fields

    result = client.get(f"tables/{table_id}", params=params)

    # Add UI URL for web interface integration
    table_fqn = result.get("fullyQualifiedName", "")
    if table_fqn:
        result["ui_url"] = f"{client.host}/table/{table_fqn}"

    return [types.TextContent(type="text", text=format_response_as_raw_json(result))]


async def get_table_by_name(
    fqn: str,
    fields: str | None = None,
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Get details of a specific table by fully qualified name.

    Args:
        fqn: Fully qualified name of the table
        fields: Comma-separated list of fields to include

    Returns:
        List of MCP content types containing table details
    """
    client = get_client()
    params = {}
    if fields:
        params["fields"] = fields

    result = client.get(f"tables/name/{fqn}", params=params)

    # Add UI URL for web interface integration
    table_fqn = result.get("fullyQualifiedName", "")
    if table_fqn:
        result["ui_url"] = f"{client.host}/table/{table_fqn}"

    return [types.TextContent(type="text", text=format_response_as_raw_json(result))]


async def create_table(
    table_data: dict[str, Any],
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Create a new table.

    Args:
        table_data: Table data including name, description, columns, etc.

    Returns:
        List of MCP content types containing created table details
    """
    client = get_client()
    result = client.post("tables", json_data=table_data)

    # Add UI URL for web interface integration
    table_fqn = result.get("fullyQualifiedName", "")
    if table_fqn:
        result["ui_url"] = f"{client.host}/table/{table_fqn}"

    return [types.TextContent(type="text", text=format_response_as_raw_json(result))]


async def update_table(
    table_id: str,
    table_data: dict[str, Any],
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Update an existing table.

    Args:
        table_id: ID of the table to update
        table_data: Updated table data

    Returns:
        List of MCP content types containing updated table details
    """
    client = get_client()
    result = client.put(f"tables/{table_id}", json_data=table_data)

    # Add UI URL for web interface integration
    table_fqn = result.get("fullyQualifiedName", "")
    if table_fqn:
        result["ui_url"] = f"{client.host}/table/{table_fqn}"

    return [types.TextContent(type="text", text=format_response_as_raw_json(result))]


async def delete_table(
    table_id: str,
    hard_delete: bool = False,
    recursive: bool = False,
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Delete a table.

    Args:
        table_id: ID of the table to delete
        hard_delete: Whether to perform a hard delete
        recursive: Whether to recursively delete children

    Returns:
        List of MCP content types confirming deletion
    """
    client = get_client()
    params = {"hardDelete": hard_delete, "recursive": recursive}
    client.delete(f"tables/{table_id}", params=params)

    return [types.TextContent(type="text", text=f"Table {table_id} deleted successfully")]
