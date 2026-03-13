# OpenVAS MCP Server — Error Handling

**Version:** 2025.03  
**Status:** Design

---

## Principles

1. **User-friendly messages** — All errors exposed to users (CLI/MCP) must be actionable
2. **No internal leakage** — Never expose file paths, stack traces, or internal state
3. **Structured errors** — Errors carry code, message, and optional details
4. **Logging separation** — Full details logged server-side, sanitized sent to client

---

## Error Hierarchy

```
GvmClientError (base)
├── ConfigurationError
│   ├── MissingConfigError
│   ├── InvalidConfigError
│   └── ConfigFileError
├── ConnectionError
│   ├── SocketNotFoundError
│   ├── HostUnreachableError
│   ├── TlsError
│   ├── ConnectionTimeoutError
│   └── ConnectionRefusedError
├── AuthenticationError
│   ├── InvalidCredentialsError
│   ├── SessionExpiredError
│   └── PermissionDeniedError
├── ValidationError
│   ├── InvalidUuidError
│   ├── InvalidHostError
│   ├── InvalidFilterError
│   ├── RequiredFieldError
│   └── FieldTooLongError
├── ResourceError
│   ├── ResourceNotFoundError
│   ├── ResourceInUseError
│   ├── ResourceExistsError
│   └── ResourceLimitError
├── OperationError
│   ├── ScanRunningError
│   ├── ScanNotRunningError
│   ├── ReportNotReadyError
│   └── UnsupportedOperationError
└── ServerError
    ├── GvmInternalError
    ├── GvmUnavailableError
    └── GvmTimeoutError
```

---

## Error Definitions

### Base Error

| Field | Type | Description |
|-------|------|-------------|
| `code` | `str` | Machine-readable error code (e.g., `CONNECTION_TIMEOUT`) |
| `message` | `str` | User-friendly message |
| `details` | `dict` | Optional structured details |
| `http_status` | `int` | Suggested HTTP status code |

---

### Configuration Errors

| Error | Code | HTTP | User Message |
|-------|------|------|--------------|
| `MissingConfigError` | `CONFIG_MISSING` | 500 | "GVM connection is not configured. Set GVM_HOST or GVM_SOCKET_PATH." |
| `InvalidConfigError` | `CONFIG_INVALID` | 500 | "Invalid configuration: {field}. {hint}" |
| `ConfigFileError` | `CONFIG_FILE_ERROR` | 500 | "Cannot read configuration file. Check file permissions." |

---

### Connection Errors

| Error | Code | HTTP | User Message |
|-------|------|------|--------------|
| `SocketNotFoundError` | `SOCKET_NOT_FOUND` | 503 | "GVM socket not found. Is gvmd running?" |
| `HostUnreachableError` | `HOST_UNREACHABLE` | 503 | "Cannot reach GVM server. Check network connectivity." |
| `TlsError` | `TLS_ERROR` | 503 | "TLS connection failed. Check certificates." |
| `ConnectionTimeoutError` | `CONNECTION_TIMEOUT` | 504 | "Connection to GVM timed out. Server may be overloaded." |
| `ConnectionRefusedError` | `CONNECTION_REFUSED` | 503 | "Connection refused. Check if gvmd is running on the specified port." |

---

### Authentication Errors

| Error | Code | HTTP | User Message |
|-------|------|------|--------------|
| `InvalidCredentialsError` | `INVALID_CREDENTIALS` | 401 | "Invalid username or password." |
| `SessionExpiredError` | `SESSION_EXPIRED` | 401 | "Session expired. Reconnecting..." |
| `PermissionDeniedError` | `PERMISSION_DENIED` | 403 | "You don't have permission to perform this action." |

---

### Validation Errors

| Error | Code | HTTP | User Message |
|-------|------|------|--------------|
| `InvalidUuidError` | `INVALID_UUID` | 400 | "Invalid ID format for {field}. Expected UUID." |
| `InvalidHostError` | `INVALID_HOST` | 400 | "Invalid host format: {value}. Use IP, CIDR, or hostname." |
| `InvalidFilterError` | `INVALID_FILTER` | 400 | "Invalid filter syntax. Check GMP filter documentation." |
| `RequiredFieldError` | `REQUIRED_FIELD` | 400 | "{field} is required." |
| `FieldTooLongError` | `FIELD_TOO_LONG` | 400 | "{field} exceeds maximum length of {max} characters." |

---

### Resource Errors

| Error | Code | HTTP | User Message |
|-------|------|------|--------------|
| `ResourceNotFoundError` | `NOT_FOUND` | 404 | "{resource_type} not found: {id}" |
| `ResourceInUseError` | `IN_USE` | 409 | "Cannot delete {resource_type} because it is in use by {count} {dependent_type}(s)." |
| `ResourceExistsError` | `ALREADY_EXISTS` | 409 | "{resource_type} with this name already exists." |
| `ResourceLimitError` | `LIMIT_EXCEEDED` | 429 | "Resource limit reached. Maximum {limit} {resource_type}s allowed." |

---

### Operation Errors

| Error | Code | HTTP | User Message |
|-------|------|------|--------------|
| `ScanRunningError` | `SCAN_RUNNING` | 409 | "Cannot modify task while scan is running. Stop the scan first." |
| `ScanNotRunningError` | `SCAN_NOT_RUNNING` | 409 | "Task is not running." |
| `ReportNotReadyError` | `REPORT_NOT_READY` | 409 | "Report is still being generated. Try again later." |
| `UnsupportedOperationError` | `UNSUPPORTED` | 400 | "This operation is not supported for {resource_type}." |

---

### Server Errors

| Error | Code | HTTP | User Message |
|-------|------|------|--------------|
| `GvmInternalError` | `GVM_INTERNAL` | 502 | "GVM server encountered an internal error. Check server logs." |
| `GvmUnavailableError` | `GVM_UNAVAILABLE` | 503 | "GVM server is currently unavailable. Try again later." |
| `GvmTimeoutError` | `GVM_TIMEOUT` | 504 | "GVM operation timed out. The operation may still be running." |

---

## Error Response Format

### MCP Response

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Target not found: 12345678-1234-1234-1234-123456789012",
    "details": {
      "resource_type": "target",
      "resource_id": "12345678-1234-1234-1234-123456789012"
    }
  }
}
```

### CLI Output

```
Error: Target not found: 12345678-1234-1234-1234-123456789012

Hint: Use 'openvas target list' to see available targets.
```

---

## GMP Error Mapping

Map GMP status codes to our errors:

| GMP Status | GMP Status Text | Our Error |
|------------|-----------------|-----------|
| 400 | Bad Request | `ValidationError` |
| 401 | Authenticate first | `InvalidCredentialsError` |
| 403 | Permission denied | `PermissionDeniedError` |
| 404 | Resource not found | `ResourceNotFoundError` |
| 409 | Resource in use | `ResourceInUseError` |
| 500 | Internal error | `GvmInternalError` |
| 503 | Service unavailable | `GvmUnavailableError` |

---

## Logging Strategy

### What to Log

| Level | Content |
|-------|---------|
| `ERROR` | Full exception with traceback, GMP request/response |
| `WARNING` | Recoverable errors (reconnection, retry) |
| `INFO` | Operations (connect, auth, major actions) |
| `DEBUG` | GMP XML payloads, timing |

### What NOT to Log

- Passwords (even masked)
- Full credentials
- User PII beyond username

### Log Format

```
2025-03-13T10:15:30Z [ERROR] openvas_mcp.services.targets: Operation failed
  error_code=NOT_FOUND
  resource_type=target
  resource_id=12345678-...
  gmp_status=404
  gmp_status_text="Resource not found"
  duration_ms=45
```

---

## CLI Hints

Each error includes CLI-specific hints:

| Error | CLI Hint |
|-------|----------|
| `ResourceNotFoundError` | "Use 'openvas {type} list' to see available {type}s." |
| `SocketNotFoundError` | "Check that gvmd is running: 'systemctl status gvmd'" |
| `InvalidCredentialsError` | "Check GVM_USERNAME and GVM_PASSWORD environment variables." |
| `TlsError` | "Verify CA certificate path or set GVM_VERIFY_SSL=false for testing." |
| `ScanRunningError` | "Stop the scan with 'openvas scan stop <id>'" |
| `InvalidFilterError` | "Filter example: 'name~web rows=10 first=1'" |

---

## Implementation Pattern

```python
@dataclass
class GvmClientError(Exception):
    code: str
    message: str
    details: dict = field(default_factory=dict)
    http_status: int = 500
    
    @property
    def cli_hint(self) -> Optional[str]:
        return None
    
    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details,
        }
    
    def to_response(self) -> dict:
        return {
            "error": self.to_dict(),
            "status": str(self.http_status),
        }


class ResourceNotFoundError(GvmClientError):
    code = "NOT_FOUND"
    http_status = 404
    
    def __init__(self, resource_type: str, resource_id: str):
        self.message = f"{resource_type.title()} not found: {resource_id}"
        self.details = {"resource_type": resource_type, "resource_id": resource_id}
    
    @property
    def cli_hint(self) -> str:
        rt = self.details.get("resource_type", "resource")
        return f"Use 'openvas {rt} list' to see available {rt}s."
```
