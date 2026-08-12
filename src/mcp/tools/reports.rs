//! Reports toolset: read surface (drill-down pages and exports land in
//! roadmap phase 4).

use rmcp::handler::server::wrapper::Parameters;
use rmcp::model::CallToolResult;
use rmcp::{ErrorData as McpError, tool, tool_router};

use crate::mcp::server::GvmMcpServer;

use super::common::{GetByIdParams, ListParams, get_passthrough, list_summarized};

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
}
