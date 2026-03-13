# OpenVAS MCP Server — Roadmap

**Status:** Planning  
**Date:** 2026-03-12

---

## Overview

This project provides an MCP (Model Context Protocol) server for OpenVAS/Greenbone Vulnerability Management, enabling AI agents to interact with GVM for vulnerability scanning, compliance auditing, and security management.

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Presentation Layer                          │
│              ┌─────────┐  ┌─────────┐  ┌─────────┐              │
│              │   MCP   │  │   CLI   │  │  Future │              │
│              │ Server  │  │         │  │ (gRPC?) │              │
│              └────┬────┘  └────┬────┘  └────┬────┘              │
└───────────────────┼────────────┼────────────┼───────────────────┘
                    │            │            │
┌───────────────────┼────────────┼────────────┼───────────────────┐
│                   ▼            ▼            ▼                   │
│                      Service Layer                              │
│   ┌──────────────┐ ┌──────────────┐ ┌──────────────┐           │
│   │TargetService │ │ ScanService  │ │ReportService │ ...       │
│   └──────┬───────┘ └──────┬───────┘ └──────┬───────┘           │
│          │                │                │                    │
│          └────────────────┼────────────────┘                    │
│                           ▼                                     │
│                    ┌─────────────┐                              │
│                    │   Client    │                              │
│                    │   Layer     │                              │
│                    └──────┬──────┘                              │
└───────────────────────────┼─────────────────────────────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │  python-gvm  │  (external dependency)
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │    gvmd      │  (GVM daemon)
                    └──────────────┘
```

---

## Phase 1: Foundation (Week 1)

### 1.1 Project Scaffold
- [ ] Repository structure setup
- [ ] Poetry/pyproject.toml configuration
- [ ] Development tooling (ruff, mypy, pytest)
- [ ] CI/CD setup (GitHub Actions)

### 1.2 Client Layer
- [ ] Abstract GvmClient base class
- [ ] LocalClient implementation (Unix socket)
- [ ] RemoteClient implementation (TLS)
- [ ] Client factory for config-based instantiation
- [ ] Connection management with retry (exponential backoff)
- [ ] Auto-reconnect on failure + idle timeout
- [ ] RLock with timeout (no pooling)

### 1.3 Configuration (see docs/CONFIGURATION.md)

**Connection Styles:**
- [ ] `local` — Unix socket to local gvmd
- [ ] `remote` — TLS connection to remote gvmd

**Local (Unix Socket) Parameters:**
| Parameter | Type | Default |
|-----------|------|---------|
| `socket_path` | str | `/run/gvmd/gvmd.sock` |

**Remote (TLS) Parameters:**
| Parameter | Type | Default |
|-----------|------|---------|
| `hostname` | str | required |
| `port` | int | `9390` |
| `certfile` | str | optional (client cert) |
| `cafile` | str | optional (CA cert) |
| `keyfile` | str | optional (client key) |
| `key_password` | str | optional |

**Common Parameters (all styles):**
| Parameter | Type | Default |
|-----------|------|---------|
| `gmp_username` | str | required |
| `gmp_password` | str | required |
| `timeout` | int | `60` |
| `retry_max_attempts` | int | `3` |

**Configuration Sources:**
- [ ] Environment variables (for MCP installation)
- [ ] TOML config file (for CLI persistence)
- [ ] Interactive prompt (CLI first-run)

### 1.4 Error Handling (see docs/ERROR_HANDLING.md)
- [ ] Custom exception hierarchy (22 error types)
  - ConfigurationError, ConnectionError, AuthenticationError
  - ValidationError, ResourceError, OperationError, ServerError
- [ ] User-friendly error messages (no internal leakage)
- [ ] CLI hints for actionable feedback
- [ ] GMP status code → custom error mapping
- [ ] `translate_gvm_error()` helper function

### 1.5 Core DTOs/Models
- [ ] Define domain models (Target, Scan, Report, etc.)
- [ ] Pydantic models for requests/responses
- [ ] XML → Model mapping utilities
- [ ] Model → JSON serialization

---

## Phase 2: Service Layer (Week 1-2)

### 2.1 Target Service
- [ ] `list_targets(filter: str) -> list[Target]`
- [ ] `get_target(id: str) -> Target`
- [ ] `create_target(name: str, hosts: list[str], ...) -> Target`
- [ ] `delete_target(id: str) -> bool`

### 2.2 Scan Service
- [ ] `list_scans(filter: str) -> list[Scan]`
- [ ] `create_scan(name: str, target_id: str, config_id: str) -> Scan`
- [ ] `start_scan(id: str) -> bool`
- [ ] `stop_scan(id: str) -> bool`
- [ ] `get_scan_status(id: str) -> ScanStatus`

### 2.3 Report Service
- [ ] `list_reports(filter: str) -> list[Report]`
- [ ] `get_report(id: str) -> Report`
- [ ] `get_report_summary(id: str) -> ReportSummary`
- [ ] `export_report(id: str, format: str) -> bytes`

### 2.4 Vulnerability Service
- [ ] `list_vulnerabilities(report_id: str) -> list[Vulnerability]`
- [ ] `get_vulnerability(id: str) -> Vulnerability`
- [ ] `search_nvts(query: str) -> list[NVT]`

### 2.5 Note/Override Service
- [ ] CRUD operations for notes
- [ ] CRUD operations for overrides

### 2.6 Compliance Service
- [ ] `list_policies() -> list[Policy]`
- [ ] `list_audits() -> list[Audit]`
- [ ] `start_audit(target_id: str, policy_id: str) -> Audit`
- [ ] `get_compliance_status(target_id: str) -> ComplianceStatus`

### 2.7 Ticket Service
- [ ] CRUD operations for remediation tickets

### 2.8 Asset Service
- [ ] `list_host_assets() -> list[HostAsset]`
- [ ] `list_os_assets() -> list[OSAsset]`
- [ ] `list_tls_certificates() -> list[TLSCertificate]`

### 2.9 System Service
- [ ] `get_version() -> VersionInfo`
- [ ] `get_status() -> SystemStatus`
- [ ] `list_scan_configs() -> list[ScanConfig]`
- [ ] `list_port_lists() -> list[PortList]`
- [ ] `list_credentials() -> list[Credential]`

---

## Phase 3: MCP Server (Week 2)

### 3.1 MCP Tool Registration
- [ ] Set up FastMCP server
- [ ] Register tools for each service method
- [ ] Input validation decorators
- [ ] Error handling / safe responses

### 3.2 Tool Categories
- [ ] Target tools (4)
- [ ] Scan tools (5)
- [ ] Report tools (4)
- [ ] Vulnerability tools (3)
- [ ] Note/Override tools (8)
- [ ] Compliance tools (6)
- [ ] Ticket tools (4)
- [ ] Asset tools (3)
- [ ] System tools (5)
- [ ] Extraction/Analysis tools (5)

**Total: ~47 MCP tools**

---

## Phase 4: CLI (Week 2-3)

### 4.1 CLI Framework
- [ ] Set up Click/Typer CLI structure
- [ ] Subcommand organization (gvm targets, gvm scans, etc.)
- [ ] Output formatting (table, JSON, YAML)
- [ ] Configuration file support

### 4.2 CLI Commands
- [ ] Mirror all service operations as CLI commands
- [ ] Interactive prompts where appropriate
- [ ] Progress indicators for long operations

---

## Phase 5: Testing (Ongoing)

### 5.1 Unit Tests
- [ ] Service layer tests (mocked client)
- [ ] Client layer tests (mocked python-gvm)
- [ ] Validation tests
- [ ] Model/DTO tests
- [ ] Target: >80% coverage

### 5.2 Integration Tests
- [ ] Docker Compose with GVM + vulnerable targets
- [ ] Lifecycle tests (target → scan → report)
- [ ] MCP protocol compliance tests
- [ ] See: INTEGRATION_TEST_SPEC.md (from Codeberg repo)

---

## Phase 6: Documentation (Week 3)

### 6.1 User Documentation
- [ ] README with quick start
- [ ] Installation guide
- [ ] Configuration reference
- [ ] MCP tool reference
- [ ] CLI command reference

### 6.2 Developer Documentation
- [ ] Architecture overview
- [ ] Contributing guide
- [ ] API documentation

---

## Migration from Codeberg Implementation

The existing implementation at https://codeberg.org/llnvd/gvm-tools contains:

### Reusable Components
- **Validation logic** (`utils/validation.py`) — UUID, filter string, host validation
- **XML helpers** (`utils/xml_helpers.py`) — XML to dict/JSON conversion
- **Error handling** (`utils/errors.py`) — `@safe_tool` decorator pattern
- **Test specifications** — TEST_SPEC.md, INTEGRATION_TEST_SPEC.md
- **Security patterns** — Input sanitization, TLS config, credential handling

### Requires Refactoring
- **Tool implementations** — Logic moves to service layer
- **Connection management** — Becomes client layer

### Migration Steps
1. Set up new project structure with layered architecture
2. Port validation utilities (minimal changes)
3. Create client layer from connection.py
4. Extract service logic from tools/*.py into services
5. Create thin MCP tool adapters
6. Port and adapt tests
7. Add CLI layer

---

## Resources

### Existing Work
- Codeberg repo: https://codeberg.org/llnvd/gvm-tools/src/branch/main/gvm_mcp
- TEST_SPEC.md: Unit test specification
- INTEGRATION_TEST_SPEC.md: Integration test specification with Docker setup

### Dependencies
- `python-gvm` — Official Greenbone Python library
- `mcp` — MCP SDK for Python
- `click` or `typer` — CLI framework

### References
- [python-gvm docs](https://python-gvm.readthedocs.io/)
- [MCP specification](https://modelcontextprotocol.io/)
- [Greenbone Community Edition](https://greenbone.github.io/docs/)

---

## Timeline Summary

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| Phase 1: Foundation | 3-4 days | Client layer, DTOs, project setup |
| Phase 2: Services | 4-5 days | All service implementations |
| Phase 3: MCP | 2-3 days | MCP server with 47 tools |
| Phase 4: CLI | 3-4 days | Full CLI implementation |
| Phase 5: Testing | Ongoing | >80% coverage |
| Phase 6: Docs | 2-3 days | Complete documentation |

**Estimated total: 2-3 weeks to feature parity + CLI**

---

## Next Steps

1. [ ] Recep pushes scaffold with layered architecture structure
2. [ ] Review and finalize service interfaces
3. [ ] Begin Phase 1 implementation
4. [ ] Iterate based on feedback
