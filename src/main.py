"""Central orchestration module for MCP OpenMetadata server.

This module configures the CLI interface with Click for transport selection,
dynamically loads and registers API modules based on user selection,
and manages server lifecycle with chosen transport protocol.
"""

from typing import Dict, List

import click
from fastmcp import FastMCP

from src.config import Config
from src.enums import APIType
from src.openmetadata.openmetadata_client import initialize_client
from src.server import get_server_runner

# Import API modules
from src.openmetadata import table, database, schema

# Map API types to their respective function collections
APITYPE_TO_FUNCTIONS = {
    APIType.TABLE: table.get_all_functions,
    APIType.DATABASE: database.get_all_functions,
    APIType.SCHEMA: schema.get_all_functions,
    # Additional API types will be added here as modules are implemented
}

DEFAULT_PORT = 8000
DEFAULT_TRANSPORT = "stdio"
SERVER_NAME = "mcp-server-openmetadata"


@click.command()
@click.option(
    "--transport",
    type=click.Choice(["stdio", "sse"]),
    default=DEFAULT_TRANSPORT,
    help="Transport type for MCP communication",
)
@click.option(
    "--port",
    default=DEFAULT_PORT,
    help="Port to listen on for SSE transport",
)
@click.option(
    "--apis",
    type=click.Choice([api.value for api in APIType]),
    default=[APIType.TABLE.value, APIType.DATABASE.value, APIType.SCHEMA.value],  # Default to core entities
    multiple=True,
    help="API groups to enable (default: table, database, schema)",
)
def main(transport: str, port: int, apis: List[str]) -> int:
    """Start the MCP OpenMetadata server with selected API groups."""
    try:
        # Get OpenMetadata credentials from environment
        config = Config.from_env()

        # Initialize global OpenMetadata client
        initialize_client(
            host=config.OPENMETADATA_HOST,
            api_token=config.OPENMETADATA_JWT_TOKEN,
            username=config.OPENMETADATA_USERNAME,
            password=config.OPENMETADATA_PASSWORD,
        )

        # Create FastMCP server
        app = FastMCP(SERVER_NAME)

        # Register selected API modules
        registered_count = 0
        for api in apis:
            api_type = APIType(api)
            if api_type in APITYPE_TO_FUNCTIONS:
                get_functions = APITYPE_TO_FUNCTIONS[api_type]
                functions = get_functions()
                
                for func, name, description in functions:
                    app.add_tool(func, name=name, description=description)
                    registered_count += 1
                
                print(f"Registered {len(functions)} tools from {api_type.value} API")
            else:
                print(f"Warning: API type '{api}' not implemented yet")

        print(f"Total registered tools: {registered_count}")
        
        # Start server with selected transport
        server_runner = get_server_runner(app, transport, port=port)
        return server_runner()

    except Exception as e:
        print(f"Server failed to start: {str(e)}")
        return 1


if __name__ == "__main__":
    main()
