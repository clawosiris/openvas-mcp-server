//! Streamable-HTTP transport: serves the MCP server at `/mcp`.
//!
//! Simple request/response tool calls answer as `application/json`, falling
//! back to SSE only when a handler streams. The server holds one shared gvmd
//! service account — a multi-tenant per-connection credential model is a
//! deliberate non-goal until the gateway grows an auth story for it.
//!
//! Inbound authentication is optional and off by default: with no auth token
//! configured the endpoint is unauthenticated (fine for stdio, or HTTP behind
//! a trusted proxy). When a token is set, every request must carry
//! `Authorization: Bearer <token>`.

use axum::extract::Request;
use axum::http::{StatusCode, header};
use axum::middleware::Next;
use axum::response::IntoResponse;
use secrecy::{ExposeSecret, SecretString};

use rmcp::transport::streamable_http_server::StreamableHttpService;
use rmcp::transport::streamable_http_server::session::local::LocalSessionManager;
use rmcp::transport::streamable_http_server::tower::StreamableHttpServerConfig;

use super::server::GvmMcpServer;

/// Constant-time byte comparison, so token checks do not leak length-prefix
/// information through timing.
fn constant_time_eq(a: &[u8], b: &[u8]) -> bool {
    if a.len() != b.len() {
        return false;
    }
    let mut diff = 0u8;
    for (x, y) in a.iter().zip(b) {
        diff |= x ^ y;
    }
    diff == 0
}

/// Serve `server` on `listener` until `shutdown` resolves.
///
/// `allowed_hosts` guards against DNS-rebinding: requests whose `Host` header
/// is not listed are rejected. The single entry `"*"` disables the check (only
/// sensible behind a reverse proxy that validates Host itself). When
/// `auth_token` is `Some`, requests must present `Authorization: Bearer
/// <token>`; otherwise the endpoint requires no authentication.
pub async fn serve(
    server: GvmMcpServer,
    listener: tokio::net::TcpListener,
    allowed_hosts: &[String],
    auth_token: Option<SecretString>,
    shutdown: impl std::future::Future<Output = ()> + Send + 'static,
) -> anyhow::Result<()> {
    let mut config = StreamableHttpServerConfig::default().with_json_response(true);
    if allowed_hosts.iter().any(|host| host == "*") {
        config = config.disable_allowed_hosts();
    } else if !allowed_hosts.is_empty() {
        config = config.with_allowed_hosts(allowed_hosts.iter().cloned());
    }

    let service = StreamableHttpService::new(
        move || Ok(server.clone()),
        LocalSessionManager::default().into(),
        config,
    );

    let mut router = axum::Router::new().nest_service("/mcp", service);

    if let Some(token) = auth_token {
        // Precompute the full expected header value once.
        let expected: std::sync::Arc<str> =
            std::sync::Arc::from(format!("Bearer {}", token.expose_secret()));
        tracing::info!("streamable-http endpoint requires bearer-token authentication");
        router = router.layer(axum::middleware::from_fn(
            move |req: Request, next: Next| {
                let expected = expected.clone();
                async move {
                    let presented = req
                        .headers()
                        .get(header::AUTHORIZATION)
                        .and_then(|value| value.to_str().ok());
                    match presented {
                        Some(value) if constant_time_eq(value.as_bytes(), expected.as_bytes()) => {
                            next.run(req).await
                        }
                        _ => (StatusCode::UNAUTHORIZED, "unauthorized").into_response(),
                    }
                }
            },
        ));
    } else {
        tracing::warn!(
            "streamable-http endpoint has no inbound authentication; set --auth-token \
             (MCP_AUTH_TOKEN) or front it with an authenticating reverse proxy"
        );
    }

    axum::serve(listener, router)
        .with_graceful_shutdown(shutdown)
        .await?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn constant_time_eq_matches_and_rejects() {
        assert!(constant_time_eq(b"Bearer abc", b"Bearer abc"));
        assert!(!constant_time_eq(b"Bearer abc", b"Bearer abd"));
        assert!(!constant_time_eq(b"Bearer abc", b"Bearer ab"));
        assert!(!constant_time_eq(b"", b"x"));
    }
}
