# Configuration Reference

**Version:** 2025.03  
**Status:** Design

---

## Overview

OpenVAS MCP supports three connection styles to gvmd:

| Style | Use Case | Transport |
|-------|----------|-----------|
| **Local** | gvmd on same machine | Unix socket |
| **Remote TLS** | gvmd on remote server | TLS over TCP |
| **Remote SSH** | gvmd via SSH tunnel | SSH + Unix socket |

---

## Configuration Classes

### Base Configuration

```python
from dataclasses import dataclass, field
from typing import Optional, Literal
from enum import Enum

class ConnectionStyle(str, Enum):
    LOCAL = "local"
    REMOTE_TLS = "remote_tls"
    REMOTE_SSH = "remote_ssh"


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
    
    # Remote TLS settings
    tls_hostname: str = "127.0.0.1"
    tls_port: int = 9390
    tls_certfile: Optional[str] = None      # Client certificate
    tls_cafile: Optional[str] = None        # CA certificate  
    tls_keyfile: Optional[str] = None       # Client private key
    tls_key_password: Optional[str] = None  # Key password (if encrypted)
    
    # Remote SSH settings
    ssh_hostname: str = "127.0.0.1"
    ssh_port: int = 22
    ssh_username: str = "gmp"
    ssh_password: str = ""
    ssh_known_hosts_file: Optional[str] = None
    ssh_auto_accept_host: bool = False
    
    # Common settings
    timeout: int = 60                        # Connection/operation timeout
    
    # Retry settings
    retry_max_attempts: int = 3
    retry_initial_delay: float = 1.0
    retry_max_delay: float = 30.0
    retry_exponential_base: float = 2.0
    
    # Idle connection management
    idle_timeout: int = 300                  # Close idle connections after 5 min
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

## Style: Remote TLS

For gvmd on a remote server with TLS encryption.

### Required Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `style` | enum | - | Must be `remote_tls` |
| `tls_hostname` | str | - | Remote server hostname/IP |
| `gmp_username` | str | - | GMP authentication username |
| `gmp_password` | str | - | GMP authentication password |

### Optional Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `tls_port` | int | `9390` | GVM TLS port |
| `tls_certfile` | str | `None` | Path to client certificate (for mTLS) |
| `tls_cafile` | str | `None` | Path to CA certificate |
| `tls_keyfile` | str | `None` | Path to client private key |
| `tls_key_password` | str | `None` | Password for encrypted key |
| `timeout` | int | `60` | Operation timeout in seconds |

### Environment Variables

```bash
# Required
GVM_STYLE=remote_tls
GVM_TLS_HOSTNAME=gvm.example.com
GVM_USERNAME=admin
GVM_PASSWORD=secret

# Optional
GVM_TLS_PORT=9390
GVM_TLS_CERTFILE=/path/to/client.pem
GVM_TLS_CAFILE=/path/to/ca.pem
GVM_TLS_KEYFILE=/path/to/client.key
GVM_TLS_KEY_PASSWORD=keypassword
GVM_TIMEOUT=60
```

### Config File (TOML)

```toml
[connection]
style = "remote_tls"
timeout = 60

[tls]
hostname = "gvm.example.com"
port = 9390
certfile = "/path/to/client.pem"
cafile = "/path/to/ca.pem"
keyfile = "/path/to/client.key"
# key_password via GVM_TLS_KEY_PASSWORD env var

[auth]
username = "admin"
# password via GVM_PASSWORD env var
```

---

## Style: Remote SSH

For gvmd accessed via SSH tunnel (connects to socket on remote machine).

### Required Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `style` | enum | - | Must be `remote_ssh` |
| `ssh_hostname` | str | - | SSH server hostname/IP |
| `gmp_username` | str | - | GMP authentication username |
| `gmp_password` | str | - | GMP authentication password |

### Optional Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `ssh_port` | int | `22` | SSH port |
| `ssh_username` | str | `gmp` | SSH username |
| `ssh_password` | str | `""` | SSH password (or use key) |
| `ssh_known_hosts_file` | str | `None` | Path to known_hosts file |
| `ssh_auto_accept_host` | bool | `False` | Auto-accept unknown hosts (⚠️ security risk) |
| `timeout` | int | `60` | Operation timeout in seconds |

### Environment Variables

```bash
# Required
GVM_STYLE=remote_ssh
GVM_SSH_HOSTNAME=gvm.example.com
GVM_USERNAME=admin
GVM_PASSWORD=secret

# Optional
GVM_SSH_PORT=22
GVM_SSH_USERNAME=gmp
GVM_SSH_PASSWORD=sshpassword
GVM_SSH_KNOWN_HOSTS=/path/to/known_hosts
GVM_SSH_AUTO_ACCEPT_HOST=false
GVM_TIMEOUT=60
```

### Config File (TOML)

```toml
[connection]
style = "remote_ssh"
timeout = 60

[ssh]
hostname = "gvm.example.com"
port = 22
username = "gmp"
known_hosts_file = "/path/to/known_hosts"
auto_accept_host = false
# password via GVM_SSH_PASSWORD env var

[auth]
username = "admin"
# password via GVM_PASSWORD env var
```

---

## Retry Configuration

All styles support retry configuration:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `retry_max_attempts` | int | `3` | Maximum retry attempts |
| `retry_initial_delay` | float | `1.0` | Initial delay in seconds |
| `retry_max_delay` | float | `30.0` | Maximum delay between retries |
| `retry_exponential_base` | float | `2.0` | Exponential backoff multiplier |
| `idle_timeout` | int | `300` | Close idle connections (seconds) |

### Environment Variables

```bash
GVM_RETRY_MAX_ATTEMPTS=3
GVM_RETRY_INITIAL_DELAY=1.0
GVM_RETRY_MAX_DELAY=30.0
GVM_IDLE_TIMEOUT=300
```

### Config File

```toml
[retry]
max_attempts = 3
initial_delay = 1.0
max_delay = 30.0
exponential_base = 2.0
idle_timeout = 300
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
idle_timeout = 300
```

```bash
export GVM_PASSWORD=admin
```

### Production Remote TLS

```toml
# /etc/openvas-mcp/config.toml
[connection]
style = "remote_tls"
timeout = 120

[tls]
hostname = "gvm.prod.example.com"
port = 9390
cafile = "/etc/openvas-mcp/ca.pem"
certfile = "/etc/openvas-mcp/client.pem"
keyfile = "/etc/openvas-mcp/client.key"

[auth]
username = "mcp-service"

[retry]
max_attempts = 5
initial_delay = 2.0
max_delay = 60.0
idle_timeout = 600
```

### SSH Tunnel (Bastion Host)

```toml
[connection]
style = "remote_ssh"
timeout = 120

[ssh]
hostname = "bastion.example.com"
port = 22
username = "gvm-tunnel"
known_hosts_file = "~/.ssh/known_hosts"

[auth]
username = "admin"

[retry]
max_attempts = 3
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

Connection style [local/remote_tls/remote_ssh]: remote_tls

=== TLS Settings ===
GVM hostname: gvm.example.com
GVM port [9390]: 
CA certificate path (optional): /path/to/ca.pem
Client certificate path (optional): 
Verify SSL? [Y/n]: 

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
| `GVM_TLS_HOSTNAME` | TLS | Yes* | - |
| `GVM_TLS_PORT` | TLS | No | `9390` |
| `GVM_TLS_CERTFILE` | TLS | No | - |
| `GVM_TLS_CAFILE` | TLS | No | - |
| `GVM_TLS_KEYFILE` | TLS | No | - |
| `GVM_TLS_KEY_PASSWORD` | TLS | No | - |
| `GVM_SSH_HOSTNAME` | SSH | Yes* | - |
| `GVM_SSH_PORT` | SSH | No | `22` |
| `GVM_SSH_USERNAME` | SSH | No | `gmp` |
| `GVM_SSH_PASSWORD` | SSH | No | - |
| `GVM_SSH_KNOWN_HOSTS` | SSH | No | - |
| `GVM_SSH_AUTO_ACCEPT_HOST` | SSH | No | `false` |
| `GVM_RETRY_MAX_ATTEMPTS` | All | No | `3` |
| `GVM_RETRY_INITIAL_DELAY` | All | No | `1.0` |
| `GVM_RETRY_MAX_DELAY` | All | No | `30.0` |
| `GVM_IDLE_TIMEOUT` | All | No | `300` |

*Required when using that style.
