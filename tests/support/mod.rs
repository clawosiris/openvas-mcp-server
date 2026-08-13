//! Shared helpers for mock-gateway integration tests.
#![allow(dead_code)] // each test binary uses a different subset

use clap::Parser;
use gvm_mcp::config::{Cli, Config};
use wiremock::matchers::{basic_auth, method, path};
use wiremock::{Mock, MockServer, ResponseTemplate};

pub const USERNAME: &str = "admin";
pub const PASSWORD: &str = "s3cret";

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

/// JSON body of a `201 Created` session response.
pub fn session_created_body(token: &str) -> serde_json::Value {
    serde_json::json!({
        "sessionToken": token,
        "expiresIn": 300,
        "gmpVersion": "22.7"
    })
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

/// Mount a login mock that issues `token` once, verifying Basic credentials.
pub async fn mount_login_once(server: &MockServer, token: &str) {
    Mock::given(method("POST"))
        .and(path("/api/v1/session"))
        .and(basic_auth(USERNAME, PASSWORD))
        .respond_with(ResponseTemplate::new(201).set_body_json(session_created_body(token)))
        .up_to_n_times(1)
        .expect(1)
        .mount(server)
        .await;
}
