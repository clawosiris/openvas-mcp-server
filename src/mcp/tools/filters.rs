//! Filters toolset: read surface over saved GMP filters.

use rmcp::handler::server::wrapper::Parameters;
use rmcp::model::CallToolResult;
use rmcp::{ErrorData as McpError, tool, tool_router};

use crate::mcp::server::GvmMcpServer;

use super::common::{GetByIdParams, ListParams, get_passthrough, list_summarized};

const ROW_KEYS: &[&str] = &["id", "name", "type", "term"];

#[tool_router(router = filters_router, vis = "pub(crate)")]
impl GvmMcpServer {
    /// List saved filters (reusable GMP filter expressions).
    #[tool(
        name = "openvas_list_filters",
        annotations(title = "List filters", read_only_hint = true)
    )]
    pub async fn list_filters(
        &self,
        Parameters(params): Parameters<ListParams>,
    ) -> Result<CallToolResult, McpError> {
        list_summarized(
            self.gateway(),
            "filters",
            "filters",
            ROW_KEYS,
            &params,
            "listing filters",
        )
        .await
    }

    /// Get one saved filter by UUID.
    #[tool(
        name = "openvas_get_filter",
        annotations(title = "Get filter", read_only_hint = true)
    )]
    pub async fn get_filter(
        &self,
        Parameters(params): Parameters<GetByIdParams>,
    ) -> Result<CallToolResult, McpError> {
        get_passthrough(
            self.gateway(),
            &["filters", &params.id],
            "fetching the filter",
        )
        .await
    }
}
