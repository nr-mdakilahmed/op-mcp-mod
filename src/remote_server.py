"""Remote MCP server with HTTP and WebSocket transport.

This module implements a FastAPI-based remote MCP server that can serve
the OpenMetadata tools over HTTP REST API and WebSocket connections,
with authentication, monitoring, and a web dashboard.
"""

import asyncio
from contextlib import asynccontextmanager
import json
import time
from typing import Any, Literal

from fastapi import Depends, FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from src.auth import User, create_access_token, require_auth
from src.config import Config
from src.google_auth import get_oauth_handler
from src.monitoring import get_logger, initialize_monitoring, log_mcp_operation, metrics
from src.server import app as mcp_app

# Import health router if available
try:
    from src.health import router as health_router

    HEALTH_ROUTER_AVAILABLE = True
except ImportError:
    HEALTH_ROUTER_AVAILABLE = False


# Pydantic models for API
class ToolRequest(BaseModel):
    """Request model for tool execution."""

    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class ContentItem(BaseModel):
    """Content item in tool response."""

    type: Literal["text", "image", "resource"]
    text: str | None = None
    url: str | None = None
    mime_type: str | None = None

    model_config = {"frozen": True}


class ToolResponse(BaseModel):
    """Response model for tool execution."""

    success: bool
    result: list[ContentItem] | None = None
    error: str | None = None
    execution_time: float


class AuthRequest(BaseModel):
    """Request model for authentication."""

    username: str
    password: str


class TokenResponse(BaseModel):
    """Response model for authentication token."""

    access_token: str
    token_type: str


class ServerStats(BaseModel):
    """Server statistics model."""

    total_tools: int
    metrics: dict[str, Any]
    uptime: float
    openmetadata_status: str


# Global variables
logger = get_logger("mcp.remote_server")
app_start_time = time.time()
connected_websockets: list[WebSocket] = []
registered_tools: dict[str, Any] = {}  # Track registered tools manually


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Manage application lifespan events."""
    # Startup
    config = Config.from_env()

    # Initialize monitoring
    monitoring_status = initialize_monitoring(config)
    logger.info("Remote MCP server starting up", monitoring_status=monitoring_status)

    # Initialize OpenMetadata connection (if needed)
    try:
        # Test OpenMetadata connection
        logger.info("Testing OpenMetadata connection", host=config.OPENMETADATA_HOST)
        # You could add actual connection test here
        logger.info("OpenMetadata connection successful")
    except (ConnectionError, TimeoutError, ValueError) as e:
        logger.error("OpenMetadata connection failed", error=str(e))

    yield

    # Shutdown
    logger.info("Remote MCP server shutting down")
    # Close any open connections
    for websocket in connected_websockets:
        try:
            await websocket.close()
        except (ConnectionError, ValueError):
            pass


def create_remote_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    config = Config.from_env()

    app = FastAPI(
        title="MCP OpenMetadata Remote Server",
        description="Remote Model Context Protocol server for OpenMetadata with authentication and monitoring",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Setup templates for web dashboard
    try:
        templates = Jinja2Templates(directory="templates")
    except (FileNotFoundError, ValueError):
        templates = None

    # Register health endpoints if available
    if HEALTH_ROUTER_AVAILABLE:
        app.include_router(health_router)
        logger.info("Health monitoring endpoints registered")

    # Helper function to get tool count
    def get_tool_count() -> int:
        """Get the number of registered tools."""
        try:
            # Use FastMCP's public tools property
            return len(getattr(mcp_app, "tools", {}))
        except (AttributeError, TypeError):
            return 0

    # Authentication endpoints
    @app.post("/auth/token", response_model=TokenResponse)
    async def login(auth_request: AuthRequest, config: Config = Depends(Config.from_env)):
        """Authenticate and return access token."""
        # Simple authentication - in production, verify against a user database
        if auth_request.username == "admin" and auth_request.password == "admin":
            access_token = create_access_token(
                data={"sub": auth_request.username, "scopes": ["read", "write"]}, config=config
            )
            return TokenResponse(access_token=access_token, token_type="bearer")
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")

    # Google OAuth endpoints
    @app.get("/auth/google/login")
    async def google_login(config: Config = Depends(Config.from_env)):
        """Initiate Google OAuth login flow."""
        if not config.google_oauth_enabled:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Google OAuth is not configured"
            )

        oauth_handler = get_oauth_handler(config)
        auth_url = oauth_handler.get_authorization_url()

        return {"auth_url": auth_url}

    @app.get("/auth/google/callback")
    async def google_callback(request: Request, config: Config = Depends(Config.from_env)):
        """Handle Google OAuth callback and return JWT token."""
        if not config.google_oauth_enabled:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Google OAuth is not configured"
            )

        oauth_handler = get_oauth_handler(config)
        user_info = await oauth_handler.handle_callback(request)

        # Create JWT token for the authenticated user
        access_token = oauth_handler.create_jwt_token_for_user(user_info)

        # Return token response
        return TokenResponse(access_token=access_token, token_type="bearer")

    @app.get("/auth/google/redirect")
    async def google_redirect(_request: Request, config: Config = Depends(Config.from_env)):
        """Redirect to Google OAuth or return error page."""
        if not config.google_oauth_enabled:
            return HTMLResponse("""
                <html>
                <head><title>OAuth Not Configured</title></head>
                <body>
                    <h1>Google OAuth Not Configured</h1>
                    <p>Please configure GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables.</p>
                    <a href="/">Back to Dashboard</a>
                </body>
                </html>
            """)

        oauth_handler = get_oauth_handler(config)
        auth_url = oauth_handler.get_authorization_url()

        return HTMLResponse(f"""
            <html>
            <head><title>Redirecting to Google...</title></head>
            <body>
                <h1>Redirecting to Google OAuth...</h1>
                <p>If you are not redirected automatically, <a href="{auth_url}">click here</a>.</p>
                <script>window.location.href = "{auth_url}";</script>
            </body>
            </html>
        """)

    # MCP Tools endpoints
    @app.get("/tools")
    async def list_tools(user: User = Depends(require_auth)):
        """List all available MCP tools."""
        try:
            # Use FastMCP's public API to list tools
            tools_result = await mcp_app.list_tools()
            tools = []

            # tools_result is actually a list[Tool] directly, not an object with .tools attribute
            if isinstance(tools_result, list):
                for tool in tools_result:
                    tools.append(
                        {
                            "name": getattr(tool, "name", None),
                            "description": getattr(tool, "description", "No description available"),
                            "inputSchema": getattr(tool, "inputSchema", None),
                        }
                    )
            else:
                logger.warning("Unexpected tools_result type: %s", type(tools_result))
                # If tools_result is not a list, just return an empty list

            logger.info("Listed tools", user=user.username, tool_count=len(tools))
            return {"tools": tools, "count": len(tools)}

        except (ValueError, AttributeError, ImportError) as e:
            logger.error("Error listing tools", error=str(e))
            raise HTTPException(status_code=500, detail=f"Failed to list tools: {str(e)}") from e

    @app.post("/tools/execute", response_model=ToolResponse)
    async def execute_tool(tool_request: ToolRequest, user: User = Depends(require_auth)):
        """Execute an MCP tool."""
        start_time = time.time()

        try:
            # Execute the tool using FastMCP's call_tool method
            result = await mcp_app.call_tool(name=tool_request.tool_name, arguments=tool_request.arguments or {})

            execution_time = time.time() - start_time

            # Process result into ContentItem objects
            content = []
            if hasattr(result, "__iter__") and not isinstance(result, str | bytes):
                # Handle iterables (lists, tuples) but not strings
                for item in result:
                    content.append(ContentItem(type="text", text=str(item)))
            else:
                # Handle single result or string
                content.append(ContentItem(type="text", text=str(result)))

            # Log successful operation
            log_mcp_operation(
                operation=f"execute_tool:{tool_request.tool_name}",
                success=True,
                duration=execution_time,
                details={"user": user.username, "arguments": tool_request.arguments},
            )

            # Record metrics
            metrics.record_tool_call(True, execution_time)

            return ToolResponse(success=True, result=content, execution_time=execution_time)

        except (ValueError, KeyError, TypeError, ConnectionError) as e:
            execution_time = time.time() - start_time
            error_msg = str(e)

            # Log failed execution
            log_mcp_operation(
                operation=f"execute_tool:{tool_request.tool_name}",
                success=False,
                duration=execution_time,
                details={"user": user.username, "arguments": tool_request.arguments},
                error=e,
            )

            # Record metrics
            metrics.record_tool_call(False, execution_time, type(e).__name__)

            return ToolResponse(success=False, error=error_msg, execution_time=execution_time)

    # Server statistics endpoint
    @app.get("/stats", response_model=ServerStats)
    async def get_stats(_user: User = Depends(require_auth)):
        """Get server statistics and metrics."""
        uptime = time.time() - app_start_time
        tool_count = get_tool_count()
        return ServerStats(
            total_tools=tool_count,
            metrics=metrics.get_stats(),
            uptime=uptime,
            openmetadata_status="connected",  # You could check actual status
        )

    # Prometheus-compatible metrics endpoint with efficient generation
    def _generate_prometheus_metrics(stats_dict):
        """Generate Prometheus metrics from stats dictionary."""
        lines = [
            "# HELP mcp_tool_calls_total Total number of MCP tool calls",
            "# TYPE mcp_tool_calls_total counter",
            f"mcp_tool_calls_total {stats_dict['total_calls']}",
            "# HELP mcp_tool_successful_calls_total Number of successful MCP tool calls",
            "# TYPE mcp_tool_successful_calls_total counter",
            f"mcp_tool_successful_calls_total {stats_dict['successful_calls']}",
            "# HELP mcp_tool_failed_calls_total Number of failed MCP tool calls",
            "# TYPE mcp_tool_failed_calls_total counter",
            f"mcp_tool_failed_calls_total {stats_dict['failed_calls']}",
            "# HELP mcp_tool_success_rate Success rate of MCP tool calls",
            "# TYPE mcp_tool_success_rate gauge",
            f"mcp_tool_success_rate {stats_dict['success_rate']:.4f}",
            "# HELP mcp_tool_average_response_time_seconds Average response time of MCP tool calls in seconds",
            "# TYPE mcp_tool_average_response_time_seconds gauge",
            f"mcp_tool_average_response_time_seconds {stats_dict['average_response_time']:.4f}",
            "# HELP mcp_tool_errors_total Number of errors by type",
            "# TYPE mcp_tool_errors_total counter",
        ]

        # Add error metrics with labels
        for error_type, count in stats_dict["errors_by_type"].items():
            lines.append(f'mcp_tool_errors_total{{error_type="{error_type}"}} {count}')

        # Add server uptime metric
        uptime = time.time() - app_start_time
        lines.append("# HELP mcp_server_uptime_seconds Server uptime in seconds")
        lines.append("# TYPE mcp_server_uptime_seconds gauge")
        lines.append(f"mcp_server_uptime_seconds {uptime:.1f}")

        return "\n".join(lines) + "\n"

    # Cache the last metrics output and timestamp
    _last_metrics = {"output": "", "timestamp": 0}
    _metrics_cache_ttl = 5  # seconds

    @app.get("/metrics")
    async def prometheus_metrics():
        """Prometheus metrics endpoint for agent compatibility."""
        current_time = time.time()

        # Check if cached metrics are still fresh (within 5 seconds)
        if current_time - _last_metrics["timestamp"] < _metrics_cache_ttl:
            # Use cached metrics
            metrics_output = _last_metrics["output"]
        else:
            # Generate fresh metrics
            stats = metrics.get_stats()
            metrics_output = _generate_prometheus_metrics(stats)

            # Update cache
            _last_metrics["output"] = metrics_output
            _last_metrics["timestamp"] = current_time

        # Return as plain text with proper content type
        return HTMLResponse(content=metrics_output, status_code=200, media_type="text/plain")

    # WebSocket endpoint for real-time communication
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        """WebSocket endpoint for real-time MCP communication."""
        await websocket.accept()
        connected_websockets.append(websocket)

        # Set up a background task for periodic heartbeat
        heartbeat_task = None

        try:
            # Start heartbeat task to keep connection alive
            async def send_heartbeat():
                """Send periodic heartbeat to keep connection alive."""
                while True:
                    try:
                        await websocket.send_text(json.dumps({"type": "heartbeat", "timestamp": time.time()}))
                        await asyncio.sleep(30)  # Send heartbeat every 30 seconds
                    except (WebSocketDisconnect, ConnectionError, RuntimeError):
                        break

            heartbeat_task = asyncio.create_task(send_heartbeat())

            while True:
                # Receive message from client with timeout
                try:
                    # Use wait_for to implement timeout
                    data = await asyncio.wait_for(
                        websocket.receive_text(),
                        timeout=60.0,  # 60 second timeout
                    )
                    message = json.loads(data)
                except asyncio.TimeoutError:
                    # No message received within timeout, but connection is still alive
                    # Heartbeat task will keep the connection
                    continue
                except json.JSONDecodeError:
                    # Invalid JSON
                    await websocket.send_text(json.dumps({"type": "error", "message": "Invalid JSON message"}))
                    continue

                # Handle different message types
                if message.get("type") == "execute_tool":
                    tool_name = message.get("tool_name")
                    arguments = message.get("arguments", {})
                    request_id = message.get("request_id")

                    start_time = time.time()

                    try:
                        # Use FastMCP's public API to execute tool
                        result = await mcp_app.call_tool(name=tool_name, arguments=arguments)

                        execution_time = time.time() - start_time

                        # Convert result to content items
                        content = []
                        if hasattr(result, "__iter__") and not isinstance(result, str | bytes):
                            # Handle iterables but not strings
                            for item in result:
                                content.append({"type": "text", "text": str(item)})
                        else:
                            # Handle single result or string
                            content.append({"type": "text", "text": str(result)})

                        response = {
                            "type": "tool_result",
                            "success": True,
                            "result": content,
                            "execution_time": execution_time,
                            "tool_name": tool_name,
                        }

                        # Include request_id in response if provided
                        if request_id:
                            response["request_id"] = request_id

                        # Log successful operation
                        log_mcp_operation(
                            operation=f"ws:execute_tool:{tool_name}",
                            success=True,
                            duration=execution_time,
                            details={"arguments": arguments},
                        )

                        # Record metrics
                        metrics.record_tool_call(True, execution_time)

                    except (ValueError, KeyError, TypeError, ConnectionError, AttributeError) as e:
                        execution_time = time.time() - start_time
                        response = {
                            "type": "tool_result",
                            "success": False,
                            "error": str(e),
                            "execution_time": execution_time,
                            "tool_name": tool_name,
                        }

                        # Include request_id in response if provided
                        if request_id:
                            response["request_id"] = request_id

                        # Log failed operation
                        log_mcp_operation(
                            operation=f"ws:execute_tool:{tool_name}",
                            success=False,
                            duration=execution_time,
                            details={"arguments": arguments},
                            error=e,
                        )

                        # Record metrics
                        metrics.record_tool_call(False, execution_time, type(e).__name__)

                    await websocket.send_text(json.dumps(response))

                elif message.get("type") == "ping":
                    # Return pong with timestamp for latency measurement
                    await websocket.send_text(
                        json.dumps(
                            {"type": "pong", "timestamp": time.time(), "request_timestamp": message.get("timestamp", 0)}
                        )
                    )

                else:
                    await websocket.send_text(
                        json.dumps({"type": "error", "message": f"Unknown message type: {message.get('type')}"})
                    )

        except WebSocketDisconnect:
            logger.info("WebSocket client disconnected")
        except (ConnectionError, ValueError, TypeError, RuntimeError) as e:
            logger.error("WebSocket error", error=str(e), error_type=type(e).__name__)
        except asyncio.TimeoutError:
            logger.warning("WebSocket timeout")
        finally:
            # Clean up
            if websocket in connected_websockets:
                connected_websockets.remove(websocket)

            # Cancel heartbeat task if running
            if heartbeat_task and not heartbeat_task.done():
                heartbeat_task.cancel()

    # Web Dashboard
    @app.get("/", response_class=HTMLResponse)
    async def dashboard(request: Request):
        """Serve the web dashboard."""
        tool_count = get_tool_count()

        if templates:
            return templates.TemplateResponse(
                "dashboard.html",
                {
                    "request": request,
                    "tool_count": tool_count,
                    "uptime": time.time() - app_start_time,
                },
            )
        else:
            # Get tool count for fallback HTML
            tool_count = get_tool_count()
            return HTMLResponse(f"""
            <html>
                <head><title>MCP OpenMetadata Server</title></head>
                <body>
                    <h1>MCP OpenMetadata Remote Server</h1>
                    <p>Server is running with {tool_count} tools available.</p>
                    <p>API Documentation: <a href='/docs'>/docs</a></p>
                </body>
            </html>
            """)

    return app


# Create the FastAPI app instance
remote_app = create_remote_app()
