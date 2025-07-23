"""Monitoring and logging setup for MCP OpenMetadata server.

This module configures Sentry for error tracking, structured logging,
and performance monitoring for both stdio and remote server modes.
"""

import logging
import sys
from typing import Any

import structlog
from structlog.stdlib import LoggerFactory

try:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration

    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False

from src.config import Config


def setup_logging(config: Config | None = None, transport: str = None) -> None:
    """Setup structured logging configuration.

    Args:
        config: Configuration object
        transport: Transport type (stdio, http, etc.) - affects output stream
    """
    if config is None:
        config = Config.from_env()

    # Configure log level
    log_level = getattr(logging, config.LOG_LEVEL.upper(), logging.INFO)

    # For stdio transport, use stderr to avoid interfering with JSON-RPC protocol
    output_stream = sys.stderr if transport == "stdio" else sys.stdout

    if config.STRUCTURED_LOGGING:
        # Setup structured logging with structlog
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer(),
            ],
            context_class=dict,
            logger_factory=LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

        # Configure standard library logging
        handler = logging.StreamHandler(output_stream)
        handler.setFormatter(logging.Formatter("%(message)s"))

        root_logger = logging.getLogger()
        root_logger.addHandler(handler)
        root_logger.setLevel(log_level)

        # Silence noisy third-party loggers
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)

    else:
        # Setup basic logging
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler(output_stream)],
        )


def setup_sentry(config: Config | None = None) -> bool:
    """Setup Sentry error monitoring."""
    if config is None:
        config = Config.from_env()

    if not SENTRY_AVAILABLE:
        logging.warning(
            "Sentry SDK not available. Install with: pip install sentry-sdk[fastapi]"
        )
        return False

    if not config.SENTRY_DSN:
        logging.info("Sentry DSN not configured. Error monitoring disabled.")
        return False

    try:
        sentry_sdk.init(
            dsn=config.SENTRY_DSN,
            environment=config.SENTRY_ENVIRONMENT,
            traces_sample_rate=config.SENTRY_TRACES_SAMPLE_RATE,
            integrations=[
                FastApiIntegration(),
                LoggingIntegration(
                    level=logging.INFO,  # Capture info and above as breadcrumbs
                    event_level=logging.ERROR,  # Send errors as events
                ),
            ],
            # Performance monitoring
            enable_tracing=True,
            # Release tracking
            release=None,  # Set this to your app version
            # Error filtering
            before_send=filter_sentry_events,
        )

        logging.info(
            "Sentry monitoring initialized for environment: %s", config.SENTRY_ENVIRONMENT
        )
        return True

    except ImportError as e:
        logging.error("Failed to initialize Sentry - Sentry SDK not available: %s", e)
        return False
    except (ValueError, TypeError, OSError) as e:
        logging.error("Failed to initialize Sentry: %s", e)
        return False


def filter_sentry_events(
    event: dict[str, Any], hint: dict[str, Any]
) -> dict[str, Any] | None:
    """Filter Sentry events to reduce noise."""
    # Don't send certain types of exceptions
    if "exc_info" in hint:
        exc_type, _, _ = hint["exc_info"]

        # Filter out common HTTP client errors
        if exc_type.__name__ in ["ConnectionError", "TimeoutError", "HTTPStatusError"]:
            return None

        # Filter out validation errors in development
        if "ValidationError" in exc_type.__name__:
            return None

    # Filter by log level in development
    if event.get("level") == "info":
        return None

    return event


def get_logger(name: str) -> Any:
    """Get a logger instance (structured or standard)."""
    try:
        config = Config.from_env()

        if hasattr(config, "STRUCTURED_LOGGING") and config.STRUCTURED_LOGGING:
            return structlog.get_logger(name)
        else:
            return logging.getLogger(name)
    except (AttributeError, TypeError, ValueError, ImportError):
        # Fallback to standard logging if config fails
        return logging.getLogger(name)


class MCPMetrics:
    """Simple metrics collection for MCP operations."""

    def __init__(self):
        self.tool_calls = 0
        self.successful_calls = 0
        self.failed_calls = 0
        self.total_response_time = 0.0
        self.errors_by_type = {}

    def record_tool_call(
        self, success: bool, response_time: float, error_type: str | None = None
    ):
        """Record metrics for a tool call."""
        self.tool_calls += 1
        self.total_response_time += response_time

        if success:
            self.successful_calls += 1
        else:
            self.failed_calls += 1
            if error_type:
                self.errors_by_type[error_type] = (
                    self.errors_by_type.get(error_type, 0) + 1
                )

    def get_stats(self) -> dict[str, Any]:
        """Get current metrics statistics."""
        avg_response_time = (
            self.total_response_time / self.tool_calls if self.tool_calls > 0 else 0.0
        )

        return {
            "total_calls": self.tool_calls,
            "successful_calls": self.successful_calls,
            "failed_calls": self.failed_calls,
            "success_rate": (
                self.successful_calls / self.tool_calls if self.tool_calls > 0 else 0.0
            ),
            "average_response_time": avg_response_time,
            "errors_by_type": self.errors_by_type,
        }

    def reset(self):
        """Reset all metrics."""
        self.tool_calls = 0
        self.successful_calls = 0
        self.failed_calls = 0
        self.total_response_time = 0.0
        self.errors_by_type = {}


# Global metrics instance
metrics = MCPMetrics()


def log_mcp_operation(
    operation: str,
    success: bool,
    duration: float,
    details: dict[str, Any] | None = None,
    error: Exception | None = None,
):
    """Log MCP operation with structured data."""
    logger = get_logger("mcp.operations")

    log_data = {
        "operation": operation,
        "success": success,
        "duration_ms": duration * 1000,  # Convert to milliseconds
        "details": details or {},
    }

    if error:
        log_data["error"] = str(error)
        log_data["error_type"] = type(error).__name__

    if success:
        logger.info("MCP operation completed", **log_data)
    else:
        logger.error("MCP operation failed", **log_data)

        # Send to Sentry if available
        if SENTRY_AVAILABLE and error:
            sentry_sdk.capture_exception(error)


def initialize_monitoring(
    config: Config | None = None, transport: str = None
) -> dict[str, bool]:
    """Initialize all monitoring systems.

    Args:
        config: Configuration object
        transport: Transport type (affects logging output stream)
    """
    if config is None:
        config = Config.from_env()

    results = {
        "logging": False,
        "sentry": False,
    }

    try:
        setup_logging(config, transport)
        results["logging"] = True
        logging.info("Logging system initialized")
    except (OSError, ValueError, TypeError) as e:
        print(f"Failed to setup logging: {e}")

    try:
        results["sentry"] = setup_sentry(config)
    except (ImportError, ValueError, TypeError) as e:
        logging.error("Failed to setup Sentry: %s", e)

    return results
