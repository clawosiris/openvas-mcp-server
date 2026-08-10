//! MCP layer: server wiring, toolset gating, error mapping.

pub mod error;
pub mod server;
pub mod toolset;

pub use server::GvmMcpServer;
