//! Report-formats toolset: read surface.

use rmcp::handler::server::wrapper::Parameters;
use rmcp::model::CallToolResult;
use rmcp::{ErrorData as McpError, tool, tool_router};

use crate::mcp::server::GvmMcpServer;

use super::common::{GetByIdParams, ListParams, get_passthrough, list_summarized};

const ROW_KEYS: &[&str] = &[
    "id",
    "name",
    "contentType",
    "extension",
    "active",
    "predefined",
];

#[tool_router(router = report_formats_router, vis = "pub(crate)")]
impl GvmMcpServer {
    /// List report formats available for exporting reports (PDF, CSV, XML…).
    #[tool(
        name = "openvas_list_report_formats",
        annotations(title = "List report formats", read_only_hint = true)
    )]
    pub async fn list_report_formats(
        &self,
        Parameters(params): Parameters<ListParams>,
    ) -> Result<CallToolResult, McpError> {
        list_summarized(
            self.gateway(),
            "report-formats",
            "reportFormats",
            ROW_KEYS,
            &params,
            "listing report formats",
        )
        .await
    }

    /// Get one report format by UUID.
    #[tool(
        name = "openvas_get_report_format",
        annotations(title = "Get report format", read_only_hint = true)
    )]
    pub async fn get_report_format(
        &self,
        Parameters(params): Parameters<GetByIdParams>,
    ) -> Result<CallToolResult, McpError> {
        get_passthrough(
            self.gateway(),
            &["report-formats", &params.id],
            "fetching the report format",
        )
        .await
    }
}
