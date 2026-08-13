# OpenVAS MCP Server

MCP server for Greenbone Vulnerability Management (GVM/OpenVAS), written in
Rust. A thin, typed MCP front end over the
[rust-gvm-api](https://github.com/greenbone-hive/rust-gvm-api) REST gateway:
all GMP/gvmd knowledge lives in the gateway, this server maps MCP tools onto
gateway HTTP endpoints.

[![CI](https://github.com/clawosiris/openvas-mcp-server/actions/workflows/ci.yml/badge.svg)](https://github.com/clawosiris/openvas-mcp-server/actions/workflows/ci.yml)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

```text
MCP client (Claude, etc.)
        │  stdio / streamable HTTP
        ▼
      gvm-mcp  (this repo, single binary)
        │  HTTP/JSON + ephemeral bearer session
        ▼
  rust-gvm-api REST gateway  (/api/v1)
        │  GMP over Unix socket
        ▼
      gvmd
```

> [!NOTE]
> The previous Python implementation (MCP server + CLI) lives under
> [`legacy/`](legacy/) until the Rust server's first tagged release, then it
> will be removed. See the [migration note](#migrating-from-the-python-server).

## Quick start

### Docker (streamable HTTP)

```bash
docker run --rm \
  -e GVM_GATEWAY_URL=http://gateway:8080 \
  -e GVM_USERNAME=admin \
  -e GVM_PASSWORD=secret \
  -p 127.0.0.1:8000:8000 \
  ghcr.io/clawosiris/openvas-mcp-server:latest
```

MCP endpoint: `http://localhost:8000/mcp`. A full stack example (gateway +
gvmd socket wiring) is in
[docker-compose.example.yml](docker-compose.example.yml).

### Binary (stdio)

Download a release binary (or `cargo build --release`), then register it with
your MCP client:

```json
{
  "mcpServers": {
    "openvas": {
      "command": "/path/to/gvm-mcp",
      "env": {
        "GVM_GATEWAY_URL": "http://localhost:8080",
        "GVM_USERNAME": "admin",
        "GVM_PASSWORD": "secret"
      }
    }
  }
}
```

Start with the `openvas_test_connection` tool — it checks gateway liveness,
the gvmd version and an authenticated session round-trip.

## Configuration

Every flag has an environment variable. Credentials are the gvmd account the
server uses to create short-lived gateway sessions (renewed automatically).

| Flag | Env | Default | Purpose |
| ---- | --- | ------- | ------- |
| `--gateway-url` | `GVM_GATEWAY_URL` | `http://127.0.0.1:8080` | rust-gvm-api origin (without `/api/v1`) |
| `--username` | `GVM_USERNAME` | — | gvmd username |
| `--password` | `GVM_PASSWORD` | — | gvmd password |
| `--password-file` | `GVM_PASSWORD_FILE` | — | file containing the password (takes precedence) |
| `--transport` | `MCP_TRANSPORT` | `stdio` | `stdio` or `streamable-http` |
| `--bind-addr` | `MCP_BIND_ADDR` | `127.0.0.1:8000` | HTTP bind address |
| `--allowed-hosts` | `MCP_ALLOWED_HOSTS` | `localhost,127.0.0.1,::1` | Host-header allow list (`*` disables) |
| `--toolsets` | `GVM_TOOLSETS` | `default` | comma-separated toolset selection |
| `--read-only` | `GVM_READ_ONLY` | `false` | expose only non-mutating tools |
| `--timeout-secs` | `GVM_HTTP_TIMEOUT` | `30` | gateway HTTP timeout |
| `--log-level` | `GVM_LOG_LEVEL` | `info` | log level when `RUST_LOG` unset |

## Toolsets

The full surface is 103 tools — far too many to hand an LLM by default, so
tools are grouped into toolsets (`gvm-mcp --list-toolsets` prints them all).
The default selection is every toolset except `identity`; add it explicitly
with `--toolsets default,identity`. `--read-only` additionally strips every
mutating tool from the listing.

| Selection | Tools |
| --------- | ----- |
| default | 80 |
| default, read-only | 48 |
| default + identity | 103 |

Highlights:

- **targets / tasks** — CRUD plus the scan lifecycle
  (`openvas_start_task` → report UUID, stop, resume).
- **reports** — list/get, drill-down pages (results, vulnerabilities,
  errors, closed CVEs, TLS certificates) and asynchronous exports:
  `openvas_export_report` → poll `openvas_get_job` →
  `openvas_download_job_result` (JSON inline, binary formats base64 up to
  3 MB).
- **scan-configs / scanners / schedules / credentials / alerts /
  port-lists / notes / overrides** — reads everywhere, writes where the
  gateway supports them.
- **nvts / results / assets / feeds / tickets / filters / tags /
  report-formats** — read surface with GMP filter expressions
  (`filter: "severity>7 and host=10.0.0.5"`).
- **identity** (opt-in) — users, groups, roles, permissions, user settings.

List tools return summarized rows plus pagination to protect the model's
token budget; `get` tools return the gateway's full JSON.

## Development

```bash
cargo test                                    # unit + mock-gateway tests
cargo fmt --all && cargo clippy --all-targets --all-features -- -D warnings
cargo run -- --list-toolsets
```

The test suite runs entirely against a mock gateway (wiremock) — no GVM
installation needed. End-to-end tests against a live stack are gated behind
`#[ignore]`:

```bash
export GVM_E2E_GATEWAY_URL=http://localhost:8080
export GVM_USERNAME=admin GVM_PASSWORD=secret
cargo test --test e2e_live -- --ignored
```

DTOs and endpoint shapes mirror the gateway's
[`spec/rest-api`](https://github.com/greenbone-hive/rust-gvm-api/tree/main/spec/rest-api)
contract. See [docs/mcp](docs/mcp/) for detailed install/usage/development
guides.

## Migrating from the Python server

Tool names are unchanged (`openvas_*`), so existing prompts keep working.
The differences that matter:

- The server no longer speaks GMP directly — it requires a running
  [rust-gvm-api](https://github.com/greenbone-hive/rust-gvm-api) gateway
  (`GVM_SOCKET_PATH`/`GVM_STYLE` are gone, `GVM_GATEWAY_URL` is new).
- The Python `openvas` CLI is not part of the Rust server; it remains in
  [`legacy/`](legacy/) until removal.
- `openvas_clone_*` and ticket/filter/tag/host write tools are not exposed
  yet: the gateway does not serve those endpoints. They return once the
  gateway does.

## License

AGPL-3.0-or-later.
