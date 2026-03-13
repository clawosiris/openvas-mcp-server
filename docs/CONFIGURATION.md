# Configuration Reference

**Version:** 2025.03  
**Status:** Design

---

## Overview

OpenVAS MCP supports two connection styles to gvmd:

| Style | Use Case | Transport |
|-------|----------|-----------|
| **Local** | gvmd on same machine | Unix socket |
| **Remote** | gvmd on remote server | TLS over TCP |

---

## Configuration Class

```python
from dataclasses import dataclass
from typing import Optional, Literal
from enum import Enum

class ConnectionStyle(str, Enum):
    LOCAL = "local"
    REMOTE = "remote"


@dataclass
class GvmConfig:
    """Complete GVM configuration."""
    
    # Connection style
    style: ConnectionStyle = ConnectionStyle.LOCAL
    
    # GMP Authentication (required for all styles)
    gmp_username: str = ""
    gmp_password: str = ""
    
    # Local (Unix Socket) settings
    socket_path: str = "/run/gvmd/gvmd.sock"
    
    # Remote (TLS) settings
    hostname: str = "127.0.0.1"
    port: int = 9390
    certfile: Optional[str] = None      # Client certificate
    cafile: Optional[str] = None        # CA certificate  
    keyfile: Optional[str] = None       # Client private key
    key_password: Optional[str] = None  # Key password (if encrypted)
    
    # Common settings
    timeout: int = 60                    # Connection/operation timeout
    
    # Retry settings (triggered on error)
    retry_max_attempts: int = 3
```

---

## Style: Local (Unix Socket)

For gvmd running on the same machine.

### Required Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `style` | enum | `local` | Connection style |
| `gmp_username` | str | - | GMP authentication username |
| `gmp_password` | str | - | GMP authentication password |

### Optional Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `socket_path` | str | `/run/gvmd/gvmd.sock` | Path to gvmd Unix socket |
| `timeout` | int | `60` | Operation timeout in seconds |

### Environment Variables

```bash
# Required
GVM_STYLE=local
GVM_USERNAME=admin
GVM_PASSWORD=secret

# Optional
GVM_SOCKET_PATH=/run/gvmd/gvmd.sock
GVM_TIMEOUT=60
```

### Config File (TOML)

```toml
[connection]
style = "local"
socket_path = "/run/gvmd/gvmd.sock"
timeout = 60

[auth]
username = "admin"
# password via GVM_PASSWORD env var
```

---

## Style: Remote (TLS)

For gvmd on a remote server with TLS encryption.

### Required Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `style` | enum | - | Must be `remote` |
| `hostname` | str | - | Remote server hostname/IP |
| `gmp_username` | str | - | GMP authentication username |
| `gmp_password` | str | - | GMP authentication password |

### Optional Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `port` | int | `9390` | GVM TLS port |
| `certfile` | str | `None` | Path to client certificate (for mTLS) |
| `cafile` | str | `None` | Path to CA certificate |
| `keyfile` | str | `None` | Path to client private key |
| `key_password` | str | `None` | Password for encrypted key |
| `timeout` | int | `60` | Operation timeout in seconds |

### Environment Variables

```bash
# Required
GVM_STYLE=remote
GVM_HOSTNAME=gvm.example.com
GVM_USERNAME=admin
GVM_PASSWORD=secret

# Optional
GVM_PORT=9390
GVM_CERTFILE=/path/to/client.pem
GVM_CAFILE=/path/to/ca.pem
GVM_KEYFILE=/path/to/client.key
GVM_KEY_PASSWORD=keypassword
GVM_TIMEOUT=60
```

### Config File (TOML)

```toml
[connection]
style = "remote"
hostname = "gvm.example.com"
port = 9390
timeout = 60

[tls]
certfile = "/path/to/client.pem"
cafile = "/path/to/ca.pem"
keyfile = "/path/to/client.key"
# key_password via GVM_KEY_PASSWORD env var

[auth]
username = "admin"
# password via GVM_PASSWORD env var
```

---

## Retry Configuration

Retry is triggered **on error only** (connection failures, timeouts, etc.).

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `retry_max_attempts` | int | `3` | Maximum retry attempts |

### Environment Variables

```bash
GVM_RETRY_MAX_ATTEMPTS=3
```

### Config File

```toml
[retry]
max_attempts = 3
```

---

## Complete Example Configurations

### Local Development

```toml
# ~/.config/openvas-mcp/config.toml
[connection]
style = "local"
socket_path = "/run/gvmd/gvmd.sock"
timeout = 60

[auth]
username = "admin"

[retry]
max_attempts = 3
```

```bash
export GVM_PASSWORD=admin
```

### Production Remote

```toml
# /etc/openvas-mcp/config.toml
[connection]
style = "remote"
hostname = "gvm.prod.example.com"
port = 9390
timeout = 120

[tls]
cafile = "/etc/openvas-mcp/ca.pem"
certfile = "/etc/openvas-mcp/client.pem"
keyfile = "/etc/openvas-mcp/client.key"

[auth]
username = "mcp-service"

[retry]
max_attempts = 5
```

---

## MCP Installation Configuration

MCP servers receive configuration via environment variables at installation:

```json
{
  "mcpServers": {
    "openvas": {
      "command": "openvas-mcp",
      "env": {
        "GVM_STYLE": "local",
        "GVM_SOCKET_PATH": "/run/gvmd/gvmd.sock",
        "GVM_USERNAME": "admin",
        "GVM_PASSWORD": "secret",
        "GVM_TIMEOUT": "60",
        "GVM_RETRY_MAX_ATTEMPTS": "3"
      }
    }
  }
}
```

---

## CLI Interactive Configuration

CLI prompts for configuration on first run:

```
$ openvas configure

OpenVAS MCP - Connection Setup

Connection style [local/remote]: remote

=== Remote Settings ===
GVM hostname: gvm.example.com
GVM port [9390]: 
CA certificate path (optional): /path/to/ca.pem
Client certificate path (optional): 

=== Authentication ===
GMP username [admin]: 
GMP password: ****

=== Timeouts ===
Operation timeout (seconds) [60]: 120

Save configuration? [Y/n]: 
Configuration saved to ~/.config/openvas-mcp/config.toml
```

---

## Environment Variable Reference

| Variable | Style | Required | Default |
|----------|-------|----------|---------|
| `GVM_STYLE` | All | Yes | `local` |
| `GVM_USERNAME` | All | Yes | - |
| `GVM_PASSWORD` | All | Yes | - |
| `GVM_TIMEOUT` | All | No | `60` |
| `GVM_SOCKET_PATH` | Local | No | `/run/gvmd/gvmd.sock` |
| `GVM_HOSTNAME` | Remote | Yes* | - |
| `GVM_PORT` | Remote | No | `9390` |
| `GVM_CERTFILE` | Remote | No | - |
| `GVM_CAFILE` | Remote | No | - |
| `GVM_KEYFILE` | Remote | No | - |
| `GVM_KEY_PASSWORD` | Remote | No | - |
| `GVM_RETRY_MAX_ATTEMPTS` | All | No | `3` |

*Required when using that style.

---

## Future: SSH Support

SSH tunnel support (`remote_ssh`) is planned for a future release.
