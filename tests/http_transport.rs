//! Streamable-HTTP transport tests: a real TCP listener served by the MCP
//! server, driven with plain JSON-RPC over HTTP.

mod support;

use gvm_mcp::mcp::GvmMcpServer;
use support::config_for;
use wiremock::matchers::{header, method, path};
use wiremock::{Mock, MockServer, ResponseTemplate};

async fn spawn_http_server(allowed_hosts: &[&str]) -> (std::net::SocketAddr, MockServer) {
    let gateway = MockServer::start().await;
    let mcp = GvmMcpServer::new(config_for(&gateway)).unwrap();
    let listener = tokio::net::TcpListener::bind("127.0.0.1:0").await.unwrap();
    let addr = listener.local_addr().unwrap();
    let hosts: Vec<String> = allowed_hosts.iter().map(|h| h.to_string()).collect();
    tokio::spawn(async move {
        gvm_mcp::mcp::http::serve(mcp, listener, &hosts, std::future::pending())
            .await
            .unwrap();
    });
    (addr, gateway)
}

/// Extract the JSON-RPC payload whether the body is plain JSON or a single
/// SSE `data:` frame.
fn parse_payload(text: &str) -> serde_json::Value {
    // SSE streams may open with an empty priming frame; take the last
    // data frame that actually carries JSON.
    let json_text = text
        .lines()
        .rev()
        .find_map(|line| {
            line.strip_prefix("data: ")
                .filter(|data| !data.trim().is_empty())
        })
        .unwrap_or(text);
    serde_json::from_str(json_text).unwrap_or_else(|err| panic!("bad payload ({err}): {text}"))
}

fn initialize_body() -> serde_json::Value {
    serde_json::json!({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "0.0.1"}
        }
    })
}

#[tokio::test]
async fn initialize_and_list_tools_over_http() {
    let (addr, _gateway) = spawn_http_server(&["127.0.0.1"]).await;
    let client = reqwest::Client::new();
    let url = format!("http://{addr}/mcp");

    let init = client
        .post(&url)
        .header("Accept", "application/json, text/event-stream")
        .json(&initialize_body())
        .send()
        .await
        .unwrap();
    assert!(init.status().is_success(), "init failed: {}", init.status());
    let session_id = init
        .headers()
        .get("mcp-session-id")
        .and_then(|v| v.to_str().ok())
        .map(str::to_owned);
    let body = parse_payload(&init.text().await.unwrap());
    assert_eq!(body["result"]["serverInfo"]["name"], "gvm-mcp");

    let mut notified = client
        .post(&url)
        .header("Accept", "application/json, text/event-stream")
        .json(&serde_json::json!({"jsonrpc": "2.0", "method": "notifications/initialized"}));
    let mut list = client
        .post(&url)
        .header("Accept", "application/json, text/event-stream")
        .json(&serde_json::json!({
            "jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}
        }));
    if let Some(session) = &session_id {
        notified = notified.header("mcp-session-id", session.clone());
        list = list.header("mcp-session-id", session.clone());
    }
    notified.send().await.unwrap();

    let list = list.send().await.unwrap();
    assert!(list.status().is_success(), "list failed: {}", list.status());
    let body = parse_payload(&list.text().await.unwrap());
    let tools = body["result"]["tools"].as_array().unwrap();
    assert!(
        tools
            .iter()
            .any(|tool| tool["name"] == "openvas_test_connection"),
        "expected openvas_test_connection in tool list"
    );
}

#[tokio::test]
async fn inbound_authorization_is_forwarded_to_the_gateway() {
    let (addr, gateway) = spawn_http_server(&["127.0.0.1"]).await;

    // The gateway answers the tool's list call only when it carries the
    // caller's bearer token — proving the inbound Authorization is forwarded,
    // overriding the configured fallback Basic credential.
    Mock::given(method("GET"))
        .and(path("/api/v1/targets"))
        .and(header("authorization", "Bearer caller-token"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({
            "data": [{"id": "tg-1", "name": "webservers", "hosts": ["10.0.0.0/24"]}],
            "pagination": {"page": 1, "perPage": 25, "total": 1, "totalPages": 1}
        })))
        .expect(1)
        .mount(&gateway)
        .await;

    let client = reqwest::Client::new();
    let url = format!("http://{addr}/mcp");
    let auth = "Bearer caller-token";

    // initialize (carry the caller's Authorization from the very first call)
    let init = client
        .post(&url)
        .header("Accept", "application/json, text/event-stream")
        .header("Authorization", auth)
        .json(&initialize_body())
        .send()
        .await
        .unwrap();
    let session_id = init
        .headers()
        .get("mcp-session-id")
        .and_then(|v| v.to_str().ok())
        .map(str::to_owned);

    let with_session = |req: reqwest::RequestBuilder| match &session_id {
        Some(s) => req.header("mcp-session-id", s.clone()),
        None => req,
    };

    with_session(
        client
            .post(&url)
            .header("Accept", "application/json, text/event-stream")
            .header("Authorization", auth)
            .json(&serde_json::json!({"jsonrpc": "2.0", "method": "notifications/initialized"})),
    )
    .send()
    .await
    .unwrap();

    // tools/call openvas_list_targets, carrying the caller's Authorization.
    let call = with_session(
        client
            .post(&url)
            .header("Accept", "application/json, text/event-stream")
            .header("Authorization", auth)
            .json(&serde_json::json!({
                "jsonrpc": "2.0", "id": 3, "method": "tools/call",
                "params": {"name": "openvas_list_targets", "arguments": {}}
            })),
    )
    .send()
    .await
    .unwrap();
    assert!(call.status().is_success(), "call failed: {}", call.status());

    let body = parse_payload(&call.text().await.unwrap());
    let result = &body["result"];
    assert_ne!(
        result["isError"],
        serde_json::Value::Bool(true),
        "got: {result}"
    );
    let text = result["content"][0]["text"].as_str().unwrap();
    let payload: serde_json::Value = serde_json::from_str(text).unwrap();
    assert_eq!(payload["targets"][0]["id"], "tg-1");
    // The gateway mock's `.expect(1)` verifies the forwarded token was used.
}

#[tokio::test]
async fn unlisted_host_header_is_rejected() {
    let (addr, _gateway) = spawn_http_server(&["mcp.internal.example"]).await;
    let client = reqwest::Client::new();

    let response = client
        .post(format!("http://{addr}/mcp"))
        .header("Accept", "application/json, text/event-stream")
        .json(&initialize_body())
        .send()
        .await
        .unwrap();
    // Host header is 127.0.0.1:<port>, which is not in the allow list.
    assert!(
        response.status().is_client_error(),
        "expected rejection, got {}",
        response.status()
    );
}
