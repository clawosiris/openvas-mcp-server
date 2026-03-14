# Project Journal: Building an MCP Server with AI

_How we built a complete MCP server for Greenbone Vulnerability Management using human-AI collaboration._

---

## The Goal

Build an MCP (Model Context Protocol) server that exposes Greenbone Vulnerability Management (GVM/OpenVAS) operations as tools for AI agents. The server needed to:

- Enable AI agents to perform vulnerability scanning and management
- Use `python-gvm` directly (not shell out to CLI tools)
- Provide structured JSON responses
- Support both Unix socket and TLS connections
- Include a CLI for human operators

**Architecture:**
```
MCP Client (Claude, OpenClaw, etc.)
    ↓ MCP Protocol (JSON-RPC)
OpenVAS MCP Server
    ↓ python-gvm
GMP Protocol (XML)
    ↓
gvmd (Greenbone Vulnerability Manager)
```

---

## How We Worked Together

The development followed a consistent pattern:

1. **Human provides direction** — high-level goals, constraints, decisions on scope
2. **AI implements** — writes code, tests, docs; follows established patterns
3. **Human reviews** — PRs, course corrections, architectural decisions
4. **Iterate** — refine based on feedback, then move to next phase

The human stayed in the driver's seat for _what_ to build and _why_. The AI handled the _how_ — translating requirements into working code, maintaining consistency across the codebase, and handling the repetitive parts of implementation.

---

## Development Log

### Starting Point: The Spec

**Human:** Filed an issue with a detailed specification:
- ~25 MCP tools across targets, scans, reports, vulnerabilities, data extraction
- Configuration schema for socket and TLS connections  
- Test requirements (unit, integration, mocks)
- Key constraint: use `python-gvm` directly, not CLI wrappers

This spec was the foundation. Having clear requirements upfront made the AI implementation much more effective — less back-and-forth on basic decisions, more focus on execution.

---

### Phase 1: Foundation

**Human:** "Start with the foundation — project scaffold, configuration loading, GVM client abstraction, error handling."

**AI Work:**
- Created project structure with Poetry, Ruff, Mypy, Pytest
- Implemented GVM client layer with factory pattern:
  - `LocalConnection` (Unix socket)
  - `RemoteConnection` (TLS)
- Built configuration loader supporting env vars and TOML config files
- Created structured error hierarchy
- Added XML-to-dict utilities for parsing GMP responses
- Wrote 34 unit tests

**Why this worked:** The human gave a clear scope ("foundation") and the AI filled in the implementation details. The AI could make reasonable decisions about structure (factory pattern, error hierarchy) without needing approval for every choice.

---

### Architecture Refinements

**Human:** "Review the CLI UI interactions. Let's see mockups for first-run setup and command output."

**AI Work:** Created mockups showing:
- First-run configuration wizard
- Help output with Rich formatting
- Table and JSON output modes

**Human:** "Simplify — just local and remote connection modes, remove SSH tunneling. Also, remove idle timeout; retry only on error."

**AI Work:** Updated architecture docs, removed SSH tunnel code path, simplified retry logic.

**Why this worked:** The human spotted complexity that wasn't needed. Quick course correction before it got baked into implementation.

---

### Phase 2: Target Service

**Human:** "Implement target management — CRUD operations for scan targets."

**AI Work:**
- Created `TargetService` with list/get/create/update/delete methods
- Built Pydantic models for validation
- Wired MCP tools: `gvm_list_targets`, `gvm_create_target`, etc.
- Added CLI commands: `openvas target list`, `openvas target create`, etc.
- Wrote unit tests

This established the pattern for all subsequent services: Service class → Pydantic models → MCP tools → CLI commands → Tests.

---

### Phase 3: Scan/Task Service

**Human:** "Now the core — scan task management. Create, start, stop, monitor, delete."

**AI Work:**
- Implemented `TaskService` following the established pattern
- Added task lifecycle methods: start, stop, resume
- Wired MCP tools and CLI commands
- Added CalVer tagging, Docker builds, and CLI artifacts to release workflow

**Why this worked:** With the pattern established in Phase 2, the AI could replicate it efficiently. The human just specified _which_ domain to implement next.

---

### Phase 4: Report Service

**Human:** "Reports are key for extraction. Need to get reports, export in multiple formats, extract vulnerability data."

**AI Work:**
- Created `ReportService` with list, get, export, delete methods
- Built report summary extraction (severity counts, host stats)
- Added export formats: PDF, CSV, XML
- Wired MCP tools and CLI

---

### Phase 5: Utility Services

**Human:** "Add the supporting infrastructure — scan configs, port lists, schedules."

**AI Work:**
- Implemented three services in one phase (established patterns made this fast):
  - `ScanConfigService`
  - `PortListService`  
  - `ScheduleService`
- MCP tools and CLI for all three

---

### Phase 6: Extended Services

**Human:** "Complete the remaining services — vulnerabilities, notes, overrides, tickets, assets, compliance."

**AI Work:**
- Implemented six more services:
  - `VulnerabilityService` — CVE data, NVT search
  - `NoteService` — annotations
  - `OverrideService` — false positive management
  - `TicketService` — remediation tracking
  - `AssetService` — host/OS queries
  - `ComplianceService` — policies and audits
- Consolidated documentation into single status file

---

## What We Built

**13 service domains**, each with:
- Service class with business logic
- Pydantic models for validation
- MCP tools for AI agents
- CLI commands for human operators
- Unit tests

| Service | MCP Tools | CLI | Tests |
|---------|-----------|-----|-------|
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

**CI/CD:** Ruff linting, Mypy strict typing, Pytest coverage, CalVer releases, Docker images to GHCR.

---

## What Worked Well

### 1. Clear Spec Upfront
The detailed issue with tool definitions, config schema, and test requirements gave the AI a clear target. Less ambiguity = better output.

### 2. Phased Development
Breaking the work into phases with clear boundaries (foundation → targets → scans → reports → utilities → extended) made progress visible and review manageable.

### 3. Pattern Establishment
Phase 2 (targets) established the pattern. Phases 3–6 followed it. The AI is good at replicating patterns consistently — this played to its strengths.

### 4. Human Stays on Architecture
The human made the architectural calls (simplify connection modes, remove idle timeout). The AI implemented. This division worked well.

### 5. PR-Based Review
Each phase went through PR review. The human could course-correct before code got merged. Standard development workflow, just with AI as the implementer.

---

## What Could Be Better

### Integration Testing
Unit tests are solid, but integration tests against a real GVM instance are still TODO. The AI can write mocks, but validating against real GMP responses needs a live environment.

### Deep Domain Knowledge
The AI knows the GMP protocol from docs, but a human with operational GVM experience would catch edge cases faster. The "deep review" phase exists for this reason.

---

## Remaining Work

- [ ] Validate services against live GVM instance
- [ ] Integration tests with Docker Compose environment
- [ ] CLI UX polish (error messages, edge cases)
- [ ] Documentation examples and troubleshooting

---

## Takeaways for Developers

1. **Write good specs.** The more detail you give upfront, the less back-and-forth later.

2. **Establish patterns early.** Get one service working the way you want, then let the AI replicate it.

3. **Stay in control of architecture.** Let the AI implement, but make the structural decisions yourself.

4. **Use standard workflows.** PRs, CI, code review — all work fine with AI as implementer.

5. **Know what AI is bad at.** Deep domain expertise, integration testing against real systems, UX intuition — keep human eyes on these.

---

## Links

- **Repository:** https://github.com/clawosiris/openvas-mcp-server
- **Original Spec:** https://codeberg.org/llnvd/gvm-tools/issues/1
- **python-gvm:** https://github.com/greenbone/python-gvm
- **MCP Specification:** https://modelcontextprotocol.io/
