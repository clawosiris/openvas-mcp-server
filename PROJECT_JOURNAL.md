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

## Latest Update (2026-03-27)

### What changed since the last journal entry

Work since the March 20 journal update focused on making integration tests reliable in CI and hardening the automation supply chain.

**Integration testing with mock GVM server:**
- Added integration tests using `gvm-mock-server`
- Added a dedicated CI workflow to run those tests
- Switched from in-workflow builds to using pre-built mock-server release artifacts for faster, more predictable CI
- Fixed test and fixture cleanup/details (`conftest.py` formatting and minor test code cleanup)

**CI/security/release pipeline updates:**
- Pinned third-party GitHub Actions to commit SHAs (supply-chain hardening)
- Updated CI auth usage to rely on `RELEASE_TOKEN` for private-repo access in relevant steps
- Continued release/workflow cleanup in open PRs (removing older standalone release workflows)

**Notable bugfixes in the same window (already merged earlier in this phase):**
- Fixed `alive_test` target handling by passing a string value instead of version-specific enum behavior
- Improved GMP protocol version handling (`determine_supported_gmp()` path)
- Reduced MCP token overhead by disabling structured content where it was unnecessarily expensive

### Open issues and PR snapshot

**Open issue:**
- #39: _Architecture: use released gvm-mock-server artifacts (GHCR image) for integration tests_ — now partially/mostly addressed by recent CI integration-test work, but should be reconciled with final architecture choice and documented closure criteria.

**Open PRs (as of this update):**
- #48: remove old standalone release workflows
- #47: add dated journal entry file (`journal/2026-03-23.md`)
- Dependabot updates for CI actions and Python dependencies: #45, #44, #43, #38, #37, #11, #7

### Decisions captured

- Integration tests should use a reproducible mock-server path in CI rather than ad-hoc local build logic.
- CI security posture should prefer pinned action SHAs.
- Token usage/cost in MCP responses is an explicit optimization concern (structured output kept off where it does not add value).

### Next steps

- Merge and validate the release-workflow cleanup PR (#48), then confirm no regressions in tag/release paths.
- Triage and batch Dependabot PRs (CI actions first, then Python deps), with compatibility checks for Typer/Ruff/Rich major/minor jumps.
- Close or update issue #39 with explicit "done" criteria based on current mock-server integration approach.
- Decide whether journaling is now canonical in `PROJECT_JOURNAL.md`, `journal/YYYY-MM-DD.md`, or both, and document that convention.
- Run/expand integration coverage against realistic GMP response scenarios now that CI plumbing is in place.

## Latest Update (2026-04-01)

### What changed since the last journal entry

One significant addition since the March 27 update:

**Rust port specification (2026-03-31):**
- Added comprehensive spec for porting the Python MCP server to Rust (`docs/rust-mcp-server-spec.md`)
- 2,500+ line document covering:
  - All 54 MCP tools mapped to `rust-gvm` commands (100% coverage)
  - Full architecture diagrams comparing Python and Rust stacks
  - 6-week implementation plan with phased milestones
  - CI/CD, testing, and deployment guidance
  - Migration guide for users moving from Python to Rust version
- Motivation: type safety, async-first concurrency, single-binary distribution, compile-time error checking
- Status: Draft, ready for team review

### Open issues and PR snapshot

**Open issue:**
- #39: _Architecture: use released gvm-mock-server artifacts (GHCR image) for integration tests_ — still open, criteria to close should be documented

**Open PRs (9 total):**
- #49: bump codecov/codecov-action from 4.6.0 to 6.0.0 (new since last update)
- #48: remove old standalone release workflows
- #47: add dated journal entry file (`journal/2026-03-23.md`)
- #45: bump actions/setup-python from 5.6.0 to 6.2.0
- #44: bump docker/build-push-action from 5.4.0 to 7.0.0
- #38: update rich from ^13.0 to ^14.3
- #37: update ruff from ^0.4 to ^0.15
- #11: update typer from ^0.12 to ^0.24
- #7: bump python from 3.12-slim to 3.14-slim

### Decisions captured

- Rust port is the strategic direction for the MCP server — better type safety, async performance, and single-binary distribution
- `rust-gvm` will replace `python-gvm` as the GMP backend
- GMP versions below 22.4 will not be supported in the Rust version
- Tool signatures will remain identical for backwards compatibility with existing MCP clients

### Next steps

- Team review of Rust port specification (docs/rust-mcp-server-spec.md)
- Decide on go/no-go for Rust port and timeline
- Continue triaging Dependabot PRs (CI actions first, then Python deps)
- Merge workflow cleanup PR (#48) and journal PR (#47)
- Close or update issue #39 with explicit completion criteria

---

## Latest Update (2026-04-27)

### What changed since the last journal entry

There have still been **no new merged commits** since the April 1 documentation updates, so the repository remains unchanged from a source-history perspective.

The maintenance queue is also **effectively unchanged** since the prior visible journal state:

- **No new commits landed** after the previous entry.
- **No open PRs were merged, closed, or newly opened** in the intervening period.
- The repo still has the same **12 open PRs**, headed by the April 20 dependency updates for `ruff` (#57) and `python-gvm` (#56).
- Issue #39 remains open and still looks more like stale tracking/admin debt than active implementation work.

### Open issues and PR snapshot

**Open issue:**
- #39: _Architecture: use released gvm-mock-server artifacts (GHCR image) for integration tests_ — still open; likely needs explicit closure or a narrowed follow-up scope.

**Open PRs (12 total):**
- #57: deps: update `ruff` requirement from `^0.4` to `>=0.4,<0.16`
- #56: deps: update `python-gvm` requirement from `^26.0` to `>=26,<28`
- #55: deps: update `rich` requirement from `^13.0` to `^15.0`
- #54: deps: update `pydantic` requirement from `^2.0` to `^2.12`
- #53: ci: bump `docker/build-push-action` from 5.4.0 to 7.1.0
- #52: ci: bump `softprops/action-gh-release` from 2.6.1 to 3.0.0
- #51: ci: bump `docker/login-action` from 4.0.0 to 4.1.0
- #49: ci: bump `codecov/codecov-action` from 4.6.0 to 6.0.0
- #48: ci: remove old standalone release workflows
- #45: ci: bump `actions/setup-python` from 5.6.0 to 6.2.0
- #11: deps: update `typer` requirement from `^0.12` to `^0.24`
- #7: docker: bump Python base image from `3.12-slim` to `3.14-slim`

### Decisions captured

- The repository remains in the same **maintenance backlog / triage holding pattern** documented in the prior entries.
- Since neither git history nor queue shape changed, the main project signal is now **continued inactivity**, not new technical direction.
- The journal should keep recording these quiet periods clearly so maintainers can distinguish true stasis from missing observation.

### Next steps

- Reduce the open PR queue instead of letting it sit unchanged: batch-review CI PRs (#53, #52, #51, #49, #45) and dependency PRs (#57, #56, #55, #54, #11, #7).
- Resolve #48 so release-workflow cleanup stops lingering as maintenance debt.
- Close or re-scope #39 with explicit remaining acceptance criteria if there is any actual follow-up work left.
- Decide whether the Rust-port specification is active roadmap work or parked design material, and document that status clearly.

---

## Latest Update (2026-05-03)

### What changed since the last journal entry

There are still **no new committed git-history changes** after the April 1 Rust-spec update, and the GitHub queue is **unchanged** from the April 27 snapshot:

- **No new commits** landed on `feat/mock-server-integration-tests` after `06bfb25` (`docs(journal): add 2026-04-01 update - Rust port spec`).
- **No issue or PR churn** was visible in GitHub: issue #39 remains the only open issue, and the same 12 open PRs are still pending.

What *did* change is the local working tree: there is now substantial in-progress implementation work toward the originally requested package layout for a standalone `gvm_mcp` server.

**Local in-progress package work (uncommitted):**
- Added a new top-level `gvm_mcp/` package with the requested structure:
  - `config.py` for env-driven config loading and validation
  - `connection.py` for python-gvm connection management
  - `server.py` as the MCP entry point
  - `tools/` modules for targets, scans, reports, vulnerabilities, and extraction
  - `utils/xml_helpers.py` for XML-to-dict conversion helpers
- Updated `pyproject.toml` to package `gvm_mcp` alongside the existing `src` tree.
- Added a new `gvm-mcp` console script entrypoint pointing at `gvm_mcp.server:main`.
- Added unit tests under `tests/unit/gvm_mcp/` for config loading and XML helper behavior.
- Captured active implementation state in `worklog.md`, including a note that the new package is runnable via `python -m gvm_mcp.server` and intended to coexist with the repository's existing `src` implementation for now.

### Open issues and PR snapshot

**Open issue:**
- #39: _Architecture: use released gvm-mock-server artifacts (GHCR image) for integration tests_ — still open and unchanged.

**Open PRs (12 total, unchanged):**
- #57: deps: update `ruff` requirement from `^0.4` to `>=0.4,<0.16`
- #56: deps: update `python-gvm` requirement from `^26.0` to `>=26,<28`
- #55: deps: update `rich` requirement from `^13.0` to `^15.0`
- #54: deps: update `pydantic` requirement from `^2.0` to `^2.12`
- #53: ci: bump `docker/build-push-action` from 5.4.0 to 7.1.0
- #52: ci: bump `softprops/action-gh-release` from 2.6.1 to 3.0.0
- #51: ci: bump `docker/login-action` from 4.0.0 to 4.1.0
- #49: ci: bump `codecov/codecov-action` from 4.6.0 to 6.0.0
- #48: ci: remove old standalone release workflows
- #45: ci: bump `actions/setup-python` from 5.6.0 to 6.2.0
- #11: deps: update `typer` requirement from `^0.12` to `^0.24`
- #7: docker: bump Python base image from `3.12-slim` to `3.14-slim`

### Decisions captured

- The repository is still externally quiet, but there is now a clear **internal implementation track** for the requested `gvm_mcp` package layout.
- The new `gvm_mcp` package is being added **in parallel** with the existing `src` implementation instead of replacing it immediately, which reduces migration risk while preserving current code paths.
- Packaging and entrypoint wiring now assume the project may need to expose **both** the legacy `openvas-mcp` path and the new `gvm-mcp` path during transition.
- The package design is leaning toward simple env-based configuration with support for both **local socket** and **remote TLS** connection styles.

### Next steps

- Commit the in-progress `gvm_mcp` package work so it becomes part of project history rather than only local state.
- Expand unit coverage beyond config/XML helpers into tool modules and report/extraction edge cases.
- Validate the new package in an environment with the full Python test toolchain installed; the current container does not have `pytest` available.
- Clean up generated `__pycache__` artifacts before commit if they are not meant to be tracked.
- Continue triaging the unchanged PR queue and decide whether issue #39 should be closed, narrowed, or explicitly tied to the new package work.

---

## Links

- **Repository:** https://github.com/clawosiris/openvas-mcp-server
- **Original Spec:** https://codeberg.org/llnvd/gvm-tools/issues/1
- **python-gvm:** https://github.com/greenbone/python-gvm
- **MCP Specification:** https://modelcontextprotocol.io/
