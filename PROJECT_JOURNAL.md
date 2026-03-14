# Project Journal

Development log for the OpenVAS MCP Server project.

---

## 2026-03-14 — Project Journal Created

Created this journal to document the development history and decisions made during the build of the OpenVAS MCP Server.

---

## Project Summary

This project delivers an **MCP (Model Context Protocol) server** that exposes Greenbone Vulnerability Management (GVM/OpenVAS) operations as tools for AI agents. It also includes a standalone **CLI** for human operators.

### Architecture

```
MCP Client → OpenVAS MCP Server → python-gvm → GMP Protocol → gvmd
```

The server uses `python-gvm` directly for native GMP protocol handling, avoiding shell-outs to `gvm-cli`.

---

## Development Timeline

### Phase 1: Foundation
- Project scaffold with `src/`, `tests/`, docs, CI workflows
- Poetry setup with Ruff (linting), Mypy (types), Pytest (testing)
- GVM client layer supporting both local (Unix socket) and remote (TLS) connections
- Configuration loading from environment variables and config files
- Error hierarchy and XML helper utilities

### Phase 2: Target Service
- Target CRUD operations (create, list, get, update, delete)
- MCP tools and CLI commands for target management
- Unit tests for target service layer

### Phase 3: Scan/Task Service
- Task/scan management (create, start, stop, resume, delete)
- Scan status monitoring and control
- MCP tools and CLI commands for scan operations

### Phase 4: Report Service
- Report retrieval and export
- Multiple export formats support
- Vulnerability extraction from reports

### Phase 5: Utility Services
- **Scan Config Service**: Scan configuration management
- **Port List Service**: Port list CRUD operations
- **Schedule Service**: Scheduled scan management

### Phase 6: Vulnerability & Extended Services
- **Vulnerability Service**: CVE data, vulnerability queries
- **Note Service**: Annotation management
- **Override Service**: False positive handling
- **Ticket Service**: Remediation tracking
- **Asset Service**: Host/OS asset management
- **Compliance Service**: Policy and audit operations

### Release Infrastructure
- CalVer tagging for versioned releases
- Docker image build/push in release workflow
- CLI artifact uploads in CI pipeline
- Manual dispatch support for releases

---

## Implementation Status

All planned service domains are implemented:

| Service | MCP Tools | CLI Commands | Tests |
|---------|-----------|--------------|-------|
| System | ✅ | ✅ | ✅ |
| Target | ✅ | ✅ | ✅ |
| Task/Scan | ✅ | ✅ | ✅ |
| Report | ✅ | ✅ | ✅ |
| Vulnerability | ✅ | ✅ | ✅ |
| Scan Config | ✅ | ✅ | ✅ |
| Port List | ✅ | ✅ | ✅ |
| Schedule | ✅ | ✅ | ✅ |
| Note | ✅ | ✅ | ✅ |
| Override | ✅ | ✅ | ✅ |
| Ticket | ✅ | ✅ | ✅ |
| Asset | ✅ | ✅ | ✅ |
| Compliance | ✅ | ✅ | ✅ |

---

## Remaining Work

Deep review and hardening:
- [ ] Validate each service against real GMP responses
- [ ] Verify each MCP tool contract in live client testing
- [ ] Verify CLI UX and flag consistency
- [ ] Expand integration tests with real GVM environment
- [ ] Final documentation pass (examples + troubleshooting)

---

## Related Repositories

- **This repo (GitHub)**: https://github.com/clawosiris/openvas-mcp-server
- **gvm-tools (Codeberg)**: https://codeberg.org/llnvd/gvm-tools — Original GVM tools fork where MCP server work began

---

## Links

- [python-gvm](https://github.com/greenbone/python-gvm) — Official Greenbone Python library
- [MCP Specification](https://modelcontextprotocol.io/) — Model Context Protocol
- [GVM Documentation](https://greenbone.github.io/docs/) — Greenbone official docs
