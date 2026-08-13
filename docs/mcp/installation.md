# MCP Installation

## Prerequisites

- [Greenbone Community Edition](https://greenbone.github.io/docs/latest/) containers installed and running
- Docker and Docker Compose

## Setup

### 1. Add the Docker Compose Override

Create a `docker-compose.override.yml` in your Greenbone Community Edition directory with the MCP service:

```yaml
services:
  openvas-mcp:
    image: ghcr.io/clawosiris/openvas-mcp-server:latest
    restart: on-failure
    ports:
      - "127.0.0.1:8080:8000"
    environment:
      MCP_TRANSPORT: streamable-http
      GVM_STYLE: local
      GVM_SOCKET_PATH: /run/gvmd/gvmd.sock
      GVM_USERNAME: ${GVM_USERNAME:?Set GVM_USERNAME in .env}
      GVM_PASSWORD: ${GVM_PASSWORD:?Set GVM_PASSWORD in .env}
      GVM_TIMEOUT: "60"
      FASTMCP_HOST: "0.0.0.0"
      FASTMCP_PORT: "8000"
    volumes:
      - gvmd_socket_vol:/run/gvmd
    depends_on:
      gvmd:
        condition: service_started
```

Or copy the full override file (includes both MCP and CLI services) from this repository:

```bash
cp docker-compose.override.yml /path/to/greenbone-community-container/
```

### 2. Set Credentials

Create a `.env` file in your Greenbone CE directory with your GVM credentials:

```env
GVM_USERNAME=<your-username>
GVM_PASSWORD=<your-password>
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
