# Development

## Layout

```text
src/
  main.rs            CLI entry: transport selection, logging (stderr)
  config.rs          clap CLI → validated Config
  gateway/           HTTP client for the rust-gvm-api gateway
    client.rs        request plumbing; attaches per-request Authorization
    auth.rs          caller-identity forwarding (task-local) + Basic fallback
    models.rs        serde DTOs mirroring the gateway spec
    error.rs         RFC 9457 problem+json → typed GatewayError
  mcp/
    server.rs        router composition, toolset + read-only gating
    toolset.rs       Toolset enum and --toolsets parsing
    error.rs         GatewayError → legible tool errors
    http.rs          streamable-HTTP transport (axum)
    tools/           one module per toolset; each exports <name>_router
tests/               mock-gateway (wiremock) integration tests
```

Principles (from the roadmap): no business logic in this server — a tool is
validate args → build gateway request → map response/error. Identity
forwarding (the caller's `Authorization`, scoped per call by `server.rs`'s
`call_tool`) and pagination are the only cross-cutting "smart" pieces. List
output is
summarized (token budget); `get` output is the gateway's JSON, unchanged.

## Adding a tool

1. Find the endpoint in the gateway's `spec/rest-api/*.yaml` (the contract).
2. Add the tool to the matching `src/mcp/tools/<toolset>.rs` under the
   `#[tool_router(router = <toolset>_router, ...)]` impl block. Reuse the
   `common.rs` helpers (`list_summarized`, `get_passthrough`,
   `create_resource`, `update_resource`, `delete_resource`, `Body`).
3. Annotate honestly: `read_only_hint = true` for reads (this is what
   `--read-only` filters on), `destructive_hint` for updates/deletes.
4. If it starts a new toolset, wire the router in `server.rs` and extend
   `toolset.rs`.
5. Add a wiremock test asserting the request shape (path, query, body) and
   the summarized output, and bump the inventory count in
   `tests/gating.rs`.

## Quality gate

```bash
cargo fmt --all --check
cargo clippy --all-targets --all-features -- -D warnings
cargo test
```

CI runs the same gate plus a release build with a CLI smoke test.

## Live end-to-end tests

`tests/e2e_live.rs` is `#[ignore]`d and drives a real gateway + gvmd:

```bash
export GVM_E2E_GATEWAY_URL=http://localhost:8080
export GVM_USERNAME=admin GVM_PASSWORD=secret
cargo test --test e2e_live -- --ignored          # read-only checks
GVM_E2E_SCAN=1 cargo test --test e2e_live -- --ignored   # + full scan lifecycle
```

The scan lifecycle test creates a target and task named `gvm-mcp-e2e-*`,
starts a scan against `127.0.0.1`, waits for it to finish and deletes what
it created.

## Releasing

Tag `v*` on main. The release workflow builds binaries for
linux/macOS (x86_64 + aarch64), attaches SHA-256 sums, and pushes the
Docker image to GHCR.
