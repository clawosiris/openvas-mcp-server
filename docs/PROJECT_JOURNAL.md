# OpenVAS MCP Server — Project Journal

*Capturing the journey for a future blog post.*

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
- Codex (via ACP) — Implementation
- Claude Code (via ACP) — Code reviews

### Roadmap Created

Osiris created and pushed `ROADMAP.md` with:
- 6 phases: Foundation → Services → MCP → CLI → Testing → Docs
- ~47 MCP tools planned
- 2-3 week timeline estimate
- Migration plan from Codeberg implementation

### Notable Quotes

**On code reuse (Recep):**
> "If I embed the entire business into the tool, I'll have to rewrite the code. The service layer will be called by the tools for the MCP. It will also be called within the CLI."

**On AI-assisted development (Daniel):**
> "We could ask Osiris to create a repo, give you access, look at what you push there, then spec out a migration."

**On the multi-agent workflow:**
> Osiris: "This maps to the multi-agent workflow we spec'd earlier — just without the separate spec-reviewer agent (I'll handle that role directly)."

### End of Session

Recep signed off at 3:15 AM Turkey time, planning to push his scaffold in the morning.

---

## Prompts & Interactions Log

### Initial Architecture Discussion
```
Recep: "Could you share current arch of project with me?"

Osiris: [Shared current Codeberg architecture diagram]

Recep: "Okay, so how do we handle writing both the MCP and the CLI 
simultaneously? If I embed the entire business into the tool, I'll 
have to rewrite the code..."
```

### Repo Creation
```
Daniel: "So please go ahead and create a repo in your github account 
for the mcp-server project and give maintainer access to Recep 
(https://github.com/recepkizilarslan) and me (https://github.com/llunved)"

Osiris: [Created repo, sent invitations]
```

### Role Assignment
```
Daniel: "Osiris in general terms I'd like you to act as the architect 
and supervisor, task codex with implementation tasks via ACP and use 
Claude Code in review mode for code reviews via ACP in this project."
```

---

*To be continued as the project progresses...*
