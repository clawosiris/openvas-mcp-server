//! Tests for toolset selection and read-only gating: what the server
//! actually exposes, per configuration.

mod support;

use gvm_mcp::mcp::GvmMcpServer;
use support::config_with_args;
use wiremock::MockServer;

#[tokio::test]
async fn default_exposes_system_targets_and_tasks_tools() {
    let server = MockServer::start().await;
    let mcp = GvmMcpServer::new(config_with_args(&server, &[])).unwrap();
    let names = mcp.tool_names();

    for expected in [
        "openvas_test_connection",
        "openvas_get_version",
        "openvas_list_targets",
        "openvas_get_target",
        "openvas_list_tasks",
        "openvas_get_task",
        "openvas_create_task",
        "openvas_start_task",
        "openvas_stop_task",
        "openvas_resume_task",
        "openvas_delete_task",
    ] {
        assert!(names.contains(&expected.to_string()), "missing {expected}");
    }
}

#[tokio::test]
async fn read_only_hides_every_mutating_tool() {
    let server = MockServer::start().await;
    let mcp = GvmMcpServer::new(config_with_args(&server, &["--read-only"])).unwrap();
    let names = mcp.tool_names();

    for read_tool in [
        "openvas_test_connection",
        "openvas_list_targets",
        "openvas_list_tasks",
        "openvas_get_task",
    ] {
        assert!(
            names.contains(&read_tool.to_string()),
            "missing {read_tool}"
        );
    }
    for write_tool in [
        "openvas_create_task",
        "openvas_start_task",
        "openvas_stop_task",
        "openvas_resume_task",
        "openvas_delete_task",
    ] {
        assert!(
            !names.contains(&write_tool.to_string()),
            "{write_tool} must be hidden in read-only mode"
        );
    }
}

#[tokio::test]
async fn toolset_selection_limits_exposure() {
    let server = MockServer::start().await;
    let mcp = GvmMcpServer::new(config_with_args(&server, &["--toolsets", "targets"])).unwrap();
    let names = mcp.tool_names();

    assert!(names.contains(&"openvas_list_targets".to_string()));
    // System rides along for openvas_test_connection.
    assert!(names.contains(&"openvas_test_connection".to_string()));
    assert!(
        !names.iter().any(|name| name.contains("task")),
        "task tools must be absent, got: {names:?}"
    );
}

#[tokio::test]
async fn read_only_and_selection_compose() {
    let server = MockServer::start().await;
    let mcp = GvmMcpServer::new(config_with_args(
        &server,
        &["--toolsets", "tasks", "--read-only"],
    ))
    .unwrap();
    let names = mcp.tool_names();

    assert!(names.contains(&"openvas_list_tasks".to_string()));
    assert!(names.contains(&"openvas_get_task".to_string()));
    assert!(!names.contains(&"openvas_start_task".to_string()));
    assert!(!names.contains(&"openvas_list_targets".to_string()));
}
