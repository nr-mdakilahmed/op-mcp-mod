# MCP Server for OpenMetadata - Complete Guide

A modernized Model Context Protocol (MCP) server for OpenMetadata, providing robust, secure, and flexible access to metadata for AI assistants and web applications.

---

## 🎯 Quick Start

### Prerequisites
- Python 3.10+
- OpenMetadata server instance
- uv package manager

### Installation

```bash
git clone https://github.com/yangkyeongmo/mcp-server-openmetadata
cd mcp-server-openmetadata

curl -LsSf https://astral.sh/uv/install.sh | sh
make install-all
```

### Configuration

```bash
cp .env.example .env
# Edit .env with your OpenMetadata server details
```

### Validation

```bash
make validate
```

### Running

```bash
make run            # stdio transport (AI assistants)
make run-web        # HTTP server
make run-web-auth   # HTTP server with authentication
```

---

## ✨ Features

- **186+ OpenMetadata Tools**: Search, lineage, glossaries, dashboards, tables, users, teams, policies, and more
- **Multi-Transport**: stdio, HTTP, WebSocket, SSE
- **Enterprise Authentication**: Username/password, API keys, Google OAuth 2.0
- **Web Dashboard**: Real-time monitoring, tool management, health checks
- **Production Ready**: Sentry monitoring, structured logging, CORS, domain restrictions
- **Fast Development**: uv package management, Makefile automation

---

## 🛠️ Make Commands

```bash
make install-all      # Install all dependencies (recommended)
make install-dev      # Development dependencies only
make install-prod     # Production dependencies only
make validate         # Validate setup
make run              # stdio transport (AI assistants)
make run-web          # HTTP server
make run-web-auth     # HTTP server with authentication
make lint             # Lint code
make format           # Format code
make test             # Run tests
make clean            # Clean build artifacts
make help             # List all available commands
```

---

## 🔐 Authentication

### Basic Auth
- Set `ENABLE_AUTH=true` and `SECRET_KEY` in `.env`
- Use `/auth/token` endpoint to get JWT

### API Key Auth
- Pass `X-API-Key` header in requests

### Google OAuth 2.0
- Set up credentials in Google Cloud Console
- Configure `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, and `GOOGLE_REDIRECT_URI` in `.env`
- Use `/auth/google/redirect` for OAuth flow

---

## 🛠️ Usage Examples

### AI Assistant Integration

```json
{
  "mcpServers": {
    "openmetadata": {
      "command": "uv",
      "args": ["run", "python", "-m", "src.main", "--transport", "stdio"],
      "cwd": "/path/to/mcp-server-openmetadata",
      "env": {
        "OPENMETADATA_HOST": "http://localhost:8585"
      }
    }
  }
}
```

### Web API Usage

```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     "http://localhost:8000/tools/execute" \
     -d '{"name": "mcp_openmetadata_search_metadata", "arguments": {"query": "users", "entity_type": "table"}}'
```

---

## ⚡ Available Tools (Sample)

- `mcp_openmetadata_search_metadata` - Search entities
- `mcp_openmetadata_get_entity_details` - Get entity details
- `mcp_openmetadata_get_entity_lineage` - Data lineage
- `mcp_openmetadata_create_glossary` - Create glossaries
- `database_get_databases` - List databases
- `table_get_tables` - List tables
- `dashboards_get_dashboards` - List dashboards
- `users_get_users` - List users
- `test_cases_get_test_cases` - List test cases
- ...and 170+ more covering the full OpenMetadata API

---

## 📊 Web Dashboard

- Access at `http://localhost:8000`
- Features: Real-time stats, tool management, health checks, API docs

---

## 🔍 Troubleshooting

- **Connection issues**: Check `OPENMETADATA_HOST_PORT` and server status
- **OAuth issues**: Verify Google credentials and redirect URI
- **Tool errors**: Use debug logging (`LOG_LEVEL=DEBUG`), validate server accessibility

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

---

## � License

MIT License - see [LICENSE](LICENSE)

---

## 🆘 Support

- GitHub Issues
- Documentation in this guide
- Security issues: contact maintainers privately

---

**You're all set! This MCP server provides everything you need for robust OpenMetadata integration with AI assistants and web applications.**
- **📚 Glossary Management**: Create and manage business glossaries
- **📋 Schema Information**: Detailed table schemas and metadata
- **186 Tools**: Complete OpenMetadata API coverage

### Enterprise Features
- **🔐 Multi-Auth**: Username/password, API keys, Google OAuth 2.0
- **🌐 Remote Server**: FastAPI HTTP/WebSocket server
- **📊 Web Dashboard**: Real-time management interface
- **📈 Monitoring**: Sentry integration and structured logging
- **🔒 Security**: JWT tokens, CORS, domain restrictions
- **⚡ Modern Tooling**: uv package management for fast development

### Transport Options
- **stdio**: Direct AI assistant integration
- **HTTP**: RESTful API for web applications
- **WebSocket**: Real-time communication

---

## 📦 Installation & Setup

### Prerequisites
- Python 3.9+
- OpenMetadata server instance
- uv package manager (recommended)

### 1. Clone and Install
```bash
git clone https://github.com/yangkyeongmo/mcp-server-openmetadata
cd mcp-server-openmetadata

# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies with all features
make install-all
```

### 2. Environment Configuration
```bash
cp .env.example .env
```

Edit `.env` with your settings:
```env
# OpenMetadata Configuration
OPENMETADATA_HOST_PORT=http://localhost:8585/api
OPENMETADATA_AUTH_PROVIDER=no-auth
# OPENMETADATA_JWT_TOKEN=your-jwt-token  # If using JWT auth

# Server Configuration
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
LOG_LEVEL=INFO

# Authentication (Optional)
SECRET_KEY=your-secret-key-here
ENABLE_AUTH=true

# Google OAuth (Optional)
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback
OAUTH_ALLOWED_DOMAINS=yourcompany.com

# Monitoring (Optional)
SENTRY_DSN=your-sentry-dsn
SENTRY_ENVIRONMENT=production
```

### 3. Run the Server

#### For AI Assistants (stdio)
```bash
make run
```

#### For Web Applications (HTTP)
```bash
make run-web
```

#### For Web with Authentication
```bash
make run-web-auth
```

#### Validate Setup
```bash
make validate
```

#### List Available Make Commands
```bash
make help  # or just 'make' to see available targets
```

---

## 🔐 Authentication Setup

### Basic Authentication
1. Set `ENABLE_AUTH=true` in `.env`
2. Set a strong `SECRET_KEY`
3. Create user credentials:
```bash
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your-password"}'
```

### API Key Authentication
```bash
# Include API key in requests
curl -H "X-API-Key: your-api-key" http://localhost:8000/tools
```

### Google OAuth 2.0 Setup

#### Step 1: Google Cloud Console
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project or select existing one
3. Enable APIs:
   - Google+ API
   - Google Identity

#### Step 2: OAuth Consent Screen
1. Navigate to **APIs & Services** > **OAuth consent screen**
2. Choose **External** user type
3. Fill required information:
   - **App name**: "MCP OpenMetadata Server"
   - **User support email**: Your email
   - **Developer contact email**: Your email
4. Add scopes: `openid`, `email`, `profile`

#### Step 3: Create OAuth Credentials
1. Navigate to **APIs & Services** > **Credentials**
2. Click **Create Credentials** > **OAuth 2.0 Client IDs**
3. Choose **Web application**
4. Configure:
   - **Name**: "MCP OpenMetadata OAuth Client"
   - **Authorized origins**: `http://localhost:8000`
   - **Redirect URIs**: `http://localhost:8000/auth/google/callback`
5. Copy Client ID and Client Secret to `.env`

#### Step 4: Test OAuth Flow
1. Start server: `python -m src.main --transport http`
2. Visit: `http://localhost:8000/auth/google/redirect`
3. Complete Google OAuth flow
4. Receive JWT token for API access

---

## 🛠️ Usage Examples

### With AI Assistants

#### Claude Desktop Configuration
Add to your Claude Desktop config:
```json
{
  "mcpServers": {
    "openmetadata": {
      "command": "uv",
      "args": ["run", "python", "-m", "src.main", "--transport", "stdio"],
      "cwd": "/path/to/mcp-server-openmetadata",
      "env": {
        "OPENMETADATA_HOST": "http://localhost:8585"
      }
    }
  }
}
```

### Web API Usage

#### Search for Tables
```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     "http://localhost:8000/tools/execute" \
     -d '{"name": "mcp_openmetadata_search_metadata", "arguments": {"query": "users", "entity_type": "table"}}'
```

#### Get Entity Details
```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     "http://localhost:8000/tools/execute" \
     -d '{"name": "mcp_openmetadata_get_entity_details", "arguments": {"entity_type": "table", "fqn": "sample_data.ecommerce_db.shopify.dim_user"}}'
```

#### Create Glossary Term
```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     "http://localhost:8000/tools/execute" \
     -d '{"name": "mcp_openmetadata_create_glossary_term", "arguments": {"glossary": "Business", "name": "Customer", "description": "Individual or organization that purchases products"}}'
```

### Python Client
```python
import requests

# Authenticate
auth_response = requests.post('http://localhost:8000/auth/token', 
    json={'username': 'admin', 'password': 'password'})
token = auth_response.json()['access_token']

headers = {'Authorization': f'Bearer {token}'}

# Search for entities
search_response = requests.post('http://localhost:8000/tools/execute',
    headers=headers,
    json={
        'name': 'mcp_openmetadata_search_metadata',
        'arguments': {'query': 'customer', 'entity_type': 'table'}
    })

print(search_response.json())
```

### JavaScript/Frontend
```javascript
// OAuth login
const authResponse = await fetch('/auth/google/login');
const { auth_url } = await authResponse.json();
window.location.href = auth_url;

// After OAuth callback, use JWT token
const token = getTokenFromCallback(); // Your implementation

// Make API calls
const toolsResponse = await fetch('/tools', {
    headers: { 'Authorization': `Bearer ${token}` }
});
const tools = await toolsResponse.json();
```

---

## ⚡ Available Make Commands

```bash
# Installation
make install          # Basic installation
make install-all      # Install with all extras (recommended)
make install-web      # Install web + auth features
make install-dev      # Install development dependencies

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
make clean            # Clean build artifacts
```

---

## 🔧 Available Tools (186 Total)

### Core Search & Discovery
- `mcp_openmetadata_search_metadata` - Search across all entities
- `mcp_openmetadata_get_entity_details` - Get detailed entity information
- `mcp_openmetadata_get_entity_lineage` - Explore data lineage

### Glossary Management
- `mcp_openmetadata_create_glossary` - Create business glossaries
- `mcp_openmetadata_create_glossary_term` - Add glossary terms

### Database & Tables
- `database_get_databases` - List all databases
- `database_get_database_schemas` - Get database schemas
- `table_get_tables` - List tables with filtering
- `table_get_table_details` - Detailed table information

### Dashboards & Charts
- `dashboards_get_dashboards` - List dashboards
- `charts_get_charts` - List charts and visualizations

### Pipelines & Services
- `pipelines_get_pipelines` - List data pipelines
- `services_get_services` - List all services

### User & Team Management
- `users_get_users` - List users
- `teams_get_teams` - List teams and roles

### Data Quality & Testing
- `test_cases_get_test_cases` - List test cases
- `test_suites_get_test_suites` - List test suites

*[...and 165+ more tools covering the complete OpenMetadata API]*

---

## 🚀 Deployment

### uv Package Manager (Recommended)
```bash
# Production deployment with all features
make install-all

# Run with validation
make validate && make run-web

# Or with authentication
make run-web-auth
```

### Manual Python Deployment
```bash
# If you can't use uv, fallback to manual setup
pip install -e .
python -m src.main --transport http --host 0.0.0.0 --port 8000
```

### Production Considerations
1. Use HTTPS for all URLs
2. Set strong secrets and API keys  
3. Configure proper CORS origins
4. Enable Sentry monitoring
5. Use domain restrictions for OAuth
6. Set up proper logging and monitoring
7. Run `make validate` before deployment

---

## 📊 Web Dashboard

Access the built-in dashboard at `http://localhost:8000` when running the HTTP server.

Features:
- **Real-time Statistics**: Active connections, API calls, errors
- **Tool Management**: Browse and test all 186 available tools
- **Authentication Status**: Current auth method and user info
- **System Health**: Server status and performance metrics
- **API Documentation**: Interactive tool reference

---

## 🔍 Troubleshooting

### Common Issues

#### "Connection failed to OpenMetadata"
- Verify `OPENMETADATA_HOST_PORT` is correct
- Check OpenMetadata server is running
- Validate authentication credentials

#### "OAuth not configured"
- Ensure `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are set
- Restart server after adding environment variables

#### "redirect_uri_mismatch"
- Verify redirect URI in Google Cloud Console matches exactly
- Check for trailing slashes and protocol (http vs https)

#### "Tool not found" errors
- Run with debug logging: `LOG_LEVEL=DEBUG`
- Check if OpenMetadata server is accessible
- Verify authentication is working

### Debug Mode
```bash
# Enable detailed logging
export LOG_LEVEL=DEBUG
make run-web

# Validate setup first
make validate

# Check what make commands are available
make
```

### Health Checks
```bash
# Check server status
curl http://localhost:8000/health

# Check available tools
curl http://localhost:8000/tools

# Check authentication status
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/stats
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

### Development Setup
```bash
# Install development dependencies
make install-dev

# Install all features for development  
make install-all

# Run validation
make validate

# Format and lint code
make format
make lint

# Run tests
make test
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/yangkyeongmo/mcp-server-openmetadata/issues)
- **Documentation**: This comprehensive guide
- **Security**: Report security issues privately to the maintainers

---

## 🏷️ Version History

- **v2.0.0**: Complete rewrite with enterprise features
  - Multi-transport support (stdio/HTTP/WebSocket)
  - Google OAuth 2.0 integration
  - Web dashboard and monitoring
  - 186 OpenMetadata tools
  - Docker deployment support

- **v1.x**: Initial TypeScript implementation (deprecated)

---

**🎉 You're all set!** This MCP server provides everything you need for robust OpenMetadata integration with AI assistants and web applications.
