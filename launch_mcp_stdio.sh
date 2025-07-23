#!/bin/bash
# Launch MCP OpenMetadata Server with STDIO transport and Inspector

cd /Users/mdakilahmed/Documents/GitHub/op-mcp-mod

# Check if --stdio-only flag is passed (when called by Inspector)
if [[ "$1" == "--stdio-only" ]]; then
    # When called by Inspector, run the server with authentication required
    # Note: You'll need to provide JWT token or API key when connecting
    exec uv run python src --transport stdio --require-auth
fi

# Main script execution (when run manually)
# Check if Inspector is already running
if ! pgrep -f "@modelcontextprotocol/inspector" > /dev/null; then
    echo "Starting MCP Inspector..."
    # Start Inspector without authentication for STDIO transport compatibility
    # Note: Inspector proxy auth conflicts with STDIO; MCP server still requires auth
    DANGEROUSLY_OMIT_AUTH=true npx @modelcontextprotocol/inspector &
    INSPECTOR_PID=$!
    
    # Wait a moment for Inspector to start
    sleep 3
    
    # Open Inspector in browser
    echo "Opening Inspector in browser..."
    open http://127.0.0.1:6274
    
    echo "Inspector started (PID: $INSPECTOR_PID)"
    echo "Inspector URL: http://127.0.0.1:6274"
else
    echo "Inspector is already running"
    echo "Inspector URL: http://127.0.0.1:6274"
fi

echo ""
echo "🔧 MCP Inspector Setup Instructions:"
echo "   1. Go to http://127.0.0.1:6274 in your browser"
echo "   2. Click 'Add Server' or configure a new connection"
echo "   3. Select 'stdio' transport"
echo "   4. Set Command: $(pwd)/launch_mcp_stdio.sh"
echo "   5. Set Arguments: --stdio-only"
echo "   6. Click 'Connect'"
echo ""
echo "🔐 Security Note:"
echo "   • Inspector UI: No auth (required for STDIO compatibility)"
echo "   • MCP Server: Requires JWT token or API key for tool access"
echo "   • Your OpenMetadata tools are still protected"
echo ""
echo "📋 Or copy this configuration to Inspector:"
echo "   Transport: stdio"
echo "   Command: $(pwd)/launch_mcp_stdio.sh"
echo "   Arguments: --stdio-only"
echo ""

echo "Script setup complete. Use the Inspector to connect with STDIO transport."
echo "Press Ctrl+C to stop the Inspector when done."
# Wait for user to stop the Inspector
wait $INSPECTOR_PID 2>/dev/null
