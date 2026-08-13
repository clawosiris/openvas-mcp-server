//! Mock-gateway tests for per-request identity forwarding: the client sends
//! the configured fallback `Basic` credential (no session, no login), surfaces
//! the gateway's typed errors, and distinguishes transport failures.

mod support;

use gvm_mcp::gateway::{GatewayClient, GatewayError};
use support::{EXPECTED_BASIC, config_for, problem_response};
use wiremock::matchers::{header, method, path};
use wiremock::{Mock, MockServer, ResponseTemplate};

#[tokio::test]
async fn sends_fallback_basic_and_never_creates_a_session() {
    let server = MockServer::start().await;
    // No /session endpoint is mounted: an unmatched request 404s. The client
    // must authenticate the resource call directly with Basic.
    Mock::given(method("GET"))
        .and(path("/api/v1/targets"))
        .and(header("authorization", EXPECTED_BASIC))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({
            "data": [],
            "pagination": {"page": 1, "perPage": 25, "total": 0, "totalPages": 0}
        })))
        .expect(1)
        .mount(&server)
        .await;

    let client = GatewayClient::new(&config_for(&server)).unwrap();
    let value: serde_json::Value = client.get_json(&["targets"]).await.unwrap();
    assert_eq!(value["pagination"]["total"], 0);
}

#[tokio::test]
async fn problem_json_maps_to_typed_api_error() {
    let server = MockServer::start().await;
    Mock::given(method("GET"))
        .and(path("/api/v1/targets/missing"))
        .respond_with(problem_response(404, "not_found", "Resource Not Found"))
        .mount(&server)
        .await;

    let client = GatewayClient::new(&config_for(&server)).unwrap();
    let err = client
        .get_json::<serde_json::Value>(&["targets", "missing"])
        .await
        .unwrap_err();
    match err {
        GatewayError::Api(problem) => {
            assert_eq!(problem.code, "not_found");
            assert_eq!(problem.status, 404);
        }
        other => panic!("expected Api error, got: {other:?}"),
    }
}

#[tokio::test]
async fn rejected_identity_surfaces_as_401() {
    let server = MockServer::start().await;
    Mock::given(method("GET"))
        .and(path("/api/v1/targets"))
        .respond_with(problem_response(401, "unauthorized", "Unauthorized"))
        .mount(&server)
        .await;

    let client = GatewayClient::new(&config_for(&server)).unwrap();
    let err = client
        .get_json::<serde_json::Value>(&["targets"])
        .await
        .unwrap_err();
    assert_eq!(err.status(), Some(401));
    assert!(err.is_unauthorized());
}

#[tokio::test]
async fn non_problem_error_maps_to_unexpected_status() {
    let server = MockServer::start().await;
    Mock::given(method("GET"))
        .and(path("/api/v1/targets"))
        .respond_with(ResponseTemplate::new(500).set_body_string("plain text crash"))
        .mount(&server)
        .await;

    let client = GatewayClient::new(&config_for(&server)).unwrap();
    let err = client
        .get_json::<serde_json::Value>(&["targets"])
        .await
        .unwrap_err();
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
    let err = client
        .get_json::<serde_json::Value>(&["targets"])
        .await
        .unwrap_err();
    assert!(matches!(err, GatewayError::Transport(_)), "got: {err:?}");
}
