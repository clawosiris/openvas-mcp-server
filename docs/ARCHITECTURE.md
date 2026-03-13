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

## Folder Structure

```
openvas-mcp-server/
│
├── .github/
│   ├── workflows/
│   │   ├── ci.yml              # Build, test, lint
│   │   ├── release.yml         # Release pipeline
│   │   └── docker.yml          # Docker build/push
│   └── dependabot.yml          # Dependency updates
│
├── docs/
│   ├── ARCHITECTURE.md         # This document
│   ├── phases/                 # Phase documents
│   ├── cli/
│   │   ├── installation.md
│   │   ├── usage.md
│   │   └── development.md
│   └── mcp/
│       ├── installation.md
│       ├── usage.md
│       └── development.md
│
├── src/
│   └── src/
│       ├── __init__.py
│       │
│       ├── infrastructure/
│       │   ├── __init__.py
│       │   ├── config.py           # Configuration loading
│       │   └── client/
│       │       ├── __init__.py
│       │       ├── base.py         # Abstract GvmClient
│       │       ├── local.py        # LocalClient (Unix socket)
│       │       ├── remote.py       # RemoteClient (TLS)
│       │       └── factory.py      # Client factory
│       │
│       ├── services/
│       │   ├── __init__.py
│       │   ├── targets/
│       │   │   ├── __init__.py
│       │   │   ├── models.py       # Target, TargetCreateRequest, etc.
│       │   │   └── service.py      # TargetService
│       │   ├── tasks/
│       │   │   ├── __init__.py
│       │   │   ├── models.py
│       │   │   └── service.py
│       │   ├── reports/
│       │   │   ├── __init__.py
│       │   │   ├── models.py
│       │   │   └── service.py
│       │   ├── vulnerabilities/
│       │   ├── notes/
│       │   ├── overrides/
│       │   ├── alerts/
│       │   ├── credentials/
│       │   ├── schedules/
│       │   ├── policies/
│       │   ├── audits/
│       │   ├── tickets/
│       │   ├── assets/
│       │   ├── scan_configs/
│       │   ├── filters/
│       │   ├── tags/
│       │   ├── users/
│       │   ├── roles/
│       │   ├── permissions/
│       │   ├── groups/
│       │   ├── port_lists/
│       │   ├── scanners/
│       │   ├── nvts/
│       │   ├── secinfo/
│       │   ├── feeds/
│       │   └── system/
│       │       ├── __init__.py
│       │       ├── models.py
│       │       └── service.py
│       │
│       ├── presentation/
│       │   ├── __init__.py
│       │   ├── mcp/
│       │   │   ├── __init__.py
│       │   │   ├── server.py       # MCP entry point
│       │   │   └── toolsets/
│       │   │       ├── __init__.py
│       │   │       ├── targets.py
│       │   │       ├── tasks.py
│       │   │       ├── reports.py
│       │   │       └── ...
│       │   └── cli/
│       │       ├── __init__.py
│       │       ├── main.py         # CLI entry point
│       │       ├── config.py       # CLI config handling
│       │       └── commands/
│       │           ├── __init__.py
│       │           ├── configure.py
│       │           ├── targets.py
│       │           ├── tasks.py
│       │           ├── reports.py
│       │           └── ...
│       │
│       ├── errors.py               # Exception hierarchy
│       │
│       └── utils/
│           ├── __init__.py
│           ├── validators.py       # Input validation
│           └── xml_helpers.py      # XML to model conversion
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                 # Shared fixtures
│   ├── infrastructure/
│   │   ├── __init__.py
│   │   ├── test_config.py
│   │   └── test_client.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── test_targets.py
│   │   └── ...
│   └── presentation/
│       ├── __init__.py
│       ├── mcp/
│       └── cli/
│
├── Dockerfile                      # MCP server Docker image
├── docker-compose.yml              # Dev environment
├── pyproject.toml                  # Poetry config
├── poetry.lock
├── README.md
├── LICENSE
└── .gitignore
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
