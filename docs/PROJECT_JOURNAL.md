# OpenVAS MCP Server — Project Journal

*Documenting human creative input and project evolution for copyright and educational purposes.*

---

## 2026-03-12: Project Inception

### Participants
- **Daniel Riek** — Project lead, Greenbone
- **Recep Kızılarslan** (@recepkizilarslan) — Developer, Greenbone
- **Osiris** — AI architect/supervisor (OpenClaw agent)

### Context

Daniel and Osiris had been working on a GVM MCP Server implementation on Codeberg (https://codeberg.org/llnvd/gvm-tools). When Recep joined the conversation, he proposed a cleaner layered architecture that would enable code reuse between MCP, CLI, and future interfaces.

### Key Discussion: Architecture

**Recep's proposal:**
> "The client should be a separate layer. Also, that client should itself be wrapped by another layer called the relevant service. The request/response handling and mapping should live there. Then the MCP endpoint would call this service and communicate through it."

**Architecture diagram shared by Recep:**
```
GVM Python Client → Client Layer → Service Layer → MCP Server / CLI / REST
```

**Osiris's analysis:**
> "You're right — the service layer is the correct abstraction. The current implementation has the business logic embedded in MCP tools, which means adding CLI = rewrite the same logic."

### Decision: Start Fresh with Layered Architecture

Rather than refactor the existing Codeberg implementation, the team decided to:
1. Create a new GitHub repo with the layered architecture
2. Use the Codeberg work as reference (specs, tests, patterns)
3. Have Recep scaffold the architecture
4. Have Osiris supervise implementation via Codex/Claude Code

### Repository Created

**Repo:** https://github.com/clawosiris/openvas-mcp-server

**Collaborators:**
- @clawosiris (Osiris) — Owner
- @recepkizilarslan (Recep) — Admin
- @llunved (Daniel) — Admin

### Workflow Established

**Air-gapped approach:**
> Daniel: "The only issue is that we need to keep Osiris air-gapped from any internal Greenbone project."

**Solution:**
```
GitHub (Osiris works here) → Human PR → greenbone/openvas-mcp-server (official)
```

### Roles Defined

> Daniel: "I'd like you to act as the architect and supervisor, task Codex with implementation tasks via ACP and use Claude Code in review mode for code reviews."

**Osiris's role:**
- Architect/Supervisor — Specs, roadmap, architecture decisions
- Implementation via direct coding
- Code reviews via ACP agents when needed

### Notable Quotes

**On code reuse (Recep):**
> "If I embed the entire business into the tool, I'll have to rewrite the code. The service layer will be called by the tools for the MCP. It will also be called within the CLI."

**On AI-assisted development (Daniel):**
> "We could ask Osiris to create a repo, give you access, look at what you push there, then spec out a migration."

---

## 2026-03-13: Implementation Sprint

### Morning Session (06:00–08:30 EDT)

**Human input (Daniel/Recep):** Review and approval of architecture docs, phase structure.

**Work completed:**
- Architecture docs with client abstraction pattern
- Error handling specification
- Configuration reference (env vars + TOML)
- Simplified from 3 connection types to 2 (local/remote only)
- Removed unnecessary complexity (idle timeout, retry delays)
- Created phase-by-phase implementation plan

**Key human decision (Recep):**
> "Remove SSH forwarding — it adds complexity without clear benefit for the initial release."

### Late Morning Session (11:00–12:00 EDT)

**Phase 1 Foundation (PR #1):**
- Project scaffold with Poetry, Ruff, Mypy, Pytest
- GVM client layer (base abstraction + local/remote implementations)
- Configuration loading from environment and TOML files
- Full error hierarchy with structured error details
- XML parsing utilities and validators
- CI/CD workflows (lint, test, docker, release)

**Human review:** Recep approved and merged PR #1.

### Midday Session (12:00–13:00 EDT)

**Rapid phase implementation after human approval of patterns:**

**Phase 2 — Target Service (PR #13):**
- Target models (Target, TargetCreateRequest, TargetListResponse)
- CRUD operations (list, get, create, delete, clone, update)
- MCP tools registered
- CLI commands implemented
- Tests passing

**Human input (Recep):**
> "Add version service in phase 2" — Led to PR #14 for system/version service.

**Phase 3 — Task/Scan Service (PR #15):**
- Task/Scan models with full state tracking
- Operations: create, start, stop, resume, delete, clone
- CalVer release workflow with manual dispatch
- Docker image build in pipeline

**Human input (Recep):**
> "Do it in another branch and open new PR for these" — Separated system service into its own PR.

**Phase 4 — Report Service (PR #16):**
- Report models with vulnerability detail
- Export to PDF/CSV/XML/HTML
- Summary statistics extraction
- 117 tests passing

**Human input (Recep):**
> "Add tagging... I should see in docker image with calver version and cli artifact end of the pipeline"
— Led to enhanced release workflow with auto-tagging, artifact upload, and docker push.

### Afternoon Session (12:30–13:00 EDT)

**Human input (Recep):**
> "Continue lets finish all phase"

**Phases 5-6 — Utility Services:**
- Scan configs, port lists, schedules
- Vulnerability search and NVT lookup
- Notes, overrides, tickets
- Assets (hosts, OS, TLS certs)
- Compliance (policies, audits, status)

**Human input (Recep):**
> "Check phase docs and be sure everything is implemented... Finish everything and remove the step-by-step documents. Create a single document and mark what you've done."

**Documentation consolidation:**
- Removed individual phase docs (PHASE_1..6.md)
- Created single IMPLEMENTATION_STATUS.md
- 138 tests passing

### Final PR

**PR #19:** Complete remaining services + consolidate documentation
- All 13 service domains implemented
- MCP tools: 45+ registered
- CLI commands: all services covered
- Single status doc for review tracking

---

## Human Creative Contributions Summary

### Architecture & Design (Human)
- Layered architecture proposal (Recep)
- Service abstraction pattern (Recep)
- Air-gapped workflow design (Daniel)
- Role separation: architect vs implementer (Daniel)

### Technical Decisions (Human)
- Remove SSH connection type (Recep)
- CalVer versioning scheme (team)
- Strict linting (Ruff + Mypy strict) (Recep)
- Package structure: `src/` flat (Recep)

### Workflow Decisions (Human)
- Separate PRs per phase (Recep)
- System service in own PR (Recep)
- Release workflow enhancements (Recep)
- Documentation consolidation (Recep)

### Review & Quality (Human)
- PR reviews and merge decisions (Recep)
- Test plan definition (Daniel)
- Deep review checklist planning (team)

---

## AI Contributions Summary

### Implementation (Osiris)
- Service layer code generation
- MCP tool registration
- CLI command implementation
- Test scaffolding
- Error handling implementation
- XML parsing utilities

### Documentation (Osiris)
- Architecture docs drafting
- Phase planning documents
- Implementation status tracking
- This journal maintenance

---

## Lessons for Agentic Engineering

1. **Clear role separation works.** Human = architect/reviewer, AI = implementer. Decisions flow down, code flows up.

2. **Iterative human steering is essential.** "Do it in another branch" and "add version service" — small course corrections kept quality high.

3. **Phased PRs enable quality.** Each PR was reviewable. No 3000-line mega-PRs.

4. **Air-gapped workflows scale.** Osiris never touched internal Greenbone code. Clean separation = clean IP.

5. **Documentation alongside code.** Journal, status docs, and architecture evolved with the implementation.

---

*To be continued as the project progresses through review and release...*
