"""OpenMetadata integration layer for MCP server.

This package provides modular access to OpenMetadata's REST API through
standardized MCP tools. Each module handles a specific API group following
consistent patterns for tool registration and function implementation.

Client Architecture:
    1. **Standard Client** (`openmetadata_client.py`): Basic API access
    2. **Enhanced Client** (`enhanced_client.py`): Production-ready with caching & pooling
    3. **Performance Utilities** (`client_performance.py`): Reusable performance components

Usage:
    # Standard client
    from src.openmetadata.openmetadata_client import get_client

    # Enhanced client (recommended for production)
    from src.openmetadata.enhanced_client import get_enhanced_client
"""

# Export the main client interfaces
try:
    from .enhanced_client import get_enhanced_client, initialize_enhanced_client
    from .openmetadata_client import get_client, initialize_client

    __all__ = ["initialize_client", "get_client", "initialize_enhanced_client", "get_enhanced_client"]
except ImportError:
    # Fallback if enhanced client dependencies aren't available
    from .openmetadata_client import get_client, initialize_client

    __all__ = ["initialize_client", "get_client"]
