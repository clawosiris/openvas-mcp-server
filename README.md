# OpenVAS MCP Server

MCP server and CLI for Greenbone Vulnerability Management (GVM/OpenVAS).

[![CI](https://github.com/clawosiris/openvas-mcp-server/actions/workflows/ci.yml/badge.svg)](https://github.com/clawosiris/openvas-mcp-server/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Quick Install

### CLI

```bash
pip install openvas-mcp

# Configure
openvas configure

# Test connection
openvas test
```

### MCP Server

```bash
# Docker
docker pull ghcr.io/clawosiris/openvas-mcp-server:latest

# Or install directly
pip install openvas-mcp
```

**MCP Client Configuration (Claude Desktop):**

```json
{
  "mcpServers": {
    "openvas": {
      "command": "openvas-mcp",
      "env": {
        "GVM_STYLE": "local",
        "GVM_SOCKET_PATH": "/run/gvmd/gvmd.sock",
        "GVM_USERNAME": "admin",
        "GVM_PASSWORD": "secret"
      }
    }
  }
}
```

---

## Documentation

### CLI

- [Installation](docs/cli/installation.md)
- [Usage](docs/cli/usage.md)
- [Development](docs/cli/development.md)

### MCP

- [Installation](docs/mcp/installation.md)
- [Usage](docs/mcp/usage.md)
- [Development](docs/mcp/development.md)

### Architecture

- [Architecture Overview](docs/ARCHITECTURE.md)
- [Implementation Status](docs/IMPLEMENTATION_STATUS.md)

---

## Features

- **MCP Server**: AI agent integration via Model Context Protocol
- **CLI**: Command-line interface for human operators
- **Full GVM Coverage**: Targets, scans, reports, vulnerabilities, compliance, and more
- **Two Connection Modes**: Local (Unix socket) and remote (TLS)
- **Retry on Error**: Automatic reconnection with retry

---

## Requirements

- Python 3.11+
- GVM/OpenVAS (gvmd daemon)
- Access to gvmd via socket or TLS

---

## Configuration

### Environment Variables

```bash
# Connection style
GVM_STYLE=local          # or 'remote'

# Local (socket)
GVM_SOCKET_PATH=/run/gvmd/gvmd.sock

# Remote (TLS)
GVM_HOSTNAME=gvm.example.com
GVM_PORT=9390
GVM_CAFILE=/path/to/ca.pem       # optional

# Authentication
GVM_USERNAME=admin
GVM_PASSWORD=secret

# Common
GVM_TIMEOUT=60
GVM_RETRY_MAX_ATTEMPTS=3
```

### Config File (CLI)

```toml
# ~/.config/openvas-mcp/config.toml
[connection]
style = "local"
socket_path = "/run/gvmd/gvmd.sock"

[auth]
username = "admin"
# password via GVM_PASSWORD env var
```

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

MIT License - see [LICENSE](LICENSE) for details.
