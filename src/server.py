"""MCP server definition and configuration.

Provides FastMCP server instance creation, transport abstraction layer,
and server lifecycle management for both stdio and SSE protocols.
"""

from typing import Callable

import anyio
from fastmcp import FastMCP
from mcp.server.stdio import stdio_server


def get_server_runner(app: FastMCP, transport: str, **kwargs) -> Callable:
    """Get server runner based on transport type.

    Args:
        app: FastMCP server instance
        transport: Transport protocol ('stdio' or 'sse')
        **kwargs: Additional transport-specific arguments

    Returns:
        Callable that starts the server

    Raises:
        ValueError: If transport type is not supported
    """
    if transport == "stdio":
        return _get_stdio_server_runner(app)
    elif transport == "sse":
        port = kwargs.get("port", 8000)
        return _get_sse_server_runner(app, port)
    else:
        raise ValueError(f"Invalid transport: {transport}")


def _get_stdio_server_runner(app: FastMCP) -> Callable:
    """Create stdio server runner for FastMCP.

    Args:
        app: FastMCP server instance

    Returns:
        Callable that starts the stdio server
    """

    def run():
        async def arun():
            async with stdio_server() as streams:
                await app.run(streams[0], streams[1], app.create_initialization_options())

        anyio.run(arun)
        return 0

    return run


def _get_sse_server_runner(app: FastMCP, port: int) -> Callable:
    """Create SSE server runner for FastMCP.

    Args:
        app: FastMCP server instance
        port: Port number to listen on

    Returns:
        Callable that starts the SSE server
    """

    def run():
        from mcp.server.sse import SseServerTransport
        from starlette.applications import Starlette
        from starlette.routing import Mount, Route

        sse = SseServerTransport("/messages/")

        async def handle_sse(request):
            async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
                await app.run(streams[0], streams[1], app.create_initialization_options())

        starlette_app = Starlette(
            debug=True,
            routes=[
                Route("/sse", endpoint=handle_sse),
                Mount("/messages/", app=sse.handle_post_message),
            ],
        )

        import uvicorn

        uvicorn.run(starlette_app, host="0.0.0.0", port=port)
        return 0

    return run
