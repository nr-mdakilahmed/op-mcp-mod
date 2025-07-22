# MCP Server for OpenMetadata

[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/yangkyeongmo-mcp-server-openmetadata-badge.png)](https://mseep.ai/app/yangkyeongmo-mcp-server-openmetadata)
[![smithery badge](https://smithery.ai/badge/@yangkyeongmo/mcp-server-openmetadata)](https://smithery.ai/server/@yangkyeongmo/mcp-server-openmetadata)

<a href="https://glama.ai/mcp/servers/lvgl5cmxa6">
  <img width="380" height="200" src="https://glama.ai/mcp/servers/lvgl5cmxa6/badge" alt="Server for OpenMetadata MCP server" />
</a>

A **modernized** Model Context Protocol (MCP) server for OpenMetadata with enterprise-grade features including Google OAuth, web dashboard, and 186 tools.

## 🚀 Quick Start

```bash
# 1. Install
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Edit .env with your OpenMetadata server details

# 3. Run
python -m src.main --transport stdio  # For AI assistants
python -m src.main --transport http   # For web apps (includes dashboard)
```

## ✨ Features

- **186 OpenMetadata Tools** - Complete API coverage
- **Multi-Transport** - stdio, HTTP, WebSocket support  
- **Enterprise Auth** - Username/password, API keys, Google OAuth 2.0
- **Web Dashboard** - Real-time monitoring and management
- **Production Ready** - Docker, Sentry monitoring, structured logging

## 📖 Complete Documentation

**👉 [See COMPLETE_GUIDE.md for full documentation](COMPLETE_GUIDE.md)**

Includes:
- Installation & setup instructions
- Authentication configuration (Google OAuth, API keys)
- All 186 available tools
- Usage examples (Python, JavaScript, curl)
- Deployment guides (Docker, production)
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
# Start HTTP server with dashboard
python -m src.main --transport http --host 0.0.0.0 --port 8000

# Access dashboard at http://localhost:8000
# Use API at http://localhost:8000/tools
```

### Docker Deployment
```bash
docker build -t mcp-openmetadata .
docker run -p 8000:8000 --env-file .env mcp-openmetadata
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
