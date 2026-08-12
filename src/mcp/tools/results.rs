//! Results toolset: read surface over individual scan findings.

use rmcp::handler::server::wrapper::Parameters;
use rmcp::model::CallToolResult;
use rmcp::{ErrorData as McpError, tool, tool_router};

use crate::mcp::server::GvmMcpServer;

use super::common::{GetByIdParams, ListParams, get_passthrough, list_summarized};

const ROW_KEYS: &[&str] = &[
    "id",
    "name",
    "host",
    "port",
    "severity",
    "threat",
    "occurrences",
];

#[tool_router(router = results_router, vis = "pub(crate)")]
impl GvmMcpServer {
    /// List individual scan results (findings) across reports. Supports GMP
    /// filter expressions like `severity>7 and host=10.0.0.5`.
    #[tool(
        name = "openvas_list_results",
        annotations(title = "List results", read_only_hint = true)
    )]
    pub async fn list_results(
        &self,
        Parameters(params): Parameters<ListParams>,
    ) -> Result<CallToolResult, McpError> {
        list_summarized(
            self.gateway(),
            "results",
            "results",
            ROW_KEYS,
            &params,
            "listing results",
        )
        .await
    }

    /// Get one scan result by UUID, including the full finding description
    /// and NVT reference.
    #[tool(
        name = "openvas_get_result",
        annotations(title = "Get result", read_only_hint = true)
    )]
    pub async fn get_result(
        &self,
        Parameters(params): Parameters<GetByIdParams>,
    ) -> Result<CallToolResult, McpError> {
        get_passthrough(
            self.gateway(),
            &["results", &params.id],
            "fetching the result",
        )
        .await
    }
}
