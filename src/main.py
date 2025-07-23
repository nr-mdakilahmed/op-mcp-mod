"""Central orchestration module for MCP OpenMetadata server.

This module configures the CLI interface with Click for transport selection,
dynamically loads and registers API modules based on user selection,
and manages server lifecycle with chosen transport protocol.
"""

import asyncio
import logging
import os
import sys

import click
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from src.config import Config
from src.enums import APIType
from src.monitoring import initialize_monitoring
from src.openmetadata.openmetadata_client import initialize_client

try:
    from src.openmetadata.enhanced_client import initialize_enhanced_client
    ENHANCED_CLIENT_AVAILABLE = True
except ImportError:
    ENHANCED_CLIENT_AVAILABLE = False
    initialize_enhanced_client = None

try:
    from src.auth import APIKeyAuthBackend, AuthDependency
    AUTH_AVAILABLE = True
except ImportError:
    AUTH_AVAILABLE = False
    APIKeyAuthBackend = None
    AuthDependency = None

try:
    from src.health import router as health_router
    HEALTH_ROUTER_AVAILABLE = True
except ImportError:
    HEALTH_ROUTER_AVAILABLE = False
    health_router = None

# Import all API module functions with descriptive aliases
from src.openmetadata.bots import get_all_functions as get_bots_functions
from src.openmetadata.charts import get_all_functions as get_charts_functions
from src.openmetadata.classifications import get_all_functions as get_classifications_functions
from src.openmetadata.containers import get_all_functions as get_containers_functions
from src.openmetadata.dashboards import get_all_functions as get_dashboards_functions
from src.openmetadata.database import get_all_functions as get_database_functions
from src.openmetadata.domains import get_all_functions as get_domains_functions
from src.openmetadata.events import get_all_functions as get_events_functions
from src.openmetadata.glossary import get_all_functions as get_glossary_functions
from src.openmetadata.lineage import get_all_functions as get_lineage_functions
from src.openmetadata.metrics import get_all_functions as get_metrics_functions
from src.openmetadata.mlmodels import get_all_functions as get_mlmodels_functions
from src.openmetadata.pipelines import get_all_functions as get_pipelines_functions
from src.openmetadata.policies import get_all_functions as get_policies_functions
from src.openmetadata.reports import get_all_functions as get_reports_functions
from src.openmetadata.roles import get_all_functions as get_roles_functions
from src.openmetadata.schema import get_all_functions as get_schema_functions
from src.openmetadata.search import get_all_functions as get_search_functions
from src.openmetadata.services import get_all_functions as get_services_functions
from src.openmetadata.table import get_all_functions as get_table_functions
from src.openmetadata.tags import get_all_functions as get_tags_functions
from src.openmetadata.teams import get_all_functions as get_teams_functions
from src.openmetadata.test_cases import get_all_functions as get_test_cases_functions
from src.openmetadata.test_suites import get_all_functions as get_test_suites_functions
from src.openmetadata.topics import get_all_functions as get_topics_functions
from src.openmetadata.usage import get_all_functions as get_usage_functions
from src.openmetadata.users import get_all_functions as get_users_functions
from src.server import app, register_tool
from src.testing import run_interactive_testing

# Mapping API types to their corresponding function getters
APITYPE_TO_FUNCTIONS = {
    APIType.TABLE: get_table_functions,
    APIType.DATABASE: get_database_functions,
    APIType.SCHEMA: get_schema_functions,
    APIType.DASHBOARD: get_dashboards_functions,
    APIType.CHART: get_charts_functions,
    APIType.PIPELINE: get_pipelines_functions,
    APIType.TOPIC: get_topics_functions,
    APIType.METRICS: get_metrics_functions,
    APIType.CONTAINER: get_containers_functions,
    APIType.REPORT: get_reports_functions,
    APIType.ML_MODEL: get_mlmodels_functions,
    APIType.USER: get_users_functions,
    APIType.TEAM: get_teams_functions,
    APIType.CLASSIFICATION: get_classifications_functions,
    APIType.GLOSSARY: get_glossary_functions,
    APIType.TAG: get_tags_functions,
    APIType.BOT: get_bots_functions,
    APIType.SERVICES: get_services_functions,
    APIType.EVENT: get_events_functions,
    APIType.LINEAGE: get_lineage_functions,
    APIType.USAGE: get_usage_functions,
    APIType.SEARCH: get_search_functions,
    APIType.TEST_CASE: get_test_cases_functions,
    APIType.TEST_SUITE: get_test_suites_functions,
    APIType.POLICY: get_policies_functions,
    APIType.ROLE: get_roles_functions,
    APIType.DOMAIN: get_domains_functions,
}


def filter_functions_for_read_only(functions):
    """Filter out write operations for read-only mode.

    Args:
        functions: List of function tuples (func, name, description, ...)

    Returns:
        Filtered list containing only read operations
    """
    # Keywords that indicate write operations
    write_keywords = {
        "create", "update", "delete", "patch", "add",
        "remove", "set", "modify", "edit"
    }

    # Filter functions to exclude write operations
    filtered_functions = []
    for func_info in functions:
        name = func_info[1].lower()
        if not any(keyword in name for keyword in write_keywords):
            filtered_functions.append(func_info)

    return filtered_functions


@click.command()
@click.option(
    "--transport",
    type=click.Choice(["stdio", "sse", "streamable-http", "http", "websocket"]),
    default="stdio",
    help=(
        "Transport type for MCP communication "
        "(stdio, sse, streamable-http for MCP; http, websocket for REST API)"
    ),
)
@click.option(
    "--host",
    default="0.0.0.0",
    help="Host for HTTP/WebSocket server (only for http/websocket transport)",
)
@click.option(
    "--port",
    default=8000,
    help="Port for HTTP/WebSocket server (only for http/websocket transport)",
)
@click.option(
    "--apis",
    multiple=True,
    type=click.Choice([api.value for api in APIType]),
    default=[
        "table", "database", "databaseschema", "dashboard", "chart",
        "pipeline", "topic", "metrics", "container"
    ],
    help="API groups to enable (default: core entities and common assets)",
)
@click.option(
    "--read-only",
    is_flag=True,
    default=False,
    help="Only expose read-only tools (GET operations, no CREATE/UPDATE/DELETE)",
)
@click.option(
    "--require-auth",
    is_flag=True,
    default=False,
    help=(
        "Require authentication for remote server "
        "(only for http/websocket transport)"
    ),
)
@click.option(
    "--test",
    is_flag=True,
    default=False,
    help="Run in interactive testing mode",
)
@click.option(
    "--enhanced-client",
    is_flag=True,
    default=False,
    help="Use enhanced OpenMetadata client with caching and connection pooling",
)
def main(transport, host, port, apis, read_only, require_auth, enhanced_client, test):
    """Start the MCP OpenMetadata server with selected API groups."""
    # Configure logging - redirect to stderr for stdio transport to avoid JSON-RPC interference
    if transport == "stdio":
        logging.basicConfig(
            level=logging.INFO,
            stream=sys.stderr,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    else:
        logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Initialize configuration
    config = Config.from_env()

    # Initialize monitoring (pass transport info for stdio logging)
    monitoring_status = initialize_monitoring(config, transport)
    logger.info("Monitoring initialized: %s", monitoring_status)

    # Handle test mode
    if test:
        asyncio.run(run_interactive_testing(config))
        return

    # Initialize global OpenMetadata client
    try:
        # Debug: Print configuration values (redacted for security)
        logger.info("OpenMetadata configuration:")
        logger.info("  HOST: %s", config.OPENMETADATA_HOST)
        logger.info("  JWT_TOKEN: %s", "***SET***" if config.OPENMETADATA_JWT_TOKEN else "Not set")
        logger.info("  USERNAME: %s", "***SET***" if config.OPENMETADATA_USERNAME else "Not set")
        logger.info("  PASSWORD: %s", "***SET***" if config.OPENMETADATA_PASSWORD else "Not set")

        # Check if enhanced client should be used
        if enhanced_client and ENHANCED_CLIENT_AVAILABLE and initialize_enhanced_client:
            try:
                # Use enhanced client with caching and connection pooling
                initialize_enhanced_client(
                    host=config.OPENMETADATA_HOST,
                    api_token=config.OPENMETADATA_JWT_TOKEN,
                    username=config.OPENMETADATA_USERNAME,
                    password=config.OPENMETADATA_PASSWORD,
                )
                logger.info(
                    "Successfully initialized Enhanced OpenMetadata client "
                    "with caching and connection pooling"
                )
            except NameError as exc:
                logger.error("Enhanced client function not available despite import check")
                raise ImportError("Enhanced client initialization failed") from exc
        else:
            if enhanced_client and not ENHANCED_CLIENT_AVAILABLE:
                logger.warning(
                    "Enhanced client requested but not available, falling back to standard client"
                )

            # Use standard client
            initialize_client(
                host=config.OPENMETADATA_HOST,
                api_token=config.OPENMETADATA_JWT_TOKEN,
                username=config.OPENMETADATA_USERNAME,
                password=config.OPENMETADATA_PASSWORD,
            )
            logger.info("Successfully initialized standard OpenMetadata client")

        logger.info("Connected to OpenMetadata server at: %s", config.OPENMETADATA_HOST)
    except (ValueError, ConnectionError) as e:
        logger.error("Failed to initialize OpenMetadata client: %s", e)
        logger.error(
            "Please check your OpenMetadata configuration and ensure "
            "the server is accessible"
        )
        return
    except (ImportError, AttributeError, ModuleNotFoundError) as e:
        logger.error("Unexpected error during OpenMetadata client initialization: %s", e)
        return

    # Register API functions with bulk loading for performance
    registered_count = 0
    functions_to_register = []

    # First gather all functions to register
    for api in apis:
        logger.debug("Adding API: %s", api)

        try:
            api_type = APIType(api)
            get_function = APITYPE_TO_FUNCTIONS.get(api_type)
            if not get_function:
                logger.warning("API type '%s' not found in function mapping", api)
                continue

            functions = get_function()
        except (ValueError, KeyError, NotImplementedError) as e:
            logger.warning("API type '%s' not available: %s", api, e)
            continue
        except (TypeError, AttributeError, ImportError) as e:
            # More specific exceptions that could occur during module loading
            logger.error("Error loading API '%s': %s", api, e)
            continue

        # Filter functions for read-only mode if requested
        if read_only:
            original_count = len(functions)
            functions = filter_functions_for_read_only(functions)
            filtered_count = original_count - len(functions)
            if filtered_count > 0:
                logger.info(
                    "Filtered out %d write operations from %s API (read-only mode)",
                    filtered_count, api
                )

        # Add to bulk registration list
        functions_to_register.extend(functions)
        logger.info("Collected %d tools from %s API", len(functions), api)

    if not functions_to_register:
        logger.error(
            "No API functions were registered. Check your API selections "
            "and server configuration."
        )
        return

    # Now register all functions in a single batch for better performance
    for func, name, description, *_ in functions_to_register:
        register_tool(func, name=name, description=description)
        registered_count += 1

    logger.info("Total registered tools: %d", registered_count)

    # Start the appropriate server
    _start_server(transport, host, port, require_auth, logger)


def _start_server(transport, host, port, require_auth, logger):
    """Start the server with the specified transport."""
    if transport in ["http", "websocket"]:
        _start_http_server(transport, host, port, require_auth, logger)
    elif transport == "sse":
        _start_sse_server(logger)
    elif transport == "streamable-http":
        _start_streamable_http_server(host, port, logger)
    else:
        _start_stdio_server(logger)


def _start_http_server(transport, host, port, require_auth, logger):
    """Start HTTP/WebSocket server with FastAPI."""
    logger.info("Starting %s server on %s:%d", transport.upper(), host, port)

    if require_auth:
        logger.info("Authentication required for %s server", transport)
    else:
        logger.info("Authentication disabled for %s server", transport)

    try:
        # Use the existing config
        config = Config.from_env()

        # Create a FastAPI app for HTTP transport
        http_app = FastAPI(
            title="OpenMetadata MCP Server",
            description="MCP server for OpenMetadata integration",
            version="0.3.0"
        )

        # Add CORS middleware
        http_app.add_middleware(
            CORSMiddleware,
            allow_origins=config.cors_origins_list,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Setup authentication and endpoints
        _setup_http_endpoints(http_app, require_auth, logger)

        # Add health monitoring endpoints
        _setup_health_endpoints(http_app, logger)

        # Configure and start Uvicorn
        logger.info("Starting FastAPI app in HTTP mode")
        uvicorn.run(
            http_app,
            host=host,
            port=port,
            log_level="info",
            workers=None,  # Default to number of CPU cores
            loop="auto",  # Use best available event loop
            http="auto",  # Use best available HTTP protocol implementation
            limit_concurrency=None,  # No artificial concurrency limit
            limit_max_requests=None,  # No restart after max requests
            timeout_keep_alive=75,  # Longer keep-alive for WebSocket connections
        )
    except ImportError as e:
        logger.error("Failed to import required modules for %s server: %s", transport, e)
        return
    except (RuntimeError, ValueError, OSError) as e:
        logger.error("Failed to start %s server: %s", transport, e)
        return


def _setup_http_endpoints(http_app, require_auth, logger):
    """Setup HTTP endpoints with optional authentication."""
    if require_auth and AUTH_AVAILABLE and APIKeyAuthBackend and AuthDependency:
        # Create authentication dependency
        auth_backend = APIKeyAuthBackend()
        auth_dependency = AuthDependency(
            require_authentication=True, backends=[auth_backend]
        )

        # Protected endpoints
        @http_app.get("/", dependencies=[Depends(auth_dependency)])
        async def root():
            return {
                "message": "OpenMetadata MCP Server is running.",
                "status": "Server running with authentication enabled",
                "version": "0.3.0"
            }

        @http_app.get("/health", dependencies=[Depends(auth_dependency)])
        async def health():
            return {"status": "ok", "mode": "http", "auth": "required"}

        @http_app.get("/metrics", dependencies=[Depends(auth_dependency)])
        async def metrics():
            return {
                "status": "ok",
                "metrics": "Prometheus metrics endpoint"
            }
    else:
        if require_auth and not AUTH_AVAILABLE:
            logger.error(
                "Authentication requested but auth modules not available. "
                "Running without authentication."
            )

        # Public endpoints
        @http_app.get("/")
        async def root():
            auth_status = "disabled" if not require_auth else "failed to load"
            return {
                "message": "OpenMetadata MCP Server is running.",
                "status": f"Server running with authentication {auth_status}",
                "version": "0.3.0"
            }

        @http_app.get("/health")
        async def health():
            auth_status = "disabled" if not require_auth else "failed"
            return {"status": "ok", "mode": "http", "auth": auth_status}

        @http_app.get("/metrics")
        async def metrics():
            return {
                "status": "ok",
                "metrics": "Prometheus metrics endpoint (no auth)"
            }


def _setup_health_endpoints(http_app, logger):
    """Setup health monitoring endpoints."""
    if HEALTH_ROUTER_AVAILABLE and health_router:
        http_app.include_router(health_router)
        logger.info("Health monitoring endpoints registered successfully")
    else:
        logger.warning("Health router not available, using basic health endpoint")

        @http_app.get("/api/health")
        async def api_health():
            return {"status": "ok", "mode": "basic", "message": "Basic health check"}


def _start_sse_server(logger):
    """Start SSE server."""
    logger.debug("Starting MCP server for OpenMetadata with SSE transport")
    try:
        app.run(transport="sse")
    except (RuntimeError, ValueError, OSError) as e:
        logger.error("Failed to start SSE server: %s", e)


def _start_streamable_http_server(host, port, logger):
    """Start Streamable HTTP server."""
    logger.info(
        "Starting MCP server for OpenMetadata with Streamable HTTP transport on %s:%d",
        host, port
    )
    try:
        # Set environment variables for streamable-http transport
        os.environ["MCP_HOST"] = host
        os.environ["MCP_PORT"] = str(port)
        app.run(transport="streamable-http")
    except (RuntimeError, ValueError, OSError) as e:
        logger.error("Failed to start Streamable HTTP server: %s", e)


def _start_stdio_server(logger):
    """Start stdio server."""
    logger.debug("Starting MCP server for OpenMetadata with stdio transport")
    try:
        app.run(transport="stdio")
    except (RuntimeError, ValueError, OSError) as e:
        logger.error("Failed to start stdio server: %s", e)


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
