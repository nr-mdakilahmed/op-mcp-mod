"""ML Model entity management for OpenMetadata.

This module provides comprehensive ML model management operations including
CRUD operations, field filtering, pagination support, and model training metadata.
ML Models are algorithms trained on data to find patterns or make predictions.
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
        (list_ml_models, "list_ml_models", "List ML models from OpenMetadata with pagination and filtering"),
        (get_ml_model, "get_ml_model", "Get details of a specific ML model by ID"),
        (get_ml_model_by_name, "get_ml_model_by_name", "Get details of a specific ML model by fully qualified name"),
        (create_ml_model, "create_ml_model", "Create a new ML model in OpenMetadata"),
        (update_ml_model, "update_ml_model", "Update an existing ML model in OpenMetadata"),
        (delete_ml_model, "delete_ml_model", "Delete an ML model from OpenMetadata"),
    ]


async def list_ml_models(
    limit: int = 10,
    offset: int = 0,
    fields: str | None = None,
    service: str | None = None,
    include_deleted: bool = False,
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """List ML models with pagination.

    Args:
        limit: Maximum number of ML models to return (1 to 1000000)
        offset: Number of ML models to skip
        fields: Comma-separated list of fields to include
        service: Filter ML models by service name
        include_deleted: Whether to include deleted ML models

    Returns:
        List of MCP content types containing ML model list and metadata
    """
    client = get_client()
    params = {"limit": min(max(1, limit), 1000000), "offset": max(0, offset)}
    if fields:
        params["fields"] = fields
    if service:
        params["service"] = service
    if include_deleted:
        params["include"] = "all"

    result = client.get("mlmodels", params=params)

    # Add UI URL for web interface integration
    if "data" in result:
        for model in result["data"]:
            model_fqn = model.get("fullyQualifiedName", "")
            if model_fqn:
                model["ui_url"] = f"{client.host}/mlmodel/{model_fqn}"

    return [types.TextContent(type="text", text=format_response_as_raw_json(result))]


async def get_ml_model(
    model_id: str,
    fields: str | None = None,
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Get details of a specific ML model by ID.

    Args:
        model_id: ID of the ML model
        fields: Comma-separated list of fields to include

    Returns:
        List of MCP content types containing ML model details
    """
    client = get_client()
    params = {}
    if fields:
        params["fields"] = fields

    result = client.get(f"mlmodels/{model_id}", params=params)

    # Add UI URL for web interface integration
    model_fqn = result.get("fullyQualifiedName", "")
    if model_fqn:
        result["ui_url"] = f"{client.host}/mlmodel/{model_fqn}"

    return [types.TextContent(type="text", text=format_response_as_raw_json(result))]


async def get_ml_model_by_name(
    fqn: str,
    fields: str | None = None,
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Get details of a specific ML model by fully qualified name.

    Args:
        fqn: Fully qualified name of the ML model
        fields: Comma-separated list of fields to include

    Returns:
        List of MCP content types containing ML model details
    """
    client = get_client()
    params = {}
    if fields:
        params["fields"] = fields

    result = client.get(f"mlmodels/name/{fqn}", params=params)

    # Add UI URL for web interface integration
    model_fqn = result.get("fullyQualifiedName", "")
    if model_fqn:
        result["ui_url"] = f"{client.host}/mlmodel/{model_fqn}"

    return [types.TextContent(type="text", text=format_response_as_raw_json(result))]


async def create_ml_model(
    model_data: dict[str, Any],
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Create a new ML model.

    Args:
        model_data: ML model data including name, description, algorithm, features, etc.

    Returns:
        List of MCP content types containing created ML model details
    """
    client = get_client()
    result = client.post("mlmodels", json_data=model_data)

    # Add UI URL for web interface integration
    model_fqn = result.get("fullyQualifiedName", "")
    if model_fqn:
        result["ui_url"] = f"{client.host}/mlmodel/{model_fqn}"

    return [types.TextContent(type="text", text=format_response_as_raw_json(result))]


async def update_ml_model(
    model_id: str,
    model_data: dict[str, Any],
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Update an existing ML model.

    Args:
        model_id: ID of the ML model to update
        model_data: Updated ML model data

    Returns:
        List of MCP content types containing updated ML model details
    """
    client = get_client()
    result = client.put(f"mlmodels/{model_id}", json_data=model_data)

    # Add UI URL for web interface integration
    model_fqn = result.get("fullyQualifiedName", "")
    if model_fqn:
        result["ui_url"] = f"{client.host}/mlmodel/{model_fqn}"

    return [types.TextContent(type="text", text=format_response_as_raw_json(result))]


async def delete_ml_model(
    model_id: str,
    hard_delete: bool = False,
    recursive: bool = False,
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Delete an ML model.

    Args:
        model_id: ID of the ML model to delete
        hard_delete: Whether to perform a hard delete
        recursive: Whether to recursively delete children

    Returns:
        List of MCP content types confirming deletion
    """
    client = get_client()
    params = {"hardDelete": hard_delete, "recursive": recursive}
    client.delete(f"mlmodels/{model_id}", params=params)

    return [types.TextContent(type="text", text=f"ML model {model_id} deleted successfully")]
