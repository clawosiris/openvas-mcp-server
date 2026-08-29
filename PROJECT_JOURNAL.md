# Project Journal: OpenVAS MCP Server

_A concise record of substantive project changes, decisions, and next steps._

---

## Current Direction

The OpenVAS MCP Server is a Rust application that exposes Greenbone
Vulnerability Management operations to MCP clients. It is a thin, typed front
end over the `rust-gvm-api` REST gateway; GMP and gvmd protocol knowledge stay
in the gateway.

```text
MCP client
    |  stdio or streamable HTTP
    v
gvm-mcp (this repository)
    |  HTTP/JSON with caller identity forwarding
    v
rust-gvm-api
    |  GMP over Unix socket
    v
gvmd
```

The canonical repository is
[`greenbone-hive/openvas-mcp-server`](https://github.com/greenbone-hive/openvas-mcp-server).

---

## Journal Convention

- Add an entry only for substantive activity newer than the latest entry.
- Record merged code, meaningful local progress, architectural decisions,
  issue or pull-request state changes, and concrete next steps.
- Do not repeat an unchanged backlog or routine no-op checks.
- Anchor every entry to a date and, when applicable, a commit or release.

---

## Reinitialized Baseline (2026-08-29)

**Baseline commit:** `e5cedc6a3bf00f45ea4202daa9ccf7da3e1a67a9`

### Repository state

- Re-established the canonical local checkout from
  `greenbone-hive/openvas-mcp-server` on `main`.
- Current release: `v0.1.0`, published 2026-08-13.
- The former Python implementation and migration remnants were removed; the
  supported implementation is now the Rust server.

### Current capabilities and decisions

- The server communicates with `rust-gvm-api` rather than speaking GMP
  directly.
- Both stdio and streamable-HTTP MCP transports are supported.
- Authentication is stateless: inbound HTTP authorization is forwarded per
  request, with configured credentials available as a fallback for stdio or
  callers without an authorization header.
- The complete surface contains 104 tools. The default selection exposes 81;
  read-only mode exposes 49. Identity tools remain opt-in.
- Reports support drill-down and asynchronous exports; target and task tools
  cover CRUD and scan lifecycle operations.
- Unit and mock-gateway tests run without a GVM installation. Live end-to-end
  tests remain opt-in.

### Recent project history captured by this baseline

- Bootstrapped the Rust MCP server over the GVM REST gateway and added the
  target/task, full read, and supported write surfaces.
- Added report exports, streamable HTTP, Docker packaging, release automation,
  and credential-store reads.
- Removed the legacy Python implementation and aligned governance with the
  `rust-gvm` and `rust-gvm-api` projects.
- Added stateless credential pass-through authentication in PR #75.

### GitHub snapshot

- Open issue #39 still describes the legacy `gvm-mock-server` integration-test
  architecture and should be reconciled with the current Rust/wiremock design.
- Open dependency PRs at reinitialization: #76, #78, #79, and #80. These are
  baseline backlog and should appear in a future entry only when their state or
  project impact changes.

### Next steps

- Triage issue #39 against the current gateway and test architecture.
- Review the open dependency updates and merge compatible changes.
- Expand live-stack coverage for realistic gateway and gvmd behavior.
- Add missing write operations as corresponding gateway endpoints become
  available.

---

Future entries begin after this baseline and cover activity newer than
2026-08-29 / `e5cedc6`.
