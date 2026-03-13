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
│   ├── config.py              # Configuration loading (env/file)
│   └── client.py              # Singleton GMP client with session mgmt
│
├── services/
│   ├── __init__.py
│   ├── targets/
│   │   ├── __init__.py
│   │   ├── models.py          # Target, TargetCreateRequest, TargetResponse
│   │   └── service.py         # TargetService implementation
│   ├── scans/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   └── service.py
│   ├── reports/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   └── service.py
│   ├── vulnerabilities/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   └── service.py
│   ├── assets/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   └── service.py
│   ├── compliance/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   └── service.py
│   ├── tickets/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   └── service.py
│   ├── notes/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   └── service.py
│   ├── overrides/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   └── service.py
│   ├── secinfo/
│   │   ├── __init__.py
│   │   ├── models.py          # NVT, CVE, CPE, Advisory
│   │   └── service.py
│   ├── credentials/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   └── service.py
│   ├── schedules/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   └── service.py
│   └── system/
│       ├── __init__.py
│       ├── models.py          # Version, Feed status
│       └── service.py
│
├── presentation/
│   ├── __init__.py
│   ├── mcp/
│   │   ├── __init__.py
│   │   ├── server.py          # FastMCP server entry point
│   │   └── toolsets/
│   │       ├── __init__.py
│   │       ├── targets.py     # Target tools (list, create, modify, delete)
│   │       ├── scans.py
│   │       ├── reports.py
│   │       ├── vulnerabilities.py
│   │       ├── assets.py
│   │       ├── compliance.py
│   │       ├── tickets.py
│   │       ├── notes.py
│   │       ├── overrides.py
│   │       └── system.py
│   │
│   └── cli/
│       ├── __init__.py
│       ├── main.py            # CLI entry point (typer)
│       └── commands/
│           ├── __init__.py
│           ├── targets.py
│           ├── scans.py
│           ├── reports.py
│           ├── vulnerabilities.py
│           ├── assets.py
│           ├── compliance.py
│           ├── tickets.py
│           └── system.py
│
├── errors.py                  # Custom exception hierarchy
└── utils/
    ├── __init__.py
    ├── xml_helpers.py         # XML to model conversion
    └── validators.py          # Input validation helpers

tests/
├── __init__.py
├── infrastructure/
│   ├── test_config.py         # Full coverage
│   └── test_client.py         # Full coverage
├── services/
│   ├── targets/
│   │   └── test_service.py    # Edge cases only
│   ├── scans/
│   │   └── test_service.py
│   └── ...
├── presentation/
│   ├── mcp/
│   │   └── test_toolsets.py   # Edge cases only
│   └── cli/
│       └── test_commands.py
└── conftest.py                # Shared fixtures
```

---

## Layer Responsibilities

### Infrastructure Layer

**Location:** `openvas_mcp/infrastructure/`

| Component | Responsibility |
|-----------|----------------|
| `config.py` | Load configuration from env vars or TOML file |
| `client.py` | Singleton GMP client with persistent session |

#### Client Design (Singleton with Session Persistence)

```python
class GvmClient:
    """Thread-safe singleton GMP client with persistent authentication."""
    
    _instance: Optional["GvmClient"] = None
    _lock: threading.Lock = threading.Lock()
    
    def __new__(cls, config: GvmConfig) -> "GvmClient":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize(config)
        return cls._instance
    
    def execute(self, operation: Callable[[Gmp], T]) -> T:
        """Execute a GMP operation with automatic reconnection."""
        with self._operation_lock:
            try:
                gmp = self._ensure_connected()
                return operation(gmp)
            except (ConnectionError, GvmError):
                self._connect()
                return operation(self._gmp)
```

**⚠️ Session Management Notes:**

1. **Session persistence confirmed:** python-gvm supports keeping authenticated sessions alive.
2. **Server-side timeout:** gvmd may close idle connections. Client auto-reconnects.
3. **Thread safety:** Operations serialized via `_operation_lock`.

---

### Service Layer

**Location:** `openvas_mcp/services/<domain>/`

Each domain has:
- `models.py` — Pydantic models for requests, responses, and entities
- `service.py` — Business logic implementation

#### Model Design Pattern

```python
# services/targets/models.py
from pydantic import BaseModel, Field

class Target(BaseModel):
    """Target entity (domain model)."""
    id: str
    name: str
    hosts: list[str]
    exclude_hosts: list[str] = []
    comment: Optional[str] = None
    alive_test: Optional[str] = None
    port_list_id: Optional[str] = None
    in_use: bool = False

class TargetCreateRequest(BaseModel):
    """Request to create a target."""
    name: str = Field(..., min_length=1, max_length=255)
    hosts: list[str] = Field(..., min_length=1)
    exclude_hosts: list[str] = []
    comment: Optional[str] = Field(None, max_length=500)

class TargetListResponse(BaseModel):
    """Response containing list of targets."""
    items: list[Target]
    count: int
```

#### Service Design Pattern

```python
# services/targets/service.py
class TargetService:
    """Service for target management operations."""
    
    def __init__(self, client: GvmClient):
        self._client = client
    
    def list(self, filter_string: str = "rows=-1") -> TargetListResponse:
        """List all targets matching filter."""
        def _operation(gmp):
            response = gmp.get_targets(filter_string=filter_string)
            targets = [parse_target(t) for t in response.findall("target")]
            return TargetListResponse(items=targets, count=len(targets))
        return self._client.execute(_operation)
    
    def create(self, request: TargetCreateRequest) -> Target:
        """Create a new target."""
        def _operation(gmp):
            response = gmp.create_target(
                name=request.name,
                hosts=request.hosts,
                ...
            )
            return parse_target(...)
        return self._client.execute(_operation)
```

---

### Presentation Layer

**Location:** `openvas_mcp/presentation/`

#### MCP Toolsets

```python
# presentation/mcp/toolsets/targets.py
def register_target_tools(server: FastMCP, service: TargetService) -> None:
    @server.tool()
    def list_targets(filter_string: str = "rows=-1") -> dict:
        """List all scan targets."""
        response = service.list(filter_string)
        return response.model_dump()
    
    @server.tool()
    def create_target(name: str, hosts: list[str], ...) -> dict:
        """Create a new scan target."""
        request = TargetCreateRequest(name=name, hosts=hosts, ...)
        target = service.create(request)
        return target.model_dump()
```

#### CLI Commands

```python
# presentation/cli/commands/targets.py
app = typer.Typer(help="Target management commands")

@app.command("list")
def list_targets(
    filter: str = typer.Option("rows=-1", "--filter", "-f"),
    json_output: bool = typer.Option(False, "--json"),
):
    """List all scan targets."""
    service = _get_service()
    response = service.list(filter)
    
    if json_output:
        console.print_json(response.model_dump_json())
    else:
        table = Table(title="Targets")
        ...
```

---

## Domain Services

| Service | Entity | Operations |
|---------|--------|------------|
| `TargetService` | Target | list, get, create, update, delete |
| `ScanService` | Scan/Task | list, get, create, start, stop, resume, delete |
| `ReportService` | Report | list, get, get_summary, delete, export |
| `VulnerabilityService` | Vulnerability | list, get, search_nvts |
| `AssetService` | Host, OS, TLS | list_hosts, list_os, list_certificates |
| `ComplianceService` | Policy, Audit | list_policies, list_audits, start, stop, check |
| `TicketService` | Ticket | list, get, create, update, delete |
| `NoteService` | Note | list, get, create, update, delete |
| `OverrideService` | Override | list, get, create, update, delete |
| `SecInfoService` | NVT, CVE, CPE | list_nvts, list_cves, list_cpes, get |
| `CredentialService` | Credential | list, get, create, delete |
| `ScheduleService` | Schedule | list, get, create, update, delete |
| `SystemService` | Version, Feed | get_version, get_feeds, describe_auth |

---

## Configuration

### Environment Variables

```bash
# Connection
GVM_CONNECTION_TYPE=tls          # tls | socket
GVM_HOST=gvm.example.com         # Required for TLS
GVM_PORT=9390                    # Default: 9390
GVM_SOCKET_PATH=/run/gvmd.sock   # Required for socket

# Authentication
GVM_USERNAME=admin
GVM_PASSWORD=secret

# TLS (optional)
GVM_CA_CERT=/path/to/ca.pem
GVM_CLIENT_CERT=/path/to/client.pem
GVM_CLIENT_KEY=/path/to/client.key
GVM_VERIFY_SSL=true

# Limits
GVM_TIMEOUT=300
GVM_MAX_RESULTS=10000
```

### Config File (Optional)

```toml
# /etc/openvas-mcp/config.toml
[connection]
type = "tls"
host = "gvm.example.com"
port = 9390

[auth]
username = "admin"
# password via env var GVM_PASSWORD

[tls]
ca_cert = "/etc/openvas-mcp/ca.pem"
verify = true

[limits]
timeout = 300
max_results = 10000
```

---

## Versioning

**CalVer Format:** `YYYY.0M.MICRO`

Examples:
- `2025.03.0` — Initial March 2025 release
- `2025.03.1` — Patch release
- `2025.04.0` — April 2025 release

---

## Distribution

### MCP Server (Docker)

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && poetry install --only main
COPY openvas_mcp ./openvas_mcp
ENTRYPOINT ["poetry", "run", "python", "-m", "openvas_mcp.presentation.mcp.server"]
```

**Registry:** GitHub Container Registry (ghcr.io)

### CLI (Python Package)

```bash
# Installation
pip install openvas-mcp

# Usage
openvas target list
openvas scan create --name "Scan" --target-id <id>
openvas report get <id> --format json
```

**Distribution:** GitHub Releases → PyPI (later)

---

## Testing Strategy

### Full Coverage

- `tests/infrastructure/test_config.py` — All config scenarios
- `tests/infrastructure/test_client.py` — Connection, auth, reconnect, thread safety

### Edge Cases Only

For services and presentation layers:
- Invalid inputs (malformed UUIDs, empty lists)
- Error handling (GVM errors, connection failures)
- Boundary conditions (max results, timeouts)
- Concurrent access scenarios

**Not tested:**
- Happy path with valid parameters (covered by integration tests)
- Simple parameter validation (covered by Pydantic)

---

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `python-gvm` | ≥24.0 | Official GMP library (locked) |
| `mcp[cli]` | ≥1.0 | MCP SDK with CLI tools |
| `pydantic` | ≥2.0 | Models & validation |
| `typer` | ≥0.9.0 | CLI framework |
| `rich` | ≥13.0 | CLI formatting |
| `tomli` | ≥2.0 | Config file parsing |
