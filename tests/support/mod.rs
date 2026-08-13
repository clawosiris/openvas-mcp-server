//! Shared helpers for mock-gateway integration tests.
#![allow(dead_code)] // each test binary uses a different subset

use clap::Parser;
use gvm_mcp::config::{Cli, Config};
use wiremock::MockServer;
use wiremock::ResponseTemplate;

pub const USERNAME: &str = "admin";
pub const PASSWORD: &str = "s3cret";

/// The `Authorization` header the client sends for `USERNAME`/`PASSWORD`
/// (`Basic base64(admin:s3cret)`), for tests that assert credential forwarding.
pub const EXPECTED_BASIC: &str = "Basic YWRtaW46czNjcmV0";

/// Config pointing at a mock gateway.
pub fn config_for(server: &MockServer) -> Config {
    config_with_args(server, &[])
}

/// Config pointing at a mock gateway, with extra CLI flags
/// (e.g. `&["--read-only"]` or `&["--toolsets", "tasks"]`).
pub fn config_with_args(server: &MockServer, extra: &[&str]) -> Config {
    let uri = server.uri();
    let mut args = vec![
        "gvm-mcp",
        "--gateway-url",
        &uri,
        "--username",
        USERNAME,
        "--password",
        PASSWORD,
    ];
    args.extend_from_slice(extra);
    let cli = Cli::parse_from(args);
    Config::from_cli(cli).expect("test config must be valid")
}

/// Config pointing at a port that is guaranteed to have no listener:
/// bind an ephemeral port, read it back, then release it.
pub fn config_for_dead_port() -> Config {
    let listener = std::net::TcpListener::bind("127.0.0.1:0").unwrap();
    let port = listener.local_addr().unwrap().port();
    drop(listener);

    let url = format!("http://127.0.0.1:{port}");
    let cli = Cli::parse_from([
        "gvm-mcp",
        "--gateway-url",
        &url,
        "--username",
        USERNAME,
        "--password",
        PASSWORD,
        "--timeout-secs",
        "2",
    ]);
    Config::from_cli(cli).expect("test config must be valid")
}

/// An RFC 9457 problem+json response with the gateway's content type.
pub fn problem_response(status: u16, code: &str, title: &str) -> ResponseTemplate {
    ResponseTemplate::new(status).set_body_raw(
        serde_json::json!({
            "type": format!("https://gvm-gateway.greenbone.net/errors/{code}"),
            "code": code,
            "title": title,
            "status": status,
            "detail": format!("{title} (test detail)")
        })
        .to_string(),
        "application/problem+json",
    )
}
