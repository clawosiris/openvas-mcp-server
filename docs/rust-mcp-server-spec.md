# GVM MCP Server — Rust Port Specification

**Version:** 1.0  
**Date:** 2026-03-31  
**Status:** Draft  
**Authors:** Recep Kızılarslan, dev-grnbn agent  
**License:** AGPL-3.0-or-later

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Background & Motivation](#2-background--motivation)
3. [Architecture Overview](#3-architecture-overview)
4. [Repository Structure](#4-repository-structure)
5. [Dependencies](#5-dependencies)
6. [Configuration](#6-configuration)
7. [Tool Inventory & Mapping](#7-tool-inventory--mapping)
8. [rust-gvm Command Coverage](#8-rust-gvm-command-coverage)
9. [Implementation Details](#9-implementation-details)
10. [Error Handling](#10-error-handling)
11. [Testing Strategy](#11-testing-strategy)
12. [CI/CD Pipeline](#12-cicd-pipeline)
13. [Performance Considerations](#13-performance-considerations)
14. [Migration Guide](#14-migration-guide)
15. [Implementation Phases](#15-implementation-phases)
16. [Success Criteria](#16-success-criteria)
17. [Open Questions](#17-open-questions)
18. [References](#18-references)

---

## 1. Executive Summary

This specification defines the port of the Python-based OpenVAS MCP server to Rust, replacing `python-gvm` with `rust-gvm` as the Greenbone Management Protocol (GMP) backend.

### Goals

| Goal | Description |
|------|-------------|
| **1:1 Tool Parity** | Identical MCP tool names, parameters, and response schemas |
| **Type Safety** | Leverage Rust's type system and `rust-gvm`'s typed responses |
| **Performance** | Async-first design with Tokio runtime |
| **Maintainability** | Share transport/protocol logic with `rust-gvm` workspace |
| **Testability** | Use `gvm-mock-server` for unit tests without live gvmd |

### Non-Goals

- Breaking changes to existing MCP tool signatures
- New features not present in the Python implementation
- Support for GMP versions below 22.4

---

## 2. Background & Motivation

### Current State

The existing Python MCP server (`openvas-mcp-server`) provides 54 tools across 14 modules for AI agents to interact with Greenbone Vulnerability Management (GVM) systems. It uses:

- **`mcp[cli]` / FastMCP** — MCP protocol implementation
- **`python-gvm`** — Synchronous GMP client library
- **Pydantic** — Data validation and serialization

### Why Rust?

| Factor | Python | Rust |
|--------|--------|------|
| Type Safety | Runtime (Pydantic) | Compile-time |
| Concurrency | GIL-limited threads | True async/await |
| Memory Safety | GC-managed | Zero-cost ownership |
| Binary Distribution | Requires Python runtime | Single static binary |
| Error Handling | Exceptions | Result types |
| Performance | Interpreted | Native code |

### Why rust-gvm?

`rust-gvm` provides:

- **Complete GMP coverage** — 150+ command builders for GMP 22.4–22.8+
- **Typed responses** — Structured response parsing with serde support
- **Async-first** — Built on Tokio for true concurrency
- **Mock server** — Programmable test server for integration testing
- **Multiple transports** — Unix socket, SSH tunnel, TCP/TLS

---

## 3. Architecture Overview

### 3.1 Current Python Stack

```
┌─────────────────────────────────────────────────────────────────┐
│                        MCP Client                                │
│               (Claude, GPT, Cursor, etc.)                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ MCP Protocol (JSON-RPC over stdio)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  openvas-mcp-server (Python)                     │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    FastMCP Server                          │  │
│  │              (MCP protocol handling)                       │  │
│  ├───────────────────────────────────────────────────────────┤  │
│  │                   Toolsets Layer                           │  │
│  │    ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐        │  │
│  │    │ targets │ │  tasks  │ │ reports │ │  vulns  │ ...    │  │
│  │    └─────────┘ └─────────┘ └─────────┘ └─────────┘        │  │
│  ├───────────────────────────────────────────────────────────┤  │
│  │                   Services Layer                           │  │
│  │    ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐        │  │
│  │    │ Target  │ │  Task   │ │ Report  │ │  Vuln   │ ...    │  │
│  │    │ Service │ │ Service │ │ Service │ │ Service │        │  │
│  │    └─────────┘ └─────────┘ └─────────┘ └─────────┘        │  │
│  ├───────────────────────────────────────────────────────────┤  │
│  │                     python-gvm                             │  │
│  │              (Synchronous GMP client)                      │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ GMP Protocol (XML over Unix socket/SSH)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                           gvmd                                   │
│              (Greenbone Vulnerability Manager)                   │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Target Rust Stack

```
┌─────────────────────────────────────────────────────────────────┐
│                        MCP Client                                │
│               (Claude, GPT, Cursor, etc.)                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ MCP Protocol (JSON-RPC over stdio)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     gvm-mcp (Rust)                               │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    rmcp Server                             │  │
│  │              (MCP protocol handling)                       │  │
│  ├───────────────────────────────────────────────────────────┤  │
│  │                   Tool Handlers                            │  │
│  │    ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐        │  │
│  │    │ targets │ │  tasks  │ │ reports │ │  vulns  │ ...    │  │
│  │    └─────────┘ └─────────┘ └─────────┘ └─────────┘        │  │
│  ├───────────────────────────────────────────────────────────┤  │
│  │                    rust-gvm Stack                          │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │              gvm-client (High-level API)            │  │  │
│  │  │         Version negotiation, typed methods          │  │  │
│  │  ├─────────────────────────────────────────────────────┤  │  │
│  │  │           gvm-gmp (Command builders)                │  │  │
│  │  │      150+ typed commands, response parsers          │  │  │
│  │  ├─────────────────────────────────────────────────────┤  │  │
│  │  │          gvm-protocol (XML framing)                 │  │  │
│  │  │       Sans-I/O XML parsing, request builder         │  │  │
│  │  ├─────────────────────────────────────────────────────┤  │  │
│  │  │         gvm-connection (Transport)                  │  │  │
│  │  │         Unix socket / SSH / TCP+TLS                 │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ GMP Protocol (XML over Unix socket/SSH)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                           gvmd                                   │
│              (Greenbone Vulnerability Manager)                   │
└─────────────────────────────────────────────────────────────────┘
```

### 3.3 Key Architectural Differences

| Aspect | Python Implementation | Rust Implementation |
|--------|----------------------|---------------------|
| **MCP SDK** | `mcp[cli]` / FastMCP | `rmcp` crate |
| **GMP Client** | `python-gvm` (sync) | `gvm-client` (async) |
| **Runtime** | Synchronous/threaded | Tokio async runtime |
| **Transport** | `UnixSocketConnection` | `gvm-connection` trait |
| **Type Safety** | Pydantic models | Native structs + serde |
| **Error Handling** | Exceptions | `Result<T, E>` types |
| **Serialization** | Pydantic `.model_dump()` | serde `#[derive(Serialize)]` |

---

## 4. Repository Structure

### 4.1 Recommended: Separate Repository

```
clawosiris/gvm-mcp/
├── .github/
│   └── workflows/
│       ├── ci.yml                 # Format, lint, test, coverage
│       ├── nightly.yml            # Cross-platform builds
│       └── release.yml            # Tagged releases
├── Cargo.toml                     # Workspace root
├── Cargo.lock
├── LICENSE                        # AGPL-3.0-or-later
├── README.md
├── CHANGELOG.md
├── rustfmt.toml
├── clippy.toml
├── deny.toml                      # cargo-deny config
│
├── src/
│   ├── main.rs                    # Entry point, CLI parsing
│   ├── lib.rs                     # Library exports
│   ├── server.rs                  # MCP server setup and lifecycle
│   ├── config.rs                  # Configuration loading (env, file)
│   ├── error.rs                   # Error types (thiserror)
│   ├── state.rs                   # Shared application state
│   │
│   └── tools/
│       ├── mod.rs                 # Tool registration
│       ├── system.rs              # openvas_get_version, openvas_test_connection
│       ├── targets.rs             # openvas_*_target(s)
│       ├── tasks.rs               # openvas_*_task(s)
│       ├── reports.rs             # openvas_*_report(s)
│       ├── scan_configs.rs        # openvas_*_scan_config(s)
│       ├── port_lists.rs          # openvas_*_port_list(s)
│       ├── schedules.rs           # openvas_*_schedule(s)
│       ├── vulns.rs               # openvas_list_vulnerabilities, openvas_search_nvts
│       ├── notes.rs               # openvas_*_note(s)
│       ├── overrides.rs           # openvas_*_override(s)
│       ├── tickets.rs             # openvas_*_ticket(s)
│       ├── assets.rs              # openvas_list_asset_*
│       └── compliance.rs          # openvas_*_compliance_*
│
├── tests/
│   ├── common/
│   │   └── mod.rs                 # Shared test utilities
│   ├── unit/
│   │   ├── mod.rs
│   │   ├── targets_test.rs
│   │   ├── tasks_test.rs
│   │   └── ...
│   └── integration/
│       ├── mod.rs
│       ├── docker_compose.yml     # gvmd + postgres for integration tests
│       └── full_workflow_test.rs
│
├── fixtures/
│   └── xml/                       # Static XML fixtures for unit tests
│       ├── targets/
│       ├── tasks/
│       └── reports/
│
└── docs/
    ├── architecture.md
    ├── tools-reference.md
    └── deployment.md
```

### 4.2 Alternative: Workspace Member in rust-gvm

```
clawosiris/rust-gvm/
├── crates/
│   ├── gvm-client/
│   ├── gvm-connection/
│   ├── gvm-gmp/
│   ├── gvm-mock-server/
│   ├── gvm-protocol/
│   └── gvm-mcp/                   # NEW CRATE
│       ├── Cargo.toml
│       └── src/
│           ├── main.rs
│           ├── lib.rs
│           └── tools/
└── Cargo.toml                     # Add to [workspace.members]
```

### 4.3 Recommendation

**Separate repository** (`clawosiris/gvm-mcp`) is recommended for:

- **Independent release cycle** — MCP server can release independently of `rust-gvm`
- **Clearer dependency boundary** — `gvm-mcp` depends on `rust-gvm`, not vice versa
- **Easier downstream consumption** — Users can depend on just the MCP server
- **Simpler CI** — No need to rebuild entire `rust-gvm` workspace for MCP changes

---

## 5. Dependencies

### 5.1 Cargo.toml

```toml
[package]
name = "gvm-mcp"
version = "0.1.0"
edition = "2021"
rust-version = "1.75.0"
license = "AGPL-3.0-or-later"
description = "MCP server for Greenbone Vulnerability Management"
repository = "https://github.com/clawosiris/gvm-mcp"
keywords = ["mcp", "greenbone", "gvm", "vulnerability", "security"]
categories = ["command-line-utilities", "network-programming"]

[dependencies]
# ─── MCP Protocol ───────────────────────────────────────────────
rmcp = { version = "0.1", features = ["server", "transport-stdio", "transport-sse"] }

# ─── GVM Client (rust-gvm) ──────────────────────────────────────
gvm-client = { git = "https://github.com/clawosiris/rust-gvm", branch = "main" }
gvm-connection = { git = "https://github.com/clawosiris/rust-gvm", branch = "main" }
gvm-gmp = { git = "https://github.com/clawosiris/rust-gvm", branch = "main", features = ["serde"] }

# ─── Async Runtime ──────────────────────────────────────────────
tokio = { version = "1", features = ["full"] }
async-trait = "0.1"

# ─── Serialization ──────────────────────────────────────────────
serde = { version = "1", features = ["derive"] }
serde_json = "1"

# ─── Error Handling ─────────────────────────────────────────────
thiserror = "2"
anyhow = "1"

# ─── Logging ────────────────────────────────────────────────────
tracing = "0.1"
tracing-subscriber = { version = "0.3", features = ["env-filter", "json"] }

# ─── Configuration ──────────────────────────────────────────────
config = "0.14"
dotenvy = "0.15"

# ─── CLI ────────────────────────────────────────────────────────
clap = { version = "4", features = ["derive", "env"] }

# ─── Utilities ──────────────────────────────────────────────────
base64 = "0.22"
uuid = { version = "1", features = ["v4"] }

[dev-dependencies]
# ─── Testing ────────────────────────────────────────────────────
rstest = "0.26"
tokio-test = "0.4"
pretty_assertions = "1"
tempfile = "3"

# ─── Mock Server ────────────────────────────────────────────────
gvm-mock-server = { git = "https://github.com/clawosiris/rust-gvm", branch = "main" }

[features]
default = []
# Enable SSH transport support
ssh = ["gvm-connection/ssh"]
# Enable TLS transport support (when available)
tls = ["gvm-connection/tls"]

[profile.release]
lto = true
codegen-units = 1
strip = true

[lints.rust]
unsafe_code = "forbid"
missing_docs = "warn"

[lints.clippy]
pedantic = { level = "warn", priority = -1 }
unwrap_used = "warn"
expect_used = "warn"
```

### 5.2 Dependency Justification

| Dependency | Purpose | Why This Choice |
|------------|---------|-----------------|
| `rmcp` | MCP protocol | Most mature Rust MCP SDK, supports stdio/SSE |
| `gvm-*` | GMP client | Our own library, full GMP coverage |
| `tokio` | Async runtime | Industry standard, best ecosystem |
| `serde` | Serialization | De facto standard for Rust |
| `thiserror` | Error types | Ergonomic error derive macros |
| `tracing` | Logging | Structured logging, compatible with OpenTelemetry |
| `clap` | CLI parsing | Full-featured, derive macros |
| `config` | Config loading | Multiple sources (file, env, CLI) |

---

## 6. Configuration

### 6.1 Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `GVM_SOCKET_PATH` | Unix socket path to gvmd | `/run/gvmd/gvmd.sock` | No* |
| `GVM_HOST` | SSH/TCP hostname | — | No* |
| `GVM_PORT` | SSH/TCP port | `22` (SSH) / `9390` (TCP) | No |
| `GVM_USERNAME` | GMP authentication username | — | Yes |
| `GVM_PASSWORD` | GMP authentication password | — | Yes |
| `GVM_SSH_USER` | SSH tunnel username | — | No |
| `GVM_SSH_KEY_PATH` | Path to SSH private key | `~/.ssh/id_rsa` | No |
| `GVM_SSH_KEY_PASSPHRASE` | SSH key passphrase | — | No |
| `GVM_TRANSPORT` | Transport type: `unix`, `ssh`, `tcp` | `unix` | No |
| `GVM_TIMEOUT_SECS` | Connection timeout in seconds | `30` | No |
| `MCP_TRANSPORT` | MCP transport: `stdio`, `sse` | `stdio` | No |
| `MCP_SSE_PORT` | SSE server port (if MCP_TRANSPORT=sse) | `8080` | No |
| `RUST_LOG` | Log level filter | `info` | No |

*Either `GVM_SOCKET_PATH` or `GVM_HOST` is required.

### 6.2 Configuration File (Optional)

```toml
# gvm-mcp.toml

[connection]
# Transport type: "unix" | "ssh" | "tcp"
transport = "unix"

# Unix socket configuration
socket_path = "/run/gvmd/gvmd.sock"

# SSH configuration (alternative to unix)
# host = "gvm.example.com"
# port = 22
# ssh_user = "gvm"
# ssh_key_path = "~/.ssh/id_rsa"
# remote_socket = "/run/gvmd/gvmd.sock"

# Connection settings
timeout_secs = 30
retry_attempts = 3
retry_delay_ms = 1000

[auth]
username = "admin"
# Password can also be set via GVM_PASSWORD env var
# password = "secret"

[mcp]
# Transport: "stdio" | "sse"
transport = "stdio"

# SSE configuration (if transport = "sse")
# sse_host = "127.0.0.1"
# sse_port = 8080

[logging]
# Log level: "trace" | "debug" | "info" | "warn" | "error"
level = "info"
# Output format: "pretty" | "json"
format = "pretty"
```

### 6.3 Configuration Priority

1. CLI arguments (highest)
2. Environment variables
3. Configuration file
4. Default values (lowest)

### 6.4 Configuration Loading Code

```rust
// src/config.rs

use std::path::PathBuf;
use serde::Deserialize;
use config::{Config, Environment, File};

#[derive(Debug, Clone, Deserialize)]
pub struct AppConfig {
    pub connection: ConnectionConfig,
    pub auth: AuthConfig,
    pub mcp: McpConfig,
    pub logging: LoggingConfig,
}

#[derive(Debug, Clone, Deserialize)]
pub struct ConnectionConfig {
    #[serde(default = "default_transport")]
    pub transport: TransportType,
    
    #[serde(default = "default_socket_path")]
    pub socket_path: PathBuf,
    
    pub host: Option<String>,
    pub port: Option<u16>,
    pub ssh_user: Option<String>,
    pub ssh_key_path: Option<PathBuf>,
    pub remote_socket: Option<PathBuf>,
    
    #[serde(default = "default_timeout")]
    pub timeout_secs: u64,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum TransportType {
    Unix,
    Ssh,
    Tcp,
}

#[derive(Debug, Clone, Deserialize)]
pub struct AuthConfig {
    pub username: String,
    pub password: String,
}

#[derive(Debug, Clone, Deserialize)]
pub struct McpConfig {
    #[serde(default = "default_mcp_transport")]
    pub transport: McpTransportType,
    pub sse_host: Option<String>,
    pub sse_port: Option<u16>,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum McpTransportType {
    Stdio,
    Sse,
}

impl AppConfig {
    pub fn load() -> Result<Self, config::ConfigError> {
        Config::builder()
            // Start with default values
            .set_default("connection.transport", "unix")?
            .set_default("connection.socket_path", "/run/gvmd/gvmd.sock")?
            .set_default("connection.timeout_secs", 30)?
            .set_default("mcp.transport", "stdio")?
            .set_default("logging.level", "info")?
            .set_default("logging.format", "pretty")?
            // Load from config file if present
            .add_source(File::with_name("gvm-mcp").required(false))
            // Override with environment variables (GVM_*, MCP_*)
            .add_source(
                Environment::default()
                    .prefix("GVM")
                    .separator("_")
            )
            .build()?
            .try_deserialize()
    }
}
```

---

## 7. Tool Inventory & Mapping

### 7.1 Complete Tool List

The MCP server exposes **54 tools** across **14 modules**:

#### 7.1.1 System Tools (2 tools)

| MCP Tool Name | Python Function | Rust Implementation | Description |
|---------------|-----------------|---------------------|-------------|
| `openvas_get_version` | `get_version()` | `client.get_version()` | Get GVM/GMP version info |
| `openvas_test_connection` | `test_connection()` | `client.get_version()` (wrapped) | Test connectivity to gvmd |

#### 7.1.2 Target Tools (6 tools)

| MCP Tool Name | Parameters | Returns | rust-gvm Command |
|---------------|------------|---------|------------------|
| `openvas_list_targets` | `filter?: string` | `{ items: Target[], total: number }` | `get_targets(opts)` |
| `openvas_get_target` | `target_id: string` | `Target` | `get_target(id)` |
| `openvas_create_target` | `name, hosts[], comment?, exclude_hosts[]?, alive_test?, port_list_id?, ssh_credential_id?, smb_credential_id?` | `Target` | `create_target(name, opts)` |
| `openvas_update_target` | `target_id, name?, hosts[]?, comment?, exclude_hosts[]?, alive_test?, port_list_id?` | `Target` | `modify_target(id, opts)` |
| `openvas_delete_target` | `target_id, ultimate?: bool` | `{ success: bool }` | `delete_target(id, ultimate)` |
| `openvas_clone_target` | `target_id` | `Target` | `clone_target(id)` |

#### 7.1.3 Task Tools (8 tools)

| MCP Tool Name | Parameters | Returns | rust-gvm Command |
|---------------|------------|---------|------------------|
| `openvas_list_tasks` | `filter?: string` | `{ items: Task[], total: number }` | `get_tasks(opts)` |
| `openvas_get_task` | `task_id: string` | `Task` | `get_task(id)` |
| `openvas_create_task` | `name, target_id, config_id, scanner_id?, comment?` | `Task` | `create_task(...)` |
| `openvas_start_task` | `task_id` | `{ task_id, report_id, status }` | `start_task(id)` |
| `openvas_stop_task` | `task_id` | `{ task_id, success, status }` | `stop_task(id)` |
| `openvas_resume_task` | `task_id` | `{ task_id, report_id, status }` | `resume_task(id)` |
| `openvas_delete_task` | `task_id, ultimate?: bool` | `{ success: bool }` | `delete_task(id, ultimate)` |
| `openvas_clone_task` | `task_id` | `Task` | `clone_task(id)` |

#### 7.1.4 Report Tools (6 tools)

| MCP Tool Name | Parameters | Returns | rust-gvm Command |
|---------------|------------|---------|------------------|
| `openvas_list_reports` | `filter?: string` | `{ items: Report[], total: number }` | `get_reports(opts)` |
| `openvas_get_report` | `report_id` | `Report` (metadata) | `get_report(id)` |
| `openvas_get_report_detail` | `report_id, min_qod?: number` | `ReportDetail` (with vulns) | `get_report(id)` + results |
| `openvas_get_report_summary` | `report_id` | `ReportSummary` | Derived from report |
| `openvas_export_report` | `report_id, format?: string` | `{ content_base64, format, size_bytes }` | `get_report(id, format)` |
| `openvas_delete_report` | `report_id` | `{ success: bool }` | `delete_report(id)` |

#### 7.1.5 Scan Config Tools (2 tools)

| MCP Tool Name | Parameters | Returns | rust-gvm Command |
|---------------|------------|---------|------------------|
| `openvas_list_scan_configs` | `filter?: string` | `{ items: ScanConfig[], total: number }` | `get_scan_configs(opts)` |
| `openvas_get_scan_config` | `config_id` | `ScanConfig` | `get_scan_config(id)` |

#### 7.1.6 Port List Tools (2 tools)

| MCP Tool Name | Parameters | Returns | rust-gvm Command |
|---------------|------------|---------|------------------|
| `openvas_list_port_lists` | `filter?: string` | `{ items: PortList[], total: number }` | `get_port_lists(opts)` |
| `openvas_get_port_list` | `port_list_id` | `PortList` | `get_port_list(id)` |

#### 7.1.7 Schedule Tools (2 tools)

| MCP Tool Name | Parameters | Returns | rust-gvm Command |
|---------------|------------|---------|------------------|
| `openvas_list_schedules` | `filter?: string` | `{ items: Schedule[], total: number }` | `get_schedules(opts)` |
| `openvas_get_schedule` | `schedule_id` | `Schedule` | `get_schedule(id)` |

#### 7.1.8 Vulnerability Tools (2 tools)

| MCP Tool Name | Parameters | Returns | rust-gvm Command |
|---------------|------------|---------|------------------|
| `openvas_list_vulnerabilities` | `report_id, min_qod?: number` | `{ items: Vulnerability[], total: number }` | `get_results(opts)` |
| `openvas_search_nvts` | `query: string` | `{ query, results: NVT[], total: number }` | `get_nvts(filter=query)` |

#### 7.1.9 Note Tools (5 tools)

| MCP Tool Name | Parameters | Returns | rust-gvm Command |
|---------------|------------|---------|------------------|
| `openvas_list_notes` | `filter?: string` | `{ items: Note[], total: number }` | `get_notes(opts)` |
| `openvas_get_note` | `note_id` | `Note` | `get_note(id)` |
| `openvas_create_note` | `text, nvt_oid?` | `Note` | `create_note(nvt_oid, opts)` |
| `openvas_update_note` | `note_id, text` | `Note` | `modify_note(id, opts)` |
| `openvas_delete_note` | `note_id` | `{ success: bool }` | `delete_note(id, false)` |

#### 7.1.10 Override Tools (5 tools)

| MCP Tool Name | Parameters | Returns | rust-gvm Command |
|---------------|------------|---------|------------------|
| `openvas_list_overrides` | `filter?: string` | `{ items: Override[], total: number }` | `get_overrides(opts)` |
| `openvas_get_override` | `override_id` | `Override` | `get_override(id)` |
| `openvas_create_override` | `text, nvt_oid?` | `Override` | `create_override(nvt_oid, opts)` |
| `openvas_update_override` | `override_id, text` | `Override` | `modify_override(id, opts)` |
| `openvas_delete_override` | `override_id` | `{ success: bool }` | `delete_override(id, false)` |

#### 7.1.11 Ticket Tools (5 tools)

| MCP Tool Name | Parameters | Returns | rust-gvm Command |
|---------------|------------|---------|------------------|
| `openvas_list_tickets` | `filter?: string` | `{ items: Ticket[], total: number }` | `get_tickets(opts)` |
| `openvas_get_ticket` | `ticket_id` | `Ticket` | `get_ticket(id)` |
| `openvas_create_ticket` | `result_id, comment?` | `Ticket` | `create_ticket(result_id, opts)` |
| `openvas_update_ticket` | `ticket_id, status, comment?` | `Ticket` | `modify_ticket(id, opts)` |
| `openvas_delete_ticket` | `ticket_id` | `{ success: bool }` | `delete_ticket(id, false)` |

#### 7.1.12 Asset Tools (3 tools)

| MCP Tool Name | Parameters | Returns | rust-gvm Command |
|---------------|------------|---------|------------------|
| `openvas_list_asset_hosts` | `filter?: string` | `{ items: Host[], total: number }` | `get_hosts(opts)` |
| `openvas_list_asset_os` | `filter?: string` | `{ items: OS[], total: number }` | `get_operating_systems(opts)` |
| `openvas_list_asset_tls_certificates` | `filter?: string` | `{ items: TlsCert[], total: number }` | `get_tls_certificates(opts)` |

#### 7.1.13 Compliance Tools (6 tools)

| MCP Tool Name | Parameters | Returns | rust-gvm Command |
|---------------|------------|---------|------------------|
| `openvas_list_compliance_policies` | — | `{ items: Policy[], total: number }` | `get_policies(opts)` |
| `openvas_list_compliance_audits` | `filter?: string` | `{ items: Audit[], total: number }` | `get_audits(opts)` |
| `openvas_get_compliance_audit` | `audit_id` | `Audit` | `get_task(id)` (usage_type=audit) |
| `openvas_start_compliance_audit` | `audit_id` | `{ audit_id, report_id }` | `start_audit(id)` |
| `openvas_stop_compliance_audit` | `audit_id` | `{ audit_id, success }` | `stop_audit(id)` |
| `openvas_get_compliance_status` | `target_id` | `ComplianceStatus` | Derived from audit reports |

### 7.2 Tool Count Summary

| Module | Tools | Status |
|--------|-------|--------|
| System | 2 | ✅ Ready |
| Targets | 6 | ✅ Ready |
| Tasks | 8 | ✅ Ready |
| Reports | 6 | ✅ Ready |
| Scan Configs | 2 | ✅ Ready |
| Port Lists | 2 | ✅ Ready |
| Schedules | 2 | ✅ Ready |
| Vulnerabilities | 2 | ✅ Ready |
| Notes | 5 | ✅ Ready |
| Overrides | 5 | ✅ Ready |
| Tickets | 5 | ✅ Ready |
| Assets | 3 | ✅ Ready |
| Compliance | 6 | ✅ Ready |
| **Total** | **54** | **100% Coverage** |

---

## 8. rust-gvm Command Coverage

### 8.1 Available Commands in rust-gvm

The `rust-gvm` library provides **150+ command builders**. Here's the complete inventory:

#### Authentication & System

| Command | Function | Status |
|---------|----------|--------|
| `authenticate` | `authenticate(user, pass)` | ✅ |
| `get_version` | `get_version()` | ✅ |
| `help` | `help(format?)` | ✅ |
| `describe_auth` | `describe_auth()` | ✅ |
| `get_settings` | `get_settings(opts)` | ✅ |
| `get_feeds` | `get_feeds()` | ✅ |
| `get_license` | `get_license()` | ✅ |
| `modify_auth` | `modify_auth(enabled)` | ✅ |
| `modify_license` | `modify_license(key)` | ✅ |
| `modify_setting` | `modify_setting(id, value)` | ✅ |

#### Targets

| Command | Function | Status |
|---------|----------|--------|
| `create_target` | `create_target(name, opts)` | ✅ |
| `get_targets` | `get_targets(opts)` | ✅ |
| `get_target` | `get_target(id)` | ✅ |
| `modify_target` | `modify_target(id, opts)` | ✅ |
| `delete_target` | `delete_target(id, ultimate)` | ✅ |
| `clone_target` | `clone_target(id)` | ✅ |

#### Tasks

| Command | Function | Status |
|---------|----------|--------|
| `create_task` | `create_task(name, config, target, scanner, opts)` | ✅ |
| `get_tasks` | `get_tasks(opts)` | ✅ |
| `get_task` | `get_task(id)` | ✅ |
| `modify_task` | `modify_task(id, opts)` | ✅ |
| `delete_task` | `delete_task(id, ultimate)` | ✅ |
| `clone_task` | `clone_task(id)` | ✅ |
| `start_task` | `start_task(id)` | ✅ |
| `stop_task` | `stop_task(id)` | ✅ |
| `resume_task` | `resume_task(id)` | ✅ |
| `move_task` | `move_task(id, slave?)` | ✅ |

#### Audits (Compliance Tasks)

| Command | Function | Status |
|---------|----------|--------|
| `create_audit` | `create_audit(name, config, target, scanner, opts)` | ✅ |
| `get_audits` | `get_audits(opts)` | ✅ |
| `modify_audit` | `modify_audit(id, opts)` | ✅ |
| `delete_audit` | `delete_audit(id)` | ✅ |
| `start_audit` | `start_audit(id)` | ✅ |
| `stop_audit` | `stop_audit(id)` | ✅ |
| `resume_audit` | `resume_audit(id)` | ✅ |

#### Reports

| Command | Function | Status |
|---------|----------|--------|
| `create_report` | `create_report(task_id, opts)` | ✅ |
| `get_reports` | `get_reports(opts)` | ✅ |
| `get_report` | `get_report(id)` | ✅ |
| `delete_report` | `delete_report(id, ultimate)` | ✅ |
| `get_audit_reports` | `get_audit_reports(opts)` | ✅ |
| `delete_audit_report` | `delete_audit_report(id)` | ✅ |

#### Results & Vulnerabilities

| Command | Function | Status |
|---------|----------|--------|
| `get_results` | `get_results(opts)` | ✅ |
| `get_result` | `get_result(id)` | ✅ |
| `get_vulns` | `get_vulns(opts)` | ✅ |
| `get_vulnerabilities` | `get_vulnerabilities(opts)` | ✅ |

#### NVTs (Network Vulnerability Tests)

| Command | Function | Status |
|---------|----------|--------|
| `get_nvts` | `get_nvts(opts)` | ✅ |
| `get_nvt` | `get_nvt(oid)` | ✅ |
| `get_nvt_families` | `get_nvt_families()` | ✅ |

#### Scan Configs & Policies

| Command | Function | Status |
|---------|----------|--------|
| `create_scan_config` | `create_scan_config(name, base_id?, opts)` | ✅ |
| `get_scan_configs` | `get_scan_configs(opts)` | ✅ |
| `get_scan_config` | `get_scan_config(id)` | ✅ |
| `modify_scan_config` | `modify_scan_config(id, opts)` | ✅ |
| `delete_scan_config` | `delete_scan_config(id, ultimate)` | ✅ |
| `clone_scan_config` | `clone_scan_config(id)` | ✅ |
| `sync_config` | `sync_config(id)` | ✅ |
| `create_policy` | `create_policy(name, opts)` | ✅ |
| `get_policies` | `get_policies(opts)` | ✅ |
| `modify_policy` | `modify_policy(id, opts)` | ✅ |
| `delete_policy` | `delete_policy(id)` | ✅ |
| `clone_policy` | `clone_policy(id)` | ✅ |

#### Port Lists

| Command | Function | Status |
|---------|----------|--------|
| `create_port_list` | `create_port_list(name, opts)` | ✅ |
| `get_port_lists` | `get_port_lists(opts)` | ✅ |
| `get_port_list` | `get_port_list(id)` | ✅ |
| `modify_port_list` | `modify_port_list(id, opts)` | ✅ |
| `delete_port_list` | `delete_port_list(id, ultimate)` | ✅ |
| `clone_port_list` | `clone_port_list(id)` | ✅ |
| `create_port_range` | `create_port_range(port_list_id, start, end, type)` | ✅ |
| `delete_port_range` | `delete_port_range(id)` | ✅ |

#### Schedules

| Command | Function | Status |
|---------|----------|--------|
| `create_schedule` | `create_schedule(name, opts)` | ✅ |
| `get_schedules` | `get_schedules(opts)` | ✅ |
| `get_schedule` | `get_schedule(id)` | ✅ |
| `modify_schedule` | `modify_schedule(id, opts)` | ✅ |
| `delete_schedule` | `delete_schedule(id, ultimate)` | ✅ |
| `clone_schedule` | `clone_schedule(id)` | ✅ |

#### Notes

| Command | Function | Status |
|---------|----------|--------|
| `create_note` | `create_note(nvt_oid, opts)` | ✅ |
| `get_notes` | `get_notes(opts)` | ✅ |
| `get_note` | `get_note(id)` | ✅ |
| `modify_note` | `modify_note(id, opts)` | ✅ |
| `delete_note` | `delete_note(id, ultimate)` | ✅ |
| `clone_note` | `clone_note(id)` | ✅ |

#### Overrides

| Command | Function | Status |
|---------|----------|--------|
| `create_override` | `create_override(nvt_oid, opts)` | ✅ |
| `get_overrides` | `get_overrides(opts)` | ✅ |
| `get_override` | `get_override(id)` | ✅ |
| `modify_override` | `modify_override(id, opts)` | ✅ |
| `delete_override` | `delete_override(id, ultimate)` | ✅ |
| `clone_override` | `clone_override(id)` | ✅ |

#### Tickets

| Command | Function | Status |
|---------|----------|--------|
| `create_ticket` | `create_ticket(result_id, opts)` | ✅ |
| `get_tickets` | `get_tickets(opts)` | ✅ |
| `get_ticket` | `get_ticket(id)` | ✅ |
| `modify_ticket` | `modify_ticket(id, opts)` | ✅ |
| `delete_ticket` | `delete_ticket(id, ultimate)` | ✅ |
| `clone_ticket` | `clone_ticket(id)` | ✅ |

#### Hosts (Assets)

| Command | Function | Status |
|---------|----------|--------|
| `create_host` | `create_host(opts)` | ✅ |
| `get_hosts` | `get_hosts(opts)` | ✅ |
| `get_host` | `get_host(id)` | ✅ |
| `modify_host` | `modify_host(id, opts)` | ✅ |
| `delete_host` | `delete_host(id, ultimate)` | ✅ |

#### Operating Systems

| Command | Function | Status |
|---------|----------|--------|
| `get_operating_systems` | `get_operating_systems(opts)` | ✅ |

#### TLS Certificates

| Command | Function | Status |
|---------|----------|--------|
| `create_tls_certificate` | `create_tls_certificate(name, opts)` | ✅ |
| `get_tls_certificates` | `get_tls_certificates(opts)` | ✅ |
| `get_tls_certificate` | `get_tls_certificate(id)` | ✅ |
| `modify_tls_certificate` | `modify_tls_certificate(id, opts)` | ✅ |
| `delete_tls_certificate` | `delete_tls_certificate(id, ultimate)` | ✅ |

#### Security Info (CVE, CPE, Advisories)

| Command | Function | Status |
|---------|----------|--------|
| `get_cves` | `get_cves(opts)` | ✅ |
| `get_cpes` | `get_cpes(opts)` | ✅ |
| `get_cert_bund_advisories` | `get_cert_bund_advisories(opts)` | ✅ |
| `get_dfn_cert_advisories` | `get_dfn_cert_advisories(opts)` | ✅ |

#### Alerts

| Command | Function | Status |
|---------|----------|--------|
| `create_alert` | `create_alert(name, opts)` | ✅ |
| `get_alerts` | `get_alerts(opts)` | ✅ |
| `get_alert` | `get_alert(id)` | ✅ |
| `modify_alert` | `modify_alert(id, opts)` | ✅ |
| `delete_alert` | `delete_alert(id, ultimate)` | ✅ |
| `clone_alert` | `clone_alert(id)` | ✅ |
| `test_alert` | `test_alert(id)` | ✅ |

#### Credentials

| Command | Function | Status |
|---------|----------|--------|
| `create_credential` | `create_credential(name, opts)` | ✅ |
| `get_credentials` | `get_credentials(opts)` | ✅ |
| `get_credential` | `get_credential(id)` | ✅ |
| `modify_credential` | `modify_credential(id, opts)` | ✅ |
| `delete_credential` | `delete_credential(id, ultimate)` | ✅ |
| `clone_credential` | `clone_credential(id)` | ✅ |

#### Users, Groups, Roles, Permissions

| Command | Function | Status |
|---------|----------|--------|
| `create_user` | `create_user(name, opts)` | ✅ |
| `get_users` | `get_users(opts)` | ✅ |
| `modify_user` | `modify_user(id, opts)` | ✅ |
| `delete_user` | `delete_user(id, ultimate)` | ✅ |
| `clone_user` | `clone_user(id)` | ✅ |
| `create_group` | `create_group(name, opts)` | ✅ |
| `get_groups` | `get_groups(opts)` | ✅ |
| `modify_group` | `modify_group(id, opts)` | ✅ |
| `delete_group` | `delete_group(id, ultimate)` | ✅ |
| `clone_group` | `clone_group(id)` | ✅ |
| `create_role` | `create_role(name, opts)` | ✅ |
| `get_roles` | `get_roles(opts)` | ✅ |
| `modify_role` | `modify_role(id, opts)` | ✅ |
| `delete_role` | `delete_role(id, ultimate)` | ✅ |
| `clone_role` | `clone_role(id)` | ✅ |
| `create_permission` | `create_permission(opts)` | ✅ |
| `get_permissions` | `get_permissions(opts)` | ✅ |
| `modify_permission` | `modify_permission(id, opts)` | ✅ |
| `delete_permission` | `delete_permission(id, ultimate)` | ✅ |
| `clone_permission` | `clone_permission(id)` | ✅ |

#### Filters, Tags, Scanners

| Command | Function | Status |
|---------|----------|--------|
| `create_filter` | `create_filter(name, opts)` | ✅ |
| `get_filters` | `get_filters(opts)` | ✅ |
| `modify_filter` | `modify_filter(id, opts)` | ✅ |
| `delete_filter` | `delete_filter(id, ultimate)` | ✅ |
| `clone_filter` | `clone_filter(id)` | ✅ |
| `create_tag` | `create_tag(name, opts)` | ✅ |
| `get_tags` | `get_tags(opts)` | ✅ |
| `modify_tag` | `modify_tag(id, opts)` | ✅ |
| `delete_tag` | `delete_tag(id, ultimate)` | ✅ |
| `clone_tag` | `clone_tag(id)` | ✅ |
| `create_scanner` | `create_scanner(name, opts)` | ✅ |
| `get_scanners` | `get_scanners(opts)` | ✅ |
| `modify_scanner` | `modify_scanner(id, opts)` | ✅ |
| `delete_scanner` | `delete_scanner(id, ultimate)` | ✅ |
| `clone_scanner` | `clone_scanner(id)` | ✅ |
| `verify_scanner` | `verify_scanner(id)` | ✅ |

#### Report Formats & Configs

| Command | Function | Status |
|---------|----------|--------|
| `create_report_format` | `create_report_format(name, opts)` | ✅ |
| `get_report_formats` | `get_report_formats(opts)` | ✅ |
| `modify_report_format` | `modify_report_format(id, opts)` | ✅ |
| `delete_report_format` | `delete_report_format(id, ultimate)` | ✅ |
| `verify_report_format` | `verify_report_format(id)` | ✅ |
| `create_report_config` | `create_report_config(name, format_id)` | ✅ |
| `get_report_configs` | `get_report_configs()` | ✅ |
| `modify_report_config` | `modify_report_config(id, opts)` | ✅ |
| `delete_report_config` | `delete_report_config(id)` | ✅ |

#### Trashcan

| Command | Function | Status |
|---------|----------|--------|
| `empty_trashcan` | `empty_trashcan()` | ✅ |
| `restore` | `restore(id)` | ✅ |

### 8.2 Coverage Summary

| Category | Commands | Needed for MCP | Coverage |
|----------|----------|----------------|----------|
| Authentication | 2 | 2 | 100% |
| System | 10 | 2 | 100% |
| Targets | 6 | 6 | 100% |
| Tasks | 10 | 8 | 100% |
| Audits | 7 | 6 | 100% |
| Reports | 6 | 5 | 100% |
| Results | 2 | 2 | 100% |
| NVTs | 3 | 2 | 100% |
| Scan Configs | 7 | 2 | 100% |
| Policies | 5 | 1 | 100% |
| Port Lists | 8 | 2 | 100% |
| Schedules | 6 | 2 | 100% |
| Notes | 6 | 5 | 100% |
| Overrides | 6 | 5 | 100% |
| Tickets | 6 | 5 | 100% |
| Hosts | 5 | 1 | 100% |
| Operating Systems | 1 | 1 | 100% |
| TLS Certificates | 5 | 1 | 100% |
| **Total** | **150+** | **54** | **100%** |

**All required commands for the MCP server are available in rust-gvm.**

---

## 9. Implementation Details

### 9.1 Tool Handler Pattern

Each tool module follows this pattern:

```rust
// src/tools/targets.rs

use std::sync::Arc;
use tokio::sync::Mutex;

use gvm_client::GmpClient;
use gvm_connection::GvmConnection;
use gvm_gmp::commands::targets::{
    create_target, clone_target, delete_target, get_target, get_targets,
    modify_target, CreateTargetOpts, GetTargetsOpts, ModifyTargetOpts,
};
use gvm_gmp::enums::AliveTest;
use gvm_gmp::responses::{CreateTargetResponse, GetTargetsResponse};
use gvm_gmp::types::EntityId;
use rmcp::{tool, McpError, ToolResult};
use serde::{Deserialize, Serialize};

use crate::error::McpToolError;
use crate::state::AppState;

// ─── Response Types ────────────────────────────────────────────────────────

/// Target item in list response (matches Python schema)
#[derive(Debug, Serialize)]
pub struct TargetItem {
    pub id: String,
    pub name: String,
    pub hosts: Vec<String>,
    pub exclude_hosts: Vec<String>,
    pub comment: Option<String>,
    pub alive_test: Option<String>,
    pub port_list: Option<NamedRef>,
    pub in_use: bool,
    pub writable: bool,
}

/// Named reference (id + name)
#[derive(Debug, Serialize)]
pub struct NamedRef {
    pub id: String,
    pub name: String,
}

/// List response wrapper (matches Python schema)
#[derive(Debug, Serialize)]
pub struct ListResponse<T> {
    pub items: Vec<T>,
    pub total: usize,
}

/// Delete/action response
#[derive(Debug, Serialize)]
pub struct ActionResponse {
    pub success: bool,
    pub target_id: String,
}

// ─── Tool Handlers ─────────────────────────────────────────────────────────

/// Target management tools
pub struct TargetTools<C: GvmConnection + Send + Sync + 'static> {
    state: Arc<AppState<C>>,
}

impl<C: GvmConnection + Send + Sync + 'static> TargetTools<C> {
    pub fn new(state: Arc<AppState<C>>) -> Self {
        Self { state }
    }

    /// List all scan targets.
    ///
    /// # Arguments
    /// * `filter` - Optional GMP filter string (e.g., "name~web")
    ///
    /// # Returns
    /// List of targets with id, name, hosts, and metadata.
    #[tool(name = "openvas_list_targets")]
    pub async fn list_targets(
        &self,
        #[arg(description = "Optional GMP filter string (e.g., 'name~web')")]
        filter: Option<String>,
    ) -> Result<ToolResult, McpError> {
        let mut client = self.state.client.lock().await;

        let opts = GetTargetsOpts {
            filter_string: filter,
            details: Some(true),
            ..Default::default()
        };

        let response = client
            .send(get_targets(opts))
            .await
            .map_err(McpToolError::from)?;

        let parsed = GetTargetsResponse::from_response(&response)
            .map_err(McpToolError::from)?;

        let items: Vec<TargetItem> = parsed
            .items
            .into_iter()
            .map(|t| TargetItem {
                id: t.meta.id.to_string(),
                name: t.meta.name,
                hosts: t.hosts,
                exclude_hosts: t.exclude_hosts,
                comment: t.meta.comment,
                alive_test: t.alive_tests,
                port_list: t.port_list.map(|pl| NamedRef {
                    id: pl.id.to_string(),
                    name: pl.name,
                }),
                in_use: t.meta.in_use,
                writable: t.meta.writable,
            })
            .collect();

        let result = ListResponse {
            total: items.len(),
            items,
        };

        Ok(ToolResult::json(result)?)
    }

    /// Get target details by ID.
    ///
    /// # Arguments
    /// * `target_id` - Target UUID
    ///
    /// # Returns
    /// Target details including hosts, credentials, port list.
    #[tool(name = "openvas_get_target")]
    pub async fn get_target(
        &self,
        #[arg(description = "Target UUID")]
        target_id: String,
    ) -> Result<ToolResult, McpError> {
        let mut client = self.state.client.lock().await;

        let id = target_id
            .parse::<EntityId>()
            .map_err(|_| McpToolError::InvalidId(target_id.clone()))?;

        let response = client
            .send(get_target(&id))
            .await
            .map_err(McpToolError::from)?;

        let parsed = GetTargetsResponse::from_response(&response)
            .map_err(McpToolError::from)?;

        let target = parsed
            .items
            .into_iter()
            .next()
            .ok_or_else(|| McpToolError::NotFound("target", target_id))?;

        let item = TargetItem {
            id: target.meta.id.to_string(),
            name: target.meta.name,
            hosts: target.hosts,
            exclude_hosts: target.exclude_hosts,
            comment: target.meta.comment,
            alive_test: target.alive_tests,
            port_list: target.port_list.map(|pl| NamedRef {
                id: pl.id.to_string(),
                name: pl.name,
            }),
            in_use: target.meta.in_use,
            writable: target.meta.writable,
        };

        Ok(ToolResult::json(item)?)
    }

    /// Create a new scan target.
    ///
    /// # Arguments
    /// * `name` - Target name
    /// * `hosts` - List of hosts (IP addresses, CIDR ranges, or hostnames)
    /// * `comment` - Optional description
    /// * `exclude_hosts` - Hosts to exclude from scan
    /// * `alive_test` - Host discovery method
    /// * `port_list_id` - Port list UUID for scan
    /// * `ssh_credential_id` - SSH credential UUID for authenticated scans
    /// * `smb_credential_id` - SMB credential UUID for authenticated scans
    ///
    /// # Returns
    /// Created target details.
    #[tool(name = "openvas_create_target")]
    pub async fn create_target(
        &self,
        #[arg(description = "Target name")]
        name: String,
        #[arg(description = "List of hosts (IPs, CIDRs, hostnames)")]
        hosts: Vec<String>,
        #[arg(description = "Optional description")]
        comment: Option<String>,
        #[arg(description = "Hosts to exclude from scan")]
        exclude_hosts: Option<Vec<String>>,
        #[arg(description = "Host discovery method (e.g., 'ICMP Ping', 'Consider Alive')")]
        alive_test: Option<String>,
        #[arg(description = "Port list UUID")]
        port_list_id: Option<String>,
        #[arg(description = "SSH credential UUID")]
        ssh_credential_id: Option<String>,
        #[arg(description = "SMB credential UUID")]
        smb_credential_id: Option<String>,
    ) -> Result<ToolResult, McpError> {
        let mut client = self.state.client.lock().await;

        // Parse alive_test string to enum
        let alive_test_enum = alive_test
            .and_then(|s| AliveTest::from_str(&s).ok());

        // Parse optional entity IDs
        let port_list = port_list_id
            .map(|s| s.parse::<EntityId>())
            .transpose()
            .map_err(|_| McpToolError::InvalidId("port_list_id".to_string()))?;

        let opts = CreateTargetOpts {
            comment,
            hosts,
            exclude_hosts: exclude_hosts.unwrap_or_default(),
            alive_test: alive_test_enum,
            port_list_id: port_list,
            ..Default::default()
        };

        let response = client
            .send(create_target(&name, opts))
            .await
            .map_err(McpToolError::from)?;

        let parsed = CreateTargetResponse::from_response(&response)
            .map_err(McpToolError::from)?;

        // Fetch the created target to return full details
        let get_response = client
            .send(get_target(&parsed.id))
            .await
            .map_err(McpToolError::from)?;

        let get_parsed = GetTargetsResponse::from_response(&get_response)
            .map_err(McpToolError::from)?;

        let target = get_parsed
            .items
            .into_iter()
            .next()
            .ok_or_else(|| McpToolError::NotFound("target", parsed.id.to_string()))?;

        let item = TargetItem {
            id: target.meta.id.to_string(),
            name: target.meta.name,
            hosts: target.hosts,
            exclude_hosts: target.exclude_hosts,
            comment: target.meta.comment,
            alive_test: target.alive_tests,
            port_list: target.port_list.map(|pl| NamedRef {
                id: pl.id.to_string(),
                name: pl.name,
            }),
            in_use: target.meta.in_use,
            writable: target.meta.writable,
        };

        Ok(ToolResult::json(item)?)
    }

    /// Update an existing target.
    #[tool(name = "openvas_update_target")]
    pub async fn update_target(
        &self,
        #[arg(description = "Target UUID to update")]
        target_id: String,
        #[arg(description = "New target name")]
        name: Option<String>,
        #[arg(description = "New host list")]
        hosts: Option<Vec<String>>,
        #[arg(description = "New comment")]
        comment: Option<String>,
        #[arg(description = "New exclude list")]
        exclude_hosts: Option<Vec<String>>,
        #[arg(description = "New alive test method")]
        alive_test: Option<String>,
        #[arg(description = "New port list UUID")]
        port_list_id: Option<String>,
    ) -> Result<ToolResult, McpError> {
        let mut client = self.state.client.lock().await;

        let id = target_id
            .parse::<EntityId>()
            .map_err(|_| McpToolError::InvalidId(target_id.clone()))?;

        let alive_test_enum = alive_test
            .and_then(|s| AliveTest::from_str(&s).ok());

        let port_list = port_list_id
            .map(|s| s.parse::<EntityId>())
            .transpose()
            .map_err(|_| McpToolError::InvalidId("port_list_id".to_string()))?;

        let opts = ModifyTargetOpts {
            name,
            comment,
            hosts: hosts.unwrap_or_default(),
            exclude_hosts: exclude_hosts.unwrap_or_default(),
            alive_test: alive_test_enum,
            port_list_id: port_list,
        };

        client
            .call(modify_target(&id, opts))
            .await
            .map_err(McpToolError::from)?;

        // Fetch updated target
        let response = client
            .send(get_target(&id))
            .await
            .map_err(McpToolError::from)?;

        let parsed = GetTargetsResponse::from_response(&response)
            .map_err(McpToolError::from)?;

        let target = parsed
            .items
            .into_iter()
            .next()
            .ok_or_else(|| McpToolError::NotFound("target", target_id))?;

        let item = TargetItem {
            id: target.meta.id.to_string(),
            name: target.meta.name,
            hosts: target.hosts,
            exclude_hosts: target.exclude_hosts,
            comment: target.meta.comment,
            alive_test: target.alive_tests,
            port_list: target.port_list.map(|pl| NamedRef {
                id: pl.id.to_string(),
                name: pl.name,
            }),
            in_use: target.meta.in_use,
            writable: target.meta.writable,
        };

        Ok(ToolResult::json(item)?)
    }

    /// Delete a target.
    #[tool(name = "openvas_delete_target")]
    pub async fn delete_target(
        &self,
        #[arg(description = "Target UUID to delete")]
        target_id: String,
        #[arg(description = "If true, permanently delete (skip trash)")]
        ultimate: Option<bool>,
    ) -> Result<ToolResult, McpError> {
        let mut client = self.state.client.lock().await;

        let id = target_id
            .parse::<EntityId>()
            .map_err(|_| McpToolError::InvalidId(target_id.clone()))?;

        client
            .call(delete_target(&id, ultimate.unwrap_or(false)))
            .await
            .map_err(McpToolError::from)?;

        let result = ActionResponse {
            success: true,
            target_id,
        };

        Ok(ToolResult::json(result)?)
    }

    /// Clone an existing target.
    #[tool(name = "openvas_clone_target")]
    pub async fn clone_target(
        &self,
        #[arg(description = "Target UUID to clone")]
        target_id: String,
    ) -> Result<ToolResult, McpError> {
        let mut client = self.state.client.lock().await;

        let id = target_id
            .parse::<EntityId>()
            .map_err(|_| McpToolError::InvalidId(target_id.clone()))?;

        let response = client
            .send(clone_target(&id))
            .await
            .map_err(McpToolError::from)?;

        let parsed = CreateTargetResponse::from_response(&response)
            .map_err(McpToolError::from)?;

        // Fetch the cloned target
        let get_response = client
            .send(get_target(&parsed.id))
            .await
            .map_err(McpToolError::from)?;

        let get_parsed = GetTargetsResponse::from_response(&get_response)
            .map_err(McpToolError::from)?;

        let target = get_parsed
            .items
            .into_iter()
            .next()
            .ok_or_else(|| McpToolError::NotFound("target", parsed.id.to_string()))?;

        let item = TargetItem {
            id: target.meta.id.to_string(),
            name: target.meta.name,
            hosts: target.hosts,
            exclude_hosts: target.exclude_hosts,
            comment: target.meta.comment,
            alive_test: target.alive_tests,
            port_list: target.port_list.map(|pl| NamedRef {
                id: pl.id.to_string(),
                name: pl.name,
            }),
            in_use: target.meta.in_use,
            writable: target.meta.writable,
        };

        Ok(ToolResult::json(item)?)
    }
}
```

### 9.2 Application State

```rust
// src/state.rs

use std::sync::Arc;
use tokio::sync::Mutex;

use gvm_client::GmpClient;
use gvm_connection::GvmConnection;

/// Shared application state
pub struct AppState<C: GvmConnection> {
    /// GMP client (mutex for exclusive access)
    pub client: Arc<Mutex<GmpClient<C>>>,
    /// Application configuration
    pub config: Arc<crate::config::AppConfig>,
}

impl<C: GvmConnection> AppState<C> {
    pub fn new(client: GmpClient<C>, config: crate::config::AppConfig) -> Self {
        Self {
            client: Arc::new(Mutex::new(client)),
            config: Arc::new(config),
        }
    }
}
```

### 9.3 Server Setup

```rust
// src/server.rs

use std::sync::Arc;

use gvm_client::GmpClient;
use gvm_connection::{GvmConnection, UnixSocketConfig, UnixSocketConnection};
use rmcp::{McpServer, McpServerBuilder};
use tracing::info;

use crate::config::{AppConfig, TransportType};
use crate::error::AppError;
use crate::state::AppState;
use crate::tools::{
    TargetTools, TaskTools, ReportTools, ScanConfigTools,
    PortListTools, ScheduleTools, VulnTools, NoteTools,
    OverrideTools, TicketTools, AssetTools, ComplianceTools,
    SystemTools,
};

pub async fn create_server(config: AppConfig) -> Result<McpServer, AppError> {
    // Create connection based on transport type
    let connection = match config.connection.transport {
        TransportType::Unix => {
            let unix_config = UnixSocketConfig::new(&config.connection.socket_path);
            UnixSocketConnection::new(unix_config)
        }
        TransportType::Ssh => {
            #[cfg(feature = "ssh")]
            {
                use gvm_connection::{SshAuth, SshConfig, SshConnection};
                let ssh_config = SshConfig::new(
                    config.connection.host.as_ref().unwrap(),
                    config.connection.ssh_user.as_ref().unwrap(),
                    SshAuth::KeyFile(
                        config.connection.ssh_key_path.clone().unwrap(),
                        None,
                    ),
                )
                .with_port(config.connection.port.unwrap_or(22))
                .with_remote_socket(
                    config.connection.remote_socket.as_ref().unwrap(),
                );
                SshConnection::new(ssh_config)
            }
            #[cfg(not(feature = "ssh"))]
            return Err(AppError::FeatureDisabled("ssh"));
        }
        TransportType::Tcp => {
            return Err(AppError::NotImplemented("TCP transport"));
        }
    };

    // Connect and authenticate
    info!("Connecting to gvmd...");
    let mut client = GmpClient::connect(connection).await?;
    info!("Connected, GMP version: {}", client.version());

    client
        .authenticate(&config.auth.username, &config.auth.password)
        .await?;
    info!("Authenticated as {}", config.auth.username);

    // Create shared state
    let state = Arc::new(AppState::new(client, config.clone()));

    // Build MCP server with all tools
    let server = McpServerBuilder::new("gvm-mcp")
        .description("Greenbone Vulnerability Management MCP Server")
        .version(env!("CARGO_PKG_VERSION"))
        // Register tool modules
        .tools(SystemTools::new(state.clone()))
        .tools(TargetTools::new(state.clone()))
        .tools(TaskTools::new(state.clone()))
        .tools(ReportTools::new(state.clone()))
        .tools(ScanConfigTools::new(state.clone()))
        .tools(PortListTools::new(state.clone()))
        .tools(ScheduleTools::new(state.clone()))
        .tools(VulnTools::new(state.clone()))
        .tools(NoteTools::new(state.clone()))
        .tools(OverrideTools::new(state.clone()))
        .tools(TicketTools::new(state.clone()))
        .tools(AssetTools::new(state.clone()))
        .tools(ComplianceTools::new(state.clone()))
        .build()?;

    Ok(server)
}

pub async fn run_server(server: McpServer, config: &AppConfig) -> Result<(), AppError> {
    match config.mcp.transport {
        crate::config::McpTransportType::Stdio => {
            info!("Starting MCP server on stdio...");
            server.run_stdio().await?;
        }
        crate::config::McpTransportType::Sse => {
            let host = config.mcp.sse_host.as_deref().unwrap_or("127.0.0.1");
            let port = config.mcp.sse_port.unwrap_or(8080);
            info!("Starting MCP server on SSE at {}:{}...", host, port);
            server.run_sse(host, port).await?;
        }
    }
    Ok(())
}
```

---

## 10. Error Handling

### 10.1 Error Types

```rust
// src/error.rs

use thiserror::Error;
use gvm_client::GvmError;
use gvm_gmp::responses::common::ParseError;

/// Application-level errors
#[derive(Error, Debug)]
pub enum AppError {
    #[error("Configuration error: {0}")]
    Config(#[from] config::ConfigError),

    #[error("GVM client error: {0}")]
    Gvm(#[from] GvmError),

    #[error("MCP server error: {0}")]
    Mcp(#[from] rmcp::Error),

    #[error("Feature not enabled: {0}")]
    FeatureDisabled(&'static str),

    #[error("Not implemented: {0}")]
    NotImplemented(&'static str),

    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
}

/// MCP tool-level errors
#[derive(Error, Debug)]
pub enum McpToolError {
    #[error("GVM error: {0}")]
    Gvm(#[from] GvmError),

    #[error("Response parse error: {0}")]
    Parse(#[from] ParseError),

    #[error("Invalid ID format: {0}")]
    InvalidId(String),

    #[error("{0} not found: {1}")]
    NotFound(&'static str, String),

    #[error("Invalid parameter: {0}")]
    InvalidParam(String),

    #[error("Operation failed: {0}")]
    OperationFailed(String),
}

impl From<McpToolError> for rmcp::McpError {
    fn from(err: McpToolError) -> Self {
        match err {
            McpToolError::NotFound(resource, id) => {
                rmcp::McpError::ResourceNotFound(format!("{} {}", resource, id))
            }
            McpToolError::InvalidId(id) => {
                rmcp::McpError::InvalidParams(format!("Invalid UUID: {}", id))
            }
            McpToolError::InvalidParam(msg) => {
                rmcp::McpError::InvalidParams(msg)
            }
            _ => rmcp::McpError::InternalError(err.to_string()),
        }
    }
}
```

### 10.2 Error Mapping

| Source Error | MCP Error Code | HTTP-like |
|--------------|----------------|-----------|
| `NotFound` | `ResourceNotFound` | 404 |
| `InvalidId` | `InvalidParams` | 400 |
| `InvalidParam` | `InvalidParams` | 400 |
| `Gvm::Server` | `InternalError` | 500 |
| `Parse` | `InternalError` | 500 |

---

## 11. Testing Strategy

### 11.1 Test Pyramid

```
                    ┌─────────────────┐
                    │   E2E Tests     │  ← Real gvmd (Docker)
                    │   (Few, slow)   │
                    └────────┬────────┘
                             │
               ┌─────────────┴─────────────┐
               │    Integration Tests       │  ← Mock server
               │   (Medium count, faster)   │
               └─────────────┬─────────────┘
                             │
    ┌────────────────────────┴────────────────────────┐
    │                 Unit Tests                       │  ← Static fixtures
    │            (Many, very fast)                     │
    └──────────────────────────────────────────────────┘
```

### 11.2 Unit Tests (Static Fixtures)

Test transformation logic with static XML:

```rust
// tests/unit/targets_test.rs

use gvm_gmp::responses::GetTargetsResponse;
use gvm_protocol::Response;
use pretty_assertions::assert_eq;

const TARGETS_XML: &str = include_str!("../../fixtures/xml/targets/list.xml");

#[test]
fn parses_target_list_response() {
    let response = Response::from(TARGETS_XML);
    let parsed = GetTargetsResponse::from_response(&response).unwrap();

    assert_eq!(parsed.items.len(), 2);
    assert_eq!(parsed.items[0].meta.name, "Web Servers");
    assert_eq!(parsed.items[0].hosts, vec!["192.168.1.0/24"]);
}

#[test]
fn handles_empty_target_list() {
    let xml = r#"<get_targets_response status="200" status_text="OK">
        <target_count>0<filtered>0</filtered></target_count>
    </get_targets_response>"#;

    let response = Response::from(xml);
    let parsed = GetTargetsResponse::from_response(&response).unwrap();

    assert!(parsed.items.is_empty());
    assert_eq!(parsed.counts.total, Some(0));
}
```

### 11.3 Integration Tests (Mock Server)

Test full tool handlers with `gvm-mock-server`:

```rust
// tests/integration/targets_test.rs

use gvm_client::GmpClient;
use gvm_connection::{UnixSocketConfig, UnixSocketConnection};
use gvm_mock_server::{GmpVersion, MockGmpServer, ServerMode};
use rstest::*;
use std::sync::Arc;
use tokio::sync::Mutex;

use gvm_mcp::state::AppState;
use gvm_mcp::tools::TargetTools;

#[fixture]
async fn mock_server() -> MockGmpServer {
    MockGmpServer::builder()
        .mode(ServerMode::Stateful)
        .version(GmpVersion::V22_5)
        .credentials("admin", "admin")
        .unix_socket_auto()
        .build()
        .await
        .unwrap()
}

#[rstest]
#[tokio::test]
async fn test_list_targets_empty(#[future] mock_server: MockGmpServer) {
    let server = mock_server.await;
    let conn = UnixSocketConnection::new(
        UnixSocketConfig::new(server.socket_path().unwrap())
    );
    let mut client = GmpClient::connect(conn).await.unwrap();
    client.authenticate("admin", "admin").await.unwrap();

    let state = Arc::new(AppState::new(client, Default::default()));
    let tools = TargetTools::new(state);

    let result = tools.list_targets(None).await.unwrap();
    let json: serde_json::Value = serde_json::from_str(&result.content).unwrap();

    assert_eq!(json["total"], 0);
    assert!(json["items"].as_array().unwrap().is_empty());

    server.shutdown().await;
}

#[rstest]
#[tokio::test]
async fn test_create_and_get_target(#[future] mock_server: MockGmpServer) {
    let server = mock_server.await;
    let conn = UnixSocketConnection::new(
        UnixSocketConfig::new(server.socket_path().unwrap())
    );
    let mut client = GmpClient::connect(conn).await.unwrap();
    client.authenticate("admin", "admin").await.unwrap();

    let state = Arc::new(AppState::new(client, Default::default()));
    let tools = TargetTools::new(state);

    // Create target
    let result = tools
        .create_target(
            "Test Target".to_string(),
            vec!["192.168.1.0/24".to_string()],
            Some("Test comment".to_string()),
            None, None, None, None, None,
        )
        .await
        .unwrap();

    let created: serde_json::Value = serde_json::from_str(&result.content).unwrap();
    let target_id = created["id"].as_str().unwrap();

    // Get target
    let result = tools.get_target(target_id.to_string()).await.unwrap();
    let fetched: serde_json::Value = serde_json::from_str(&result.content).unwrap();

    assert_eq!(fetched["name"], "Test Target");
    assert_eq!(fetched["hosts"][0], "192.168.1.0/24");

    server.shutdown().await;
}
```

### 11.4 E2E Tests (Docker)

```yaml
# tests/integration/docker-compose.yml

version: '3.8'

services:
  gvmd:
    image: greenbone/gvmd:stable
    environment:
      - GVM_ADMIN_PASSWORD=admin
    volumes:
      - gvmd_socket:/run/gvmd
    healthcheck:
      test: ["CMD", "gvm-cli", "--version"]
      interval: 10s
      timeout: 5s
      retries: 10

  mcp-test:
    build:
      context: ../..
      dockerfile: Dockerfile.test
    depends_on:
      gvmd:
        condition: service_healthy
    environment:
      - GVM_SOCKET_PATH=/run/gvmd/gvmd.sock
      - GVM_USERNAME=admin
      - GVM_PASSWORD=admin
    volumes:
      - gvmd_socket:/run/gvmd:ro

volumes:
  gvmd_socket:
```

---

## 12. CI/CD Pipeline

### 12.1 CI Workflow

```yaml
# .github/workflows/ci.yml

name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  CARGO_TERM_COLOR: always
  RUST_BACKTRACE: 1

jobs:
  check:
    name: Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
      - uses: Swatinem/rust-cache@v2
      - run: cargo check --all-features

  fmt:
    name: Format
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
        with:
          components: rustfmt
      - run: cargo fmt --all -- --check

  clippy:
    name: Clippy
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
        with:
          components: clippy
      - uses: Swatinem/rust-cache@v2
      - run: cargo clippy --all-features -- -D warnings

  test:
    name: Test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
      - uses: Swatinem/rust-cache@v2
      - run: cargo test --all-features

  coverage:
    name: Coverage
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
      - uses: Swatinem/rust-cache@v2
      - uses: taiki-e/install-action@cargo-llvm-cov
      - run: cargo llvm-cov --all-features --lcov --output-path lcov.info
      - uses: codecov/codecov-action@v4
        with:
          files: lcov.info
          fail_ci_if_error: true

  deny:
    name: Deny
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: EmbarkStudios/cargo-deny-action@v1

  msrv:
    name: MSRV
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@1.75.0
      - uses: Swatinem/rust-cache@v2
      - run: cargo check --all-features

  integration:
    name: Integration Tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
      - uses: Swatinem/rust-cache@v2
      - run: cargo test --test '*' --features integration
```

### 12.2 Release Workflow

```yaml
# .github/workflows/release.yml

name: Release

on:
  push:
    tags:
      - 'v*'

permissions:
  contents: write

jobs:
  build:
    name: Build ${{ matrix.target }}
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        include:
          - os: ubuntu-latest
            target: x86_64-unknown-linux-gnu
            artifact: gvm-mcp-linux-amd64
          - os: ubuntu-latest
            target: x86_64-unknown-linux-musl
            artifact: gvm-mcp-linux-amd64-musl
          - os: ubuntu-latest
            target: aarch64-unknown-linux-gnu
            artifact: gvm-mcp-linux-arm64
          - os: macos-latest
            target: x86_64-apple-darwin
            artifact: gvm-mcp-macos-amd64
          - os: macos-latest
            target: aarch64-apple-darwin
            artifact: gvm-mcp-macos-arm64

    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
        with:
          targets: ${{ matrix.target }}
      - uses: Swatinem/rust-cache@v2
      - name: Build
        run: cargo build --release --target ${{ matrix.target }}
      - name: Package
        run: |
          mkdir -p dist
          cp target/${{ matrix.target }}/release/gvm-mcp dist/
          cd dist && tar -czvf ${{ matrix.artifact }}.tar.gz gvm-mcp
      - uses: actions/upload-artifact@v4
        with:
          name: ${{ matrix.artifact }}
          path: dist/${{ matrix.artifact }}.tar.gz

  release:
    name: Release
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/download-artifact@v4
        with:
          path: artifacts
      - name: Create checksums
        run: |
          cd artifacts
          find . -name '*.tar.gz' -exec sh -c 'sha256sum "$1" > "$1.sha256"' _ {} \;
      - name: Release
        uses: softprops/action-gh-release@v1
        with:
          files: artifacts/**/*
          generate_release_notes: true
```

---

## 13. Performance Considerations

### 13.1 Connection Pooling

For high-throughput scenarios, consider connection pooling:

```rust
// Future enhancement: connection pool
use deadpool::managed::{Manager, Pool};

struct GmpConnectionManager {
    config: ConnectionConfig,
}

#[async_trait]
impl Manager for GmpConnectionManager {
    type Type = GmpClient<UnixSocketConnection>;
    type Error = GvmError;

    async fn create(&self) -> Result<Self::Type, Self::Error> {
        let conn = UnixSocketConnection::new(
            UnixSocketConfig::new(&self.config.socket_path)
        );
        let mut client = GmpClient::connect(conn).await?;
        client.authenticate(&self.config.username, &self.config.password).await?;
        Ok(client)
    }

    async fn recycle(&self, client: &mut Self::Type) -> Result<(), Self::Error> {
        // Verify connection is still valid
        client.get_version().await?;
        Ok(())
    }
}
```

### 13.2 Response Caching

For read-heavy workloads:

```rust
use std::time::{Duration, Instant};
use tokio::sync::RwLock;

struct CachedResponse<T> {
    data: T,
    fetched_at: Instant,
}

struct Cache<T> {
    data: RwLock<Option<CachedResponse<T>>>,
    ttl: Duration,
}

impl<T: Clone> Cache<T> {
    async fn get_or_fetch<F, E>(&self, fetch: F) -> Result<T, E>
    where
        F: std::future::Future<Output = Result<T, E>>,
    {
        // Check cache first
        if let Some(cached) = self.data.read().await.as_ref() {
            if cached.fetched_at.elapsed() < self.ttl {
                return Ok(cached.data.clone());
            }
        }

        // Fetch and cache
        let data = fetch.await?;
        *self.data.write().await = Some(CachedResponse {
            data: data.clone(),
            fetched_at: Instant::now(),
        });
        Ok(data)
    }
}
```

### 13.3 Benchmarks

Target performance metrics:

| Operation | Python (baseline) | Rust (target) | Improvement |
|-----------|-------------------|---------------|-------------|
| `list_targets` (10 items) | ~50ms | ~15ms | 3x |
| `create_target` | ~80ms | ~25ms | 3x |
| `start_task` | ~100ms | ~30ms | 3x |
| `get_report_detail` (1000 vulns) | ~500ms | ~100ms | 5x |
| Memory usage (idle) | ~50MB | ~5MB | 10x |
| Binary size | N/A (interpreter) | ~10MB | N/A |

---

## 14. Migration Guide

### 14.1 For MCP Clients

**No changes required.** The Rust implementation exposes identical tool names, parameters, and response schemas.

### 14.2 For Operators

#### Environment Variable Changes

None — same environment variables are supported.

#### Configuration File Changes

New optional TOML format supported alongside environment variables.

#### Deployment Changes

| Aspect | Python | Rust |
|--------|--------|------|
| Runtime | Python 3.10+ | None (static binary) |
| Installation | `pip install` | Download binary |
| Container | Python base image | Scratch/distroless |
| Memory | ~50MB | ~5MB |

#### Example Deployment

```bash
# Download
curl -LO https://github.com/clawosiris/gvm-mcp/releases/latest/download/gvm-mcp-linux-amd64.tar.gz
tar -xzf gvm-mcp-linux-amd64.tar.gz
chmod +x gvm-mcp

# Configure
export GVM_SOCKET_PATH=/run/gvmd/gvmd.sock
export GVM_USERNAME=admin
export GVM_PASSWORD=secret

# Run
./gvm-mcp
```

---

## 15. Implementation Phases

### Phase 1: Foundation (Week 1)

- [ ] Create repository with CI/CD
- [ ] Set up Cargo workspace and dependencies
- [ ] Implement configuration loading
- [ ] Create MCP server skeleton with `rmcp`
- [ ] Implement `AppState` and error types
- [ ] Implement system tools (`get_version`, `test_connection`)
- [ ] Write unit tests for config and errors

**Deliverable:** Working MCP server that connects to gvmd and exposes 2 tools.

### Phase 2: Core CRUD (Week 2)

- [ ] Implement target tools (6 tools)
- [ ] Implement task tools (8 tools)
- [ ] Implement report tools (6 tools)
- [ ] Write unit tests with static fixtures
- [ ] Write integration tests with mock server

**Deliverable:** 22 tools working, core vulnerability scanning workflow functional.

### Phase 3: Supporting Resources (Week 3)

- [ ] Implement scan_config tools (2 tools)
- [ ] Implement port_list tools (2 tools)
- [ ] Implement schedule tools (2 tools)
- [ ] Implement vulnerability/NVT tools (2 tools)
- [ ] Write tests for all new tools

**Deliverable:** 30 tools working, full scan configuration possible.

### Phase 4: Notes, Overrides, Tickets (Week 4)

- [ ] Implement note tools (5 tools)
- [ ] Implement override tools (5 tools)
- [ ] Implement ticket tools (5 tools)
- [ ] Write tests for all new tools

**Deliverable:** 45 tools working, vulnerability management workflow complete.

### Phase 5: Assets & Compliance (Week 5)

- [ ] Implement asset tools (3 tools)
- [ ] Implement compliance tools (6 tools)
- [ ] Write tests for all new tools
- [ ] End-to-end Docker tests

**Deliverable:** All 54 tools working.

### Phase 6: Polish & Release (Week 6)

- [ ] Performance benchmarking
- [ ] Documentation (README, API reference)
- [ ] Cross-platform binary builds
- [ ] Container image (GHCR)
- [ ] Release v0.1.0

**Deliverable:** Production-ready release.

---

## 16. Success Criteria

| Criterion | Target | Measurement |
|-----------|--------|-------------|
| **Tool Parity** | 54/54 tools | Automated comparison |
| **Schema Compatibility** | 100% | JSON schema validation |
| **Test Coverage** | >80% | `cargo llvm-cov` |
| **Performance** | ≥Python baseline | Benchmarks |
| **Documentation** | Complete | README, API docs |
| **CI/CD** | Green | All workflows pass |
| **Cross-platform** | 5 targets | Release artifacts |

---

## 17. Open Questions

### 17.1 Decisions Needed

| Question | Options | Recommendation |
|----------|---------|----------------|
| Repository location | Separate repo vs workspace member | **Separate repo** |
| MCP SDK | `rmcp` vs `mcp-rs` vs custom | **`rmcp`** (most mature) |
| Breaking changes | Strict 1:1 vs improvements | **Strict 1:1** for v1.0 |
| Release coordination | Independent vs coordinated with rust-gvm | **Independent** |

### 17.2 Future Enhancements (Post v1.0)

- Connection pooling for high-throughput
- Response caching
- Streaming for large reports
- WebSocket transport
- Prometheus metrics
- OpenTelemetry tracing

---

## 18. References

### 18.1 Project Links

- [rust-gvm repository](https://github.com/clawosiris/rust-gvm)
- [openvas-mcp-server (Python)](https://github.com/clawosiris/openvas-mcp-server)
- [rmcp crate](https://crates.io/crates/rmcp)

### 18.2 Specifications

- [MCP specification](https://modelcontextprotocol.io/specification)
- [GMP 22.5 documentation](https://docs.greenbone.net/API/GMP/gmp-22.5.html)
- [GMP 22.6 documentation](https://docs.greenbone.net/API/GMP/gmp-22.6.html)

### 18.3 Related Tools

- [python-gvm](https://github.com/greenbone/python-gvm) — Official Python GMP library
- [gvmd](https://github.com/greenbone/gvmd) — Greenbone Vulnerability Manager daemon
- [OpenVAS](https://github.com/greenbone/openvas) — Open Vulnerability Assessment Scanner

---

## Appendix A: Python Tool Signatures

<details>
<summary>Click to expand full Python tool signatures</summary>

```python
# System
def openvas_get_version() -> dict[str, Any]
def openvas_test_connection() -> dict[str, Any]

# Targets
def openvas_list_targets(filter: str = "") -> dict[str, Any]
def openvas_get_target(target_id: str) -> dict[str, Any]
def openvas_create_target(
    name: str,
    hosts: list[str],
    comment: str = "",
    exclude_hosts: list[str] | None = None,
    alive_test: str = "Scan Config Default",
    port_list_id: str | None = None,
    ssh_credential_id: str | None = None,
    smb_credential_id: str | None = None,
) -> dict[str, Any]
def openvas_update_target(
    target_id: str,
    name: str | None = None,
    hosts: list[str] | None = None,
    comment: str | None = None,
    exclude_hosts: list[str] | None = None,
    alive_test: str | None = None,
    port_list_id: str | None = None,
) -> dict[str, Any]
def openvas_delete_target(target_id: str, ultimate: bool = False) -> dict[str, Any]
def openvas_clone_target(target_id: str) -> dict[str, Any]

# Tasks
def openvas_list_tasks(filter: str = "") -> dict[str, Any]
def openvas_get_task(task_id: str) -> dict[str, Any]
def openvas_create_task(
    name: str,
    target_id: str,
    config_id: str,
    scanner_id: str | None = None,
    comment: str = "",
) -> dict[str, Any]
def openvas_start_task(task_id: str) -> dict[str, Any]
def openvas_stop_task(task_id: str) -> dict[str, Any]
def openvas_resume_task(task_id: str) -> dict[str, Any]
def openvas_delete_task(task_id: str, ultimate: bool = False) -> dict[str, Any]
def openvas_clone_task(task_id: str) -> dict[str, Any]

# Reports
def openvas_list_reports(filter: str = "") -> dict[str, Any]
def openvas_get_report(report_id: str) -> dict[str, Any]
def openvas_get_report_detail(report_id: str, min_qod: int = 70) -> dict[str, Any]
def openvas_get_report_summary(report_id: str) -> dict[str, Any]
def openvas_export_report(report_id: str, format: str = "pdf") -> dict[str, Any]
def openvas_delete_report(report_id: str) -> dict[str, Any]

# Scan Configs
def openvas_list_scan_configs(filter: str = "") -> dict[str, Any]
def openvas_get_scan_config(config_id: str) -> dict[str, Any]

# Port Lists
def openvas_list_port_lists(filter: str = "") -> dict[str, Any]
def openvas_get_port_list(port_list_id: str) -> dict[str, Any]

# Schedules
def openvas_list_schedules(filter: str = "") -> dict[str, Any]
def openvas_get_schedule(schedule_id: str) -> dict[str, Any]

# Vulnerabilities
def openvas_list_vulnerabilities(report_id: str, min_qod: int = 70) -> dict[str, Any]
def openvas_search_nvts(query: str) -> dict[str, Any]

# Notes
def openvas_list_notes(filter: str = "") -> dict[str, Any]
def openvas_get_note(note_id: str) -> dict[str, Any]
def openvas_create_note(text: str, nvt_oid: str = "") -> dict[str, Any]
def openvas_update_note(note_id: str, text: str) -> dict[str, Any]
def openvas_delete_note(note_id: str) -> dict[str, Any]

# Overrides
def openvas_list_overrides(filter: str = "") -> dict[str, Any]
def openvas_get_override(override_id: str) -> dict[str, Any]
def openvas_create_override(text: str, nvt_oid: str = "") -> dict[str, Any]
def openvas_update_override(override_id: str, text: str) -> dict[str, Any]
def openvas_delete_override(override_id: str) -> dict[str, Any]

# Tickets
def openvas_list_tickets(filter: str = "") -> dict[str, Any]
def openvas_get_ticket(ticket_id: str) -> dict[str, Any]
def openvas_create_ticket(result_id: str, comment: str = "") -> dict[str, Any]
def openvas_update_ticket(ticket_id: str, status: str, comment: str = "") -> dict[str, Any]
def openvas_delete_ticket(ticket_id: str) -> dict[str, Any]

# Assets
def openvas_list_asset_hosts(filter: str = "") -> dict[str, Any]
def openvas_list_asset_os(filter: str = "") -> dict[str, Any]
def openvas_list_asset_tls_certificates(filter: str = "") -> dict[str, Any]

# Compliance
def openvas_list_compliance_policies() -> dict[str, Any]
def openvas_list_compliance_audits(filter: str = "") -> dict[str, Any]
def openvas_get_compliance_audit(audit_id: str) -> dict[str, Any]
def openvas_start_compliance_audit(audit_id: str) -> dict[str, Any]
def openvas_stop_compliance_audit(audit_id: str) -> dict[str, Any]
def openvas_get_compliance_status(target_id: str) -> dict[str, Any]
```

</details>

---

## Appendix B: Response Schema Examples

<details>
<summary>Click to expand example response schemas</summary>

### Target List Response

```json
{
  "items": [
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "name": "Web Servers",
      "hosts": ["192.168.1.0/24", "10.0.0.1"],
      "exclude_hosts": ["192.168.1.1"],
      "comment": "Production web tier",
      "alive_test": "ICMP Ping",
      "port_list": {
        "id": "p1q2r3s4-t5u6-7890-vwxy-z12345678901",
        "name": "All TCP and Nmap top 100 UDP"
      },
      "in_use": true,
      "writable": true
    }
  ],
  "total": 1
}
```

### Task Detail Response

```json
{
  "id": "t1a2s3k4-i5d6-7890-abcd-ef1234567890",
  "name": "Weekly Web Scan",
  "status": "Done",
  "progress": 100,
  "target": {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "name": "Web Servers"
  },
  "config": {
    "id": "c1o2n3f4-i5g6-7890-abcd-ef1234567890",
    "name": "Full and fast"
  },
  "scanner": {
    "id": "s1c2a3n4-n5e6-7890-abcd-ef1234567890",
    "name": "OpenVAS Default"
  },
  "schedule": {
    "id": "s1c2h3e4-d5u6-7890-abcd-ef1234567890",
    "name": "Weekly Sunday 2AM"
  },
  "last_report": {
    "id": "r1e2p3o4-r5t6-7890-abcd-ef1234567890",
    "timestamp": "2026-03-30T02:45:00Z"
  },
  "report_count": 12,
  "trend": "up",
  "in_use": false,
  "writable": true
}
```

### Report Summary Response

```json
{
  "report_id": "r1e2p3o4-r5t6-7890-abcd-ef1234567890",
  "task_name": "Weekly Web Scan",
  "scan_start": "2026-03-30T02:00:00Z",
  "scan_end": "2026-03-30T02:45:00Z",
  "duration_seconds": 2700,
  "host_count": 15,
  "vulnerability_counts": {
    "critical": 2,
    "high": 8,
    "medium": 25,
    "low": 42,
    "log": 156
  },
  "total_vulnerabilities": 233
}
```

</details>

---

*Document generated: 2026-03-31*  
*Last updated: 2026-03-31*
