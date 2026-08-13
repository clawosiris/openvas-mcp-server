//! Streamable-HTTP transport tests: a real TCP listener served by the MCP
//! server, driven with plain JSON-RPC over HTTP.

mod support;

use gvm_mcp::mcp::GvmMcpServer;
use support::config_for;
use wiremock::MockServer;

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
