//! MCP server for Greenbone Vulnerability Management (GVM/OpenVAS).
//!
//! Thin, typed MCP front end over the `rust-gvm-api` REST gateway. All GMP
//! knowledge lives in the gateway; this crate only maps MCP tools onto gateway
//! HTTP endpoints. See `docs/rust-mcp-server-spec.md` for the tool inventory.

pub mod config;
pub mod gateway;
pub mod mcp;
