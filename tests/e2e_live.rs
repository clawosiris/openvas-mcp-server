//! Compose-gated end-to-end tests against a real rust-gvm-api gateway and
//! gvmd. Ignored by default; opt in with `--ignored` and the env below:
//!
//! ```bash
//! export GVM_E2E_GATEWAY_URL=http://localhost:8080
//! export GVM_USERNAME=admin GVM_PASSWORD=secret
//! cargo test --test e2e_live -- --ignored          # read-only checks
//! GVM_E2E_SCAN=1 cargo test --test e2e_live -- --ignored   # + scan lifecycle
//! ```
//!
//! These mirror the gateway's own e2e style: exercise the MCP tools exactly
//! as a client would, against live infrastructure, and clean up after.

#![cfg(test)]

use clap::Parser;
use gvm_mcp::config::{Cli, Config};
use gvm_mcp::mcp::GvmMcpServer;
use gvm_mcp::mcp::tools::common::{DeleteParams, GetByIdParams, ListParams};
use gvm_mcp::mcp::tools::targets::CreateTargetParams;
use gvm_mcp::mcp::tools::tasks::CreateTaskParams;
use rmcp::handler::server::wrapper::Parameters;
use rmcp::model::{CallToolResult, ContentBlock};

/// Build a server from the e2e environment, or skip (return None) when it is
/// not configured. Tests print a skip line and pass rather than fail, so the
/// suite is safe to run with `--ignored` on a machine without a stack.
fn live_server() -> Option<GvmMcpServer> {
    let gateway = std::env::var("GVM_E2E_GATEWAY_URL").ok()?;
    if std::env::var("GVM_USERNAME").is_err() || std::env::var("GVM_PASSWORD").is_err() {
        eprintln!("skipping: GVM_USERNAME / GVM_PASSWORD not set");
        return None;
    }
    let cli = Cli::parse_from(["gvm-mcp", "--gateway-url", &gateway]);
    let config = Config::from_cli(cli).expect("valid e2e config");
    Some(GvmMcpServer::new(config).expect("build server"))
}

fn text_of(result: &CallToolResult) -> String {
    result
        .content
        .iter()
        .filter_map(|block| match block {
            ContentBlock::Text(text) => Some(text.text.clone()),
            _ => None,
        })
        .collect::<Vec<_>>()
        .join("\n")
}

fn json_of(result: &CallToolResult) -> serde_json::Value {
    serde_json::from_str(&text_of(result)).expect("tool output is JSON")
}

fn assert_ok(result: &CallToolResult, what: &str) {
    assert_ne!(
        result.is_error,
        Some(true),
        "{what} failed: {}",
        text_of(result)
    );
}

#[tokio::test]
#[ignore = "requires a live gateway + gvmd (set GVM_E2E_GATEWAY_URL)"]
async fn connection_and_read_surface() {
    let Some(mcp) = live_server() else { return };

    let conn = mcp.test_connection().await.unwrap();
    assert_ok(&conn, "test_connection");
    let report = json_of(&conn);
    assert_eq!(report["gatewayStatus"], "ok");
    assert_eq!(report["sessionState"], "active");
    eprintln!("connected: gvmd GMP {}", report["gmpVersion"]);

    // A few list tools should return without error against a fresh stack.
    let targets = mcp
        .list_targets(Parameters(ListParams::default()))
        .await
        .unwrap();
    assert_ok(&targets, "list_targets");

    let configs = mcp
        .list_scan_configs(Parameters(ListParams::default()))
        .await
        .unwrap();
    assert_ok(&configs, "list_scan_configs");

    let scanners = mcp
        .list_scanners(Parameters(ListParams::default()))
        .await
        .unwrap();
    assert_ok(&scanners, "list_scanners");
    assert!(
        !json_of(&scanners)["scanners"]
            .as_array()
            .unwrap()
            .is_empty(),
        "a live stack should expose at least one scanner"
    );
}

/// Full lifecycle: create a target + task, start a scan against localhost,
/// wait for completion, then delete everything created. Gated behind
/// `GVM_E2E_SCAN=1` because it mutates gvmd and takes minutes.
#[tokio::test]
#[ignore = "requires a live stack and GVM_E2E_SCAN=1 (mutates gvmd, slow)"]
async fn scan_lifecycle() {
    if std::env::var("GVM_E2E_SCAN").is_err() {
        eprintln!("skipping: set GVM_E2E_SCAN=1 to run the mutating scan test");
        return;
    }
    let Some(mcp) = live_server() else { return };

    // Resolve a scan config ("Full and fast" or the first available) and a
    // scanner (the OpenVAS default or the first available).
    let configs = json_of(
        &mcp.list_scan_configs(Parameters(ListParams::default()))
            .await
            .unwrap(),
    );
    let scan_config_id = pick_id(&configs["scanConfigs"], "Full and fast");
    let scanners = json_of(
        &mcp.list_scanners(Parameters(ListParams::default()))
            .await
            .unwrap(),
    );
    let scanner_id = pick_id(&scanners["scanners"], "OpenVAS Default");

    let suffix = std::env::var("GVM_E2E_SUFFIX").unwrap_or_else(|_| "run".into());
    let target = mcp
        .create_target(Parameters(CreateTargetParams {
            name: format!("gvm-mcp-e2e-target-{suffix}"),
            hosts: vec!["127.0.0.1".into()],
            comment: Some("created by gvm-mcp e2e".into()),
            exclude_hosts: None,
            alive_test: Some("Consider Alive".into()),
            port_list_id: None,
            reverse_lookup_only: None,
            reverse_lookup_unify: None,
            ssh_credential_id: None,
            smb_credential_id: None,
            esxi_credential_id: None,
            snmp_credential_id: None,
        }))
        .await
        .unwrap();
    assert_ok(&target, "create_target");
    let target_id = json_of(&target)["id"].as_str().unwrap().to_owned();

    let task = mcp
        .create_task(Parameters(CreateTaskParams {
            name: format!("gvm-mcp-e2e-task-{suffix}"),
            comment: Some("created by gvm-mcp e2e".into()),
            target_id: target_id.clone(),
            scan_config_id,
            scanner_id,
            schedule_id: None,
            alert_ids: None,
            alterable: Some(true),
        }))
        .await
        .unwrap();
    assert_ok(&task, "create_task");
    let task_id = json_of(&task)["id"].as_str().unwrap().to_owned();

    let started = mcp
        .start_task(Parameters(GetByIdParams {
            id: task_id.clone(),
        }))
        .await
        .unwrap();
    assert_ok(&started, "start_task");

    // Poll until the task leaves the running states or we time out.
    let status = wait_for_done(&mcp, &task_id).await;
    eprintln!("final task status: {status}");
    assert!(
        matches!(status.as_str(), "Done" | "Stopped" | "Interrupted"),
        "unexpected terminal status: {status}"
    );

    // Cleanup: delete the task (ultimate), then the target.
    let del_task = mcp
        .delete_task(Parameters(DeleteParams {
            id: task_id,
            ultimate: Some(true),
        }))
        .await
        .unwrap();
    assert_ok(&del_task, "delete_task");
    let del_target = mcp
        .delete_target(Parameters(DeleteParams {
            id: target_id,
            ultimate: Some(true),
        }))
        .await
        .unwrap();
    assert_ok(&del_target, "delete_target");
}

/// Pick a resource UUID by preferred name, falling back to the first row.
fn pick_id(rows: &serde_json::Value, preferred: &str) -> String {
    let rows = rows.as_array().expect("summarized rows are an array");
    assert!(!rows.is_empty(), "no rows to pick from");
    rows.iter()
        .find(|row| row["name"] == preferred)
        .unwrap_or(&rows[0])["id"]
        .as_str()
        .expect("row has a string id")
        .to_owned()
}

/// Poll `openvas_get_task` until the status is terminal or ~10 minutes pass.
async fn wait_for_done(mcp: &GvmMcpServer, task_id: &str) -> String {
    for _ in 0..120 {
        let task = mcp
            .get_task(Parameters(GetByIdParams {
                id: task_id.to_owned(),
            }))
            .await
            .unwrap();
        assert_ok(&task, "get_task");
        let status = json_of(&task)["status"].as_str().unwrap_or("").to_owned();
        if !matches!(
            status.as_str(),
            "New" | "Requested" | "Queued" | "Running" | "Processing"
        ) {
            return status;
        }
        tokio::time::sleep(std::time::Duration::from_secs(5)).await;
    }
    "Timeout".into()
}
