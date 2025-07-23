# MCP Server for OpenMetadata

[![MseeP.ai Security Assessment Badge# Start development server
make run-web

# Access dashboard at http://localhost:8000
# Use API at http://localhost:8000/tools
```

## 🔧 Available Commandsp.net/pr/yangkyeongmo-mcp-server-openmetadata-badge.png)](https://mseep.ai/app/yangkyeongmo-mcp-server-openmetadata)
[![smithery badge](https://smithery.ai/badge/@yangkyeongmo/mcp-server-openmetadata)](https://smithery.ai/server/@yangkyeongmo/mcp-server-openmetadata)

<a href="https://glama.ai/mcp/servers/lvgl5cmxa6">
  <img width="380" height="200" src="https://glama.ai/mcp/servers/lvgl5cmxa6/badge" alt="Server for OpenMetadata MCP server" />
</a>

A **modernized** Model Context Protocol (MCP) server for OpenMetadata with enterprise-grade features including Google OAuth, web dashboard, and 186 tools.

## 🚀 Quick Start

```bash
# 1. Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Install dependencies (includes web + auth + monitoring)
make install-all

# 3. Configure
cp .env.example .env
# Edit .env with your OpenMetadata server details

# 4. Validate setup
make validate

# 5. Run
make run            # For AI assistants (stdio)
make run-web        # For web apps (includes dashboard)
make run-web-auth   # With authentication enabled
```

## ✨ Features

- **186 OpenMetadata Tools** - Complete API coverage
- **Multi-Transport** - stdio, HTTP, WebSocket support  
- **Enterprise Auth** - Username/password, API keys, Google OAuth 2.0
- **Web Dashboard** - Real-time monitoring and management
- **Production Ready** - uv package management, Sentry monitoring, structured logging

## 📖 Complete Documentation

**👉 [See COMPLETE_GUIDE.md for full documentation](COMPLETE_GUIDE.md)**

Includes:
- Installation & setup instructions
- Authentication configuration (Google OAuth, API keys)
- All 186 available tools
- Usage examples (Python, JavaScript, curl)
- Production deployment guides
- Troubleshooting and support

## 🛠️ Common Use Cases

### With AI Assistants (Claude, ChatGPT)
```json
// Claude Desktop config
{
  "mcpServers": {
    "openmetadata": {
      "command": "python",
      "args": ["-m", "src.main", "--transport", "stdio"],
      "cwd": "/path/to/mcp-server-openmetadata"
    }
  }
}
```

### As Web Service
```bash
# Start development server
make run-web

# Access dashboard at http://localhost:8000
# Use API at http://localhost:8000/tools
```

## 🔧 Available Commands

```bash
# Installation
make install          # Basic installation
make install-all      # Install with all extras (recommended)
make install-web      # Install web + auth features

# Setup validation
make validate         # Verify setup is correct

# Running the server
make run              # stdio transport (for AI assistants)
make run-sse          # SSE transport
make run-web          # HTTP server on port 8000
make run-web-auth     # HTTP server with authentication

# Development
make lint             # Check code quality
make format           # Format code
make test             # Run tests
```

## 🔧 Configuration

Create `.env` file:
```env
# OpenMetadata connection
OPENMETADATA_HOST_PORT=http://localhost:8585/api
OPENMETADATA_AUTH_PROVIDER=no-auth

# Server settings  
SERVER_HOST=0.0.0.0
SERVER_PORT=8000

# Optional: Authentication
ENABLE_AUTH=true
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-secret
```

## 📊 Available Tools

- **Search & Discovery**: Find any entity across your data ecosystem
- **Lineage Analysis**: Track data flow and dependencies  
- **Glossary Management**: Create business terms and definitions
- **Schema Exploration**: Browse database and table structures
- **Data Quality**: Access test cases and validation results
- **User Management**: Handle teams, roles, and permissions

*[See complete tool list in COMPLETE_GUIDE.md](COMPLETE_GUIDE.md)*

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Submit pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) file.

---

**📖 For complete setup instructions, authentication guides, and API documentation, see [COMPLETE_GUIDE.md](COMPLETE_GUIDE.md)**
