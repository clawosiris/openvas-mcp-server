# OpenVAS MCP Server — Architecture

**Version:** 2025.03  
**Status:** Design Phase

---

## Overview

This document defines the clean architecture for the OpenVAS MCP Server, providing both MCP (Model Context Protocol) and CLI interfaces to Greenbone Vulnerability Management.

---

## Project Structure

```
openvas_mcp/
├── __init__.py
├── infrastructure/
│   ├── __init__.py
│   ├── config.py              # Configuration models
│   ├── client/
│   │   ├── __init__.py
│   │   ├── base.py            # Abstract GvmClient
│   │   ├── socket_client.py   # LocalSocketClient implementation
│   │   └── remote_client.py   # RemoteClient (TLS) implementation
│   └── factory.py             # Client factory
│
├── services/
│   ├── __init__.py
│   ├── targets/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   └── service.py
│   ├── scans/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   └── service.py
│   └── ... (other domain services)
│
├── presentation/
│   ├── __init__.py
│   ├── mcp/
│   │   ├── __init__.py
│   │   ├── server.py          # MCP server entry point
│   │   ├── config.py          # MCP-specific config (from params)
│   │   └── toolsets/
│   │       └── ...
│   └── cli/
│       ├── __init__.py
│       ├── main.py            # CLI entry point
│       ├── config.py          # CLI config (interactive prompt)
│       └── commands/
│           └── ...
│
├── errors.py
└── utils/
    └── ...
```

---

## Client Abstraction

### Class Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│                    GvmClient (Abstract)                     │
│  ─────────────────────────────────────────────────────────  │
│  + execute(operation) -> T                                  │
│  + disconnect() -> None                                     │
│  + is_connected() -> bool                                   │
│  # _connect() -> None (abstract)                            │
│  # _create_connection() -> GvmConnection (abstract)         │
└─────────────────────────┬───────────────────────────────────┘
                          │
          ┌───────────────┴───────────────┐
          │                               │
          ▼                               ▼
┌─────────────────────┐       ┌─────────────────────┐
│  LocalSocketClient  │       │    RemoteClient     │
│  ─────────────────  │       │  ─────────────────  │
│  Unix socket conn   │       │  TLS connection     │
│  No SSL context     │       │  Certificate mgmt   │
│  Local gvmd only    │       │  Remote gvmd        │
└─────────────────────┘       └─────────────────────┘
```

### Abstract Base Client

```python
# infrastructure/client/base.py
from abc import ABC, abstractmethod
from typing import Callable, TypeVar, Optional
import threading
import time

from gvm.protocols.gmp import Gmp

T = TypeVar("T")

class GvmClient(ABC):
    """Abstract base client for GVM connections.
    
    Provides:
    - Thread-safe operation execution
    - Automatic reconnection on failure
    - Exponential backoff retry
    - Idle connection cleanup
    """
    
    def __init__(self, config: "BaseClientConfig"):
        self._config = config
        self._gmp: Optional[Gmp] = None
        self._lock = threading.RLock()
        self._last_used: float = 0.0
    
    @abstractmethod
    def _create_connection(self):
        """Create the underlying GVM connection. Implementation-specific."""
        pass
    
    @abstractmethod
    def _get_credentials(self) -> tuple[str, str]:
        """Return (username, password) for authentication."""
        pass
    
    def execute(self, operation: Callable[[Gmp], T], timeout: Optional[float] = None) -> T:
        """Execute operation with retry and auto-reconnect."""
        timeout = timeout or self._config.operation_timeout
        
        acquired = self._lock.acquire(timeout=timeout)
        if not acquired:
            raise ConnectionTimeoutError(
                "Timeout waiting for GVM connection. Another operation is in progress."
            )
        
        try:
            return self._execute_with_retry(operation)
        finally:
            self._lock.release()
    
    def _execute_with_retry(self, operation: Callable[[Gmp], T]) -> T:
        """Execute with exponential backoff retry."""
        last_error = None
        
        for attempt in range(self._config.retry_max_attempts):
            try:
                self._ensure_connected()
                result = operation(self._gmp)
                self._last_used = time.time()
                return result
            except GvmError as e:
                last_error = e
                if not self._is_retryable(e):
                    raise
                if attempt < self._config.retry_max_attempts - 1:
                    delay = self._calculate_delay(attempt)
                    time.sleep(delay)
                    self._reconnect()
        
        raise last_error
    
    def _ensure_connected(self):
        """Ensure connection is alive, reconnect if needed."""
        if self._gmp is None or not self._gmp.is_connected():
            self._connect()
    
    def _connect(self):
        """Establish connection and authenticate."""
        connection = self._create_connection()
        self._gmp = Gmp(connection=connection, transform=EtreeCheckCommandTransform())
        self._gmp.connect()
        
        username, password = self._get_credentials()
        self._gmp.authenticate(username=username, password=password)
    
    def _reconnect(self):
        """Force reconnection."""
        self._disconnect()
        self._connect()
    
    def _disconnect(self):
        """Clean disconnect."""
        if self._gmp:
            try:
                self._gmp.disconnect()
            except Exception:
                pass
            self._gmp = None
    
    def disconnect(self):
        """Public disconnect method."""
        with self._lock:
            self._disconnect()
    
    @property
    def is_connected(self) -> bool:
        return self._gmp is not None and self._gmp.is_connected()
```

### Local Socket Client

```python
# infrastructure/client/socket_client.py
from gvm.connections import UnixSocketConnection
from .base import GvmClient

class LocalSocketClient(GvmClient):
    """Client for local Unix socket connections.
    
    Usage:
        config = SocketClientConfig(
            socket_path="/run/gvmd/gvmd.sock",
            username="admin",
            password="secret"
        )
        client = LocalSocketClient(config)
    """
    
    def __init__(self, config: "SocketClientConfig"):
        super().__init__(config)
        self._socket_config = config
    
    def _create_connection(self):
        return UnixSocketConnection(
            path=self._socket_config.socket_path,
            timeout=self._socket_config.connection_timeout,
        )
    
    def _get_credentials(self) -> tuple[str, str]:
        return (
            self._socket_config.username,
            self._socket_config.password,
        )
```

### Remote Client (TLS)

```python
# infrastructure/client/remote_client.py
import ssl
from gvm.connections import TLSConnection
from .base import GvmClient

class RemoteClient(GvmClient):
    """Client for remote TLS connections.
    
    Usage:
        config = RemoteClientConfig(
            host="gvm.example.com",
            port=9390,
            username="admin",
            password="secret",
            ca_cert="/path/to/ca.pem",  # optional
            verify_ssl=True
        )
        client = RemoteClient(config)
    """
    
    def __init__(self, config: "RemoteClientConfig"):
        super().__init__(config)
        self._remote_config = config
    
    def _create_connection(self):
        ssl_context = self._create_ssl_context()
        return TLSConnection(
            hostname=self._remote_config.host,
            port=self._remote_config.port,
            timeout=self._remote_config.connection_timeout,
            ssl_context=ssl_context,
        )
    
    def _create_ssl_context(self) -> ssl.SSLContext:
        if not self._remote_config.verify_ssl:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            return context
        
        context = ssl.create_default_context()
        
        if self._remote_config.ca_cert:
            context.load_verify_locations(cafile=self._remote_config.ca_cert)
        
        if self._remote_config.client_cert:
            context.load_cert_chain(
                certfile=self._remote_config.client_cert,
                keyfile=self._remote_config.client_key,
            )
        
        return context
    
    def _get_credentials(self) -> tuple[str, str]:
        return (
            self._remote_config.username,
            self._remote_config.password,
        )
```

---

## Configuration Models

```python
# infrastructure/config.py
from dataclasses import dataclass
from typing import Optional, Literal

@dataclass
class BaseClientConfig:
    """Base configuration for all clients."""
    username: str
    password: str
    
    # Timeouts (seconds)
    connection_timeout: int = 30
    operation_timeout: int = 300
    
    # Retry settings (triggered on error)
    retry_max_attempts: int = 3


@dataclass
class SocketClientConfig(BaseClientConfig):
    """Configuration for local socket client."""
    socket_path: str = "/run/gvmd/gvmd.sock"


@dataclass  
class RemoteClientConfig(BaseClientConfig):
    """Configuration for remote TLS client."""
    host: str
    port: int = 9390
    
    # TLS settings
    verify_ssl: bool = True
    ca_cert: Optional[str] = None
    client_cert: Optional[str] = None
    client_key: Optional[str] = None


@dataclass
class GvmTargetConfig:
    """User-facing configuration for GVM target."""
    connection_type: Literal["socket", "tls"]
    
    # Socket settings
    socket_path: Optional[str] = None
    
    # TLS settings
    host: Optional[str] = None
    port: int = 9390
    verify_ssl: bool = True
    ca_cert: Optional[str] = None
    client_cert: Optional[str] = None
    client_key: Optional[str] = None
    
    # Auth
    username: str = ""
    password: str = ""
    
    # Timeouts
    timeout: int = 300
```

### Client Factory

```python
# infrastructure/factory.py
from .config import GvmTargetConfig, SocketClientConfig, RemoteClientConfig
from .client.base import GvmClient
from .client.socket_client import LocalSocketClient
from .client.remote_client import RemoteClient

def create_client(config: GvmTargetConfig) -> GvmClient:
    """Factory function to create appropriate client from config."""
    
    if config.connection_type == "socket":
        socket_config = SocketClientConfig(
            socket_path=config.socket_path or "/run/gvmd/gvmd.sock",
            username=config.username,
            password=config.password,
            operation_timeout=config.timeout,
        )
        return LocalSocketClient(socket_config)
    
    elif config.connection_type == "tls":
        if not config.host:
            raise ValueError("host is required for TLS connection")
        
        remote_config = RemoteClientConfig(
            host=config.host,
            port=config.port,
            username=config.username,
            password=config.password,
            verify_ssl=config.verify_ssl,
            ca_cert=config.ca_cert,
            client_cert=config.client_cert,
            client_key=config.client_key,
            operation_timeout=config.timeout,
        )
        return RemoteClient(remote_config)
    
    else:
        raise ValueError(f"Unknown connection type: {config.connection_type}")
```

---

## MCP Configuration (Installation Parameters)

```python
# presentation/mcp/config.py
"""
MCP server receives configuration as installation parameters.

Example MCP client config (Claude Desktop):
{
  "mcpServers": {
    "openvas": {
      "command": "openvas-mcp",
      "args": [],
      "env": {
        "GVM_CONNECTION_TYPE": "socket",
        "GVM_SOCKET_PATH": "/run/gvmd/gvmd.sock",
        "GVM_USERNAME": "admin",
        "GVM_PASSWORD": "secret"
      }
    }
  }
}

Or for remote:
{
  "mcpServers": {
    "openvas": {
      "command": "openvas-mcp",
      "env": {
        "GVM_CONNECTION_TYPE": "tls",
        "GVM_HOST": "gvm.example.com",
        "GVM_PORT": "9390",
        "GVM_USERNAME": "admin",
        "GVM_PASSWORD": "secret",
        "GVM_VERIFY_SSL": "true"
      }
    }
  }
}
"""

import os
from ..infrastructure.config import GvmTargetConfig

def load_mcp_config() -> GvmTargetConfig:
    """Load configuration from environment variables (MCP installation params)."""
    
    connection_type = os.environ.get("GVM_CONNECTION_TYPE", "socket")
    
    return GvmTargetConfig(
        connection_type=connection_type,
        
        # Socket
        socket_path=os.environ.get("GVM_SOCKET_PATH"),
        
        # TLS
        host=os.environ.get("GVM_HOST"),
        port=int(os.environ.get("GVM_PORT", "9390")),
        verify_ssl=os.environ.get("GVM_VERIFY_SSL", "true").lower() == "true",
        ca_cert=os.environ.get("GVM_CA_CERT"),
        client_cert=os.environ.get("GVM_CLIENT_CERT"),
        client_key=os.environ.get("GVM_CLIENT_KEY"),
        
        # Auth
        username=os.environ.get("GVM_USERNAME", ""),
        password=os.environ.get("GVM_PASSWORD", ""),
        
        # Timeout
        timeout=int(os.environ.get("GVM_TIMEOUT", "300")),
    )
```

---

## CLI Configuration (Interactive Prompt)

```python
# presentation/cli/config.py
"""
CLI prompts user for connection details on initialization.
Configuration is saved to ~/.config/openvas-mcp/config.toml
"""

import os
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.prompt import Prompt, Confirm

try:
    import tomllib
except ImportError:
    import tomli as tomllib

import tomli_w

from ..infrastructure.config import GvmTargetConfig

CONFIG_DIR = Path.home() / ".config" / "openvas-mcp"
CONFIG_FILE = CONFIG_DIR / "config.toml"

console = Console()


def load_cli_config() -> Optional[GvmTargetConfig]:
    """Load existing CLI configuration if available."""
    if not CONFIG_FILE.exists():
        return None
    
    with open(CONFIG_FILE, "rb") as f:
        data = tomllib.load(f)
    
    return GvmTargetConfig(
        connection_type=data.get("connection_type", "socket"),
        socket_path=data.get("socket_path"),
        host=data.get("host"),
        port=data.get("port", 9390),
        verify_ssl=data.get("verify_ssl", True),
        ca_cert=data.get("ca_cert"),
        client_cert=data.get("client_cert"),
        client_key=data.get("client_key"),
        username=data.get("username", ""),
        password=data.get("password", ""),
        timeout=data.get("timeout", 300),
    )


def save_cli_config(config: GvmTargetConfig) -> None:
    """Save CLI configuration to file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    
    data = {
        "connection_type": config.connection_type,
        "socket_path": config.socket_path,
        "host": config.host,
        "port": config.port,
        "verify_ssl": config.verify_ssl,
        "ca_cert": config.ca_cert,
        "client_cert": config.client_cert,
        "client_key": config.client_key,
        "username": config.username,
        # Note: password not saved for security
        "timeout": config.timeout,
    }
    
    # Remove None values
    data = {k: v for k, v in data.items() if v is not None}
    
    with open(CONFIG_FILE, "wb") as f:
        tomli_w.dump(data, f)
    
    console.print(f"[green]Configuration saved to {CONFIG_FILE}[/green]")


def prompt_for_config() -> GvmTargetConfig:
    """Interactive prompt for GVM connection configuration."""
    
    console.print("\n[bold]OpenVAS MCP - Connection Setup[/bold]\n")
    
    # Connection type
    connection_type = Prompt.ask(
        "Connection type",
        choices=["socket", "tls"],
        default="socket"
    )
    
    config_data = {"connection_type": connection_type}
    
    if connection_type == "socket":
        config_data["socket_path"] = Prompt.ask(
            "Socket path",
            default="/run/gvmd/gvmd.sock"
        )
    else:
        config_data["host"] = Prompt.ask("GVM hostname")
        config_data["port"] = int(Prompt.ask("GVM port", default="9390"))
        config_data["verify_ssl"] = Confirm.ask("Verify SSL certificate?", default=True)
        
        if config_data["verify_ssl"]:
            ca_cert = Prompt.ask("CA certificate path (optional)", default="")
            if ca_cert:
                config_data["ca_cert"] = ca_cert
    
    # Authentication
    config_data["username"] = Prompt.ask("GVM username", default="admin")
    config_data["password"] = Prompt.ask("GVM password", password=True)
    
    # Timeout
    config_data["timeout"] = int(Prompt.ask("Operation timeout (seconds)", default="300"))
    
    return GvmTargetConfig(**config_data)


def get_or_prompt_config(force_prompt: bool = False) -> GvmTargetConfig:
    """Get config from file or prompt user."""
    
    existing = load_cli_config()
    
    if existing and not force_prompt:
        # Have existing config, just need password
        console.print(f"[dim]Using saved config: {existing.connection_type} connection[/dim]")
        
        password = Prompt.ask(
            f"Password for {existing.username}",
            password=True
        )
        existing.password = password
        return existing
    
    # No config or forced prompt
    config = prompt_for_config()
    
    if Confirm.ask("Save this configuration?", default=True):
        save_cli_config(config)
    
    return config
```

### CLI Main Entry Point

```python
# presentation/cli/main.py
import typer
from rich.console import Console

from .config import get_or_prompt_config
from ..infrastructure.factory import create_client

app = typer.Typer(
    name="openvas",
    help="OpenVAS/GVM command-line interface"
)
console = Console()

# Global client (initialized on first command)
_client = None


def get_client():
    """Get or initialize the GVM client."""
    global _client
    
    if _client is None:
        config = get_or_prompt_config()
        _client = create_client(config)
    
    return _client


@app.command()
def configure(force: bool = typer.Option(False, "--force", "-f", help="Force reconfiguration")):
    """Configure GVM connection."""
    config = get_or_prompt_config(force_prompt=True)
    console.print("[green]Configuration complete![/green]")


@app.command()
def test():
    """Test GVM connection."""
    client = get_client()
    
    try:
        result = client.execute(lambda gmp: gmp.get_version())
        console.print(f"[green]✓ Connected to GVM version: {result}[/green]")
    except Exception as e:
        console.print(f"[red]✗ Connection failed: {e}[/red]")
        raise typer.Exit(1)


# Import command groups
from .commands import targets, scans, reports

app.add_typer(targets.app, name="target")
app.add_typer(scans.app, name="scan")
app.add_typer(reports.app, name="report")


def main():
    app()


if __name__ == "__main__":
    main()
```

---

## Service Layer

Services receive client via dependency injection:

```python
# services/targets/service.py
from ...infrastructure.client.base import GvmClient

class TargetService:
    def __init__(self, client: GvmClient):
        self._client = client
    
    def list(self, filter_string: str = "rows=-1") -> TargetListResponse:
        def _operation(gmp):
            response = gmp.get_targets(filter_string=filter_string)
            ...
        return self._client.execute(_operation)
```

---

## Summary

| Component | Configuration Source |
|-----------|---------------------|
| **MCP Server** | Environment variables (set during installation) |
| **CLI** | Interactive prompt → saved to `~/.config/openvas-mcp/config.toml` |
| **Client** | Factory creates `LocalSocketClient` or `RemoteClient` based on config |

| Client Type | Use Case |
|-------------|----------|
| `LocalSocketClient` | gvmd on same machine, Unix socket |
| `RemoteClient` | gvmd on remote server, TLS connection |

| Concern | Solution |
|---------|----------|
| Thread safety | `RLock` with timeout |
| Connection pooling | **Removed** — dangerous, gvmd is single-threaded |
| Retry | Exponential backoff (3 attempts) |
| Reconnect | On error |
