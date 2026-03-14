# OpenVAS MCP Server

MCP server and CLI for Greenbone Vulnerability Management (GVM/OpenVAS).

[![CI](https://github.com/clawosiris/openvas-mcp-server/actions/workflows/ci.yml/badge.svg)](https://github.com/clawosiris/openvas-mcp-server/actions/workflows/ci.yml)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

---

## Quick Start

### Prerequisites

- [Greenbone Community Edition](https://greenbone.github.io/docs/latest/) containers installed and running

### 1. Add OpenVAS to Your Greenbone Stack

```bash
# Clone this repository
git clone https://github.com/clawosiris/openvas-mcp-server.git

# Copy the override file to your Greenbone CE directory
cp openvas-mcp-server/docker-compose.override.yml /path/to/greenbone-community-container/

# Start the services you need
cd /path/to/greenbone-community-container
docker compose up -d openvas-mcp              # MCP server only
docker compose up -d openvas-cli              # CLI only
docker compose up -d openvas-mcp openvas-cli  # Both
```

### 2. Configure Your MCP Client

Add to Claude Desktop or Claude Code configuration:

```json
{
  "mcpServers": {
    "openvas": {
      "url": "http://localhost:8080/mcp"
    }
  }
}
```

### 3. Set Up the CLI (Optional)

```bash
# Add alias to your shell (zsh)
echo 'alias openvas="docker exec -it greenbone-community-edition-openvas-cli-1 openvas"' >> ~/.zshrc
source ~/.zshrc

# Test
openvas system test
```

---

## Documentation

### CLI

- [Installation](docs/cli/installation.md)
- [Usage](docs/cli/usage.md)

### MCP

- [Installation](docs/mcp/installation.md)
- [Usage](docs/mcp/usage.md)

### Architecture

- [Architecture Overview](docs/ARCHITECTURE.md)
- [Implementation Status](docs/IMPLEMENTATION_STATUS.md)

---

## Features

- **MCP Server**: AI agent integration via Model Context Protocol
- **CLI**: Command-line interface for human operators
- **Full GVM Coverage**: Targets, scans, reports, vulnerabilities, compliance, and more
- **Fully Dockerized**: Separate MCP and CLI containers, runs inside the Greenbone Community Container stack
- **Two Connection Modes**: Local (Unix socket) and remote (TLS)
- **Retry on Error**: Automatic reconnection with retry

---

## Requirements

- Docker and Docker Compose
- Greenbone Community Edition containers

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio`, `sse`, or `streamable-http` |
| `GVM_STYLE` | `local` | Connection style: `local` or `remote` |
| `GVM_SOCKET_PATH` | `/run/gvmd/gvmd.sock` | Unix socket path |
| `GVM_HOSTNAME` | `127.0.0.1` | Remote GVM hostname |
| `GVM_PORT` | `9390` | Remote GVM port |
| `GVM_USERNAME` | - | GMP username (required) |
| `GVM_PASSWORD` | - | GMP password (required) |
| `GVM_TIMEOUT` | `60` | Operation timeout (seconds) |
| `GVM_RETRY_MAX_ATTEMPTS` | `3` | Max retry attempts |

---

## Development

```bash
# Clone repository
git clone https://github.com/clawosiris/openvas-mcp-server.git
cd openvas-mcp-server

# Install dependencies
poetry install

# Run tests
poetry run pytest

# Run linting
poetry run ruff check src tests
poetry run mypy src

# Run CLI
poetry run openvas --help

# Run MCP server
poetry run openvas-mcp
```

---

## License

AGPL-3.0 License - see [LICENSE](LICENSE) for details.
