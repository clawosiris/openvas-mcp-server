//! Reports toolset: read surface (drill-down pages and exports land in
//! roadmap phase 4).

use rmcp::handler::server::wrapper::Parameters;
use rmcp::model::CallToolResult;
use rmcp::{ErrorData as McpError, tool, tool_router};

use crate::mcp::server::GvmMcpServer;

use super::common::{
    DeleteParams, GetByIdParams, ListParams, delete_resource, get_passthrough, list_summarized,
};

const ROW_KEYS: &[&str] = &[
    "id",
    "task",
    "scanStart",
    "scanEnd",
    "severity",
    "resultCount",
];

#[tool_router(router = reports_router, vis = "pub(crate)")]
impl GvmMcpServer {
    /// List scan reports with severity and result counts.
    #[tool(
        name = "openvas_list_reports",
        annotations(title = "List reports", read_only_hint = true)
    )]
    pub async fn list_reports(
        &self,
        Parameters(params): Parameters<ListParams>,
    ) -> Result<CallToolResult, McpError> {
        list_summarized(
            self.gateway(),
            "reports",
            "reports",
            ROW_KEYS,
            &params,
            "listing reports",
        )
        .await
    }

    /// Get one scan report by UUID (summary level: task, timing, severity,
    /// result counts).
    #[tool(
        name = "openvas_get_report",
        annotations(title = "Get report", read_only_hint = true)
    )]
    pub async fn get_report(
        &self,
        Parameters(params): Parameters<GetByIdParams>,
    ) -> Result<CallToolResult, McpError> {
        get_passthrough(
            self.gateway(),
            &["reports", &params.id],
            "fetching the report",
        )
        .await
    }

    /// Delete a scan report (to the trashcan by default; `ultimate` deletes
    /// permanently). The task itself is not affected.
    #[tool(
        name = "openvas_delete_report",
        annotations(
            title = "Delete report",
            read_only_hint = false,
            destructive_hint = true
        )
    )]
    pub async fn delete_report(
        &self,
        Parameters(params): Parameters<DeleteParams>,
    ) -> Result<CallToolResult, McpError> {
        delete_resource(self.gateway(), "reports", &params, "deleting the report").await
    }
}
