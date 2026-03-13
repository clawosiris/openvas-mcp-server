# MCP Installation

## Requirements

- Python 3.11+ (or Docker)
- Access to GVM daemon (gvmd)

## Docker (Recommended)

```bash
docker pull ghcr.io/clawosiris/openvas-mcp-server:latest
```

## Install via pip

```bash
pip install openvas-mcp
```

## Configuration

MCP server receives configuration via environment variables.

### Claude Desktop

Add to `~/.config/claude/config.json`:

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

### Remote GVM Server

```json
{
  "mcpServers": {
    "openvas": {
      "command": "openvas-mcp",
      "env": {
        "GVM_STYLE": "remote",
        "GVM_HOSTNAME": "gvm.example.com",
        "GVM_PORT": "9390",
        "GVM_USERNAME": "admin",
        "GVM_PASSWORD": "secret",
        "GVM_CAFILE": "/path/to/ca.pem"
      }
    }
  }
}
```

### Docker

```json
{
  "mcpServers": {
    "openvas": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-v", "/run/gvmd/gvmd.sock:/run/gvmd/gvmd.sock",
        "-e", "GVM_STYLE=local",
        "-e", "GVM_USERNAME=admin",
        "-e", "GVM_PASSWORD=secret",
        "ghcr.io/clawosiris/openvas-mcp-server:latest"
      ]
    }
  }
}
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GVM_STYLE` | Yes | `local` | Connection style (`local` or `remote`) |
| `GVM_SOCKET_PATH` | For local | `/run/gvmd/gvmd.sock` | Unix socket path |
| `GVM_HOSTNAME` | For remote | - | GVM server hostname |
| `GVM_PORT` | No | `9390` | GVM server port |
| `GVM_USERNAME` | Yes | - | GMP username |
| `GVM_PASSWORD` | Yes | - | GMP password |
| `GVM_CAFILE` | No | - | CA certificate path |
| `GVM_TIMEOUT` | No | `60` | Operation timeout (seconds) |
| `GVM_RETRY_MAX_ATTEMPTS` | No | `3` | Max retry attempts |
