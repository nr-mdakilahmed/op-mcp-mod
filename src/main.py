"""Central orchestration module for MCP OpenMetadata server.

This module configures the CLI interface with Click for transport selection,
dynamically loads and registers API modules based on user selection,
and manages server lifecycle with chosen transport protocol.
"""

import logging
import asyncio

import click
import uvicorn
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from src.config import Config
from src.enums import APIType
from src.monitoring import initialize_monitoring
from src.openmetadata.openmetadata_client import initialize_client
from src.server import app, register_tool
from src.testing import run_interactive_testing

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
    write_keywords = {'create', 'update', 'delete', 'patch', 'add', 'remove', 'set', 'modify', 'edit'}
    
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
    type=click.Choice(["stdio", "sse", "http", "websocket"]),
    default="stdio",
    help="Transport type for MCP communication",
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
    default=["table", "database", "databaseschema", "dashboard", "chart", "pipeline", "topic", "metrics", "container"],
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
    help="Require authentication for remote server (only for http/websocket transport)",
)
@click.option(
    "--test",
    is_flag=True,
    default=False,
    help="Run in interactive testing mode",
)
def main(transport, host, port, apis, read_only, require_auth, test):
    """Start the MCP OpenMetadata server with selected API groups."""
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Initialize configuration
    config = Config.from_env()
    
    # Initialize monitoring
    monitoring_status = initialize_monitoring(config)
    logger.info("Monitoring initialized: %s", monitoring_status)

    # Handle test mode
    if test:
        asyncio.run(run_interactive_testing(config))
        return

    # Initialize global OpenMetadata client
    try:
        initialize_client(
            host=config.OPENMETADATA_HOST,
            api_token=config.OPENMETADATA_JWT_TOKEN,
            username=config.OPENMETADATA_USERNAME,
            password=config.OPENMETADATA_PASSWORD,
        )
        logger.info("Successfully initialized OpenMetadata client for host: %s", config.OPENMETADATA_HOST)
    except (ValueError, ConnectionError) as e:
        logger.error("Failed to initialize OpenMetadata client: %s", e)
        logger.error("Please check your OpenMetadata configuration and ensure the server is accessible")
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
                logger.info("Filtered out %d write operations from %s API (read-only mode)", 
                            filtered_count, api)
            
        # Add to bulk registration list
        functions_to_register.extend(functions)
        logger.info("Collected %d tools from %s API", len(functions), api)
    
    if not functions_to_register:
        logger.error("No API functions were registered. Check your API selections and server configuration.")
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
        logger.info("Starting %s server on %s:%d", transport.upper(), host, port)
        
        if require_auth:
            logger.info("Authentication required for %s server", transport)
        else:
            logger.info("Authentication disabled for %s server", transport)
        
        try:
            # Use the existing config
            config = Config.from_env()
            
            # Create a minimal app that can at least start
            minimal_app = FastAPI(
                title="OpenMetadata MCP Server",
                description="MCP server for OpenMetadata integration",
                version="1.0.0"
            )
            
            # Add CORS middleware
            minimal_app.add_middleware(
                CORSMiddleware,
                allow_origins=config.cors_origins_list,
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )
            
            # Add basic authentication if required
            if require_auth:
                try:
                    from src.auth import AuthDependency, APIKeyAuthBackend
                    
                    # Create a simplified auth dependency with just API key validation for minimal mode
                    auth_backend = APIKeyAuthBackend()
                    auth_dependency = AuthDependency(require_authentication=True, backends=[auth_backend])
                    
                    # Update endpoints to require authentication
                    @minimal_app.get("/", dependencies=[Depends(auth_dependency)])
                    async def root():
                        return {
                            "message": "OpenMetadata MCP Server is running in minimal mode.", 
                            "status": "There was an error loading the full server functionality. Please check server logs."
                        }
                    
                    @minimal_app.get("/health", dependencies=[Depends(auth_dependency)])
                    async def health():
                        return {"status": "ok", "mode": "minimal", "auth": "required"}
                    
                    @minimal_app.get("/metrics", dependencies=[Depends(auth_dependency)])
                    async def metrics():
                        return {"status": "ok", "metrics": "Prometheus metrics endpoint (minimal mode)"}
                except ImportError:
                    logger.error("Failed to import authentication modules. Running with minimal security.")
                    # Fallback to basic endpoints without authentication
                    @minimal_app.get("/")
                    async def root():
                        return {
                            "message": "OpenMetadata MCP Server is running in minimal mode with no authentication.", 
                            "status": "There was an error loading authentication modules. Please check server logs."
                        }
                    
                    @minimal_app.get("/health")
                    async def health():
                        return {"status": "ok", "mode": "minimal", "auth": "failed"}
                    
                    @minimal_app.get("/metrics")
                    async def metrics():
                        return {"status": "ok", "metrics": "Prometheus metrics endpoint (minimal mode, no auth)"}
            else:
                @minimal_app.get("/")
                async def root():
                    return {
                        "message": "OpenMetadata MCP Server is running in minimal mode.", 
                        "status": "There was an error loading the full server functionality. Please check server logs."
                    }
                
                @minimal_app.get("/health")
                async def health():
                    return {"status": "ok", "mode": "minimal", "auth": "none"}
                
                @minimal_app.get("/metrics")
                async def metrics():
                    return {"status": "ok", "metrics": "Prometheus metrics endpoint (minimal mode)"}
                
            # Configure Uvicorn with optimized settings
            logger.info("Using minimal FastAPI app (standalone mode)")
            uvicorn.run(
                minimal_app, 
                host=host, 
                port=port, 
                log_level="info",
                workers=None,  # Default to number of CPU cores
                loop="auto",   # Use best available event loop
                http="auto",   # Use best available HTTP protocol implementation
                limit_concurrency=None,  # No artificial concurrency limit
                limit_max_requests=None,  # No restart after max requests
                timeout_keep_alive=75,   # Longer keep-alive for WebSocket connections
            )
        except ImportError as e:
            logger.error("Failed to import required modules for %s server: %s", transport, e)
            return
        except (RuntimeError, ValueError, OSError) as e:
            logger.error("Failed to start %s server: %s", transport, e)
            return
        
    elif transport == "sse":
        logger.debug("Starting MCP server for OpenMetadata with SSE transport")
        try:
            app.run(transport="sse")
        except (RuntimeError, ValueError, OSError) as e:
            logger.error("Failed to start SSE server: %s", e)
    else:
        logger.debug("Starting MCP server for OpenMetadata with stdio transport")
        try:
            app.run(transport="stdio")
        except (RuntimeError, ValueError, OSError) as e:
            logger.error("Failed to start stdio server: %s", e)


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
