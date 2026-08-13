//! HTTP client for the `rust-gvm-api` REST gateway.

pub mod client;
pub mod error;
pub mod models;
pub mod session;

pub use client::GatewayClient;
pub use error::{GatewayError, ProblemDetail};
pub use session::SessionManager;
