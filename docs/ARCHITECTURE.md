# OpenVAS MCP Server — Architecture

**Version:** 2025.03

---

## Overview

MCP server and CLI for Greenbone Vulnerability Management (GVM/OpenVAS).

```
┌─────────────────────────────────────────────────────────────┐
│                   Presentation Layer                        │
│            ┌─────────┐        ┌─────────┐                   │
│            │   MCP   │        │   CLI   │                   │
│            │ Server  │        │         │                   │
│            └────┬────┘        └────┬────┘                   │
└─────────────────┼──────────────────┼────────────────────────┘
                  │                  │
┌─────────────────┼──────────────────┼────────────────────────┐
│                 ▼                  ▼                        │
│                    Service Layer                            │
│   ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│   │ Target   │ │  Scan    │ │ Report   │ │  ...     │      │
│   │ Service  │ │ Service  │ │ Service  │ │          │      │
│   └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘      │
│        │            │            │            │             │
│        └────────────┴─────┬──────┴────────────┘             │
│                           │                                 │
│                    ┌──────▼──────┐                          │
│                    │   Client    │                          │
│                    │   Layer     │                          │
│                    └──────┬──────┘                          │
└───────────────────────────┼─────────────────────────────────┘
                            │
                     ┌──────▼──────┐
                     │ python-gvm  │
                     └──────┬──────┘
                            │
                     ┌──────▼──────┐
                     │    gvmd     │
                     └─────────────┘
```

---

## Project Structure

```
openvas_mcp/
├── infrastructure/
│   ├── config.py           # Configuration
│   └── client/
│       ├── base.py         # Abstract GvmClient
│       ├── local.py        # LocalClient (socket)
│       └── remote.py       # RemoteClient (TLS)
│
├── services/
│   ├── targets/
│   │   ├── models.py       # Pydantic models
│   │   └── service.py      # TargetService
│   ├── scans/
│   ├── reports/
│   └── ...
│
├── presentation/
│   ├── mcp/
│   │   ├── server.py       # MCP entry point
│   │   └── toolsets/       # Tool registrations
│   └── cli/
│       ├── main.py         # CLI entry point
│       └── commands/       # CLI commands
│
├── errors.py               # Exception hierarchy
└── utils/
    ├── validators.py       # Input validation
    └── xml_helpers.py      # XML parsing
```

---

## Layers

### Client Layer

Two client implementations:

| Client | Transport | Use Case |
|--------|-----------|----------|
| `LocalClient` | Unix socket | gvmd on same machine |
| `RemoteClient` | TLS | gvmd on remote server |

Features:
- Thread-safe (RLock)
- Retry on error
- Auto-reconnect

### Service Layer

Domain-based services with Pydantic models:

| Service | Operations |
|---------|------------|
| TargetService | list, get, create, delete |
| ScanService | list, create, start, stop |
| ReportService | list, get, export |
| VulnerabilityService | list, search |
| ComplianceService | list_policies, run_audit |
| TicketService | CRUD |
| AssetService | list_hosts, list_os |
| SystemService | version, status |

### Presentation Layer

| Interface | Configuration |
|-----------|---------------|
| MCP | Environment variables |
| CLI | Interactive prompt + TOML file |

---

## Configuration

**Styles:** `local` (socket) or `remote` (TLS)

**Local:**
```
socket_path=/run/gvmd/gvmd.sock
```

**Remote:**
```
hostname=gvm.example.com
port=9390
certfile=/path/to/client.pem  (optional)
cafile=/path/to/ca.pem        (optional)
```

**Common:**
```
gmp_username=admin
gmp_password=secret
timeout=60
retry_max_attempts=3
```

---

## Error Handling

22 custom exception types:

| Category | Examples |
|----------|----------|
| Configuration | MissingConfigError, InvalidConfigError |
| Connection | SocketNotFoundError, TlsError, TimeoutError |
| Authentication | InvalidCredentialsError, PermissionDeniedError |
| Validation | InvalidUuidError, InvalidHostError |
| Resource | NotFoundError, InUseError |
| Operation | ScanRunningError, ReportNotReadyError |
| Server | GvmInternalError, GvmUnavailableError |

All errors provide:
- User-friendly message
- Machine-readable code
- CLI hint

---

## Phases

| Phase | Focus | Document |
|-------|-------|----------|
| 1 | Foundation | [phases/PHASE_1.md](phases/PHASE_1.md) |
| 2 | Service Layer | [phases/PHASE_2.md](phases/PHASE_2.md) |
| 3 | MCP Server | [phases/PHASE_3.md](phases/PHASE_3.md) |
| 4 | CLI | [phases/PHASE_4.md](phases/PHASE_4.md) |
| 5 | Testing | [phases/PHASE_5.md](phases/PHASE_5.md) |
| 6 | Documentation | [phases/PHASE_6.md](phases/PHASE_6.md) |

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `python-gvm` | GMP protocol |
| `mcp` | MCP SDK |
| `typer` | CLI framework |
| `pydantic` | Models |
| `rich` | CLI formatting |

---

## Versioning

**CalVer:** `YYYY.0M.MICRO` (e.g., 2025.03.0)
