//! Targets toolset: read surface (writes land in roadmap phase 3).

use rmcp::handler::server::wrapper::Parameters;
use rmcp::model::CallToolResult;
use rmcp::{ErrorData as McpError, tool, tool_router};
use serde::Serialize;

use crate::gateway::models::{Pagination, Target, TargetList};
use crate::mcp::error::gateway_tool_error;
use crate::mcp::server::GvmMcpServer;

use super::common::{GetByIdParams, ListParams, json_result};

/// Summarized list row: compact on purpose (LLM token budget). Full details
/// come from `openvas_get_target`.
#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
struct TargetRow {
    id: String,
    name: String,
    hosts: Vec<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    port_list: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    in_use: Option<bool>,
}

#[derive(Debug, Serialize)]
struct TargetListResult {
    targets: Vec<TargetRow>,
    pagination: Pagination,
}

fn summarize(target: Target) -> TargetRow {
    TargetRow {
        id: target.id,
        name: target.name,
        hosts: target.hosts,
        port_list: target.port_list.and_then(|pl| pl.name),
        in_use: target.in_use,
    }
}

#[tool_router(router = targets_router, vis = "pub(crate)")]
impl GvmMcpServer {
    /// List scan targets. Returns summarized rows plus pagination; use
    /// openvas_get_target for full details of one target.
    #[tool(
        name = "openvas_list_targets",
        annotations(title = "List targets", read_only_hint = true)
    )]
    pub async fn list_targets(
        &self,
        Parameters(params): Parameters<ListParams>,
    ) -> Result<CallToolResult, McpError> {
        let list: TargetList = match self
            .gateway()
            .get_json_query(&["targets"], &params.to_query())
            .await
        {
            Ok(list) => list,
            Err(err) => return Ok(gateway_tool_error("listing targets", &err)),
        };

        json_result(&TargetListResult {
            targets: list.data.into_iter().map(summarize).collect(),
            pagination: list.pagination,
        })
    }

    /// Get one scan target by UUID, including credentials, alive test and
    /// port list bindings.
    #[tool(
        name = "openvas_get_target",
        annotations(title = "Get target", read_only_hint = true)
    )]
    pub async fn get_target(
        &self,
        Parameters(params): Parameters<GetByIdParams>,
    ) -> Result<CallToolResult, McpError> {
        match self
            .gateway()
            .get_json::<Target>(&["targets", &params.id])
            .await
        {
            Ok(target) => json_result(&target),
            Err(err) => Ok(gateway_tool_error("fetching the target", &err)),
        }
    }
}
