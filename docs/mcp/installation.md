# Installation

The MCP server needs a running
[rust-gvm-api](https://github.com/greenbone-hive/rust-gvm-api) REST gateway
in front of gvmd. It never speaks GMP itself.

## Prerequisites

- A gvmd installation — typically the
  [Greenbone Community Edition](https://greenbone.github.io/docs/latest/)
  containers.
- The rust-gvm-api gateway attached to gvmd's Unix socket, listening on
  HTTP (default assumed here: `http://localhost:8080`).
- A gvmd account for the server. Prefer a dedicated account; combine with
  `--read-only` for reporting-only setups.

## Option 1: Docker

```bash
docker run --rm \
  -e GVM_GATEWAY_URL=http://gateway:8080 \
  -e GVM_USERNAME=admin \
  -e GVM_PASSWORD=secret \
  -p 127.0.0.1:8000:8000 \
  ghcr.io/clawosiris/openvas-mcp-server:latest
```

The image is distroless, runs as nonroot and defaults to the
streamable-HTTP transport on `0.0.0.0:8000` with the Host-header check
disabled (`MCP_ALLOWED_HOSTS=*`) for container networks — front it with a
reverse proxy if you expose it beyond localhost.

A compose file wiring gateway + MCP server is provided in
[docker-compose.example.yml](../../docker-compose.example.yml).

## Option 2: Release binary

Download the archive for your platform from the GitHub releases page,
verify the checksum, unpack, and place `gvm-mcp` on your `PATH`:

```bash
tar xzf gvm-mcp-<version>-<target>.tar.gz
shasum -c gvm-mcp-<version>-<target>.tar.gz.sha256
```

## Option 3: Build from source

```bash
git clone https://github.com/clawosiris/openvas-mcp-server.git
cd openvas-mcp-server
cargo build --release      # requires Rust 1.90+
./target/release/gvm-mcp --help
```

## MCP client registration

### stdio (Claude Desktop / Claude Code)

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

### Streamable HTTP

Run the server with `--transport streamable-http`, then register the URL:

```json
{
  "mcpServers": {
    "openvas": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

## Secrets

Prefer `GVM_PASSWORD_FILE` (a mounted secret file) over `GVM_PASSWORD` in
production; it takes precedence when both are set. The password never
appears in logs, `Debug` output or MCP responses, and the gateway bearer
token is renewed automatically when it expires.
