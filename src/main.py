"""Central orchestration module for MCP OpenMetadata server.

This module configures the CLI interface with Click for transport selection,
dynamically loads and registers API modules based on user selection,
and manages server lifecycle with chosen transport protocol.
"""

from typing import List

import click
from fastmcp import FastMCP

from src.config import Config
from src.enums import APIType

# Import API modules
from src.openmetadata import (
    bots,
    charts,
    classifications,
    containers,
    dashboards,
    database,
    domains,
    events,
    glossary,
    lineage,
    metrics,
    mlmodels,
    pipelines,
    policies,
    reports,
    roles,
    schema,
    search,
    services,
    table,
    tags,
    teams,
    test_cases,
    test_suites,
    topics,
    usage,
    users,
)
from src.openmetadata.openmetadata_client import initialize_client
from src.server import get_server_runner

# Map API types to their respective function collections
APITYPE_TO_FUNCTIONS = {
    # Core Data Entities
    APIType.TABLE: table.get_all_functions,
    APIType.DATABASE: database.get_all_functions,
    APIType.SCHEMA: schema.get_all_functions,
    # Data Assets
    APIType.DASHBOARD: dashboards.get_all_functions,
    APIType.CHART: charts.get_all_functions,
    APIType.PIPELINE: pipelines.get_all_functions,
    APIType.TOPIC: topics.get_all_functions,
    APIType.METRICS: metrics.get_all_functions,
    APIType.CONTAINER: containers.get_all_functions,
    APIType.REPORT: reports.get_all_functions,
    APIType.ML_MODEL: mlmodels.get_all_functions,
    # Users & Teams
    APIType.USER: users.get_all_functions,
    APIType.TEAM: teams.get_all_functions,
    # Governance & Classification
    APIType.CLASSIFICATION: classifications.get_all_functions,
    APIType.GLOSSARY: glossary.get_all_functions,
    APIType.TAG: tags.get_all_functions,
    # System & Operations
    APIType.BOT: bots.get_all_functions,
    APIType.SERVICES: services.get_all_functions,
    APIType.EVENT: events.get_all_functions,
    # Analytics & Monitoring
    APIType.LINEAGE: lineage.get_all_functions,
    APIType.USAGE: usage.get_all_functions,
    APIType.SEARCH: search.get_all_functions,
    # Data Quality
    APIType.TEST_CASE: test_cases.get_all_functions,
    APIType.TEST_SUITE: test_suites.get_all_functions,
    # Access Control & Security
    APIType.POLICY: policies.get_all_functions,
    APIType.ROLE: roles.get_all_functions,
    # Domain Management
    APIType.DOMAIN: domains.get_all_functions,
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
    default=[
        APIType.TABLE.value,
        APIType.DATABASE.value,
        APIType.SCHEMA.value,
        APIType.DASHBOARD.value,
        APIType.CHART.value,
        APIType.PIPELINE.value,
        APIType.TOPIC.value,
        APIType.METRICS.value,
        APIType.CONTAINER.value,
        APIType.USER.value,
        APIType.TEAM.value,
        APIType.CLASSIFICATION.value,
        APIType.GLOSSARY.value,
        APIType.BOT.value,
        APIType.LINEAGE.value,
        APIType.USAGE.value,
        APIType.SEARCH.value,
        APIType.SERVICES.value,
        APIType.REPORT.value,
        APIType.ML_MODEL.value,
    ],  # Default to all implemented APIs
    multiple=True,
    help="API groups to enable (default: core entities and common assets)",
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
