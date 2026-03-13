# Phase 1: Foundation

**Duration:** 3-4 days  
**Status:** Completed

---

## 1.1 Project Scaffold

- [ ] Repository structure setup
- [ ] Poetry/pyproject.toml configuration
- [ ] Development tooling (ruff, mypy, pytest)
- [ ] CI/CD setup (GitHub Actions)

---

## 1.2 Client Layer

### Abstract Base

```python
class GvmClient(ABC):
    def execute(self, operation: Callable[[Gmp], T]) -> T
    def disconnect(self) -> None
    def is_connected(self) -> bool
```

### Implementations

| Client | File | Transport |
|--------|------|-----------|
| `LocalClient` | `client/local.py` | Unix socket |
| `RemoteClient` | `client/remote.py` | TLS |

### Features

- [ ] Thread-safe execution (RLock)
- [ ] Retry on error (`retry_max_attempts`)
- [ ] Auto-reconnect on connection failure
- [ ] Client factory for config-based instantiation

---

## 1.3 Configuration

### Connection Styles

| Style | Parameters |
|-------|------------|
| `local` | `socket_path` |
| `remote` | `hostname`, `port`, `certfile`, `cafile`, `keyfile`, `key_password` |

### Common Parameters

| Parameter | Type | Default | Required |
|-----------|------|---------|----------|
| `gmp_username` | str | - | Yes |
| `gmp_password` | str | - | Yes |
| `timeout` | int | 60 | No |
| `retry_max_attempts` | int | 3 | No |

### Configuration Sources

| Interface | Source |
|-----------|--------|
| MCP | Environment variables |
| CLI | Interactive prompt → TOML file |

### Environment Variables

```bash
# Style
GVM_STYLE=local|remote

# Local
GVM_SOCKET_PATH=/run/gvmd/gvmd.sock

# Remote
GVM_HOSTNAME=gvm.example.com
GVM_PORT=9390
GVM_CERTFILE=/path/to/client.pem
GVM_CAFILE=/path/to/ca.pem
GVM_KEYFILE=/path/to/client.key
GVM_KEY_PASSWORD=secret

# Auth
GVM_USERNAME=admin
GVM_PASSWORD=secret

# Common
GVM_TIMEOUT=60
GVM_RETRY_MAX_ATTEMPTS=3
```

### TOML Config File

```toml
# ~/.config/openvas-mcp/config.toml
[connection]
style = "remote"
hostname = "gvm.example.com"
port = 9390
timeout = 60

[tls]
cafile = "/path/to/ca.pem"

[auth]
username = "admin"
# password via GVM_PASSWORD env var

[retry]
max_attempts = 3
```

---

## 1.4 Error Handling

### Exception Hierarchy

```
GvmClientError (base)
├── ConfigurationError
│   ├── MissingConfigError
│   └── InvalidConfigError
├── ConnectionError
│   ├── SocketNotFoundError
│   ├── HostUnreachableError
│   ├── TlsError
│   ├── ConnectionTimeoutError
│   └── ConnectionRefusedError
├── AuthenticationError
│   ├── InvalidCredentialsError
│   └── PermissionDeniedError
├── ValidationError
│   ├── InvalidUuidError
│   ├── InvalidHostError
│   ├── InvalidFilterError
│   └── RequiredFieldError
├── ResourceError
│   ├── ResourceNotFoundError
│   ├── ResourceInUseError
│   └── ResourceExistsError
├── OperationError
│   ├── ScanRunningError
│   ├── ScanNotRunningError
│   └── ReportNotReadyError
└── ServerError
    ├── GvmInternalError
    ├── GvmUnavailableError
    └── GvmTimeoutError
```

### Error Structure

```python
@dataclass
class GvmClientError(Exception):
    code: str           # Machine-readable (e.g., "NOT_FOUND")
    message: str        # User-friendly message
    details: dict       # Structured details
    http_status: int    # Suggested HTTP status
    
    @property
    def cli_hint(self) -> str:
        """Actionable hint for CLI users."""
        pass
```

### GMP Error Mapping

| GMP Status | Our Error |
|------------|-----------|
| 400 | ValidationError |
| 401 | InvalidCredentialsError |
| 403 | PermissionDeniedError |
| 404 | ResourceNotFoundError |
| 409 | ResourceInUseError |
| 500 | GvmInternalError |
| 503 | GvmUnavailableError |

---

## 1.5 Core DTOs/Models

### Pydantic Models

```python
# Entity
class Target(BaseModel):
    id: str
    name: str
    hosts: list[str]
    comment: Optional[str]
    in_use: bool

# Request
class TargetCreateRequest(BaseModel):
    name: str = Field(..., min_length=1)
    hosts: list[str] = Field(..., min_length=1)
    comment: Optional[str] = None

# Response
class TargetListResponse(BaseModel):
    items: list[Target]
    count: int
```

### Utils

- [ ] `xml_helpers.py` — XML to model conversion
- [ ] `validators.py` — UUID, host, filter validation

---

## Deliverables

- [ ] Working `LocalClient` and `RemoteClient`
- [ ] Configuration loading from env/file
- [ ] Complete error hierarchy
- [ ] Core Pydantic models
- [ ] Unit tests for client and config
