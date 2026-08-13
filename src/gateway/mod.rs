//! HTTP client for the `rust-gvm-api` REST gateway.

pub mod auth;
pub mod client;
pub mod error;
pub mod models;

pub use client::GatewayClient;
pub use error::{GatewayError, ProblemDetail};
