
# MCP Server for OpenMetadata

A modern, production-ready Model Context Protocol (MCP) server for OpenMetadata, supporting AI assistants, web dashboards, and enterprise authentication.

## 🚀 Quick Start

```bash
# 1. Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Install all dependencies (creates .env from template)
make install-all

# 3. Configure your OpenMetadata connection
# Edit .env with your OpenMetadata server details

# 4. Validate setup
make validate

# 5. Run the server
make run            # For AI assistants (stdio)
make run-web        # For web apps (HTTP dashboard)
make run-web-auth   # With authentication enabled
```

## ✨ Features

- **186+ OpenMetadata Tools**: Full API coverage for search, lineage, glossaries, dashboards, and more
- **Multi-Transport**: stdio, HTTP, WebSocket, SSE
- **Enterprise Auth**: Username/password, API keys, Google OAuth 2.0
- **Web Dashboard**: Real-time monitoring and management
- **Production Ready**: Sentry monitoring, structured logging, CORS, domain restrictions
- **Fast Development**: uv package management, Makefile automation

## 📦 Installation

See [complete_guide.md](complete_guide.md) for full setup, configuration, and advanced usage.

## �️ Make Commands

```bash
make install-all      # Install all dependencies (recommended)
make install-dev      # Development dependencies only
make install-prod     # Production dependencies only
make validate         # Validate setup
make run              # stdio transport (AI assistants)
make run-web          # HTTP server
make run-web-auth     # HTTP server with authentication
make help             # List all available commands
```

## � Documentation

- [Complete Guide](complete_guide.md): Full setup, configuration, API usage, and troubleshooting
- [LICENSE](LICENSE): MIT License

---

**For full documentation, advanced configuration, and troubleshooting, see [complete_guide.md](complete_guide.md).**
