//! Tasks toolset: read surface plus the full task lifecycle.

use rmcp::handler::server::wrapper::Parameters;
use rmcp::model::CallToolResult;
use rmcp::{ErrorData as McpError, schemars, tool, tool_router};
use serde::{Deserialize, Serialize};

use crate::gateway::models::{CreateTask, Pagination, ResourceCreated, Task, TaskAction, TaskList};
use crate::mcp::error::gateway_tool_error;
use crate::mcp::server::GvmMcpServer;

use super::common::{Body, DeleteParams, GetByIdParams, ListParams, json_result, update_resource};

/// Summarized list row: compact on purpose (LLM token budget). Full details
/// come from `openvas_get_task`.
#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
struct TaskRow {
    id: String,
    name: String,
    status: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    progress: Option<i32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    target: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    last_report_id: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    report_count: Option<i64>,
}

#[derive(Debug, Serialize)]
struct TaskListResult {
    tasks: Vec<TaskRow>,
    pagination: Pagination,
}

fn summarize(task: Task) -> TaskRow {
    TaskRow {
        id: task.id,
        name: task.name,
        status: task.status,
        progress: task.progress,
        target: task.target.and_then(|t| t.name),
        last_report_id: task.last_report.map(|r| r.id),
        report_count: task.report_count,
    }
}

/// Arguments for `openvas_create_task`.
#[derive(Debug, Deserialize, schemars::JsonSchema)]
pub struct CreateTaskParams {
    /// Task name
    pub name: String,
    /// Optional comment
    pub comment: Option<String>,
    /// UUID of the scan target
    pub target_id: String,
    /// UUID of the scan config (e.g. "Full and fast")
    pub scan_config_id: String,
    /// UUID of the scanner to run the task on
    pub scanner_id: String,
    /// Optional schedule UUID
    pub schedule_id: Option<String>,
    /// Optional alert UUIDs to attach
    pub alert_ids: Option<Vec<String>>,
    /// Whether the task stays modifiable after the first run
    pub alterable: Option<bool>,
}

#[tool_router(router = tasks_router, vis = "pub(crate)")]
impl GvmMcpServer {
    /// List scan tasks with status and progress. Returns summarized rows
    /// plus pagination; use openvas_get_task for full details of one task.
    #[tool(
        name = "openvas_list_tasks",
        annotations(title = "List tasks", read_only_hint = true)
    )]
    pub async fn list_tasks(
        &self,
        Parameters(params): Parameters<ListParams>,
    ) -> Result<CallToolResult, McpError> {
        let list: TaskList = match self
            .gateway()
            .get_json_query(&["tasks"], &params.to_query())
            .await
        {
            Ok(list) => list,
            Err(err) => return Ok(gateway_tool_error("listing tasks", &err)),
        };

        json_result(&TaskListResult {
            tasks: list.data.into_iter().map(summarize).collect(),
            pagination: list.pagination,
        })
    }

    /// Get one scan task by UUID, including scan config, scanner, schedule
    /// and report references.
    #[tool(
        name = "openvas_get_task",
        annotations(title = "Get task", read_only_hint = true)
    )]
    pub async fn get_task(
        &self,
        Parameters(params): Parameters<GetByIdParams>,
    ) -> Result<CallToolResult, McpError> {
        match self
            .gateway()
            .get_json::<Task>(&["tasks", &params.id])
            .await
        {
            Ok(task) => json_result(&task),
            Err(err) => Ok(gateway_tool_error("fetching the task", &err)),
        }
    }

    /// Create a scan task binding a target, scan config and scanner.
    /// Returns the new task's UUID; the task is not started automatically.
    #[tool(
        name = "openvas_create_task",
        annotations(
            title = "Create task",
            read_only_hint = false,
            destructive_hint = false
        )
    )]
    pub async fn create_task(
        &self,
        Parameters(params): Parameters<CreateTaskParams>,
    ) -> Result<CallToolResult, McpError> {
        let body = CreateTask {
            name: params.name,
            comment: params.comment,
            target_id: params.target_id,
            scan_config_id: params.scan_config_id,
            scanner_id: params.scanner_id,
            schedule_id: params.schedule_id,
            alert_ids: params.alert_ids,
            alterable: params.alterable,
            schedule_periods: None,
        };
        match self
            .gateway()
            .post_json::<ResourceCreated>(&["tasks"], &body)
            .await
        {
            Ok(created) => json_result(&created),
            Err(err) => Ok(gateway_tool_error("creating the task", &err)),
        }
    }

    /// Start a scan task. Returns the UUID of the report the run writes to.
    #[tool(
        name = "openvas_start_task",
        annotations(title = "Start task", read_only_hint = false, destructive_hint = false)
    )]
    pub async fn start_task(
        &self,
        Parameters(params): Parameters<GetByIdParams>,
    ) -> Result<CallToolResult, McpError> {
        match self
            .gateway()
            .post_action::<TaskAction>(&["tasks", &params.id, "start"])
            .await
        {
            Ok(action) => json_result(&action),
            Err(err) => Ok(gateway_tool_error("starting the task", &err)),
        }
    }

    /// Stop a running scan task.
    #[tool(
        name = "openvas_stop_task",
        annotations(title = "Stop task", read_only_hint = false, destructive_hint = false)
    )]
    pub async fn stop_task(
        &self,
        Parameters(params): Parameters<GetByIdParams>,
    ) -> Result<CallToolResult, McpError> {
        match self
            .gateway()
            .post_action_empty(&["tasks", &params.id, "stop"])
            .await
        {
            Ok(()) => json_result(&serde_json::json!({ "stopped": true, "id": params.id })),
            Err(err) => Ok(gateway_tool_error("stopping the task", &err)),
        }
    }

    /// Resume a stopped scan task. Returns the UUID of the report the
    /// resumed run writes to.
    #[tool(
        name = "openvas_resume_task",
        annotations(
            title = "Resume task",
            read_only_hint = false,
            destructive_hint = false
        )
    )]
    pub async fn resume_task(
        &self,
        Parameters(params): Parameters<GetByIdParams>,
    ) -> Result<CallToolResult, McpError> {
        match self
            .gateway()
            .post_action::<TaskAction>(&["tasks", &params.id, "resume"])
            .await
        {
            Ok(action) => json_result(&action),
            Err(err) => Ok(gateway_tool_error("resuming the task", &err)),
        }
    }

    /// Delete a scan task (to the trashcan by default; `ultimate` deletes
    /// permanently).
    #[tool(
        name = "openvas_delete_task",
        annotations(title = "Delete task", read_only_hint = false, destructive_hint = true)
    )]
    pub async fn delete_task(
        &self,
        Parameters(params): Parameters<DeleteParams>,
    ) -> Result<CallToolResult, McpError> {
        match self
            .gateway()
            .delete(&["tasks", &params.id], &params.to_query())
            .await
        {
            Ok(()) => json_result(&serde_json::json!({ "deleted": true, "id": params.id })),
            Err(err) => Ok(gateway_tool_error("deleting the task", &err)),
        }
    }

    /// Update a scan task's bindings or metadata. Idempotent (PUT): omitted
    /// fields stay unchanged; fails with 409 while the task is running.
    #[tool(
        name = "openvas_update_task",
        annotations(title = "Update task", read_only_hint = false, destructive_hint = true)
    )]
    pub async fn update_task(
        &self,
        Parameters(params): Parameters<UpdateTaskParams>,
    ) -> Result<CallToolResult, McpError> {
        let body = Body::new()
            .set_opt("name", params.name)
            .set_opt("comment", params.comment)
            .set_opt("targetId", params.target_id)
            .set_opt("scanConfigId", params.scan_config_id)
            .set_opt("scannerId", params.scanner_id)
            .set_opt("scheduleId", params.schedule_id)
            .set_opt("alertIds", params.alert_ids)
            .set_opt("schedulePeriods", params.schedule_periods);
        update_resource(
            self.gateway(),
            &["tasks", &params.id],
            body,
            "updating the task",
        )
        .await
    }
}

/// Arguments for `openvas_update_task`: all fields optional, omitted fields
/// stay unchanged.
#[derive(Debug, Deserialize, schemars::JsonSchema)]
pub struct UpdateTaskParams {
    /// UUID of the task to update
    pub id: String,
    pub name: Option<String>,
    pub comment: Option<String>,
    /// Replacement target UUID
    pub target_id: Option<String>,
    /// Replacement scan config UUID
    pub scan_config_id: Option<String>,
    /// Replacement scanner UUID
    pub scanner_id: Option<String>,
    /// Replacement schedule UUID
    pub schedule_id: Option<String>,
    /// Replacement alert UUIDs
    pub alert_ids: Option<Vec<String>>,
    pub schedule_periods: Option<i32>,
}
