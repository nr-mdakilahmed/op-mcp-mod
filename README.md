[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/yangkyeongmo-mcp-server-openmetadata-badge.png)](https://mseep.ai/app/yangkyeongmo-mcp-server-openmetadata)

# mcp-server-openmetadata

[![smithery badge](https://smithery.ai/badge/@yangkyeongmo/mcp-server-openmetadata)](https://smithery.ai/server/@yangkyeongmo/mcp-server-openmetadata)

A Model Context Protocol (MCP) server implementation for OpenMetadata, enabling seamless integration with MCP clients. This project provides a standardized way to interact with OpenMetadata through the Model Context Protocol.

<a href="https://glama.ai/mcp/servers/lvgl5cmxa6">
  <img width="380" height="200" src="https://glama.ai/mcp/servers/lvgl5cmxa6/badge" alt="Server for OpenMetadata MCP server" />
</a>

## About

This project implements a [Model Context Protocol](https://modelcontextprotocol.io/introduction) server that wraps OpenMetadata's REST API, allowing MCP clients to interact with OpenMetadata in a standardized way.

## Feature Implementation Status

### Core Data Entities (`table`, `database`, `databaseschema`)

| Feature | API Path | Status |
|---------|----------|--------|
| **Tables** | | |
| List Tables | `/api/v1/tables` | ✅ |
| Get Table | `/api/v1/tables/{id}` | ✅ |
| Get Table by Name | `/api/v1/tables/name/{fqn}` | ✅ |
| Create Table | `/api/v1/tables` | ✅ |
| Update Table | `/api/v1/tables/{id}` | ✅ |
| Delete Table | `/api/v1/tables/{id}` | ✅ |
| **Databases** | | |
| List Databases | `/api/v1/databases` | ✅ |
| Get Database | `/api/v1/databases/{id}` | ✅ |
| Get Database by Name | `/api/v1/databases/name/{fqn}` | ✅ |
| Create Database | `/api/v1/databases` | ✅ |
| Update Database | `/api/v1/databases/{id}` | ✅ |
| Delete Database | `/api/v1/databases/{id}` | ✅ |
| **Database Schemas** | | |
| List Database Schemas | `/api/v1/databaseSchemas` | ✅ |
| Get Database Schema | `/api/v1/databaseSchemas/{id}` | ✅ |
| Get Database Schema by Name | `/api/v1/databaseSchemas/name/{fqn}` | ✅ |
| Create Database Schema | `/api/v1/databaseSchemas` | ✅ |
| Update Database Schema | `/api/v1/databaseSchemas/{id}` | ✅ |
| Delete Database Schema | `/api/v1/databaseSchemas/{id}` | ✅ |

### Data Assets (`dashboard`, `chart`, `pipeline`, `topic`, `metric`, `container`)

| Feature | API Path | Status |
|---------|----------|--------|
| **Dashboards** | | |
| List Dashboards | `/api/v1/dashboards` | ✅ |
| Get Dashboard | `/api/v1/dashboards/{id}` | ✅ |
| Get Dashboard by Name | `/api/v1/dashboards/name/{fqn}` | ✅ |
| Create Dashboard | `/api/v1/dashboards` | ✅ |
| Update Dashboard | `/api/v1/dashboards/{id}` | ✅ |
| Delete Dashboard | `/api/v1/dashboards/{id}` | ✅ |
| **Charts** | | |
| List Charts | `/api/v1/charts` | ✅ |
| Get Chart | `/api/v1/charts/{id}` | ✅ |
| Get Chart by Name | `/api/v1/charts/name/{fqn}` | ✅ |
| Create Chart | `/api/v1/charts` | ✅ |
| Update Chart | `/api/v1/charts/{id}` | ✅ |
| Delete Chart | `/api/v1/charts/{id}` | ✅ |
| **Pipelines** | | |
| List Pipelines | `/api/v1/pipelines` | ✅ |
| Get Pipeline | `/api/v1/pipelines/{id}` | ✅ |
| Get Pipeline by Name | `/api/v1/pipelines/name/{fqn}` | ✅ |
| Create Pipeline | `/api/v1/pipelines` | ✅ |
| Update Pipeline | `/api/v1/pipelines/{id}` | ✅ |
| Delete Pipeline | `/api/v1/pipelines/{id}` | ✅ |
| **Topics** | | |
| List Topics | `/api/v1/topics` | ✅ |
| Get Topic | `/api/v1/topics/{id}` | ✅ |
| Get Topic by Name | `/api/v1/topics/name/{fqn}` | ✅ |
| Create Topic | `/api/v1/topics` | ✅ |
| Update Topic | `/api/v1/topics/{id}` | ✅ |
| Delete Topic | `/api/v1/topics/{id}` | ✅ |
| **Metrics** | | |
| List Metrics | `/api/v1/metrics` | ✅ |
| Get Metric | `/api/v1/metrics/{id}` | ✅ |
| Get Metric by Name | `/api/v1/metrics/name/{fqn}` | ✅ |
| Create Metric | `/api/v1/metrics` | ✅ |
| Update Metric | `/api/v1/metrics/{id}` | ✅ |
| Delete Metric | `/api/v1/metrics/{id}` | ✅ |
| **Containers** | | |
| List Containers | `/api/v1/containers` | ✅ |
| Get Container | `/api/v1/containers/{id}` | ✅ |
| Get Container by Name | `/api/v1/containers/name/{fqn}` | ✅ |
| Create Container | `/api/v1/containers` | ✅ |
| Update Container | `/api/v1/containers/{id}` | ✅ |
| Delete Container | `/api/v1/containers/{id}` | ✅ |

### Users & Teams (`user`, `team`)

| Feature | API Path | Status |
|---------|----------|--------|
| **Teams** | | |
| List Teams | `/api/v1/teams` | ✅ |
| Get Team | `/api/v1/teams/{id}` | ✅ |
| Get Team by Name | `/api/v1/teams/name/{name}` | ✅ |
| Create Team | `/api/v1/teams` | ✅ |
| Update Team | `/api/v1/teams/{id}` | ✅ |
| Delete Team | `/api/v1/teams/{id}` | ✅ |
| **Users** | | |
| List Users | `/api/v1/users` | ✅ |
| Get User | `/api/v1/users/{id}` | ✅ |
| Get User by Name | `/api/v1/users/name/{name}` | ✅ |
| Create User | `/api/v1/users` | ✅ |
| Update User | `/api/v1/users/{id}` | ✅ |
| Delete User | `/api/v1/users/{id}` | ✅ |

### Governance & Classification (`classification`, `glossary`)

| Feature | API Path | Status |
|---------|----------|--------|
| **Classifications** | | |
| List Classifications | `/api/v1/classifications` | ✅ |
| Get Classification | `/api/v1/classifications/{id}` | ✅ |
| Get Classification by Name | `/api/v1/classifications/name/{name}` | ✅ |
| Create Classification | `/api/v1/classifications` | ✅ |
| Update Classification | `/api/v1/classifications/{id}` | ✅ |
| Delete Classification | `/api/v1/classifications/{id}` | ✅ |
| **Glossaries** | | |
| List Glossaries | `/api/v1/glossaries` | ✅ |
| Get Glossary | `/api/v1/glossaries/{id}` | ✅ |
| Get Glossary by Name | `/api/v1/glossaries/name/{name}` | ✅ |
| Create Glossary | `/api/v1/glossaries` | ✅ |
| Update Glossary | `/api/v1/glossaries/{id}` | ✅ |
| Delete Glossary | `/api/v1/glossaries/{id}` | ✅ |
| List Glossary Terms | `/api/v1/glossaryTerms` | ✅ |
| Get Glossary Term | `/api/v1/glossaryTerms/{id}` | ✅ |

### System & Operations (`bot`)

| Feature | API Path | Status |
|---------|----------|--------|
| **Bots** | | |
| List Bots | `/api/v1/bots` | ✅ |
| Get Bot | `/api/v1/bots/{id}` | ✅ |
| Get Bot by Name | `/api/v1/bots/name/{name}` | ✅ |
| Create Bot | `/api/v1/bots` | ✅ |
| Update Bot | `/api/v1/bots/{id}` | ✅ |
| Delete Bot | `/api/v1/bots/{id}` | ✅ |

### Analytics & Monitoring (`lineage`, `usage`)

| Feature | API Path | Status |
|---------|----------|--------|
| **Lineage** | | |
| Get Lineage by Entity ID | `/api/v1/lineage/{entity}/{id}` | ✅ |
| Get Lineage by Entity Name | `/api/v1/lineage/{entity}/name/{fqn}` | ✅ |
| Add/Update Lineage | `/api/v1/lineage` | ✅ |
| Delete Lineage | `/api/v1/lineage` | ✅ |
| **Usage** | | |
| Get Entity Usage | `/api/v1/usage/{entity}/{id}` | ✅ |
| Add Usage Data | `/api/v1/usage` | ✅ |
| Get Usage Summary | `/api/v1/usage/summary` | ✅ |

### Not Yet Implemented

| Feature | API Path | Status |
|---------|----------|--------|
| **Search & Discovery** | | |
| Search Query | `/api/v1/search/query` | ❌ |
| Search Suggest | `/api/v1/search/suggest` | ❌ |
| **API Management** | | |
| API Collections | `/api/v1/apiCollections` | ❌ |
| API Endpoints | `/api/v1/apiEndpoints` | ❌ |
| **Data Quality** | | |
| Test Cases | `/api/v1/testCases` | ❌ |
| Test Definitions | `/api/v1/testDefinitions` | ❌ |
| Test Suites | `/api/v1/testSuites` | ❌ |
| **Other Assets** | | |
| Reports | `/api/v1/reports` | ❌ |
| ML Models | `/api/v1/mlmodels` | ❌ |
| **Services & Infrastructure** | | |
| Services | `/api/v1/services` | ❌ |
| Events | `/api/v1/events` | ❌ |
| Apps | `/api/v1/apps` | ❌ |
| **Domain Management** | | |
| Domains | `/api/v1/domains` | ❌ |
| Data Products | `/api/v1/dataProducts` | ❌ |

## API Groups

The server supports modular API group selection via command line arguments. Available API groups:

### Core Data Entities
- `table` - Table entity management
- `database` - Database entity management  
- `databaseschema` - Database schema management

### Data Assets
- `dashboard` - Dashboard entity management
- `chart` - Chart entity management
- `pipeline` - Pipeline entity management
- `topic` - Topic entity management
- `metric` - Metric entity management
- `container` - Container entity management

### Users & Teams
- `user` - User entity management
- `team` - Team entity management

### Governance & Classification
- `classification` - Classification entity management
- `glossary` - Glossary and glossary terms management

### System & Operations
- `bot` - Bot entity management

### Analytics & Monitoring
- `lineage` - Data lineage management
- `usage` - Usage analytics management

You can specify which API groups to enable when running the server:

```bash
# Enable only core entities
python -m src.main --apis table,database,databaseschema

# Enable all available APIs
python -m src.main --apis table,database,databaseschema,dashboard,chart,pipeline,topic,metric,container,user,team,classification,glossary,bot,lineage,usage

# Use default selection (core entities + common assets)
python -m src.main
```

## Setup

### Installing via Smithery

To install OpenMetadata MCP Server for Claude Desktop automatically via [Smithery](https://smithery.ai/server/@yangkyeongmo/mcp-server-openmetadata):

```bash
npx -y @smithery/cli install @yangkyeongmo/mcp-server-openmetadata --client claude
```

### Environment Variables

Set one of the following authentication methods:

#### Token Authentication (Recommended)
```
OPENMETADATA_HOST=<your-openmetadata-host>
OPENMETADATA_JWT_TOKEN=<your-jwt-token>
```

#### Basic Authentication
```
OPENMETADATA_HOST=<your-openmetadata-host>
OPENMETADATA_USERNAME=<your-username>
OPENMETADATA_PASSWORD=<your-password>
```

### Usage with Claude Desktop

Add to your `claude_desktop_config.json` using one of the following authentication methods:

#### Token Authentication (Recommended)
```json
{
  "mcpServers": {
    "mcp-server-openmetadata": {
      "command": "uvx",
      "args": ["mcp-server-openmetadata"],
      "env": {
        "OPENMETADATA_HOST": "https://your-openmetadata-host",
        "OPENMETADATA_JWT_TOKEN": "your-jwt-token"
      }
    }
  }
}
```

#### Basic Authentication
```json
{
  "mcpServers": {
    "mcp-server-openmetadata": {
      "command": "uvx",
      "args": ["mcp-server-openmetadata"],
      "env": {
        "OPENMETADATA_HOST": "https://your-openmetadata-host",
        "OPENMETADATA_USERNAME": "your-username",
        "OPENMETADATA_PASSWORD": "your-password"
      }
    }
  }
}
```

Alternative configuration using `uv`:

#### Token Authentication (Recommended)
```json
{
  "mcpServers": {
    "mcp-server-openmetadata": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/mcp-server-openmetadata",
        "run",
        "mcp-server-openmetadata"
      ],
      "env": {
        "OPENMETADATA_HOST": "https://your-openmetadata-host",
        "OPENMETADATA_JWT_TOKEN": "your-jwt-token"
      }
    }
  }
}
```

#### Basic Authentication
```json
{
  "mcpServers": {
    "mcp-server-openmetadata": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/mcp-server-openmetadata",
        "run",
        "mcp-server-openmetadata"
      ],
      "env": {
        "OPENMETADATA_HOST": "https://your-openmetadata-host",
        "OPENMETADATA_USERNAME": "your-username",
        "OPENMETADATA_PASSWORD": "your-password"
      }
    }
  }
}
```

Replace `/path/to/mcp-server-openmetadata` with the actual path where you've cloned the repository.

### Manual Execution

You can also run the server manually:
```bash
python src/server.py
```

Options:
- `--port`: Port to listen on for SSE (default: 8000)
- `--transport`: Transport type (stdio/sse, default: stdio)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License