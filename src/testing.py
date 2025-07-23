"""Interactive testing module for MCP OpenMetadata server.

This module provides testing capabilities that were previously in enhanced_server.py.
"""

from typing import Any, cast

from src.config import Config
from src.monitoring import get_logger, initialize_monitoring
from src.openmetadata.openmetadata_client import initialize_client
from src.server import app as mcp_app, get_server_status, register_tool

# Import search functions for testing
from src.openmetadata.search import get_all_functions as get_search_functions

logger = get_logger("testing")


async def register_tools_for_testing(config: Config) -> None:
    """Register a basic set of tools for testing purposes."""
    try:
        # Initialize the OpenMetadata client
        initialize_client(
            host=config.OPENMETADATA_HOST,
            api_token=config.OPENMETADATA_JWT_TOKEN,
            username=config.OPENMETADATA_USERNAME,
            password=config.OPENMETADATA_PASSWORD,
        )
        logger.info("Initialized OpenMetadata client for testing")

        # Register search tools for testing
        search_functions = get_search_functions()
        for func, name, description, *_ in search_functions:
            register_tool(func, name=name, description=description)

        logger.info("Registered %d search tools for testing", len(search_functions))

    except (ValueError, ConnectionError, ImportError, AttributeError) as e:
        logger.error("Failed to register tools for testing", error=str(e))
        raise


async def test_tool_execution() -> None:
    """Test tool execution directly."""
    try:
        logger.info("Testing tool execution...")

        # Test search tool
        result = await mcp_app.call_tool(
            name="search_entities", arguments={"q": "test", "size": 2}
        )

        logger.info("Tool execution successful", result_type=type(result))

        # Convert result to serializable format
        if hasattr(result, "__iter__"):
            content = []
            for item in result:
                # Use getattr with default values to avoid attribute errors
                if hasattr(item, "text"):
                    content.append({
                        "type": "text",
                        "text": getattr(item, "text", str(item))
                    })
                elif hasattr(item, "data"):
                    content.append({
                        "type": "resource",
                        "data": str(getattr(item, "data", str(item)))
                    })
                else:
                    content.append({"type": "unknown", "data": str(item)})

            print(f"Tool execution result: {content}")
        else:
            print(f"Tool execution result: {result}")

    except ImportError as e:
        logger.error("Tool execution failed - import error", error=str(e))
        print(f"Tool execution error (import): {e}")
    except AttributeError as e:
        logger.error("Tool execution failed - attribute error", error=str(e))
        print(f"Tool execution error (attribute): {e}")
    except ValueError as e:
        logger.error("Tool execution failed - value error", error=str(e))
        print(f"Tool execution error (value): {e}")


async def list_available_tools() -> list[Any]:
    """List available tools."""
    try:
        logger.info("Listing available tools...")

        if hasattr(mcp_app, "list_tools"):
            tools = await mcp_app.list_tools()
            logger.info("Found tools", count=len(tools))
            print(f"Available tools ({len(tools)}):")
            for i, tool in enumerate(tools, 1):
                tool_name = getattr(tool, "name", "Unknown")
                tool_desc = getattr(tool, "description", "No description")
                print(f"  {i}. {tool_name} - {tool_desc}")
            return tools
        else:
            logger.warning("Unable to list tools - method not available")
            print("Tool listing not available")
            return []

    except ImportError as e:
        logger.error("Failed to list tools - import error", error=str(e))
        return []
    except AttributeError as e:
        logger.error("Failed to list tools - attribute error", error=str(e))
        return []


async def run_interactive_testing(config: Config) -> None:
    """Run in interactive mode for testing."""
    print("=== MCP OpenMetadata Server - Interactive Testing ===")
    print("Interactive testing mode")
    print()

    # Initialize monitoring
    monitoring_status = initialize_monitoring(config)
    logger.info("Monitoring initialized", status=monitoring_status)

    # Register tools for testing
    try:
        await register_tools_for_testing(config)
        logger.info("Tools registered successfully for testing")
    except (ValueError, ConnectionError, ImportError, AttributeError) as e:
        logger.error("Failed to register tools for testing", error=str(e))
        print(f"Error registering tools: {e}")
        return

    while True:
        print("\nAvailable commands:")
        print("1. List tools")
        print("2. Test tool execution")
        print("3. Check server status")
        print("4. Exit")

        try:
            choice = input("\nEnter choice (1-4): ").strip()

            if choice == "1":
                await list_available_tools()
            elif choice == "2":
                await test_tool_execution()
            elif choice == "3":
                # Cast the status to Dict[str, Any] to satisfy type checking
                status_dict = cast(dict[str, Any], get_server_status())
                metadata = cast(dict[str, str], status_dict.get("metadata", {}))

                print("\n=== Server Status ===")
                print(f"Status: {status_dict.get('status', 'unknown')}")
                print(
                    f"Server: {metadata.get('title', 'Unknown')} "
                    f"v{metadata.get('version', '0.0.0')}"
                )
                print(f"Description: {metadata.get('description', 'No description')}")
                print(f"Tools registered: {status_dict.get('registered_tools_count', 0)}")
                print(f"Config: OpenMetadata Host: {config.OPENMETADATA_HOST}")
                print("=" * 20)
            elif choice == "4":
                print("Exiting...")
                break
            else:
                print("Invalid choice")

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except (ImportError, AttributeError, ValueError) as e:
            logger.error("Command failed", error=str(e))
            print(f"Error: {e}")
