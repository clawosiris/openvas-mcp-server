# MCP Installation

## Prerequisites

- [Greenbone Community Edition](https://greenbone.github.io/docs/latest/) containers installed and running
- Docker and Docker Compose

## Setup

### 1. Copy the Docker Compose Override

Copy the override file from this repository into your Greenbone Community Edition directory:

```bash
cp docker-compose.override.yml /path/to/greenbone-community-container/
```

### 2. Set Credentials (Optional)

If your GVM credentials differ from the default (`admin`/`admin`), create or edit a `.env` file in your Greenbone CE directory:

```env
GVM_USERNAME=admin
GVM_PASSWORD=your-password-here
```

### 3. Start the MCP Server

```bash
cd /path/to/greenbone-community-container
docker compose up -d openvas-mcp
```

The MCP server will start alongside the Greenbone services.

### 4. Verify

```bash
# Check the container is running
docker compose ps openvas-mcp

# Test GVM connectivity via CLI (requires openvas-cli container)
docker exec greenbone-community-edition-openvas-cli-1 openvas system test
```

## MCP Client Configuration

### Streamable HTTP (Recommended)

Add to your MCP client configuration (Claude Desktop, Claude Code, etc.):

```json
{
  "mcpServers": {
    "openvas": {
      "url": "http://localhost:8080/mcp"
    }
  }
}
```

### stdio via Docker

If your MCP client only supports stdio transport:

```json
{
  "mcpServers": {
    "openvas": {
      "command": "docker",
      "args": [
        "exec", "-i",
        "greenbone-community-edition-openvas-mcp-1",
        "openvas-mcp"
      ]
    }
  }
}
```

> **Note:** The container runs with `MCP_TRANSPORT=streamable-http` by default. The `docker exec` approach starts a separate stdio process inside the same container.

## Docker Image

The MCP server runs in its own container (`ghcr.io/clawosiris/openvas-mcp-server`), separate from the CLI. Start only the services you need:

```bash
docker compose up -d openvas-mcp              # MCP server only
docker compose up -d openvas-cli              # CLI only
docker compose up -d openvas-mcp openvas-cli  # Both
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MCP_TRANSPORT` | No | `stdio` | Transport mode: `stdio`, `sse`, or `streamable-http` |
| `GVM_STYLE` | Yes | `local` | Connection style: `local` or `remote` |
| `GVM_SOCKET_PATH` | For local | `/run/gvmd/gvmd.sock` | Unix socket path |
| `GVM_HOSTNAME` | For remote | - | GVM server hostname |
| `GVM_PORT` | No | `9390` | GVM server port |
| `GVM_USERNAME` | Yes | - | GMP username |
| `GVM_PASSWORD` | Yes | - | GMP password |
| `GVM_TIMEOUT` | No | `60` | Operation timeout (seconds) |
| `GVM_RETRY_MAX_ATTEMPTS` | No | `3` | Max retry attempts |
| `FASTMCP_HOST` | No | `127.0.0.1` | HTTP server bind address |
| `FASTMCP_PORT` | No | `8000` | HTTP server port |

## Troubleshooting

**Port conflict:** If port 8080 is already in use, change the port mapping in `docker-compose.override.yml`:

```yaml
ports:
  - "127.0.0.1:9090:8000"  # change 9090 to any available port
```

**Container name differs:** If your Greenbone CE project has a custom name, find the actual container name with:

```bash
docker compose ps openvas-mcp
```
