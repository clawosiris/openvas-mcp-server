//! Mock-gateway tests for the session lifecycle: lazy login, bearer
//! injection, single-flight renewal on 401, and typed error mapping.

mod support;

use gvm_mcp::gateway::{GatewayClient, GatewayError};
use support::{config_for, mount_login_once, problem_response, session_created_body};
use wiremock::matchers::{basic_auth, bearer_token, method, path};
use wiremock::{Mock, MockServer, ResponseTemplate};

fn session_info_body(user: &str) -> serde_json::Value {
    serde_json::json!({
        "user": user,
        "state": "active",
        "createdAt": "2026-08-09T21:00:00Z",
        "lastUsedAt": "2026-08-09T21:01:00Z",
        "expiresIn": 300
    })
}

#[tokio::test]
async fn logs_in_lazily_and_sends_bearer_token() {
    let server = MockServer::start().await;
    mount_login_once(&server, "token-a").await;

    Mock::given(method("GET"))
        .and(path("/api/v1/session"))
        .and(bearer_token("token-a"))
        .respond_with(ResponseTemplate::new(200).set_body_json(session_info_body("admin")))
        .expect(1)
        .mount(&server)
        .await;

    let client = GatewayClient::new(&config_for(&server)).unwrap();
    let info = client.session_info().await.unwrap();
    assert_eq!(info.user, "admin");
    assert_eq!(info.state, "active");
}

#[tokio::test]
async fn renews_session_once_on_401_and_retries() {
    let server = MockServer::start().await;

    // First login issues token-a, second login issues token-b.
    mount_login_once(&server, "token-a").await;
    Mock::given(method("POST"))
        .and(path("/api/v1/session"))
        .respond_with(ResponseTemplate::new(201).set_body_json(session_created_body("token-b")))
        .up_to_n_times(1)
        .expect(1)
        .mount(&server)
        .await;

    // token-a is always rejected as expired; token-b succeeds.
    Mock::given(method("GET"))
        .and(path("/api/v1/session"))
        .and(bearer_token("token-a"))
        .respond_with(problem_response(401, "session_expired", "Session Expired"))
        .expect(1)
        .mount(&server)
        .await;
    Mock::given(method("GET"))
        .and(path("/api/v1/session"))
        .and(bearer_token("token-b"))
        .respond_with(ResponseTemplate::new(200).set_body_json(session_info_body("admin")))
        .expect(1)
        .mount(&server)
        .await;

    let client = GatewayClient::new(&config_for(&server)).unwrap();
    let info = client.session_info().await.unwrap();
    assert_eq!(info.user, "admin");
    // Mock expectations verify: exactly two logins, one 401, one retry.
}

#[tokio::test]
async fn concurrent_401s_trigger_a_single_renewal() {
    let server = MockServer::start().await;

    mount_login_once(&server, "token-a").await;
    // Exactly one renewal login is allowed; a third login would fail the
    // `expect(1)` below and any unmatched request returns 404.
    Mock::given(method("POST"))
        .and(path("/api/v1/session"))
        .respond_with(ResponseTemplate::new(201).set_body_json(session_created_body("token-b")))
        .up_to_n_times(1)
        .expect(1)
        .mount(&server)
        .await;

    // Warm-up: token-a works exactly once, then expires.
    Mock::given(method("GET"))
        .and(path("/api/v1/session"))
        .and(bearer_token("token-a"))
        .respond_with(ResponseTemplate::new(200).set_body_json(session_info_body("admin")))
        .up_to_n_times(1)
        .mount(&server)
        .await;
    Mock::given(method("GET"))
        .and(path("/api/v1/session"))
        .and(bearer_token("token-a"))
        .respond_with(problem_response(401, "session_expired", "Session Expired"))
        .mount(&server)
        .await;
    Mock::given(method("GET"))
        .and(path("/api/v1/session"))
        .and(bearer_token("token-b"))
        .respond_with(ResponseTemplate::new(200).set_body_json(session_info_body("admin")))
        .mount(&server)
        .await;

    let client = GatewayClient::new(&config_for(&server)).unwrap();
    client.session_info().await.unwrap();

    // Eight concurrent calls all hit the expired token-a and race to renew;
    // single-flight must collapse them into one login.
    let results = tokio::join!(
        client.session_info(),
        client.session_info(),
        client.session_info(),
        client.session_info(),
        client.session_info(),
        client.session_info(),
        client.session_info(),
        client.session_info(),
    );
    let results = [
        results.0, results.1, results.2, results.3, results.4, results.5, results.6, results.7,
    ];
    for result in results {
        assert_eq!(result.unwrap().user, "admin");
    }
}

#[tokio::test]
async fn bad_credentials_surface_as_typed_401() {
    let server = MockServer::start().await;
    Mock::given(method("POST"))
        .and(path("/api/v1/session"))
        .and(basic_auth(support::USERNAME, support::PASSWORD))
        .respond_with(problem_response(401, "unauthorized", "Unauthorized"))
        .mount(&server)
        .await;

    let client = GatewayClient::new(&config_for(&server)).unwrap();
    let err = client.session_info().await.unwrap_err();
    match err {
        GatewayError::Api(problem) => {
            assert_eq!(problem.status, 401);
            assert_eq!(problem.code, "unauthorized");
        }
        other => panic!("expected Api error, got: {other:?}"),
    }
}

#[tokio::test]
async fn problem_json_maps_to_typed_api_error() {
    let server = MockServer::start().await;
    mount_login_once(&server, "token-a").await;
    Mock::given(method("GET"))
        .and(path("/api/v1/session"))
        .respond_with(problem_response(404, "not_found", "Resource Not Found"))
        .mount(&server)
        .await;

    let client = GatewayClient::new(&config_for(&server)).unwrap();
    let err = client.session_info().await.unwrap_err();
    match err {
        GatewayError::Api(problem) => {
            assert_eq!(problem.code, "not_found");
            assert_eq!(problem.status, 404);
            assert!(problem.detail.is_some());
        }
        other => panic!("expected Api error, got: {other:?}"),
    }
}

#[tokio::test]
async fn non_problem_error_maps_to_unexpected_status() {
    let server = MockServer::start().await;
    mount_login_once(&server, "token-a").await;
    Mock::given(method("GET"))
        .and(path("/api/v1/session"))
        .respond_with(ResponseTemplate::new(500).set_body_string("plain text crash"))
        .mount(&server)
        .await;

    let client = GatewayClient::new(&config_for(&server)).unwrap();
    let err = client.session_info().await.unwrap_err();
    match err {
        GatewayError::UnexpectedStatus { status, body } => {
            assert_eq!(status, 500);
            assert!(body.contains("plain text crash"));
        }
        other => panic!("expected UnexpectedStatus, got: {other:?}"),
    }
}

#[tokio::test]
async fn unreachable_gateway_maps_to_transport_error() {
    let config = support::config_for_dead_port();
    let client = GatewayClient::new(&config).unwrap();
    let err = client.session_info().await.unwrap_err();
    assert!(matches!(err, GatewayError::Transport(_)), "got: {err:?}");
}
