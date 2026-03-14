# Project Journal

Development log for the OpenVAS MCP Server — an AI-assisted build.

---

## Project Origin

**Human Input:** Daniel Riek filed [Issue #1 on Codeberg](https://codeberg.org/llnvd/gvm-tools/issues/1) with a detailed specification for building an MCP server that exposes Greenbone Vulnerability Management operations to AI agents. The spec included:

- Target architecture: MCP Client → GVM MCP Server → python-gvm → GMP → gvmd
- ~25 tool definitions across targets, scans, reports, vulnerabilities, and data extraction
- Configuration schema supporting Unix socket and TLS connections
- Test requirements (unit, integration, mocks)
- A focus on **data extraction and reporting** — enabling agents to prioritize remediation, compare reports, and generate executive summaries

**Key Constraint:** Use `python-gvm` directly for native GMP protocol handling. Do NOT shell out to `gvm-cli`.

---

## Development Log

### Phase 1: Foundation

**Human Input:** "Start with the foundation — project scaffold, configuration loading, GVM client abstraction, error handling."

**Work Done:**
- Created project structure: `src/`, `tests/`, `docs/`, CI workflows
- Set up Poetry with Ruff (linting), Mypy (strict typing), Pytest
- Implemented GVM client layer with factory pattern:
  - `LocalConnection` (Unix socket via `UnixSocketConnection`)
  - `RemoteConnection` (TLS via `TLSConnection`)
- Built configuration loader supporting:
  - Environment variables (`GVM_STYLE`, `GVM_SOCKET_PATH`, `GVM_USERNAME`, etc.)
  - TOML config file (`~/.config/openvas-mcp/config.toml`)
- Created structured error hierarchy (`GVMError`, `ConnectionError`, `AuthenticationError`, `ValidationError`, etc.)
- Added XML-to-dict helper utilities for parsing GMP responses
- Wrote 34 unit tests for infrastructure layer

**PR:** [#1 — Phase 1: Foundation](https://github.com/clawosiris/openvas-mcp-server/pull/1)

---

### Architecture Decisions

**Human Input:** "Review the CLI UI interactions. Let's see mockups for first-run setup, help, and command output."

**Work Done:**
- Created `docs/CLI_UI_REVIEW.md` with mockups for:
  - First-run configuration wizard
  - Help output with Rich formatting
  - Table output for list commands
  - JSON output mode
- Decided on `openvas` CLI command name (not `gvm` to avoid conflict with existing tools)
- Designed `openvas configure` interactive setup and `openvas test` connection validation

**Human Input:** "Simplify the connection modes — just local and remote, remove SSH tunneling. Also, remove idle timeout; retry should only trigger on error."

**Work Done:**
- Removed SSH tunnel connection type from architecture docs
- Simplified retry logic: no delay parameters, just `max_attempts` with retry-on-error
- Updated `docs/ARCHITECTURE.md` to reflect simplified design

---

### Phase 2: Target Service

**Human Input:** "Implement target management — CRUD operations for scan targets."

**Work Done:**
- Created `TargetService` with methods:
  - `list_targets()` — list all targets with filtering
  - `get_target(id)` — get target details
  - `create_target(name, hosts, port_list_id, ...)` — create new target
  - `update_target(id, ...)` — modify existing target
  - `delete_target(id)` — remove target
- Built Pydantic models: `Target`, `TargetCreate`, `TargetUpdate`
- Wired MCP tools: `gvm_list_targets`, `gvm_get_target`, `gvm_create_target`, `gvm_delete_target`
- Added CLI commands: `openvas target list`, `openvas target get`, `openvas target create`, etc.
- Wrote unit tests for service layer

**PR:** [#13 — Phase 2: Target Service](https://github.com/clawosiris/openvas-mcp-server/pull/13)

---

### System Service (Interlude)

**Human Input:** "Add a system/version endpoint so agents can verify connectivity and GVM version."

**Work Done:**
- Created `SystemService` with `get_version()` method
- Exposed `gvm_get_version` MCP tool
- Added `openvas system version` CLI command
- Set up manual release trigger in CI workflow

**PR:** [#14 — System Service](https://github.com/clawosiris/openvas-mcp-server/pull/14)

---

### Phase 3: Scan/Task Service

**Human Input:** "Now the core — scan task management. Create, start, stop, monitor, delete."

**Work Done:**
- Created `TaskService` with methods:
  - `list_tasks()` — list all scan tasks
  - `get_task(id)` — get task details with status
  - `create_task(name, target_id, config_id, ...)` — create scan task
  - `start_task(id)` — launch scan
  - `stop_task(id)` — abort running scan
  - `resume_task(id)` — resume stopped scan
  - `delete_task(id)` — remove task
- Built Pydantic models: `Task`, `TaskStatus`, `TaskCreate`
- Wired MCP tools: `gvm_list_scans`, `gvm_start_scan`, `gvm_stop_scan`, `gvm_get_scan_status`
- Added CLI commands: `openvas scan list`, `openvas scan start <id>`, etc.
- Added CalVer tagging to release workflow
- Added Docker image build/push to CI
- Added CLI artifact uploads

**PR:** [#15 — Phase 3: Scan Service](https://github.com/clawosiris/openvas-mcp-server/pull/15)

---

### Phase 4: Report Service

**Human Input:** "Reports are key for extraction. Need to get reports, export in multiple formats, and extract vulnerability data."

**Work Done:**
- Created `ReportService` with methods:
  - `list_reports()` — list all reports with filters
  - `get_report(id)` — get full report with results
  - `get_report_summary(id)` — severity counts and host stats
  - `export_report(id, format)` — export as PDF, CSV, XML, etc.
  - `delete_report(id)` — remove report
- Built models: `Report`, `ReportResult`, `ReportSummary`
- Wired MCP tools: `gvm_list_reports`, `gvm_get_report`, `gvm_export_report`
- Added CLI: `openvas report list`, `openvas report export <id> --format pdf`

**PR:** [#16 — Phase 4: Report Service](https://github.com/clawosiris/openvas-mcp-server/pull/16)

---

### Phase 5: Utility Services

**Human Input:** "Add the supporting infrastructure — scan configs, port lists, schedules."

**Work Done:**
- **ScanConfigService**: List and manage scan configurations
- **PortListService**: CRUD for port list definitions
- **ScheduleService**: Create and manage scheduled scans
- MCP tools and CLI commands for all three
- Maintained consistent patterns from earlier phases

**PR:** [#17 — Phase 5: Utility Services](https://github.com/clawosiris/openvas-mcp-server/pull/17)

---

### Phase 6: Vulnerability & Extended Services

**Human Input:** "Complete the remaining services from the spec — vulnerabilities, notes, overrides, tickets, assets, compliance."

**Work Done:**
- **VulnerabilityService**: Query CVE data, search NVTs, extract vuln details
- **NoteService**: Add/manage annotations on vulnerabilities
- **OverrideService**: False positive management
- **TicketService**: Remediation tracking
- **AssetService**: Host and OS asset queries
- **ComplianceService**: Policy and audit management
- Consolidated all phase docs into single `IMPLEMENTATION_STATUS.md`
- Aligned usage docs with implemented commands

**PRs:** [#18](https://github.com/clawosiris/openvas-mcp-server/pull/18), [#19](https://github.com/clawosiris/openvas-mcp-server/pull/19)

---

## Implementation Summary

All 13 service domains from the original spec are implemented:

| Service | Description | MCP Tools | CLI | Tests |
|---------|-------------|-----------|-----|-------|
| System | Version/status | ✅ | ✅ | ✅ |
| Target | Scan targets | ✅ | ✅ | ✅ |
| Task | Scan execution | ✅ | ✅ | ✅ |
| Report | Results & export | ✅ | ✅ | ✅ |
| Vulnerability | CVE/NVT data | ✅ | ✅ | ✅ |
| Scan Config | Scan profiles | ✅ | ✅ | ✅ |
| Port List | Port definitions | ✅ | ✅ | ✅ |
| Schedule | Recurring scans | ✅ | ✅ | ✅ |
| Note | Annotations | ✅ | ✅ | ✅ |
| Override | False positives | ✅ | ✅ | ✅ |
| Ticket | Remediation | ✅ | ✅ | ✅ |
| Asset | Hosts/OS | ✅ | ✅ | ✅ |
| Compliance | Policies/audits | ✅ | ✅ | ✅ |

---

## Remaining Work

Deep review and hardening (per original spec):

- [ ] Validate each service against real GMP responses from live gvmd
- [ ] Verify each MCP tool contract with actual MCP client testing
- [ ] CLI UX review — flag consistency, help text, error messages
- [ ] Integration tests with Docker Compose GVM environment
- [ ] Documentation polish — examples, troubleshooting, edge cases

---

## CI/CD

- **Linting:** Ruff
- **Typing:** Mypy (strict)
- **Tests:** Pytest with coverage
- **Releases:** CalVer tagging, manual dispatch
- **Artifacts:** Docker images to GHCR, CLI wheel uploads

---

## Related Repositories

- **GitHub (this repo):** https://github.com/clawosiris/openvas-mcp-server
- **Codeberg (original):** https://codeberg.org/llnvd/gvm-tools

---

## References

- [python-gvm](https://github.com/greenbone/python-gvm) — Official Greenbone Python library
- [MCP Specification](https://modelcontextprotocol.io/) — Model Context Protocol
- [GMP Protocol](https://docs.greenbone.net/API/GMP/gmp.html) — Greenbone Management Protocol
- [Greenbone Documentation](https://greenbone.github.io/docs/)
